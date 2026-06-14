# utils/data.py

UZB_REGIONS = {
    "Toshkent shahri": ["Yunusobod", "Chilonzor", "Mirzo Ulug'bek", "Yashnobod", "Mirobod", "Yakkasaroy", "Sergeli", "Olmazor", "Uchtepa", "Shayxontohur", "Bektemir", "Yangihayot"],
    "Sirdaryo": ["Guliston sh.", "Yangiyer sh.", "Shirin sh.", "Boyovut", "Guliston t.", "Mirzaobod", "Oqoltin", "Sardoba", "Sayxunobod", "Sirdaryo t.", "Xavos"],
    "Samarqand": ["Samarqand sh.", "Kattaqo'rg'on sh.", "Oqdaryo", "Bulung'ur", "Jomboy", "Ishtixon", "Kattaqo'rg'on t.", "Qo'shrabot", "Narpay", "Nurobod", "Payariq", "Pastdarg'om", "Paxtachi", "Samarqand t.", "Toyloq", "Urgut"],
    "Farg'ona": ["Farg'ona sh.", "Qo'qon sh.", "Marg'ilon sh.", "Beshariq", "Bog'dod", "Buvayda", "Dang'ara", "Farg'ona t.", "Furqat", "O'zbekiston", "Oltiariq", "Qo'shtepa", "Quva", "Rishton", "So'x", "Toshloq", "Uchko'prik", "Yozyovon"],
    "Toshkent viloyati": ["Nurafshon sh.", "Olmaliq sh.", "Angren sh.", "Bekobod t.", "Bo'stonliq", "Zangiota", "Qibray", "Quyichirchiq", "O'rtachirchiq", "Chinoz", "Yuqorichirchiq", "Yangiyo'l"],
    "Andijon": ["Andijon sh.", "Asaka", "Baliqchi", "Buloqboshi", "Bo'z", "Jalaquduq", "Izboskan", "Marhamat", "Oltinko'l", "Paxtaobod", "Qo'rg'ontepa", "Shahrixon", "Xo'jaobod"],
    "Buxoro": ["Buxoro sh.", "G'ijduvon", "Jondor", "Kogon", "Olot", "Peshku", "Qorako'l", "Qorovulbozor", "Romitan", "Shofirkon", "Vobkent"],
    "Jizzax": ["Jizzax sh.", "Arnasoy", "Baxmal", "Do'stlik", "Forish", "G'allaorol", "Mirzacho'l", "Paxtakor", "Yangiobod", "Zafarobod", "Zarbdor", "Zomin"],
    "Xorazm": ["Urganch sh.", "Xiva sh.", "Bog'ot", "Gurlan", "Qo'shko'pir", "Shovot", "Xonqa", "Xazorasp", "Yangiariq", "Yangibozor"],
    "Namangan": ["Namangan sh.", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq", "Namangan t.", "Norin", "Pop", "To'raqo'rg'on", "Uchqo'rg'on", "Uychi", "Yangiqo'rg'on"],
    "Navoiy": ["Navoiy sh.", "Zarafshon sh.", "Karmana", "Konimex", "Navbahor", "Nurota", "Qiziltepa", "Tomdi", "Uchquduq", "Xatirchi"],
    "Qashqadaryo": ["Qarshi sh.", "Shakhrisabz sh.", "Chiroqchi", "Dehqonobod", "G'uzor", "Qamashi", "Kasbi", "Kitob", "Koson", "Mirishkor", "Muborak", "Nishon", "Yakkabog'"],
    "Surxondaryo": ["Termiz sh.", "Angor", "Bandixon", "Boysun", "Denov", "Jarqo'rg'on", "Muzrabot", "Oltinsoy", "Qiziriq", "Qumqo'rg'on", "Sariosiyo", "Sherobod", "Sho'rchi", "Uzun"],
    "Qoraqalpog'iston": ["Nukus sh.", "Amudaryo", "Beruniy", "Chimboy", "Ellikqal'a", "Kegeyli", "Mo'ynoq", "Nukus t.", "Qanliko'l", "Qo'ng'irot", "Qorao'zak", "Shumanay", "Taxtako'pir", "To'rtko'l", "Xo'jayli"]
}

LANGUAGES = {
    "eng": "🇬🇧 Ingliz tili",
    "rus": "🇷🇺 Rus tili",
    "ger": "🇩🇪 Nemis tili",
    "ara": "🇸🇦 Arab tili"
}

PACKAGES = {
    "group": "👥 Guruh (10 kishi) - 3 oylik",
    "solo": "👤 Individual (Yakka tartibda)"
}