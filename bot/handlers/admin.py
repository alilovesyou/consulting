# handlers/admin.py
from html import escape
import json

from aiogram import Router, types, F
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.data import LANGUAGES
from utils.i18n import t, all_texts

from database.db import (
    update_teacher_status,
    get_all_teachers,
    create_new_group,
    get_bot_statistics,
    get_all_groups,
    change_group_teacher,
    delete_group,
    get_kick_request,
    update_kick_request_status,
    remove_student_from_group,
    get_user_role,
    log_admin_action,
    get_superadmin_ids,
    get_api_superadmin_admin_actions,
    get_api_superadmin_teacher_groups,
    get_api_superadmin_group_students,
    get_api_superadmin_student_results,
    get_api_superadmin_all_results,
    get_api_superadmin_teachers_by_language,
    get_api_superadmin_student_profile,
    get_user_interface_lang,
    get_staff_users,
    get_recent_users_for_role_assignment,
    set_user_role,
    get_admin_action_detail,
)
from utils.states import (
    AdminGroupCB,
    AdminTeacherApproveCB,
    AdminTeacherRejectCB,
    CreateGroup,
    AssignTeacherCB,
    KickApproveCB,
    KickRejectCB,
    StaffListCB,
    StaffUserCB,
    StaffRoleCB,
    StaffManualRoleState,
    StaffManualRoleCB,
)

admin_router = Router()


# ==========================================
# LOCAL TRANSLATIONS FOR ADMIN.PY
# ==========================================

