# utils/i18n.py

TEXTS = {
    "choose_language": {
        "uz": "Iltimos, bot tilini tanlang:",
        "ru": "Пожалуйста, выберите язык бота:",
        "en": "Please choose the bot language:",
    },

    "language_saved": {
        "uz": "✅ Til saqlandi.",
        "ru": "✅ Язык сохранён.",
        "en": "✅ Language saved.",
    },

    "welcome": {
        "uz": "Assalomu alaykum! Visa & Language Consulting tizimiga xush kelibsiz.\n\nTizimdan qanday maqsadda foydalanmoqchisiz?",
        "ru": "Здравствуйте! Добро пожаловать в систему Visa & Language Consulting.\n\nКак вы хотите использовать систему?",
        "en": "Hello! Welcome to Visa & Language Consulting.\n\nHow would you like to use the system?",
    },

    "student_register": {
        "uz": "👨‍🎓 O'quvchi bo'lib o'qish",
        "ru": "👨‍🎓 Учиться как студент",
        "en": "👨‍🎓 Study as a student",
    },

    "teacher_register": {
        "uz": "👨‍🏫 Ustoz bo'lib ishlash",
        "ru": "👨‍🏫 Работать преподавателем",
        "en": "👨‍🏫 Work as a teacher",
    },

    "courses": {
        "uz": "📚 Kurslar",
        "ru": "📚 Курсы",
        "en": "📚 Courses",
    },

    "profile": {
        "uz": "👤 Profil",
        "ru": "👤 Профиль",
        "en": "👤 Profile",
    },

    "my_lessons": {
        "uz": "📖 Mening darslarim",
        "ru": "📖 Мои уроки",
        "en": "📖 My lessons",
    },

    "mini_app": {
        "uz": "🚀 Mini App ochish",
        "ru": "🚀 Открыть Mini App",
        "en": "🚀 Open Mini App",
    },

    "admin_manage": {
        "uz": "👥 Xodimlarni boshqarish",
        "ru": "👥 Управление сотрудниками",
        "en": "👥 Staff management",
    },

    "teachers_view": {
        "uz": "👨‍🏫 Ustozlarni ko‘rish",
        "ru": "👨‍🏫 Преподаватели",
        "en": "👨‍🏫 Teachers",
    },

    "create_group": {
        "uz": "➕ Guruh yaratish",
        "ru": "➕ Создать группу",
        "en": "➕ Create group",
    },

    "groups_list": {
        "uz": "📚 Guruhlar ro'yxati",
        "ru": "📚 Список групп",
        "en": "📚 Groups list",
    },

    "all_results": {
        "uz": "📊 Barcha natijalar",
        "ru": "📊 Все результаты",
        "en": "📊 All results",
    },

    "admin_actions": {
        "uz": "📌 Admin harakatlari",
        "ru": "📌 Действия админов",
        "en": "📌 Admin actions",
    },

    "statistics": {
        "uz": "📊 Statistika",
        "ru": "📊 Статистика",
        "en": "📊 Statistics",
    },

    "teacher_welcome": {
        "uz": "👨‍🏫 Assalomu alaykum, Ustoz! Ish paneliga xush kelibsiz.",
        "ru": "👨‍🏫 Здравствуйте, преподаватель! Добро пожаловать в рабочую панель.",
        "en": "👨‍🏫 Hello, Teacher! Welcome to your work panel.",
    },

    "student_home": {
        "uz": "🏠 Asosiy menyuga qaytdingiz.",
        "ru": "🏠 Вы вернулись в главное меню.",
        "en": "🏠 You are back to the main menu.",
    },

    "admin_welcome": {
        "uz": "👨‍💻 Assalomu alaykum, Admin! Boshqaruv paneliga xush kelibsiz.",
        "ru": "👨‍💻 Здравствуйте, Admin! Добро пожаловать в панель управления.",
        "en": "👨‍💻 Hello, Admin! Welcome to the control panel.",
    },

    "superadmin_welcome": {
        "uz": "👑 Assalomu alaykum, Superadmin! Boshqaruv paneliga xush kelibsiz.",
        "ru": "👑 Здравствуйте, Superadmin! Добро пожаловать в панель управления.",
        "en": "👑 Hello, Superadmin! Welcome to the control panel.",
    },
    "accountant_welcome": {
        "uz": "💰 Assalomu alaykum! Accounting panelga xush kelibsiz.",
        "ru": "💰 Здравствуйте! Добро пожаловать в панель бухгалтерии.",
        "en": "💰 Hello! Welcome to the accounting panel.",
    },
    "accounting_panel": {
        "uz": "💰 Accounting panel",
        "ru": "💰 Бухгалтерия",
        "en": "💰 Accounting",
    },
}


def t(key: str, lang: str = "uz") -> str:
    item = TEXTS.get(key, {})
    return item.get(lang) or item.get("uz") or key


def all_texts(key: str):
    item = TEXTS.get(key, {})
    return list(item.values())