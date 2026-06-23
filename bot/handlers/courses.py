# handlers/courses.py
import os

from aiogram import Bot, Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import (
    add_payment,
    get_user,
    get_accounting_staff_ids,
    get_user_interface_lang,
)
from utils.states import (
    OrderCourse,
    LangCB,
    PackCB,
    AdminApproveCB,
    AdminRejectCB,
    AccountingPaymentCB,
)
from utils.data import LANGUAGES, PACKAGES
from utils.i18n import all_texts

courses_router = Router()


# ==========================================
# LOCAL TRANSLATIONS FOR COURSES.PY
# ==========================================

LOCAL_TEXTS = {
    "choose_course_lang": {
        "uz": "Qaysi tilni o'rganmoqchisiz? Tanlang:",
        "ru": "Какой язык вы хотите изучать? Выберите:",
        "en": "Which language would you like to study? Choose:",
    },
    "back_to_langs": {
        "uz": "🔙 Tillarga qaytish",
        "ru": "🔙 Назад к языкам",
        "en": "🔙 Back to languages",
    },
    "back": {
        "uz": "🔙 Orqaga",
        "ru": "🔙 Назад",
        "en": "🔙 Back",
    },
    "selected_language": {
        "uz": "📚 Tanlangan til: <b>{lang_name}</b>\n\nO'qish formatini (Paketni) tanlang:\n<i>Guruh darslarida max 10 kishi bo'ladi. Individual darsda faqat siz va ustoz.</i>",
        "ru": "📚 Выбранный язык: <b>{lang_name}</b>\n\nВыберите формат обучения:\n<i>В групповых занятиях максимум 10 человек. Индивидуально — только вы и преподаватель.</i>",
        "en": "📚 Selected language: <b>{lang_name}</b>\n\nChoose your study format:\n<i>Group lessons have up to 10 people. Individual lessons are only you and the teacher.</i>",
    },
    "your_choice": {
        "uz": "📝 <b>Sizning tanlovingiz:</b>\nTil: {lang_name}\nPaket: {pack_name}\n\nTo'lovni qanday usulda amalga oshirasiz?",
        "ru": "📝 <b>Ваш выбор:</b>\nЯзык: {lang_name}\nПакет: {pack_name}\n\nКак вы хотите оплатить?",
        "en": "📝 <b>Your choice:</b>\nLanguage: {lang_name}\nPackage: {pack_name}\n\nHow would you like to pay?",
    },
    "pay_card": {
        "uz": "💳 Karta orqali",
        "ru": "💳 Картой",
        "en": "💳 By card",
    },
    "pay_cash": {
        "uz": "💵 Naqd pul orqali",
        "ru": "💵 Наличными",
        "en": "💵 By cash",
    },
    "card_payment": {
        "uz": "💳 <b>Karta orqali to'lov</b>\n\nKarta raqami: <code>8600 1234 5678 9012</code>\nQabul qiluvchi: Visa & Language Consulting\n\nTo'lovni amalga oshirgach, <b>chek rasmini (skrinshot) yoki PDF faylini</b> shu yerga yuboring:",
        "ru": "💳 <b>Оплата картой</b>\n\nНомер карты: <code>8600 1234 5678 9012</code>\nПолучатель: Visa & Language Consulting\n\nПосле оплаты отправьте сюда <b>фото чека, скриншот или PDF-файл</b>:",
        "en": "💳 <b>Card payment</b>\n\nCard number: <code>8600 1234 5678 9012</code>\nRecipient: Visa & Language Consulting\n\nAfter payment, please send <b>a receipt photo, screenshot, or PDF file</b> here:",
    },
    "cash_payment_info": {
        "uz": "🏢 <b>Ofisimiz manzili:</b> Sirdaryo viloyati, Guliston shahri, IT Park binosi.\n\nKelib to'lovni amalga oshirganingizdan so'ng, accounting/admin tizimda tasdiqlaydi va siz guruhga qo'shilasiz.",
        "ru": "🏢 <b>Адрес офиса:</b> Сырдарьинская область, город Гулистан, здание IT Park.\n\nПосле оплаты в офисе бухгалтерия/администратор подтвердит оплату в системе, и вы будете добавлены в группу.",
        "en": "🏢 <b>Office address:</b> Sirdaryo region, Gulistan city, IT Park building.\n\nAfter you make the payment at the office, accounting/admin will confirm it in the system and you will be added to the group.",
    },
    "receipt_accepted": {
        "uz": "✅ <b>Chek qabul qilindi va bazaga saqlandi!</b>\n\nAccounting/admin to'lovni tekshirib, tez orada sizga guruh havolasini yuboradi. Iltimos, kuting.",
        "ru": "✅ <b>Чек принят и сохранён в базе!</b>\n\nБухгалтерия/администратор проверит оплату и скоро отправит вам ссылку на группу. Пожалуйста, ожидайте.",
        "en": "✅ <b>Your receipt has been received and saved!</b>\n\nAccounting/admin will check the payment and send you the group link soon. Please wait.",
    },
}