LOCAL_TEXTS = {
    "only_superadmin": {
        "uz": "⛔ Bu bo'lim faqat Superadmin uchun.",
        "ru": "⛔ Этот раздел доступен только Superadmin.",
        "en": "⛔ This section is only for Superadmin.",
    },
    "payment_not_found": {
        "uz": "To'lov so'rovi topilmadi.",
        "ru": "Запрос оплаты не найден.",
        "en": "Payment request was not found.",
    },
    "already_processed": {
        "uz": "Bu so'rov allaqachon ko'rib chiqilgan!",
        "ru": "Этот запрос уже был обработан!",
        "en": "This request has already been processed!",
    },
    "no_active_groups": {
        "uz": "Bazada hech qanday faol guruh yo'q! Avval guruh qo'shing.",
        "ru": "В базе нет активных групп! Сначала создайте группу.",
        "en": "There are no active groups in the database! Please create a group first.",
    },
    "group_not_found": {
        "uz": "Guruh topilmadi.",
        "ru": "Группа не найдена.",
        "en": "Group not found.",
    },
    "choose_group_for_student": {
        "uz": "✅ O'quvchini qaysi guruhga qo'shamiz?",
        "ru": "✅ В какую группу добавить студента?",
        "en": "✅ Which group should the student be added to?",
    },
    "payment_rejected_status": {
        "uz": "❌ <b>Holat: RAD ETILDI</b>",
        "ru": "❌ <b>Статус: ОТКЛОНЕНО</b>",
        "en": "❌ <b>Status: REJECTED</b>",
    },
    "payment_approved_status": {
        "uz": "✅ <b>Holat: TASDIQLANDI</b>\nBiriktirildi: {group_name}",
        "ru": "✅ <b>Статус: ПОДТВЕРЖДЕНО</b>\nНазначена группа: {group_name}",
        "en": "✅ <b>Status: APPROVED</b>\nAssigned to: {group_name}",
    },
    "student_payment_rejected": {
        "uz": "❌ Kechirasiz, sizning to'lov chekingiz ma'muriyat tomonidan tasdiqlanmadi (Chek xato yoki noaniq bo'lishi mumkin).\n\n<b>Qaytadan urinib ko'rish yoki boshqa chek yuborish uchun pastdagi 📚 Kurslar menyusidan qaytadan to'lov qiling.</b>",
        "ru": "❌ К сожалению, ваш чек оплаты не был подтверждён администрацией. Возможно, чек неверный или неясный.\n\n<b>Чтобы попробовать снова или отправить другой чек, заново оформите оплату через меню 📚 Курсы.</b>",
        "en": "❌ Sorry, your payment receipt was not approved by the administration. The receipt may be incorrect or unclear.\n\n<b>To try again or send another receipt, please make the payment again through the 📚 Courses menu.</b>",
    },
    "student_payment_approved": {
        "uz": "🎉 <b>Tabriklaymiz! Sizning to'lovingiz tasdiqlandi!</b>\n\nSiz <b>{group_name}</b> guruhiga biriktirildingiz.\n\nGuruhga qo'shilish havolasi 👇\n{group_link}",
        "ru": "🎉 <b>Поздравляем! Ваша оплата подтверждена!</b>\n\nВы добавлены в группу <b>{group_name}</b>.\n\nСсылка для вступления в группу 👇\n{group_link}",
        "en": "🎉 <b>Congratulations! Your payment has been approved!</b>\n\nYou have been assigned to <b>{group_name}</b>.\n\nGroup invitation link 👇\n{group_link}",
    },
    "teacher_rejected_status": {
        "uz": "❌ <b>QAROR: RAD ETILDI</b>",
        "ru": "❌ <b>РЕШЕНИЕ: ОТКЛОНЕНО</b>",
        "en": "❌ <b>DECISION: REJECTED</b>",
    },
    "teacher_approved_status": {
        "uz": "✅ <b>QAROR: QABUL QILINDI</b>",
        "ru": "✅ <b>РЕШЕНИЕ: ПРИНЯТО</b>",
        "en": "✅ <b>DECISION: APPROVED</b>",
    },
    "teacher_rejected_message": {
        "uz": "❌ Kechirasiz, sizning ustozlik arizangiz ma'muriyat tomonidan tasdiqlanmadi.",
        "ru": "❌ К сожалению, ваша заявка преподавателя не была подтверждена администрацией.",
        "en": "❌ Sorry, your teacher application was not approved by the administration.",
    },
    "teacher_approved_message": {
        "uz": "🎉 <b>Tabriklaymiz! Siz ishga qabul qilindingiz.</b>\n\nSizga Ustoz maqomi berildi. Iltimos, /start buyrug'ini bosib o'z ish panelingizga kiring.",
        "ru": "🎉 <b>Поздравляем! Вы приняты на работу.</b>\n\nВам выдан статус преподавателя. Нажмите /start, чтобы открыть рабочую панель.",
        "en": "🎉 <b>Congratulations! You have been accepted.</b>\n\nYou have been given Teacher status. Please press /start to open your work panel.",
    },
    "statistics_title": {
        "uz": "📊 <b>Platforma Statistikasi:</b>",
        "ru": "📊 <b>Статистика платформы:</b>",
        "en": "📊 <b>Platform Statistics:</b>",
    },
    "students_total": {
        "uz": "👨‍🎓 Jami O'quvchilar",
        "ru": "👨‍🎓 Всего студентов",
        "en": "👨‍🎓 Total students",
    },
    "teachers_total": {
        "uz": "👨‍🏫 Jami Ustozlar",
        "ru": "👨‍🏫 Всего преподавателей",
        "en": "👨‍🏫 Total teachers",
    },
    "groups_total": {
        "uz": "📚 Faol Guruhlar",
        "ru": "📚 Активные группы",
        "en": "📚 Active groups",
    },
    "create_group_name": {
        "uz": "📝 Yangi guruh nomini kiriting:\n<i>(Masalan: IELTS - N1 yoki Dasturlash - 1)</i>",
        "ru": "📝 Введите название новой группы:\n<i>(Например: IELTS - N1 или Programming - 1)</i>",
        "en": "📝 Enter the new group name:\n<i>(Example: IELTS - N1 or Programming - 1)</i>",
    },
    "choose_group_language": {
        "uz": "Qaysi til/fan o'qitiladi?",
        "ru": "Какой язык/предмет будет преподаваться?",
        "en": "Which language/subject will be taught?",
    },
    "language_selected": {
        "uz": "Til tanlandi: {language} ✅",
        "ru": "Язык выбран: {language} ✅",
        "en": "Language selected: {language} ✅",
    },
    "capacity_request": {
        "uz": "👥 Guruh sig'imi (Limit) qancha bo'ladi? Faqat raqam yozing:\n<i>(Masalan: 15)</i>",
        "ru": "👥 Какой будет лимит группы? Введите только число:\n<i>(Например: 15)</i>",
        "en": "👥 What is the group capacity? Enter only a number:\n<i>(Example: 15)</i>",
    },
    "digits_only": {
        "uz": "Iltimos, faqat raqam kiriting!",
        "ru": "Пожалуйста, введите только число!",
        "en": "Please enter numbers only!",
    },
    "group_link_request": {
        "uz": "🔗 Telegram guruh/kanal havolasini yuboring:\n<i>(Masalan: https://t.me/+AbCdEf...)</i>",
        "ru": "🔗 Отправьте ссылку Telegram группы/канала:\n<i>(Например: https://t.me/+AbCdEf...)</i>",
        "en": "🔗 Send the Telegram group/channel link:\n<i>(Example: https://t.me/+AbCdEf...)</i>",
    },
    "no_teachers_for_group": {
        "uz": "⚠️ Bazada tasdiqlangan ustozlar yo'q! Guruh ochish uchun avval ustoz ishga qabul qiling.",
        "ru": "⚠️ В базе нет подтверждённых преподавателей! Сначала примите преподавателя.",
        "en": "⚠️ There are no approved teachers in the database! Please approve a teacher first.",
    },
    "choose_teacher_for_group": {
        "uz": "👨‍🏫 Bu guruhga qaysi ustozni biriktiramiz?",
        "ru": "👨‍🏫 Какого преподавателя назначить этой группе?",
        "en": "👨‍🏫 Which teacher should be assigned to this group?",
    },
    "group_created": {
        "uz": "✅ <b>{group_name}</b> guruhi muvaffaqiyatli yaratildi va ustozga biriktirildi!",
        "ru": "✅ Группа <b>{group_name}</b> успешно создана и назначена преподавателю!",
        "en": "✅ Group <b>{group_name}</b> has been created and assigned to the teacher!",
    },
    "no_groups": {
        "uz": "Guruhlar mavjud emas.",
        "ru": "Группы отсутствуют.",
        "en": "There are no groups.",
    },
    "choose_group_edit": {
        "uz": "Tahrirlamoqchi bo'lgan guruhni tanlang:",
        "ru": "Выберите группу для управления:",
        "en": "Choose the group you want to manage:",
    },
    "group_options": {
        "uz": "Guruh bilan nima qilamiz?",
        "ru": "Что сделать с группой?",
        "en": "What should we do with this group?",
    },
    "view_students": {
        "uz": "👥 O'quvchilarni ko‘rish",
        "ru": "👥 Посмотреть студентов",
        "en": "👥 View students",
    },
    "change_teacher": {
        "uz": "🔄 Ustozni almashtirish",
        "ru": "🔄 Сменить преподавателя",
        "en": "🔄 Change teacher",
    },
    "delete_group": {
        "uz": "❌ Guruhni o'chirish",
        "ru": "❌ Удалить группу",
        "en": "❌ Delete group",
    },
    "no_teachers": {
        "uz": "Bazada tasdiqlangan ustozlar yo'q.",
        "ru": "В базе нет подтверждённых преподавателей.",
        "en": "There are no approved teachers in the database.",
    },
    "choose_new_teacher": {
        "uz": "Yangi ustozni tanlang:",
        "ru": "Выберите нового преподавателя:",
        "en": "Choose a new teacher:",
    },
    "teacher_changed": {
        "uz": "✅ Ustoz muvaffaqiyatli almashtirildi!",
        "ru": "✅ Преподаватель успешно изменён!",
        "en": "✅ Teacher changed successfully!",
    },
    "group_deleted": {
        "uz": "✅ Guruh muvaffaqiyatli o‘chirildi.",
        "ru": "✅ Группа успешно удалена.",
        "en": "✅ Group deleted successfully.",
    },
    "kick_not_found": {
        "uz": "So'rov topilmadi.",
        "ru": "Запрос не найден.",
        "en": "Request not found.",
    },
    "kick_already_processed": {
        "uz": "Bu so'rov allaqachon ko'rib chiqilgan.",
        "ru": "Этот запрос уже был обработан.",
        "en": "This request has already been processed.",
    },
    "kick_approved_status": {
        "uz": "✅ <b>QAROR: CHETLATISH TASDIQLANDI</b>",
        "ru": "✅ <b>РЕШЕНИЕ: ИСКЛЮЧЕНИЕ ПОДТВЕРЖДЕНО</b>",
        "en": "✅ <b>DECISION: REMOVAL APPROVED</b>",
    },
    "kick_rejected_status": {
        "uz": "❌ <b>QAROR: RAD ETILDI</b>",
        "ru": "❌ <b>РЕШЕНИЕ: ОТКЛОНЕНО</b>",
        "en": "❌ <b>DECISION: REJECTED</b>",
    },
    "kick_teacher_approved": {
        "uz": "✅ Siz yuborgan chetlatish so'rovi tasdiqlandi.\n\n👤 O'quvchi: {student_name}\n📚 Guruh: {group_name}",
        "ru": "✅ Ваш запрос на исключение подтверждён.\n\n👤 Студент: {student_name}\n📚 Группа: {group_name}",
        "en": "✅ Your removal request has been approved.\n\n👤 Student: {student_name}\n📚 Group: {group_name}",
    },
    "kick_teacher_rejected": {
        "uz": "❌ Siz yuborgan chetlatish so'rovi admin tomonidan rad etildi.\n\n👤 O'quvchi: {student_name}\n📚 Guruh: {group_name}",
        "ru": "❌ Ваш запрос на исключение был отклонён администратором.\n\n👤 Студент: {student_name}\n📚 Группа: {group_name}",
        "en": "❌ Your removal request was rejected by the admin.\n\n👤 Student: {student_name}\n📚 Group: {group_name}",
    },
    "kick_student_removed": {
        "uz": "❌ Siz <b>{group_name}</b> guruhidan chetlatildingiz.\n\nSabab va batafsil ma'lumot uchun ma'muriyat bilan bog'laning.",
        "ru": "❌ Вы исключены из группы <b>{group_name}</b>.\n\nДля подробной информации свяжитесь с администрацией.",
        "en": "❌ You have been removed from <b>{group_name}</b>.\n\nFor details, please contact the administration.",
    },
    "admin_manage_title": {
        "uz": "👨‍💻 <b>Adminlarni boshqarish</b>\n\nBu bo‘limda yangi admin qo‘shish yoki mavjud adminni olib tashlash mumkin.",
        "ru": "👨‍💻 <b>Управление админами</b>\n\nВ этом разделе можно добавить нового админа или снять права у существующего.",
        "en": "👨‍💻 <b>Manage admins</b>\n\nIn this section, you can add a new admin or remove an existing admin.",
    },
    "add_admin": {
        "uz": "➕ Admin qo‘shish",
        "ru": "➕ Добавить админа",
        "en": "➕ Add admin",
    },
    "admin_list": {
        "uz": "📋 Adminlar ro‘yxati",
        "ru": "📋 Список админов",
        "en": "📋 Admin list",
    },
    "add_admin_request_id": {
        "uz": "➕ <b>Yangi admin qo‘shish</b>\n\nAdmin qilmoqchi bo‘lgan odamning Telegram ID raqamini yuboring.\n\nMasalan:\n<code>123456789</code>",
        "ru": "➕ <b>Добавить нового админа</b>\n\nОтправьте Telegram ID человека, которого хотите сделать админом.\n\nНапример:\n<code>123456789</code>",
        "en": "➕ <b>Add new admin</b>\n\nSend the Telegram ID of the person you want to make an admin.\n\nExample:\n<code>123456789</code>",
    },
    "send_digits_only": {
        "uz": "Iltimos, faqat raqam yuboring. Masalan: 123456789",
        "ru": "Пожалуйста, отправьте только цифры. Например: 123456789",
        "en": "Please send numbers only. Example: 123456789",
    },
    "admin_name_request": {
        "uz": "Adminning ismini kiriting.\n\nAgar ismini bilmasangiz, `-` yuboring.",
        "ru": "Введите имя админа.\n\nЕсли не знаете имя, отправьте `-`.",
        "en": "Enter the admin's name.\n\nIf you do not know the name, send `-`.",
    },
    "admin_added": {
        "uz": "✅ Admin muvaffaqiyatli qo‘shildi.\n\nTelegram ID: <code>{telegram_id}</code>",
        "ru": "✅ Админ успешно добавлен.\n\nTelegram ID: <code>{telegram_id}</code>",
        "en": "✅ Admin added successfully.\n\nTelegram ID: <code>{telegram_id}</code>",
    },
    "new_admin_message": {
        "uz": "🎉 <b>Sizga Admin huquqi berildi.</b>\n\nIltimos, /start bosib admin panelga kiring.",
        "ru": "🎉 <b>Вам выданы права Admin.</b>\n\nНажмите /start, чтобы открыть админ-панель.",
        "en": "🎉 <b>You have been granted Admin rights.</b>\n\nPlease press /start to open the admin panel.",
    },
    "admins_not_found": {
        "uz": "Adminlar topilmadi.",
        "ru": "Админы не найдены.",
        "en": "No admins found.",
    },
    "admins_list_title": {
        "uz": "📋 <b>Adminlar ro‘yxati:</b>\n\n",
        "ru": "📋 <b>Список админов:</b>\n\n",
        "en": "📋 <b>Admin list:</b>\n\n",
    },
    "remove_admin_button": {
        "uz": "❌ {name} adminlikdan olish",
        "ru": "❌ Снять права у {name}",
        "en": "❌ Remove {name}",
    },
    "cannot_remove_self": {
        "uz": "O‘zingizni adminlikdan olib tashlay olmaysiz.",
        "ru": "Вы не можете снять права у самого себя.",
        "en": "You cannot remove your own admin rights.",
    },
    "cannot_remove_superadmin": {
        "uz": "Superadminni bu yerdan olib tashlab bo‘lmaydi.",
        "ru": "Нельзя снять права Superadmin через этот раздел.",
        "en": "Superadmin cannot be removed from here.",
    },
    "user_not_admin": {
        "uz": "Bu foydalanuvchi admin emas.",
        "ru": "Этот пользователь не является админом.",
        "en": "This user is not an admin.",
    },
    "admin_removed": {
        "uz": "✅ Admin huquqi olib tashlandi.\n\nTelegram ID: <code>{telegram_id}</code>",
        "ru": "✅ Права Admin сняты.\n\nTelegram ID: <code>{telegram_id}</code>",
        "en": "✅ Admin rights removed.\n\nTelegram ID: <code>{telegram_id}</code>",
    },
    "admin_removed_message": {
        "uz": "⚠️ <b>Sizning Admin huquqingiz olib tashlandi.</b>\n\nEndi siz oddiy foydalanuvchi sifatida ko‘rinasiz.",
        "ru": "⚠️ <b>Ваши права Admin были сняты.</b>\n\nТеперь вы отображаетесь как обычный пользователь.",
        "en": "⚠️ <b>Your Admin rights have been removed.</b>\n\nYou are now shown as a regular user.",
    },
    "no_admin_actions": {
        "uz": "📌 Hali admin harakatlari mavjud emas.",
        "ru": "📌 Действий админов пока нет.",
        "en": "📌 There are no admin actions yet.",
    },
    "admin_actions_title": {
        "uz": "📌 <b>Oxirgi admin harakatlari:</b>\n\n",
        "ru": "📌 <b>Последние действия админов:</b>\n\n",
        "en": "📌 <b>Последние действия админов:</b>\n\n",
    },
    "choose_teacher_language": {
        "uz": "👨‍🏫 <b>Qaysi til bo‘yicha ustozlarni ko‘rmoqchisiz?</b>",
        "ru": "👨‍🏫 <b>По какому языку показать преподавателей?</b>",
        "en": "👨‍🏫 <b>Which language’s teachers would you like to view?</b>",
    },
    "language_not_found": {
        "uz": "Til topilmadi.",
        "ru": "Язык не найден.",
        "en": "Language not found.",
    },
    "no_teachers_by_language": {
        "uz": "Bu til bo‘yicha hozircha tasdiqlangan ustoz yo‘q.",
        "ru": "По этому языку пока нет подтверждённых преподавателей.",
        "en": "There are no approved teachers for this language yet.",
    },
    "teachers_by_language_title": {
        "uz": "👨‍🏫 <b>{language} ustozlari:</b>\n\n",
        "ru": "👨‍🏫 <b>Преподаватели: {language}</b>\n\n",
        "en": "👨‍🏫 <b>Teachers: {language}</b>\n\n",
    },
    "teacher_no_groups": {
        "uz": "Bu ustozga hali faol guruh biriktirilmagan.",
        "ru": "Этому преподавателю пока не назначена активная группа.",
        "en": "No active group has been assigned to this teacher yet.",
    },
    "teacher_groups_title": {
        "uz": "📚 <b>Ustoz guruhlari</b>\n🆔 Teacher ID: <code>{teacher_id}</code>\n\nGuruh ichidagi o‘quvchilarni ko‘rish uchun pastdagi tugmani bosing.",
        "ru": "📚 <b>Группы преподавателя</b>\n🆔 Teacher ID: <code>{teacher_id}</code>\n\nЧтобы увидеть студентов группы, нажмите кнопку ниже.",
        "en": "📚 <b>Teacher groups</b>\n🆔 Teacher ID: <code>{teacher_id}</code>\n\nPress a button below to view the students in a group.",
    },
    "group_has_no_students": {
        "uz": "Bu guruhda hozircha o‘quvchilar yo‘q.",
        "ru": "В этой группе пока нет студентов.",
        "en": "There are no students in this group yet.",
    },
    "group_students_title": {
        "uz": "👥 <b>Guruh o‘quvchilari</b>\n🆔 Group ID: <code>{group_id}</code>\n\nJami o‘quvchilar: <b>{count}</b>\n\nKo‘proq ma’lumot yoki baholar uchun o‘quvchini tanlang.",
        "ru": "👥 <b>Студенты группы</b>\n🆔 Group ID: <code>{group_id}</code>\n\nВсего студентов: <b>{count}</b>\n\nДля подробной информации или оценок выберите студента.",
        "en": "👥 <b>Group students</b>\n🆔 Group ID: <code>{group_id}</code>\n\nTotal students: <b>{count}</b>\n\nChoose a student for more information or results.",
    },
    "student_not_found": {
        "uz": "O‘quvchi topilmadi.",
        "ru": "Студент не найден.",
        "en": "Student not found.",
    },
    "student_profile_title": {
        "uz": "ℹ️ <b>O‘quvchi ma’lumotlari</b>",
        "ru": "ℹ️ <b>Информация о студенте</b>",
        "en": "ℹ️ <b>Student information</b>",
    },
    "view_results_button": {
        "uz": "📊 Baholarini ko‘rish",
        "ru": "📊 Посмотреть оценки",
        "en": "📊 View results",
    },
    "no_student_results": {
        "uz": "Bu o‘quvchiga hali baho/natija kiritilmagan.",
        "ru": "Для этого студента пока нет оценок/результатов.",
        "en": "No results have been added for this student yet.",
    },
    "student_results_title": {
        "uz": "📊 <b>O‘quvchi baholari</b>\n🆔 Student ID: <code>{student_id}</code>\n\n",
        "ru": "📊 <b>Оценки студента</b>\n🆔 Student ID: <code>{student_id}</code>\n\n",
        "en": "📊 <b>Student results</b>\n🆔 Student ID: <code>{student_id}</code>\n\n",
    },
    "students_removed_instruction": {
        "uz": "O‘quvchilarni ko‘rish endi shu tartibda ishlaydi:\n\n👨‍🏫 Ustozlarni ko‘rish → Til tanlash → Ustoz → Guruh → O‘quvchi",
        "ru": "Просмотр студентов теперь работает так:\n\n👨‍🏫 Преподаватели → Выбор языка → Преподаватель → Группа → Студент",
        "en": "Students are now viewed through:\n\n👨‍🏫 Teachers → Choose language → Teacher → Group → Student",
    },
    "no_results": {
        "uz": "📊 Hali hech qanday natija kiritilmagan.",
        "ru": "📊 Результаты пока не добавлены.",
        "en": "📊 No results have been added yet.",
    },
    "all_results_title": {
        "uz": "📊 <b>Oxirgi barcha natijalar:</b>\n\n",
        "ru": "📊 <b>Последние результаты:</b>\n\n",
        "en": "📊 <b>Latest results:</b>\n\n",
    },
    "staff_manage_title": {
        "uz": "👥 <b>Xodimlarni boshqarish</b>\n\nBu bo‘limda admin, accountant va superadmin rollarini berish yoki olib tashlash mumkin.",
        "ru": "👥 <b>Управление сотрудниками</b>\n\nВ этом разделе можно выдавать или снимать роли admin, accountant и superadmin.",
        "en": "👥 <b>Staff management</b>\n\nIn this section, you can assign or remove admin, accountant, and superadmin roles.",
    },
    "give_role": {
        "uz": "➕ Role berish",
        "ru": "➕ Выдать роль",
        "en": "➕ Assign role",
    },
    "manual_role": {
        "uz": "🆔 Telegram ID orqali",
        "ru": "🆔 Через Telegram ID",
        "en": "🆔 By Telegram ID",
    },
    "staff_admins": {
        "uz": "👨‍💻 Adminlar",
        "ru": "👨‍💻 Админы",
        "en": "👨‍💻 Admins",
    },
    "staff_accountants": {
        "uz": "💰 Accountantlar",
        "ru": "💰 Бухгалтерия",
        "en": "💰 Accountants",
    },
    "staff_superadmins": {
        "uz": "👑 Superadminlar",
        "ru": "👑 Superadmins",
        "en": "👑 Superadmins",
    },
    "staff_actions": {
        "uz": "📌 Staff actionlar",
        "ru": "📌 Действия сотрудников",
        "en": "📌 Staff actions",
    },
    "recent_users_title": {
        "uz": "➕ <b>Role berish</b>\n\nOxirgi ro‘yxatdan o‘tgan userlar. Kerakli odamni tanlang:",
        "ru": "➕ <b>Выдать роль</b>\n\nПоследние зарегистрированные пользователи. Выберите нужного человека:",
        "en": "➕ <b>Assign role</b>\n\nRecently registered users. Choose the person:",
    },
    "staff_list_title": {
        "uz": "📋 <b>{role} ro‘yxati</b>\n\nKerakli odamni tanlang:",
        "ru": "📋 <b>Список: {role}</b>\n\nВыберите нужного человека:",
        "en": "📋 <b>{role} list</b>\n\nChoose the person:",
    },
    "staff_empty": {
        "uz": "Bu ro‘yxatda user topilmadi.",
        "ru": "В этом списке пользователи не найдены.",
        "en": "No users found in this list.",
    },
    "choose_role": {
        "uz": "👤 <b>{full_name}</b>\n🆔 <code>{telegram_id}</code>\n🔐 Hozirgi role: <b>{current_role}</b>\n\nQaysi role beramiz?",
        "ru": "👤 <b>{full_name}</b>\n🆔 <code>{telegram_id}</code>\n🔐 Текущая роль: <b>{current_role}</b>\n\nКакую роль назначить?",
        "en": "👤 <b>{full_name}</b>\n🆔 <code>{telegram_id}</code>\n🔐 Current role: <b>{current_role}</b>\n\nWhich role should be assigned?",
    },
    "role_admin": {
        "uz": "👨‍💻 Admin",
        "ru": "👨‍💻 Admin",
        "en": "👨‍💻 Admin",
    },
    "role_accountant": {
        "uz": "💰 Accountant",
        "ru": "💰 Accountant",
        "en": "💰 Accountant",
    },
    "role_superadmin": {
        "uz": "👑 Superadmin",
        "ru": "👑 Superadmin",
        "en": "👑 Superadmin",
    },
    "role_user": {
        "uz": "👤 Userga qaytarish",
        "ru": "👤 Вернуть в user",
        "en": "👤 Return to user",
    },
    "role_set_done": {
        "uz": "✅ Role muvaffaqiyatli o‘zgartirildi.\n\n👤 User: <code>{telegram_id}</code>\n🔐 Yangi role: <b>{role}</b>",
        "ru": "✅ Роль успешно изменена.\n\n👤 User: <code>{telegram_id}</code>\n🔐 Новая роль: <b>{role}</b>",
        "en": "✅ Role changed successfully.\n\n👤 User: <code>{telegram_id}</code>\n🔐 New role: <b>{role}</b>",
    },
    "role_notify": {
        "uz": "🔐 <b>Sizning rolingiz o‘zgartirildi.</b>\n\nYangi role: <b>{role}</b>\n\nIltimos, /start bosib panelni yangilang.",
        "ru": "🔐 <b>Ваша роль была изменена.</b>\n\nНовая роль: <b>{role}</b>\n\nНажмите /start, чтобы обновить панель.",
        "en": "🔐 <b>Your role has been changed.</b>\n\nNew role: <b>{role}</b>\n\nPlease press /start to refresh your panel.",
    },
    "cannot_change_self": {
        "uz": "O‘zingizni bu role’ga o‘zgartira olmaysiz.",
        "ru": "Вы не можете изменить свою роль на эту.",
        "en": "You cannot change your own role to this.",
    },
    "manual_id_request": {
        "uz": "🆔 Role bermoqchi bo‘lgan odamning Telegram ID raqamini yuboring.\n\nMasalan:\n<code>123456789</code>",
        "ru": "🆔 Отправьте Telegram ID человека, которому хотите выдать роль.\n\nНапример:\n<code>123456789</code>",
        "en": "🆔 Send the Telegram ID of the person you want to assign a role to.\n\nExample:\n<code>123456789</code>",
    },
    "manual_name_request": {
        "uz": "Ismini kiriting.\n\nAgar bilmasangiz, `-` yuboring.",
        "ru": "Введите имя.\n\nЕсли не знаете, отправьте `-`.",
        "en": "Enter the name.\n\nIf you do not know it, send `-`.",
    },
    "prev": {
        "uz": "⬅️ Oldingi",
        "ru": "⬅️ Назад",
        "en": "⬅️ Previous",
    },
    "next": {
        "uz": "Keyingi ➡️",
        "ru": "Далее ➡️",
        "en": "Next ➡️",
    },
        "actions_list_title": {
        "uz": "📌 <b>Admin / Staff harakatlari</b>\n\nPage: <b>{page}</b>\n\nDetail ko‘rish uchun actionni tanlang:",
        "ru": "📌 <b>Действия Admin / Staff</b>\n\nСтраница: <b>{page}</b>\n\nВыберите действие для подробностей:",
        "en": "📌 <b>Admin / Staff actions</b>\n\nPage: <b>{page}</b>\n\nChoose an action to view details:",
    },
    "action_detail_title": {
        "uz": "📌 <b>Action detail</b>",
        "ru": "📌 <b>Детали действия</b>",
        "en": "📌 <b>Action detail</b>",
    },
    "action_not_found": {
        "uz": "Action topilmadi.",
        "ru": "Действие не найдено.",
        "en": "Action not found.",
    },
    "back_to_actions": {
        "uz": "🔙 Actionlar ro‘yxati",
        "ru": "🔙 Список действий",
        "en": "🔙 Actions list",
    },
}


