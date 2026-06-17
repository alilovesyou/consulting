# consulting
python 3.12.3

# Visa & Language Consulting Telegram Bot — Foydalanish Qo‘llanmasi

Ushbu hujjat Telegram botdan qanday foydalanishni oddiy va tushunarli tarzda tushuntiradi. Bot o‘quvchilarni ro‘yxatdan o‘tkazish, kurs tanlash, to‘lovlarni qabul qilish, admin tomonidan tasdiqlash, ustozlarni boshqarish, dars yuklash va o‘quvchi natijalarini yuritish uchun ishlatiladi.

---

## 1. Botdagi asosiy rollar

Botda 4 ta asosiy rol mavjud:

| Rol        | Vazifasi                                                                              |
| ---------- | ------------------------------------------------------------------------------------- |
| O‘quvchi   | Ro‘yxatdan o‘tadi, kurs tanlaydi, to‘lov qiladi, darslarni ko‘radi                    |
| Ustoz      | O‘z guruhlarini ko‘radi, dars yuklaydi, natija kiritadi, chetlatish so‘rovi yuboradi  |
| Admin      | To‘lovlarni tasdiqlaydi, guruh yaratadi, ustozlarni tasdiqlaydi, statistikani ko‘radi |
| Superadmin | Telegram bot ichida admin kabi ishlaydi va yuqori nazorat huquqiga ega                |

---

## 2. Asosiy komandalar

Botda asosiy komandalar kam. Ko‘p ishlar tugmalar orqali bajariladi.

| Komanda     | Kim ishlatadi | Vazifasi                                                       |
| ----------- | ------------- | -------------------------------------------------------------- |
| `/start`    | Hamma         | Botni boshlash yoki asosiy menyuga qaytish                     |
| `/group_ID` | Faqat ustoz   | Ma’lum guruhni boshqarish panelini ochish. Masalan: `/group_1` |

Misol:

```text
/group_1
```

Bu komanda 1-ID raqamli guruhning boshqaruv panelini ochadi. Faqat shu guruhga biriktirilgan ustoz foydalana oladi.

---

# 3. O‘quvchi uchun foydalanish tartibi

## 3.1. Botga kirish

O‘quvchi botga kiradi va quyidagini bosadi:

```text
/start
```

Bot quyidagi tanlovni chiqaradi:

```text
👨‍🎓 O'quvchi bo'lib o'qish
👨‍🏫 Ustoz bo'lib ishlash
```

O‘quvchi quyidagini tanlaydi:

```text
👨‍🎓 O'quvchi bo'lib o'qish
```

---

## 3.2. O‘quvchi ro‘yxatdan o‘tishi

Bot o‘quvchidan quyidagi ma’lumotlarni so‘raydi:

1. F.I.O
2. Telefon raqam
3. Viloyat
4. Tuman/shahar
5. Yosh

Oxirida bot kiritilgan ma’lumotlarni ko‘rsatadi va tasdiqlashni so‘raydi.

Tugmalar:

```text
✅ Tasdiqlash
✏️ Tahrirlash (Boshidan)
```

Agar ma’lumotlar to‘g‘ri bo‘lsa, o‘quvchi `✅ Tasdiqlash` tugmasini bosadi.

Shundan keyin o‘quvchi asosiy menyuga tushadi.

---

## 3.3. O‘quvchi asosiy menyusi

O‘quvchi menyusida quyidagi tugmalar bo‘ladi:

```text
📖 Mening darslarim
📚 Kurslar
👤 Profil
```

---

## 3.4. Kurs tanlash

O‘quvchi quyidagini bosadi:

```text
📚 Kurslar
```

Bot mavjud tillarni chiqaradi:

```text
🇬🇧 Ingliz tili
🇷🇺 Rus tili
🇩🇪 Nemis tili
🇸🇦 Arab tili
```

O‘quvchi kerakli tilni tanlaydi.

Keyin bot o‘qish formatini chiqaradi:

```text
👥 Guruh (10 kishi) - 3 oylik
👤 Individual (Yakka tartibda)
```

O‘quvchi kerakli paketni tanlaydi.

---

## 3.5. To‘lov qilish

Paket tanlangandan keyin bot to‘lov turini so‘raydi:

```text
💳 Karta orqali
💵 Naqd pul orqali
```

### Karta orqali to‘lov