COURSE_LANGUAGES_I18N = {
    "eng": {
        "uz": "🇬🇧 Ingliz tili",
        "ru": "🇬🇧 Английский язык",
        "en": "🇬🇧 English",
    },
    "rus": {
        "uz": "🇷🇺 Rus tili",
        "ru": "🇷🇺 Русский язык",
        "en": "🇷🇺 Russian",
    },
    "ger": {
        "uz": "🇩🇪 Nemis tili",
        "ru": "🇩🇪 Немецкий язык",
        "en": "🇩🇪 German",
    },
    "ara": {
        "uz": "🇸🇦 Arab tili",
        "ru": "🇸🇦 Арабский язык",
        "en": "🇸🇦 Arabic",
    },
}


PACKAGES_I18N = {
    "group": {
        "uz": "👥 Guruh (10 kishi) - 3 oylik",
        "ru": "👥 Группа (10 человек) - 3 месяца",
        "en": "👥 Group (10 people) - 3 months",
    },
    "solo": {
        "uz": "👤 Individual (Yakka tartibda)",
        "ru": "👤 Индивидуально",
        "en": "👤 Individual",
    },
}


def ct(key: str, lang: str = "uz", **kwargs) -> str:
    item = LOCAL_TEXTS.get(key, {})
    text = item.get(lang) or item.get("uz") or key
    return text.format(**kwargs)


async def user_lang(user_id: int) -> str:
    lang = await get_user_interface_lang(user_id)
    return lang or "uz"


def course_lang_name(code: str, lang: str = "uz") -> str:
    item = COURSE_LANGUAGES_I18N.get(code)
    if item:
        return item.get(lang) or item.get("uz")

    return LANGUAGES.get(code, code)


def package_name(pack_type: str, lang: str = "uz") -> str:
    item = PACKAGES_I18N.get(pack_type)
    if item:
        return item.get(lang) or item.get("uz")

    return PACKAGES.get(pack_type, pack_type)


def languages_keyboard():
    builder = InlineKeyboardBuilder()

    for code in LANGUAGES.keys():
        builder.button(
            text=course_lang_name(code, "uz"),
            callback_data=LangCB(code=code)
        )

    builder.adjust(2)
    return builder.as_markup()