def at(key: str, lang: str = "uz", **kwargs) -> str:
    item = LOCAL_TEXTS.get(key, {})
    text = item.get(lang) or item.get("uz") or key
    return text.format(**kwargs)


def h(value):
    """HTML parse_mode uchun xavfsiz text."""
    if value is None:
        return "-"
    return escape(str(value))


async def user_lang(user_id: int) -> str:
    lang = await get_user_interface_lang(user_id)
    return lang or "uz"


# ==========================================
# ACCESS FILTERS
# ==========================================

class AdminOnly(BaseFilter):
    async def __call__(self, event) -> bool:
        if not getattr(event, "from_user", None):
            return False

        role = await get_user_role(event.from_user.id)
        return role in ["admin", "superadmin"]


admin_router.message.filter(AdminOnly())
admin_router.callback_query.filter(AdminOnly())


async def is_superadmin(user_id: int) -> bool:
    role = await get_user_role(user_id)
    return role == "superadmin"


async def require_superadmin_message(message: types.Message, state: FSMContext | None = None) -> bool:
    lang = await user_lang(message.from_user.id)

    if not await is_superadmin(message.from_user.id):
        if state:
            await state.clear()

        await message.answer(at("only_superadmin", lang))
        return False

    return True


async def require_superadmin_callback(callback: types.CallbackQuery) -> bool:
    lang = await user_lang(callback.from_user.id)

    if not await is_superadmin(callback.from_user.id):
        await callback.answer(at("only_superadmin", lang), show_alert=True)
        return False

    return True