Agar o‘quvchi `💳 Karta orqali` ni tanlasa, bot karta ma’lumotlarini beradi.

O‘quvchi to‘lov qilgandan keyin chek rasmini yoki PDF faylini botga yuboradi.

Bot chekni qabul qiladi va adminga yuboradi.

O‘quvchiga quyidagi mazmunda xabar boradi:

```text
Chek qabul qilindi.
Adminlar to‘lovni tekshirib, tez orada javob berishadi.
```

### Naqd pul orqali to‘lov

Agar o‘quvchi `💵 Naqd pul orqali` ni tanlasa, bot ofis manzilini beradi.

Admin tizimda bu to‘lovni ko‘radi va o‘quvchi kelib to‘lov qilgandan keyin tasdiqlaydi.

---

## 3.6. To‘lov tasdiqlangandan keyin

Admin to‘lovni tasdiqlasa, o‘quvchi guruhga biriktiriladi.

O‘quvchiga Telegram guruh havolasi yuboriladi:

```text
Tabriklaymiz! Sizning to‘lovingiz tasdiqlandi.
Siz guruhga biriktirildingiz.
Guruhga qo‘shilish havolasi:
https://t.me/...
```

---

## 3.7. O‘quvchi darslarini ko‘rishi

O‘quvchi quyidagini bosadi:

```text
📖 Mening darslarim
```

Bot o‘quvchi qo‘shilgan guruhlarni chiqaradi.

O‘quvchi guruhni tanlaydi.

Keyin bot shu guruhdagi darslarni ko‘rsatadi.

O‘quvchi darsni tanlasa, bot unga video, rasm yoki hujjat faylini yuboradi.

---

## 3.8. O‘quvchi profilini ko‘rish

O‘quvchi quyidagini bosadi:

```text
👤 Profil
```

Bot quyidagi ma’lumotlarni ko‘rsatadi:

* F.I.O
* Telefon
* Hudud
* Yosh
* Status

Status quyidagilardan biri bo‘lishi mumkin:

```text
🆕 Yangi O'quvchi
⏳ To'lov tasdig'i kutilmoqda
✅ Tasdiqlangan O'quvchi
❌ To'lov cheki rad etilgan
```

---

# 4. Ustoz uchun foydalanish tartibi

## 4.1. Ustoz bo‘lib ariza topshirish

Yangi foydalanuvchi botga kiradi:

```text
/start
```

Keyin quyidagini tanlaydi:

```text
👨‍🏫 Ustoz bo'lib ishlash
```

Bot ustozdan quyidagi ma’lumotlarni so‘raydi:

1. F.I.O
2. Telefon raqam
3. Viloyat
4. Tuman/shahar
5. Yosh
6. Qaysi til/fanni o‘qitishi
7. Tajriba yoki CV

Tajriba matn ko‘rinishida yozilishi mumkin.

CV esa quyidagi formatlarda yuborilishi mumkin:

```text
PDF
DOCX
Rasm
```

Oxirida bot ma’lumotlarni tekshirish uchun ko‘rsatadi.

Tugmalar:

```text
✅ Tasdiqlash va Yuborish
✏️ Tahrirlash (Boshidan)
```

Ustoz `✅ Tasdiqlash va Yuborish` tugmasini bosgandan keyin ariza adminga yuboriladi.

---

## 4.2. Ustoz arizasi holati

Agar ariza hali ko‘rib chiqilayotgan bo‘lsa, ustoz `/start` bosganda quyidagini ko‘radi:

```text
Sizning ustozlik arizangiz ma'muriyat tomonidan ko'rib chiqilmoqda.
```

Agar admin ustozni tasdiqlasa, ustozga xabar boradi.

Keyin ustoz `/start` bosib o‘z paneliga kiradi.

---

## 4.3. Ustoz asosiy menyusi

Tasdiqlangan ustoz menyusida quyidagi tugmalar bo‘ladi:

```text
📚 Mening guruhlarim
📝 Natija kiritish
❌ Chetlatish so'rovi
👤 Profil
```

---

## 4.4. Ustoz o‘z guruhlarini ko‘rishi

Ustoz quyidagini bosadi:

```text
📚 Mening guruhlarim
```

Bot ustozga biriktirilgan guruhlarni ko‘rsatadi.

Har bir guruh yonida boshqaruv komandasi chiqadi:

```text
/group_1
/group_2
/group_3
```

Ustoz kerakli guruh komandasi orqali guruh panelini ochadi.

Masalan:

```text
/group_1
```

Muhim: ustoz faqat o‘ziga biriktirilgan guruhni boshqara oladi. Boshqa guruh ID sini yozsa, bot ruxsat bermaydi.

---

## 4.5. Guruh paneli

Ustoz `/group_ID` komandasini yuborganda guruh boshqaruv paneli ochiladi.

Panelda quyidagi tugmalar chiqadi:

```text
➕ Dars yuklash
👥 O'quvchilar
```

---

## 4.6. Dars yuklash

Ustoz guruh panelida quyidagini bosadi:

```text
➕ Dars yuklash
```

Bot dars mavzusini so‘raydi.

Masalan:

```text
1-Dars. Present Simple
```

Keyin bot dars materialini yuborishni so‘raydi.

Ustoz quyidagi fayl turlaridan birini yuborishi mumkin:

```text
Video
PDF
Rasm
Hujjat
```

Bot faylni saqlaydi va darsni o‘quvchilar uchun ochadi.

---

## 4.7. Guruhdagi o‘quvchilarni ko‘rish

Ustoz guruh panelida quyidagini bosadi:

```text
👥 O'quvchilar
```

Bot guruhdagi o‘quvchilar ro‘yxatini chiqaradi:

* F.I.O
* Telefon raqam

---

## 4.8. Natija kiritish

Ustoz asosiy menyudan quyidagini bosadi:

```text
📝 Natija kiritish
```

Jarayon:

1. Ustoz guruhni tanlaydi
2. O‘quvchini tanlaydi
3. Natija nomini yozadi
4. Ball yoki bahoni yozadi
5. Izoh yozadi

Misol:

```text
Natija nomi: 1-test
Ball: 85/100
Izoh: Yaxshi natija
```

Agar izoh bo‘lmasa, ustoz `-` yuborishi mumkin.

Natija saqlangandan keyin o‘quvchiga xabar boradi.

---

## 4.9. Chetlatish so‘rovi yuborish

Agar o‘quvchi darslarga qatnashmasa yoki o‘zlashtirmasa, ustoz adminga chetlatish so‘rovi yuborishi mumkin.

Ustoz quyidagini bosadi:

```text
❌ Chetlatish so'rovi
```

Jarayon:

1. Guruh tanlanadi
2. O‘quvchi tanlanadi
3. Chetlatish sababi yoziladi

Misol sabab:

```text
3 marta darsga kelmadi, testlarni topshirmadi.
```

So‘rov adminga yuboriladi.

Admin tasdiqlasa, o‘quvchi guruhdan chiqariladi.

---

# 5. Admin uchun foydalanish tartibi

## 5.1. Admin botga kirishi

Admin botga kiradi:

```text
/start
```

Agar admin roli oldindan berilgan bo‘lsa, bot admin panelini chiqaradi.

Admin menyusi:

```text
➕ Guruh yaratish
📚 Guruhlar ro'yxati
📊 Statistika
```

---

## 5.2. To‘lovlarni tasdiqlash

O‘quvchi karta orqali chek yuborsa yoki naqd to‘lovni tanlasa, adminga avtomatik xabar keladi.

Admin xabar ichida quyidagi tugmalarni ko‘radi:

```text
✅ Tasdiqlash
❌ Rad etish
```

### To‘lovni tasdiqlash

Admin `✅ Tasdiqlash` tugmasini bosadi.

Bot faol guruhlar ro‘yxatini chiqaradi.

Har bir guruhda sig‘im ko‘rsatiladi:

```text
Ingliz tili - 1-guruh — 5/10
```

Admin o‘quvchini qaysi guruhga qo‘shishni tanlaydi.

Agar guruh to‘lmagan bo‘lsa, o‘quvchi guruhga qo‘shiladi va unga guruh havolasi yuboriladi.

Agar guruh to‘lgan bo‘lsa, bot adminni ogohlantiradi.

### To‘lovni rad etish

Admin `❌ Rad etish` tugmasini bossa, to‘lov rad etiladi.

O‘quvchiga chek tasdiqlanmagani haqida xabar yuboriladi.

---

## 5.3. Ustoz arizasini ko‘rib chiqish

Yangi ustoz ariza yuborsa, adminga avtomatik xabar keladi.