def payment_notification_keyboard(payment_id: int):
    """
    Notification ichidagi tugmalar.

    🔎 Ko'rish / Detail — keyingi stepda accounting.py ushlaydi.
    ✅ / ❌ — hozirgi eski admin.py approve/reject flow bilan compatibility uchun qoldi.
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🔎 Ko‘rish / Detail",
        callback_data=AccountingPaymentCB(payment_id=payment_id, action="detail")
    )
    builder.button(
        text="✅ Tasdiqlash",
        callback_data=AdminApproveCB(payment_id=payment_id)
    )
    builder.button(
        text="❌ Rad etish",
        callback_data=AdminRejectCB(payment_id=payment_id)
    )

    builder.adjust(1, 2)
    return builder.as_markup()


# ==========================================
# 1. KURS TUGMASI BOSILGANDA
# ==========================================

@courses_router.message(F.text.in_(all_texts("courses")))
async def show_languages(message: types.Message):
    lang = await user_lang(message.from_user.id)

    await message.answer(
        ct("choose_course_lang", lang),
        reply_markup=languages_keyboard()
    )


# ==========================================
# 2. TIL TANLANGANDA
# ==========================================

@courses_router.callback_query(LangCB.filter())
async def show_packages(callback: types.CallbackQuery, callback_data: LangCB):
    lang = await user_lang(callback.from_user.id)

    lang_code = callback_data.code
    lang_name = course_lang_name(lang_code, lang)

    builder = InlineKeyboardBuilder()

    for p_type in PACKAGES.keys():
        builder.button(
            text=package_name(p_type, lang),
            callback_data=PackCB(lang_code=lang_code, pack_type=p_type)
        )

    builder.button(
        text=ct("back_to_langs", lang),
        callback_data="back_to_langs"
    )
    builder.adjust(1)

    await callback.message.edit_text(
        ct("selected_language", lang, lang_name=lang_name),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


# ==========================================
# TILLARGA QAYTISH
# ==========================================

@courses_router.callback_query(F.data == "back_to_langs")
async def back_to_langs(callback: types.CallbackQuery):
    lang = await user_lang(callback.from_user.id)

    await callback.message.edit_text(
        ct("choose_course_lang", lang),
        reply_markup=languages_keyboard()
    )


# ==========================================
# 3. PAKET TANLANGANDA
# ==========================================

@courses_router.callback_query(PackCB.filter())
async def show_payment_options(
    callback: types.CallbackQuery,
    callback_data: PackCB,
    state: FSMContext
):
    lang = await user_lang(callback.from_user.id)

    lang_name = course_lang_name(callback_data.lang_code, lang)
    pack_name = package_name(callback_data.pack_type, lang)

    await state.update_data(
        selected_lang=lang_name,
        selected_pack=pack_name
    )

    builder = InlineKeyboardBuilder()
    builder.button(text=ct("pay_card", lang), callback_data="pay_card")
    builder.button(text=ct("pay_cash", lang), callback_data="pay_cash")
    builder.button(
        text=ct("back", lang),
        callback_data=LangCB(code=callback_data.lang_code).pack()
    )
    builder.adjust(2, 1)

    await callback.message.edit_text(
        ct(
            "your_choice",
            lang,
            lang_name=lang_name,
            pack_name=pack_name
        ),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


# ==========================================
# 4. KARTA ORQALI TO'LOV
# ==========================================

@courses_router.callback_query(F.data == "pay_card")
async def pay_card(callback: types.CallbackQuery, state: FSMContext):
    lang = await user_lang(callback.from_user.id)

    await callback.message.edit_text(
        ct("card_payment", lang),
        parse_mode="HTML"
    )

    await state.set_state(OrderCourse.receipt)


# ==========================================
# 5. NAQD PUL ORQALI TO'LOV
# ==========================================

@courses_router.callback_query(F.data == "pay_cash")
async def pay_cash(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    lang = await user_lang(callback.from_user.id)

    data = await state.get_data()
    course_info = f"{data['selected_lang']} ({data['selected_pack']})"

    payment_id = await add_payment(
        callback.from_user.id,
        course_info,
        "cash",
        None
    )
    user_data = await get_user(callback.from_user.id)

    staff_ids = await get_accounting_staff_ids()

    if staff_ids:
        admin_text = (
            f"💵 <b>Yangi NAQD to'lov so'rovi!</b>\n\n"
            f"🆔 Payment ID: <code>{payment_id}</code>\n"
            f"👤 O'quvchi: {user_data['full_name']}\n"
            f"📞 Telefon: {user_data['phone']}\n"
            f"📚 Kurs: {course_info}\n\n"
            f"📌 Status: <b>pending</b>"
        )

        for staff_id in staff_ids:
            try:
                await bot.send_message(
                    chat_id=staff_id,
                    text=admin_text,
                    parse_mode="HTML",
                    reply_markup=payment_notification_keyboard(payment_id)
                )
            except Exception:
                pass

    await callback.message.edit_text(
        ct("cash_payment_info", lang),
        parse_mode="HTML"
    )

    await state.clear()


# ==========================================
# 6. CHEK RASMI / PDF KELGANDA
# ==========================================

@courses_router.message(OrderCourse.receipt, F.photo | F.document)
async def process_receipt(message: types.Message, state: FSMContext, bot: Bot):
    lang = await user_lang(message.from_user.id)

    data = await state.get_data()
    course_info = f"{data['selected_lang']} ({data['selected_pack']})"

    os.makedirs("media/receipts", exist_ok=True)

    receipt_type = "photo"
    original_filename = None

    if message.photo:
        file_id = message.photo[-1].file_id
        ext = ".jpg"
        receipt_type = "photo"
        original_filename = "receipt.jpg"
    else:
        file_id = message.document.file_id
        original_filename = message.document.file_name or "receipt_file"
        ext = os.path.splitext(original_filename)[1] or ".bin"
        receipt_type = "document"

    file = await bot.get_file(file_id)
    file_path = f"media/receipts/{message.from_user.id}_{file_id[:10]}{ext}"

    await bot.download_file(file.file_path, file_path)

    payment_id = await add_payment(
        message.from_user.id,
        course_info,
        "card",
        file_path
    )
    user_data = await get_user(message.from_user.id)

    staff_ids = await get_accounting_staff_ids()

    if staff_ids:
        admin_text = (
            f"💳 <b>Karta orqali yangi to'lov!</b>\n\n"
            f"🆔 Payment ID: <code>{payment_id}</code>\n"
            f"👤 O'quvchi: {user_data['full_name']}\n"
            f"📞 Telefon: {user_data['phone']}\n"
            f"📚 Kurs: {course_info}\n"
            f"📎 Fayl: {original_filename}\n\n"
            f"📌 Status: <b>pending</b>"
        )

        receipt_file = FSInputFile(file_path, filename=original_filename)

        for staff_id in staff_ids:
            try:
                if receipt_type == "photo":
                    await bot.send_photo(
                        chat_id=staff_id,
                        photo=receipt_file,
                        caption=admin_text,
                        parse_mode="HTML",
                        reply_markup=payment_notification_keyboard(payment_id)
                    )
                else:
                    await bot.send_document(
                        chat_id=staff_id,
                        document=receipt_file,
                        caption=admin_text,
                        parse_mode="HTML",
                        reply_markup=payment_notification_keyboard(payment_id)
                    )
            except Exception:
                pass

    await message.answer(
        ct("receipt_accepted", lang),
        parse_mode="HTML"
    )

    await state.clear()