async def notify_superadmins(bot, actor_id: int, text: str):
    superadmin_ids = await get_superadmin_ids()

    for superadmin_id in superadmin_ids:
        if superadmin_id == actor_id:
            continue

        try:
            await bot.send_message(
                chat_id=superadmin_id,
                text=text,
                parse_mode="HTML",
            )
        except Exception:
            pass


# ==========================================
# KEYBOARDS
# ==========================================

async def panel_keyboard_for_user(user_id: int):
    role = await get_user_role(user_id)
    lang = await user_lang(user_id)

    if role == "superadmin":
        return superadmin_menu_keyboard(lang)

    return admin_menu_keyboard(lang)


def admin_menu_keyboard(lang: str = "uz"):
    kb = [
        [types.KeyboardButton(text=t("accounting_panel", lang))],
        [types.KeyboardButton(text=t("teachers_view", lang))],
        [
            types.KeyboardButton(text=t("create_group", lang)),
            types.KeyboardButton(text=t("groups_list", lang)),
        ],
        [types.KeyboardButton(text=t("all_results", lang))],
        [types.KeyboardButton(text=t("statistics", lang))],
    ]

    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def superadmin_menu_keyboard(lang: str = "uz"):
    kb = [
        [types.KeyboardButton(text=t("admin_manage", lang))],
        [types.KeyboardButton(text=t("accounting_panel", lang))],
        [types.KeyboardButton(text=t("teachers_view", lang))],
        [
            types.KeyboardButton(text=t("create_group", lang)),
            types.KeyboardButton(text=t("groups_list", lang)),
        ],
        [types.KeyboardButton(text=t("all_results", lang))],
        [types.KeyboardButton(text=t("statistics", lang))],
    ]

    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# ==========================================
# 1. TEACHER APPLICATION REJECT
# Admin + Superadmin
# ==========================================