Admin arizada quyidagilarni ko‘radi:

* F.I.O
* Telefon
* Hudud
* Yosh
* Fan yoki til
* Tajriba yoki CV

Admin tugmalardan birini bosadi:

```text
✅ Ishga qabul qilish
❌ Rad etish
```

Agar admin qabul qilsa, foydalanuvchi ustoz roliga o‘tadi.

Agar rad etsa, foydalanuvchiga rad etilgani haqida xabar boradi.

---

## 5.4. Guruh yaratish

Admin quyidagini bosadi:

```text
➕ Guruh yaratish
```

Bot ketma-ket quyidagi ma’lumotlarni so‘raydi:

1. Guruh nomi
2. Til yoki fan
3. Guruh sig‘imi
4. Telegram guruh havolasi
5. Ustoz tanlash

Misol:

```text
Guruh nomi: Ingliz tili - 1-guruh
Til: Ingliz tili
Sig‘im: 10
Telegram link: https://t.me/...
Ustoz: Aliyev Ali
```

Oxirida bot guruh yaratilganini tasdiqlaydi.

---

## 5.5. Guruhlar ro‘yxatini boshqarish

Admin quyidagini bosadi:

```text
📚 Guruhlar ro'yxati
```

Bot faol guruhlarni chiqaradi.

Admin guruhni tanlaydi.

Keyin quyidagi imkoniyatlar chiqadi:

```text
🔄 Ustozni almashtirish
❌ Guruhni o'chirish
```

### Ustozni almashtirish

Admin `🔄 Ustozni almashtirish` tugmasini bosadi.

Bot mavjud ustozlar ro‘yxatini chiqaradi.

Admin yangi ustozni tanlaydi.

Guruh ustozga qayta biriktiriladi.

### Guruhni o‘chirish

Admin `❌ Guruhni o'chirish` tugmasini bosadi.

Guruh tizimdan butunlay o‘chmaydi, faqat faol emas holatga o‘tkaziladi.

Bu xavfsiz usul hisoblanadi.

---

## 5.6. Statistikani ko‘rish

Admin quyidagini bosadi:

```text
📊 Statistika
```

Bot umumiy statistikani chiqaradi:

```text
Jami o‘quvchilar
Jami ustozlar
Faol guruhlar
```

---

## 5.7. Chetlatish so‘rovlarini ko‘rib chiqish

Ustoz o‘quvchini chetlatish so‘rovi yuborsa, adminga avtomatik xabar keladi.

Admin xabarda quyidagilarni ko‘radi:

* So‘rov ID
* Ustoz
* O‘quvchi
* Guruh
* Sabab

Admin tugmalardan birini tanlaydi:

```text
✅ Chetlatishni tasdiqlash
❌ Rad etish
```

Agar admin tasdiqlasa:

* O‘quvchi guruhdan chiqariladi
* Ustozga tasdiqlangani haqida xabar boradi
* O‘quvchiga guruhdan chiqarilgani haqida xabar boradi

Agar admin rad etsa:

* So‘rov rad etiladi
* Ustozga rad etilgani haqida xabar boradi

---

# 6. Superadmin uchun foydalanish tartibi

Telegram bot ichida superadmin admin panel imkoniyatlaridan foydalanadi.

Superadmin ham quyidagilarni qila oladi:

```text
➕ Guruh yaratish
📚 Guruhlar ro'yxati
📊 Statistika
To‘lovlarni tasdiqlash
Ustoz arizalarini tasdiqlash
Chetlatish so‘rovlarini tasdiqlash
```

Hozirgi Telegram bot ichida superadmin uchun alohida maxsus menyu yo‘q. Superadmin admin panel bilan bir xil ishlaydi, faqat tizimda yuqori rol sifatida saqlanadi.

---

# 7. Oddiy ish jarayoni

Quyidagi jarayon botning asosiy ishlash tartibini ko‘rsatadi.

## 7.1. O‘quvchi kursga yozilishi

```text
O‘quvchi /start bosadi
↓
O‘quvchi bo‘lib o‘qish ni tanlaydi
↓
Ro‘yxatdan o‘tadi
↓
Kurs tanlaydi
↓
To‘lov turini tanlaydi
↓
Chek yuboradi yoki naqd to‘lovni tanlaydi
↓
Admin tasdiqlaydi
↓
Admin guruh tanlaydi
↓
O‘quvchi guruh havolasini oladi
```