@admin_router.callback_query(AdminTeacherRejectCB.filter())
async def admin_reject_teacher(callback: types.CallbackQuery, callback_data: AdminTeacherRejectCB):
    lang = await user_lang(callback.from_user.id)

    teacher_id = callback_data.teacher_id

    await update_teacher_status(teacher_id, "rejected_teacher")

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="teacher_application_rejected_from_bot",
        entity_type="user",
        entity_id=teacher_id,
        details={
            "teacher_id": teacher_id,
            "new_status": "rejected_teacher",
        },
    )

    status_text = at("teacher_rejected_status", lang)

    if callback.message.photo or callback.message.document:
        await callback.message.edit_caption(
            caption=f"{callback.message.html_text}\n\n{status_text}",
            parse_mode="HTML",
            reply_markup=None,
        )
    else:
        await callback.message.edit_text(
            f"{callback.message.html_text}\n\n{status_text}",
            parse_mode="HTML",
            reply_markup=None,
        )

    teacher_lang = await user_lang(teacher_id)

    await callback.bot.send_message(
        chat_id=teacher_id,
        text=at("teacher_rejected_message", teacher_lang),
    )

    await notify_superadmins(
        bot=callback.bot,
        actor_id=callback.from_user.id,
        text=(
            "📌 <b>Admin harakati</b>\n\n"
            f"Admin ID: <code>{callback.from_user.id}</code>\n"
            f"Action: <b>teacher application rejected</b>\n"
            f"Teacher ID: <code>{teacher_id}</code>"
        ),
    )


# ==========================================
# 2. TEACHER APPLICATION APPROVE
# Admin + Superadmin
# ==========================================

@admin_router.callback_query(AdminTeacherApproveCB.filter())
async def admin_approve_teacher(callback: types.CallbackQuery, callback_data: AdminTeacherApproveCB):
    lang = await user_lang(callback.from_user.id)

    teacher_id = callback_data.teacher_id

    await update_teacher_status(teacher_id, "teacher")

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="teacher_application_approved_from_bot",
        entity_type="user",
        entity_id=teacher_id,
        details={
            "teacher_id": teacher_id,
            "new_status": "teacher",
        },
    )

    status_text = at("teacher_approved_status", lang)

    if callback.message.photo or callback.message.document:
        await callback.message.edit_caption(
            caption=f"{callback.message.html_text}\n\n{status_text}",
            parse_mode="HTML",
            reply_markup=None,
        )
    else:
        await callback.message.edit_text(
            f"{callback.message.html_text}\n\n{status_text}",
            parse_mode="HTML",
            reply_markup=None,
        )

    teacher_lang = await user_lang(teacher_id)

    await callback.bot.send_message(
        chat_id=teacher_id,
        text=at("teacher_approved_message", teacher_lang),
        parse_mode="HTML",
    )

    await notify_superadmins(
        bot=callback.bot,
        actor_id=callback.from_user.id,
        text=(
            "📌 <b>Admin harakati</b>\n\n"
            f"Admin ID: <code>{callback.from_user.id}</code>\n"
            f"Action: <b>teacher application approved</b>\n"
            f"Teacher ID: <code>{teacher_id}</code>"
        ),
    )


# ==========================================
# 3. STATISTICS
# Admin + Superadmin
# ==========================================

@admin_router.message(F.text.in_(all_texts("statistics")))
async def show_statistics(message: types.Message):
    lang = await user_lang(message.from_user.id)

    stats = await get_bot_statistics()

    text = (
        f"{at('statistics_title', lang)}\n\n"
        f"{at('students_total', lang)}: <b>{stats['students']}</b>\n"
        f"{at('teachers_total', lang)}: <b>{stats['teachers']}</b>\n"
        f"{at('groups_total', lang)}: <b>{stats['groups']}</b>\n"
    )

    await message.answer(text, parse_mode="HTML")


# ==========================================
# 4. CREATE GROUP
# Admin + Superadmin
# ==========================================

@admin_router.message(F.text.in_(all_texts("create_group")))
async def start_create_group(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    await message.answer(
        at("create_group_name", lang),
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove(),
    )

    await state.set_state(CreateGroup.name)


@admin_router.message(CreateGroup.name)
async def cg_name(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    await state.update_data(name=message.text)

    builder = InlineKeyboardBuilder()

    for code, name in LANGUAGES.items():
        builder.button(text=name, callback_data=f"cglang_{name}")

    builder.adjust(2)

    await message.answer(at("choose_group_language", lang), reply_markup=builder.as_markup())
    await state.set_state(CreateGroup.language)


@admin_router.callback_query(CreateGroup.language, F.data.startswith("cglang_"))
async def cg_lang(callback: types.CallbackQuery, state: FSMContext):
    lang = await user_lang(callback.from_user.id)

    selected_language = callback.data.split("_", 1)[1]
    await state.update_data(language=selected_language)

    await callback.message.edit_text(at("language_selected", lang, language=h(selected_language)))
    await callback.message.answer(
        at("capacity_request", lang),
        parse_mode="HTML",
    )

    await state.set_state(CreateGroup.capacity)


@admin_router.message(CreateGroup.capacity)
async def cg_capacity(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if not message.text.isdigit():
        await message.answer(at("digits_only", lang))
        return

    await state.update_data(capacity=int(message.text))

    await message.answer(
        at("group_link_request", lang),
        parse_mode="HTML",
    )

    await state.set_state(CreateGroup.link)


@admin_router.message(CreateGroup.link)
async def cg_link(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    await state.update_data(link=message.text)

    teachers = await get_all_teachers()

    if not teachers:
        await message.answer(
            at("no_teachers_for_group", lang),
            reply_markup=await panel_keyboard_for_user(message.from_user.id),
        )
        await state.clear()
        return

    builder = InlineKeyboardBuilder()

    for teacher in teachers:
        builder.button(
            text=f"{teacher['full_name']} ({teacher['teach_lang']})",
            callback_data=AssignTeacherCB(teacher_id=teacher["telegram_id"]),
        )

    builder.adjust(1)

    await message.answer(at("choose_teacher_for_group", lang), reply_markup=builder.as_markup())
    await state.set_state(CreateGroup.teacher)


@admin_router.callback_query(CreateGroup.teacher, AssignTeacherCB.filter())
async def cg_teacher(callback: types.CallbackQuery, callback_data: AssignTeacherCB, state: FSMContext):
    lang = await user_lang(callback.from_user.id)

    data = await state.get_data()
    teacher_id = callback_data.teacher_id

    await create_new_group(
        data["name"],
        data["language"],
        data["capacity"],
        data["link"],
        teacher_id,
    )

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="group_created_from_bot",
        entity_type="group",
        entity_id=None,
        details={
            "name": data["name"],
            "language": data["language"],
            "capacity": data["capacity"],
            "link": data["link"],
            "teacher_id": teacher_id,
        },
    )

    await callback.message.delete()
    await callback.message.answer(
        at("group_created", lang, group_name=h(data["name"])),
        parse_mode="HTML",
        reply_markup=await panel_keyboard_for_user(callback.from_user.id),
    )

    await notify_superadmins(
        bot=callback.bot,
        actor_id=callback.from_user.id,
        text=(
            "📌 <b>Admin harakati</b>\n\n"
            f"Admin ID: <code>{callback.from_user.id}</code>\n"
            f"Action: <b>group created</b>\n"
            f"Group: <b>{h(data['name'])}</b>\n"
            f"Teacher ID: <code>{teacher_id}</code>"
        ),
    )

    await state.clear()


# ==========================================
# 5. GROUP MANAGEMENT
# Admin + Superadmin
# ==========================================

@admin_router.message(F.text.in_(all_texts("groups_list")))
async def list_groups_for_admin(message: types.Message):
    lang = await user_lang(message.from_user.id)

    groups = await get_all_groups()

    if not groups:
        await message.answer(at("no_groups", lang))
        return

    builder = InlineKeyboardBuilder()

    for group in groups:
        builder.button(
            text=group["name"],
            callback_data=AdminGroupCB(payment_id=0, group_id=group["id"]),
        )

    builder.adjust(1)

    await message.answer(at("choose_group_edit", lang), reply_markup=builder.as_markup())


@admin_router.callback_query(AdminGroupCB.filter(F.payment_id == 0))
async def manage_group_options(callback: types.CallbackQuery, callback_data: AdminGroupCB):
    lang = await user_lang(callback.from_user.id)

    group_id = callback_data.group_id

    builder = InlineKeyboardBuilder()
    builder.button(text=at("view_students", lang), callback_data=f"sa_gs_{group_id}")
    builder.button(text=at("change_teacher", lang), callback_data=f"ch_tch_{group_id}")
    builder.button(text=at("delete_group", lang), callback_data=f"del_grp_{group_id}")
    builder.adjust(1)

    await callback.message.edit_text(at("group_options", lang), reply_markup=builder.as_markup())


@admin_router.callback_query(F.data.startswith("ch_tch_"))
async def change_teacher_start(callback: types.CallbackQuery):
    lang = await user_lang(callback.from_user.id)

    group_id = int(callback.data.split("_")[2])
    teachers = await get_all_teachers()

    if not teachers:
        await callback.answer(at("no_teachers", lang), show_alert=True)
        return

    builder = InlineKeyboardBuilder()

    for teacher in teachers:
        builder.button(
            text=teacher["full_name"],
            callback_data=f"set_new_t_{group_id}_{teacher['telegram_id']}",
        )

    builder.adjust(1)

    await callback.message.edit_text(at("choose_new_teacher", lang), reply_markup=builder.as_markup())


@admin_router.callback_query(F.data.startswith("set_new_t_"))
async def set_new_teacher(callback: types.CallbackQuery):
    lang = await user_lang(callback.from_user.id)

    parts = callback.data.split("_")
    group_id = int(parts[3])
    teacher_id = int(parts[4])

    await change_group_teacher(group_id, teacher_id)

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="group_teacher_changed_from_bot",
        entity_type="group",
        entity_id=group_id,
        details={
            "group_id": group_id,
            "new_teacher_id": teacher_id,
        },
    )

    await callback.message.edit_text(at("teacher_changed", lang))

    await notify_superadmins(
        bot=callback.bot,
        actor_id=callback.from_user.id,
        text=(
            "📌 <b>Admin harakati</b>\n\n"
            f"Admin ID: <code>{callback.from_user.id}</code>\n"
            f"Action: <b>group teacher changed</b>\n"
            f"Group ID: <code>{group_id}</code>\n"
            f"New Teacher ID: <code>{teacher_id}</code>"
        ),
    )


@admin_router.callback_query(F.data.startswith("del_grp_"))
async def delete_group_handler(callback: types.CallbackQuery):
    lang = await user_lang(callback.from_user.id)

    group_id = int(callback.data.split("_")[2])

    await delete_group(group_id)

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="group_deleted_from_bot",
        entity_type="group",
        entity_id=group_id,
        details={
            "group_id": group_id,
        },
    )

    await callback.message.edit_text(at("group_deleted", lang))

    await notify_superadmins(
        bot=callback.bot,
        actor_id=callback.from_user.id,
        text=(
            "📌 <b>Admin harakati</b>\n\n"
            f"Admin ID: <code>{callback.from_user.id}</code>\n"
            f"Action: <b>group deleted</b>\n"
            f"Group ID: <code>{group_id}</code>"
        ),
    )


# ==========================================
# 6. KICK REQUEST APPROVE
# Admin + Superadmin
# ==========================================

@admin_router.callback_query(KickApproveCB.filter())
async def approve_kick_request(callback: types.CallbackQuery, callback_data: KickApproveCB):
    lang = await user_lang(callback.from_user.id)

    request_id = callback_data.request_id
    request = await get_kick_request(request_id)

    if not request:
        await callback.answer(at("kick_not_found", lang), show_alert=True)
        return

    if request["status"] != "pending":
        await callback.answer(at("kick_already_processed", lang), show_alert=True)
        return

    await remove_student_from_group(request["user_id"], request["group_id"])
    await update_kick_request_status(request_id, "approved")

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="kick_request_approved_from_bot",
        entity_type="kick_request",
        entity_id=request_id,
        details={
            "request_id": request_id,
            "student_id": request["user_id"],
            "group_id": request["group_id"],
            "teacher_id": request["teacher_id"],
        },
    )

    await callback.message.edit_text(
        f"{callback.message.html_text}\n\n{at('kick_approved_status', lang)}",
        parse_mode="HTML",
        reply_markup=None,
    )

    teacher_lang = await user_lang(request["teacher_id"])

    await callback.bot.send_message(
        chat_id=request["teacher_id"],
        text=at(
            "kick_teacher_approved",
            teacher_lang,
            student_name=request["student_name"],
            group_name=request["group_name"],
        ),
    )

    student_lang = await user_lang(request["user_id"])

    await callback.bot.send_message(
        chat_id=request["user_id"],
        text=at("kick_student_removed", student_lang, group_name=h(request["group_name"])),
        parse_mode="HTML",
    )

    await notify_superadmins(
        bot=callback.bot,
        actor_id=callback.from_user.id,
        text=(
            "📌 <b>Admin harakati</b>\n\n"
            f"Admin ID: <code>{callback.from_user.id}</code>\n"
            f"Action: <b>kick request approved</b>\n"
            f"Request ID: <code>{request_id}</code>\n"
            f"Student ID: <code>{request['user_id']}</code>\n"
            f"Group ID: <code>{request['group_id']}</code>"
        ),
    )


# ==========================================
# 7. KICK REQUEST REJECT
# Admin + Superadmin
# ==========================================

@admin_router.callback_query(KickRejectCB.filter())
async def reject_kick_request(callback: types.CallbackQuery, callback_data: KickRejectCB):
    lang = await user_lang(callback.from_user.id)

    request_id = callback_data.request_id
    request = await get_kick_request(request_id)

    if not request:
        await callback.answer(at("kick_not_found", lang), show_alert=True)
        return

    if request["status"] != "pending":
        await callback.answer(at("kick_already_processed", lang), show_alert=True)
        return

    await update_kick_request_status(request_id, "rejected")

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="kick_request_rejected_from_bot",
        entity_type="kick_request",
        entity_id=request_id,
        details={
            "request_id": request_id,
            "student_id": request["user_id"],
            "group_id": request["group_id"],
            "teacher_id": request["teacher_id"],
        },
    )

    await callback.message.edit_text(
        f"{callback.message.html_text}\n\n{at('kick_rejected_status', lang)}",
        parse_mode="HTML",
        reply_markup=None,
    )

    teacher_lang = await user_lang(request["teacher_id"])

    await callback.bot.send_message(
        chat_id=request["teacher_id"],
        text=at(
            "kick_teacher_rejected",
            teacher_lang,
            student_name=request["student_name"],
            group_name=request["group_name"],
        ),
    )

    await notify_superadmins(
        bot=callback.bot,
        actor_id=callback.from_user.id,
        text=(
            "📌 <b>Admin harakati</b>\n\n"
            f"Admin ID: <code>{callback.from_user.id}</code>\n"
            f"Action: <b>kick request rejected</b>\n"
            f"Request ID: <code>{request_id}</code>\n"
            f"Student ID: <code>{request['user_id']}</code>\n"
            f"Group ID: <code>{request['group_id']}</code>"
        ),
    )


# ==========================================
# 8. STAFF MANAGEMENT
# Superadmin only
# ==========================================