---

## 7.2. Ustoz ishga kirishi

```text
Ustoz /start bosadi
↓
Ustoz bo‘lib ishlash ni tanlaydi
↓
Anketa to‘ldiradi
↓
CV yoki tajriba yuboradi
↓
Admin arizani ko‘radi
↓
Admin qabul qiladi
↓
Ustoz /start orqali panelga kiradi
```

---

## 7.3. Dars yuklash

```text
Ustoz /start bosadi
↓
Mening guruhlarim ni tanlaydi
↓
/group_ID komandasini yuboradi
↓
Dars yuklash tugmasini bosadi
↓
Dars mavzusini yozadi
↓
Video/PDF/Rasm yuboradi
↓
Dars o‘quvchilar uchun ochiladi
```

---

## 7.4. Natija kiritish

```text
Ustoz Natija kiritish tugmasini bosadi
↓
Guruhni tanlaydi
↓
O‘quvchini tanlaydi
↓
Natija nomini yozadi
↓
Ballni yozadi
↓
Izoh yozadi
↓
Natija saqlanadi
↓
O‘quvchiga xabar boradi
```

---

## 7.5. O‘quvchini chetlatish

```text
Ustoz Chetlatish so‘rovi tugmasini bosadi
↓
Guruhni tanlaydi
↓
O‘quvchini tanlaydi
↓
Sabab yozadi
↓
Admin so‘rovni oladi
↓
Admin tasdiqlaydi yoki rad etadi
↓
Tasdiqlansa, o‘quvchi guruhdan chiqariladi
```

---

# 8. Botda ishlatiladigan tugmalar ro‘yxati

## Umumiy tugmalar

```text
/start
👤 Profil
🔙 Orqaga
```

## O‘quvchi tugmalari

```text
👨‍🎓 O'quvchi bo'lib o'qish
📚 Kurslar
📖 Mening darslarim
👤 Profil
💳 Karta orqali
💵 Naqd pul orqali
```

## Ustoz tugmalari

```text
👨‍🏫 Ustoz bo'lib ishlash
📚 Mening guruhlarim
📝 Natija kiritish
❌ Chetlatish so'rovi
➕ Dars yuklash
👥 O'quvchilar
```

## Admin tugmalari

```text
➕ Guruh yaratish
📚 Guruhlar ro'yxati
📊 Statistika
✅ Tasdiqlash
❌ Rad etish
✅ Ishga qabul qilish
🔄 Ustozni almashtirish
❌ Guruhni o'chirish
✅ Chetlatishni tasdiqlash
```

---

# 9. Muhim eslatmalar

1. O‘quvchi to‘lov qilmaguncha guruhga qo‘shilmaydi.
2. Admin to‘lovni tasdiqlagandan keyingina o‘quvchiga guruh havolasi yuboriladi.
3. Guruh sig‘imi to‘lgan bo‘lsa, yangi o‘quvchi shu guruhga qo‘shilmaydi.
4. Ustoz faqat o‘ziga biriktirilgan guruhni boshqara oladi.
5. Oddiy foydalanuvchi admin funksiyalaridan foydalana olmaydi.
6. Guruh o‘chirilganda bazadan butunlay o‘chmaydi, faqat faol emas holatiga o‘tadi.
7. Ustoz yuklagan darslar o‘quvchilarga bot orqali yuboriladi.
8. O‘quvchi chetlatilishi faqat admin tasdiqlagandan keyin amalga oshadi.

---

# 10. Qisqa xulosa

Telegram bot kompaniya uchun o‘quv markazini boshqaruvchi avtomatlashtirilgan tizim sifatida ishlaydi.

Bot orqali:

* O‘quvchilar ro‘yxatdan o‘tadi
* Kurs tanlaydi
* To‘lov qiladi
* Admin to‘lovni tasdiqlaydi
* O‘quvchi guruhga qo‘shiladi
* Ustoz dars yuklaydi
* Ustoz natija kiritadi
* Admin barcha asosiy jarayonlarni nazorat qiladi

Bu tizim qo‘lda ro‘yxat yuritish, guruh havolasini qo‘lda yuborish, cheklarni alohida tekshirish va ustoz/o‘quvchi nazoratini qo‘lda bajarish ishlarini ancha osonlashtiradi.