@admin_router.message(F.text.in_(all_texts("admin_manage")))
async def manage_staff_menu(message: types.Message):
    lang = await user_lang(message.from_user.id)

    if not await require_superadmin_message(message):
        return

    builder = InlineKeyboardBuilder()

    builder.button(
        text=at("give_role", lang),
        callback_data=StaffListCB(role="recent", page=1)
    )
    builder.button(
        text=at("manual_role", lang),
        callback_data="staff_manual_role"
    )
    builder.button(
        text=at("staff_admins", lang),
        callback_data=StaffListCB(role="admin", page=1)
    )
    builder.button(
        text=at("staff_accountants", lang),
        callback_data=StaffListCB(role="accountant", page=1)
    )
    builder.button(
        text=at("staff_superadmins", lang),
        callback_data=StaffListCB(role="superadmin", page=1)
    )
    builder.button(
        text=at("staff_actions", lang),
        callback_data="staff_actions"
    )

    builder.adjust(1)

    await message.answer(
        at("staff_manage_title", lang),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@admin_router.callback_query(StaffListCB.filter())
async def show_staff_list(callback: types.CallbackQuery, callback_data: StaffListCB):
    lang = await user_lang(callback.from_user.id)

    if not await require_superadmin_callback(callback):
        return

    page = max(callback_data.page, 1)
    limit = 10
    offset = (page - 1) * limit
    role = callback_data.role

    if role == "recent":
        users = await get_recent_users_for_role_assignment(limit=limit, offset=offset)
        title = at("recent_users_title", lang)
    else:
        users = await get_staff_users(role=role)
        title = at("staff_list_title", lang, role=role)

    if not users:
        await callback.message.edit_text(
            at("staff_empty", lang),
            parse_mode="HTML"
        )
        return

    text = title + "\n\n"
    builder = InlineKeyboardBuilder()

    for user in users[:limit]:
        telegram_id = user["telegram_id"]
        full_name = user["full_name"] or "Ism yo‘q"
        user_role = user["role"] or "user"
        phone = user["phone"] or "-"

        text += (
            f"👤 <b>{h(full_name)}</b>\n"
            f"🆔 <code>{telegram_id}</code>\n"
            f"📞 {h(phone)}\n"
            f"🔐 Role: <b>{h(user_role)}</b>\n\n"
        )

        builder.button(
            text=f"🔐 {full_name[:25]}",
            callback_data=StaffUserCB(telegram_id=telegram_id)
        )

    if role == "recent":
        if page > 1:
            builder.button(
                text=at("prev", lang),
                callback_data=StaffListCB(role=role, page=page - 1)
            )

        if len(users) == limit:
            builder.button(
                text=at("next", lang),
                callback_data=StaffListCB(role=role, page=page + 1)
            )

    builder.adjust(1)

    await callback.message.edit_text(
        text[:3900],
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@admin_router.callback_query(StaffUserCB.filter())
async def choose_staff_user_role(callback: types.CallbackQuery, callback_data: StaffUserCB):
    lang = await user_lang(callback.from_user.id)

    if not await require_superadmin_callback(callback):
        return

    telegram_id = callback_data.telegram_id

    current_role = await get_user_role(telegram_id)

    # User ma'lumotini olish uchun recent listdan yoki staff listdan alohida profile query yo'q.
    # Shuning uchun ismni staff/recent listdan emas, qisqa ko'rsatamiz.
    full_name = str(telegram_id)

    builder = InlineKeyboardBuilder()

    builder.button(
        text=at("role_admin", lang),
        callback_data=StaffRoleCB(telegram_id=telegram_id, role="admin")
    )
    builder.button(
        text=at("role_accountant", lang),
        callback_data=StaffRoleCB(telegram_id=telegram_id, role="accountant")
    )
    builder.button(
        text=at("role_superadmin", lang),
        callback_data=StaffRoleCB(telegram_id=telegram_id, role="superadmin")
    )
    builder.button(
        text=at("role_user", lang),
        callback_data=StaffRoleCB(telegram_id=telegram_id, role="user")
    )

    builder.adjust(1)

    await callback.message.edit_text(
        at(
            "choose_role",
            lang,
            full_name=h(full_name),
            telegram_id=telegram_id,
            current_role=h(current_role)
        ),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@admin_router.callback_query(StaffRoleCB.filter())
async def set_staff_role_handler(callback: types.CallbackQuery, callback_data: StaffRoleCB):
    lang = await user_lang(callback.from_user.id)

    if not await require_superadmin_callback(callback):
        return

    telegram_id = callback_data.telegram_id
    new_role = callback_data.role

    # Superadmin o'zini user/admin/accountant qilib yubormasin.
    if telegram_id == callback.from_user.id and new_role != "superadmin":
        await callback.answer(at("cannot_change_self", lang), show_alert=True)
        return

    old_role = await get_user_role(telegram_id)

    await set_user_role(
        telegram_id=telegram_id,
        role=new_role,
        full_name=None
    )

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="staff_role_changed_from_bot",
        entity_type="user",
        entity_id=telegram_id,
        details={
            "target_user_id": telegram_id,
            "old_role": old_role,
            "new_role": new_role,
        },
    )

    try:
        target_lang = await user_lang(telegram_id)

        await callback.bot.send_message(
            chat_id=telegram_id,
            text=at("role_notify", target_lang, role=h(new_role)),
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.message.edit_text(
        at("role_set_done", lang, telegram_id=telegram_id, role=h(new_role)),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data == "staff_manual_role")
async def start_manual_staff_role(callback: types.CallbackQuery, state: FSMContext):
    lang = await user_lang(callback.from_user.id)

    if not await require_superadmin_callback(callback):
        return

    await callback.message.edit_text(
        at("manual_id_request", lang),
        parse_mode="HTML"
    )

    await state.set_state(StaffManualRoleState.telegram_id)


@admin_router.message(StaffManualRoleState.telegram_id)
async def process_manual_staff_id(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if not await require_superadmin_message(message, state):
        return

    if not message.text.isdigit():
        await message.answer(at("send_digits_only", lang))
        return

    await state.update_data(telegram_id=int(message.text))

    await message.answer(at("manual_name_request", lang))

    await state.set_state(StaffManualRoleState.full_name)


@admin_router.message(StaffManualRoleState.full_name)
async def process_manual_staff_name(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if not await require_superadmin_message(message, state):
        return

    full_name = message.text.strip()

    if full_name == "-":
        full_name = None

    await state.update_data(full_name=full_name)

    builder = InlineKeyboardBuilder()

    builder.button(
        text=at("role_admin", lang),
        callback_data=StaffManualRoleCB(role="admin")
    )
    builder.button(
        text=at("role_accountant", lang),
        callback_data=StaffManualRoleCB(role="accountant")
    )
    builder.button(
        text=at("role_superadmin", lang),
        callback_data=StaffManualRoleCB(role="superadmin")
    )
    builder.button(
        text=at("role_user", lang),
        callback_data=StaffManualRoleCB(role="user")
    )

    builder.adjust(1)

    await message.answer(
        "Qaysi role beramiz?",
        reply_markup=builder.as_markup()
    )

    await state.set_state(StaffManualRoleState.role)


@admin_router.callback_query(StaffManualRoleState.role, StaffManualRoleCB.filter())
async def process_manual_staff_role(
    callback: types.CallbackQuery,
    callback_data: StaffManualRoleCB,
    state: FSMContext
):
    lang = await user_lang(callback.from_user.id)

    if not await require_superadmin_callback(callback):
        await state.clear()
        return

    data = await state.get_data()

    telegram_id = data["telegram_id"]
    full_name = data.get("full_name")
    new_role = callback_data.role

    if telegram_id == callback.from_user.id and new_role != "superadmin":
        await callback.answer(at("cannot_change_self", lang), show_alert=True)
        return

    old_role = await get_user_role(telegram_id)

    await set_user_role(
        telegram_id=telegram_id,
        role=new_role,
        full_name=full_name
    )

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="staff_role_changed_manual_from_bot",
        entity_type="user",
        entity_id=telegram_id,
        details={
            "target_user_id": telegram_id,
            "full_name": full_name,
            "old_role": old_role,
            "new_role": new_role,
        },
    )

    try:
        target_lang = await user_lang(telegram_id)

        await callback.bot.send_message(
            chat_id=telegram_id,
            text=at("role_notify", target_lang, role=h(new_role)),
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.message.edit_text(
        at("role_set_done", lang, telegram_id=telegram_id, role=h(new_role)),
        parse_mode="HTML"
    )

    await state.clear()


# ==========================================
# ADMIN / STAFF ACTIONS PAGINATED
# Superadmin only
# ==========================================

def format_action_button_text(item):
    created_at = item["created_at"].strftime("%d.%m %H:%M") if item["created_at"] else "-"
    admin_name = item["admin_name"] or "Noma'lum"
    action = item["action"] or "-"

    return f"#{item['id']} | {created_at} | {admin_name[:12]} | {action[:22]}"


async def render_actions_page(target, user_id: int, page: int = 1, edit: bool = True):
    lang = await user_lang(user_id)

    limit = 10
    page = max(page, 1)
    offset = (page - 1) * limit

    actions = await get_api_superadmin_admin_actions(limit=limit, offset=offset)

    if not actions:
        text = at("no_admin_actions", lang)

        if edit:
            await target.message.edit_text(text)
        else:
            await target.answer(text)
        return

    text = at("actions_list_title", lang, page=page)

    builder = InlineKeyboardBuilder()

    for item in actions:
        builder.button(
            text=format_action_button_text(item),
            callback_data=f"staff_action_detail_{item['id']}_{page}"
        )

    if page > 1:
        builder.button(
            text=at("prev", lang),
            callback_data=f"staff_actions_page_{page - 1}"
        )

    if len(actions) == limit:
        builder.button(
            text=at("next", lang),
            callback_data=f"staff_actions_page_{page + 1}"
        )

    builder.adjust(1)

    if edit:
        await target.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    else:
        await target.answer(
            text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )


@admin_router.callback_query(F.data == "staff_actions")
async def show_staff_actions_callback(callback: types.CallbackQuery):
    if not await require_superadmin_callback(callback):
        return

    await render_actions_page(callback, callback.from_user.id, page=1, edit=True)


@admin_router.callback_query(F.data.startswith("staff_actions_page_"))
async def show_staff_actions_page(callback: types.CallbackQuery):
    if not await require_superadmin_callback(callback):
        return

    page = int(callback.data.split("_")[-1])

    await render_actions_page(callback, callback.from_user.id, page=page, edit=True)


@admin_router.callback_query(F.data.startswith("staff_action_detail_"))
async def show_staff_action_detail(callback: types.CallbackQuery):
    lang = await user_lang(callback.from_user.id)

    if not await require_superadmin_callback(callback):
        return

    parts = callback.data.split("_")
    action_id = int(parts[3])
    page = int(parts[4]) if len(parts) > 4 else 1

    item = await get_admin_action_detail(action_id)

    if not item:
        await callback.answer(at("action_not_found", lang), show_alert=True)
        return

    created_at = item["created_at"].strftime("%d.%m.%Y %H:%M:%S") if item["created_at"] else "-"

    details = item["details"] or {}

    try:
        details_text = json.dumps(details, ensure_ascii=False, indent=2)
    except Exception:
        details_text = str(details)

    if len(details_text) > 1200:
        details_text = details_text[:1200] + "\n..."

    text = (
        f"{at('action_detail_title', lang)}\n\n"
        f"🆔 Action ID: <code>{item['id']}</code>\n"
        f"👤 Admin: <b>{h(item['admin_name'])}</b>\n"
        f"🔐 Admin ID: <code>{item['admin_id']}</code>\n"
        f"🏷 Role: <b>{h(item['admin_role'])}</b>\n"
        f"⚙️ Action: <code>{h(item['action'])}</code>\n"
        f"📦 Entity: {h(item['entity_type'])} / {h(item['entity_id'])}\n"
        f"🕒 Vaqt: {created_at}\n\n"
        f"📄 Details:\n<pre>{h(details_text)}</pre>"
    )

    builder = InlineKeyboardBuilder()
    builder.button(
        text=at("back_to_actions", lang),
        callback_data=f"staff_actions_page_{page}"
    )
    builder.adjust(1)

    await callback.message.edit_text(
        text[:3900],
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@admin_router.message(F.text.in_(all_texts("admin_actions")))
async def show_admin_actions(message: types.Message):
    if not await require_superadmin_message(message):
        return

    await render_actions_page(message, message.from_user.id, page=1, edit=False)


# ==========================================
# 10. TEACHERS VIEW BY LANGUAGE
# Admin + Superadmin
# ==========================================

@admin_router.message(F.text.in_(all_texts("teachers_view")))
async def show_teacher_language_menu(message: types.Message):
    lang = await user_lang(message.from_user.id)

    builder = InlineKeyboardBuilder()

    for code, name in LANGUAGES.items():
        builder.button(
            text=name,
            callback_data=f"sa_tl_{code}"
        )

    builder.adjust(2)

    await message.answer(
        at("choose_teacher_language", lang),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@admin_router.callback_query(F.data.startswith("sa_tl_"))
async def show_teachers_by_language(callback: types.CallbackQuery):
    lang = await user_lang(callback.from_user.id)

    lang_code = callback.data.split("_")[2]
    language = LANGUAGES.get(lang_code)

    if not language:
        await callback.answer(at("language_not_found", lang), show_alert=True)
        return

    teachers = await get_api_superadmin_teachers_by_language(language)

    if not teachers:
        await callback.message.edit_text(
            f"👨‍🏫 <b>{h(language)}</b>\n\n"
            f"{at('no_teachers_by_language', lang)}",
            parse_mode="HTML"
        )
        return

    text = at("teachers_by_language_title", lang, language=h(language))
    builder = InlineKeyboardBuilder()

    for teacher in teachers:
        teacher_id = teacher["telegram_id"]
        full_name = teacher["full_name"] or "Ism yo‘q"

        text += (
            f"👤 <b>{h(full_name)}</b>\n"
            f"🆔 <code>{teacher_id}</code>\n"
            f"👥 Guruhlar: <b>{teacher['groups_count']}</b>\n"
            f"👨‍🎓 O‘quvchilar: <b>{teacher['students_count']}</b>\n\n"
        )

        builder.button(
            text=f"📚 {full_name}",
            callback_data=f"sa_tg_{teacher_id}"
        )

    builder.adjust(1)

    await callback.message.edit_text(
        text[:3900],
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@admin_router.callback_query(F.data.startswith("sa_tg_"))
async def show_teacher_groups(callback: types.CallbackQuery):
    lang = await user_lang(callback.from_user.id)

    teacher_id = int(callback.data.split("_")[2])
    groups = await get_api_superadmin_teacher_groups(teacher_id)

    if not groups:
        await callback.message.edit_text(at("teacher_no_groups", lang))
        return

    text = at("teacher_groups_title", lang, teacher_id=teacher_id)

    builder = InlineKeyboardBuilder()

    for group in groups:
        btn_text = (
            f"{group['name']} — "
            f"{group['current_count']}/{group['max_capacity']}"
        )

        builder.button(
            text=btn_text,
            callback_data=f"sa_gs_{group['id']}"
        )

    builder.adjust(1)

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


# ==========================================
# 11. GROUP STUDENTS VIEW COMPACT
# Admin + Superadmin
# ==========================================

@admin_router.callback_query(F.data.startswith("sa_gs_"))
async def show_group_students(callback: types.CallbackQuery):
    lang = await user_lang(callback.from_user.id)

    group_id = int(callback.data.split("_")[2])
    students = await get_api_superadmin_group_students(group_id)

    if not students:
        await callback.message.edit_text(at("group_has_no_students", lang))
        return

    text = at("group_students_title", lang, group_id=group_id, count=len(students))

    builder = InlineKeyboardBuilder()

    for student in students:
        student_id = student["telegram_id"]
        full_name = student["full_name"] or "Ism yo‘q"

        builder.button(
            text=f"ℹ️ {full_name}",
            callback_data=f"sa_st_{student_id}"
        )
        builder.button(
            text=at("view_results_button", lang),
            callback_data=f"sa_sr_{student_id}"
        )

    builder.adjust(2)

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@admin_router.callback_query(F.data.startswith("sa_st_"))
async def show_student_profile(callback: types.CallbackQuery):
    lang = await user_lang(callback.from_user.id)

    student_id = int(callback.data.split("_")[2])
    student = await get_api_superadmin_student_profile(student_id)

    if not student:
        await callback.message.edit_text(at("student_not_found", lang))
        return

    created_at = student["created_at"].strftime("%d.%m.%Y") if student["created_at"] else "-"

    text = (
        f"{at('student_profile_title', lang)}\n\n"
        f"👤 <b>F.I.O:</b> {h(student['full_name'])}\n"
        f"🆔 <b>Telegram ID:</b> <code>{student['telegram_id']}</code>\n"
        f"📞 <b>Telefon:</b> {h(student['phone'])}\n"
        f"📍 <b>Hudud:</b> {h(student['region'])}\n"
        f"📅 <b>Yosh:</b> {h(student['age'])}\n"
        f"🔐 <b>Role:</b> {h(student['role'])}\n"
        f"👥 <b>Guruhlar:</b> {student['groups_count']}\n"
        f"📊 <b>Baholar:</b> {student['results_count']}\n"
        f"🕒 <b>Ro‘yxatdan o‘tgan:</b> {created_at}"
    )

    builder = InlineKeyboardBuilder()
    builder.button(
        text=at("view_results_button", lang),
        callback_data=f"sa_sr_{student_id}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


# ==========================================
# 12. STUDENT RESULTS VIEW
# Admin + Superadmin
# ==========================================

@admin_router.callback_query(F.data.startswith("sa_sr_"))
async def show_student_results(callback: types.CallbackQuery):
    lang = await user_lang(callback.from_user.id)

    student_id = int(callback.data.split("_")[2])
    results = await get_api_superadmin_student_results(student_id)

    if not results:
        await callback.message.edit_text(at("no_student_results", lang))
        return

    text = at("student_results_title", lang, student_id=student_id)

    for result in results:
        created_at = result["created_at"].strftime("%d.%m.%Y") if result["created_at"] else "-"

        text += (
            f"📝 <b>{h(result['result_title'])}</b>\n"
            f"📊 Ball: <b>{h(result['score'])}</b>\n"
            f"📚 Guruh: {h(result['group_name'])}\n"
            f"👨‍🏫 Ustoz: {h(result['teacher_name'])}\n"
            f"💬 Izoh: {h(result['comment'])}\n"
            f"🕒 Sana: {created_at}\n\n"
        )

    await callback.message.edit_text(text[:3900], parse_mode="HTML")


# ==========================================
# 13. OLD STUDENTS BUTTON FALLBACK
# Admin + Superadmin
# ==========================================

@admin_router.message(F.text == "👨‍🎓 O‘quvchilarni ko‘rish")
async def show_students_overview_removed(message: types.Message):
    lang = await user_lang(message.from_user.id)

    await message.answer(at("students_removed_instruction", lang))


# ==========================================
# 14. ALL RESULTS VIEW
# Admin + Superadmin
# ==========================================

@admin_router.message(F.text.in_(all_texts("all_results")))
async def show_all_results(message: types.Message):
    lang = await user_lang(message.from_user.id)

    results = await get_api_superadmin_all_results(limit=40, offset=0)

    if not results:
        await message.answer(at("no_results", lang))
        return

    text = at("all_results_title", lang)

    for result in results:
        created_at = result["created_at"].strftime("%d.%m.%Y") if result["created_at"] else "-"

        text += (
            f"👨‍🎓 <b>{h(result['student_name'])}</b>\n"
            f"📝 {h(result['result_title'])}: <b>{h(result['score'])}</b>\n"
            f"📚 Guruh: {h(result['group_name'])}\n"
            f"👨‍🏫 Ustoz: {h(result['teacher_name'])}\n"
            f"🕒 Sana: {created_at}\n\n"
        )

    await message.answer(text[:3900], parse_mode="HTML")