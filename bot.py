import logging
import os
import json
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Update,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===================== SOZLAMALAR =====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8932867764:AAFd-2yHxCqWBcnjQoK3Wy03T2hx3S04iCE")
ADMIN_ID = 692744901

KARTA_RAQAM = "9860 3566 1848 3396"
KARTA_EGA_SI = "J.F."
FIXED_COMMISSION = 4000 

REGIONS = {
    "Andijon viloyati": ["Andijon sh.", "Andijon t.", "Asaka t.", "Baliqchi t.", "Bo'ston t.", "Buloqboshi t.", "Izboskan t.", "Jalaquduq t.", "Marhamat t.", "Oltinko'l t.", "Paxtaobod t.", "Xo'jaobod t.", "Shahrixon t.", "Xonobod sh."],
    "Buxoro viloyati": ["Buxoro sh.", "Buxoro t.", "Kogon sh.", "Kogon t.", "Olot t.", "G'ijduvon t.", "Jondor t.", "Qorako'l t.", "Peshku t.", "Romitan t.", "Shofirkon t.", "Vobkent t."],
    "Farg'ona viloyati": ["Farg'ona sh.", "Farg'ona t.", "Marg'ilon sh.", "Qo'qon sh.", "Quva t.", "Quvasoy sh.", "Oltiariq t.", "Bag'dod t.", "Beshariq t.", "Buvayda t.", "Dang'ara t.", "Yozyovon t.", "Qo'shtepa t.", "Rishton t.", "So'x t.", "Toshloq t.", "Uchko'prik t.", "O'zbekiston t."],
    "Jizzax viloyati": ["Jizzax sh.", "Arnasoy t.", "G'allaorol t.", "Sharaf Rashidov t.", "Do'stlik t.", "Zomin t.", "Zarbdor t.", "Zafarobod t.", "Mirzacho'l t.", "Paxtakor t.", "Forish t.", "Baxmal t.", "Yangiobod t."],
    "Xorazm viloyati": ["Urganch sh.", "Urganch t.", "Xiva sh.", "Xiva t.", "Bog'ot t.", "Gurlan t.", "Qo'shko'pir t.", "Shovot t.", "Xonqa t.", "Hazorasp t.", "Yangiariq t.", "Yangibozor t.", "Tuproqqal'a t."],
    "Namangan viloyati": ["Namangan sh.", "Chartaq t.", "Chust t.", "Kosonsoy t.", "Mingbuloq t.", "Namangan t.", "Naryn t.", "Pop t.", "To'raqo'rg'on t.", "Uychi t.", "Uchqo'rg'on t.", "Yangiqo'rg'on t."],
    "Navoiy viloyati": ["Navoiy sh.", "Zarafshon sh.", "Karmana t.", "Konimex t.", "Qiziltepa t.", "Navbahor t.", "Nurota t.", "Tomdi t.", "Uchquduq t.", "Xatirchi t."],
    "Qashqadaryo viloyati": ["Karshi sh.", "Karshi t.", "Shaxrisabz sh.", "Shaxrisabz t.", "Dehqonobod t.", "Kasbi t.", "Kitob t.", "Koson t.", "Mirishkor t.", "Muborak t.", "Nishon t.", "Chiroqchi t.", "Ko'kdala t.", "Kamashi t.", "Yakkabog' t."],
    "Samarqand viloyati": ["Samarqand sh.", "Samarqand t.", "Oqdaryo t.", "Bulung'ur t.", "Jomboy t.", "Ishtixon t.", "Kattaqo'rg'on sh.", "Kattaqo'rg'on t.", "Qo'shrabot t.", "Narpay t.", "Nurobod t.", "Payariq t.", "Pasdarg'om t.", "Paxtachi t.", "Toyloq t.", "Urgut t."],
    "Sirdaryo viloyati": ["Guliston sh.", "Guliston t.", "Shirin sh.", "Yangiyer sh.", "Boyovut t.", "Oqoltin t.", "Sardoba t.", "Sayxunobod t.", "Sirdaryo t.", "Xavast t.", "Mirzaobod t."],
    "Surxondaryo viloyati": ["Termiz sh.", "Termiz t.", "Angor t.", "Boysun t.", "Denov t.", "Jarqo'rg'on t.", "Qiziriq t.", "Qumqo'rg'on t.", "Muzrabot t.", "Oltinsoy t.", "Sariosiyo t.", "Sherobod t.", "Sho'rchi t.", "Uzun t."],
    "Toshkent shahri": ["Bektemir r.", "Chilonzor r.", "Yashnobod r.", "Mirobod r.", "Mirzo Ulug'bek r.", "Olmazor r.", "Sergeli r.", "Shayxontohur r.", "Uchtepa r.", "Yakkasaroy r.", "Yunusobod r.", "Yangihayot r."],
    "Toshkent viloyati": ["Nurafshon sh.", "Angren sh.", "Olmaliq sh.", "Chirchiq sh.", "Bekobod sh.", "Bekobod t.", "Bo'tonliq t.", "Bo'ka t.", "Chinoz t.", "Qibray t.", "Ohangaron t.", "Parkent t.", "Piskent t.", "Quyi Chirchiq t.", "O'rtachirchiq t.", "Yangiyo'l t.", "Yuqori Chirchiq t.", "Zangiota t."],
    "Qoraqalpog'iston": ["Nukus sh.", "Amudaryo t.", "Beruniy t.", "Chimboy t.", "Ellikqal'a t.", "Kegeyli t.", "Mo'ynoq t.", "Nukus t.", "Qonliko'l t.", "Qorauzaq t.", "Qo'ng'irot t.", "Shumanay t.", "Taxtako'pir t.", "To'rtko'l t.", "Xo'jayli t.", "Taxiatosh sh.", "Bo'zatov t."]
}

REG_KEYS = list(REGIONS.keys())

# HOLATLAR (STATES)
(
    LANG, ROLE,
    C_REGION, C_DISTRICT, C_TARGET, C_DESC, C_TIME, C_PHONE, C_LOCATION, C_CONFIRM,
    W_REGION, W_DISTRICT, W_NAME, W_CAR_MODEL, W_CAR_COLOR, W_CAR_NUMBER, W_PHONE, W_CONFIRM,
    PAY_AMOUNT, CH_REGION, CH_DISTRICT
) = range(21)

DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                workers = {int(k): v for k, v in loaded.get("workers", {}).items()}
                orders = {int(k): v for k, v in loaded.get("orders", {}).items()}
                counter = loaded.get("order_counter", [1])
                return workers, orders, counter
        except Exception as e:
            logger.error(f"Bazani yuklashda xato: {e}")
            return {}, {}, [1]
    return {}, {}, [1]

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"workers": workers, "orders": orders, "order_counter": order_counter}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Bazaga yozishda xato: {e}")

workers, orders, order_counter = load_data()

# ===================== MENYULAR =====================
def start_menu_keyboard(lang="uz"):
    text = "🚀 Botni boshlash / Rol tanlash" if lang == "uz" else "🚀 Запустить бота / Выбор роли"
    return ReplyKeyboardMarkup([[KeyboardButton(text)]], resize_keyboard=True)

def client_menu_keyboard(lang="uz"):
    if lang == "uz":
        return ReplyKeyboardMarkup([[KeyboardButton("📦 Yuk yuborish (Buyurtma)")], [KeyboardButton("ℹ️ Yordam / Ma'lumot")]], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([[KeyboardButton("📦 Отправить груз (Заказ)")], [KeyboardButton("ℹ️ Помощь / Информация")]], resize_keyboard=True)

def driver_menu_keyboard(lang="uz"):
    if lang == "uz":
        return ReplyKeyboardMarkup([
            [KeyboardButton("🔍 Buyurtmalarni qidirish")],
            [KeyboardButton("💳 Shaxsiy Kabinet (Haydovchilar)"), KeyboardButton("ℹ️ Yordam / Ma'lumot")]
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([
            [KeyboardButton("🔍 Поиск заказов")],
            [KeyboardButton("💳 Личный кабинет (Водители)"), KeyboardButton("ℹ️ Помощь / Информация")]
        ], resize_keyboard=True)

def regions_keyboard(prefix="reg_"):
    kb = []
    row = []
    for idx, region in enumerate(REG_KEYS):
        row.append(InlineKeyboardButton(region, callback_data=f"{prefix}{idx}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    return InlineKeyboardMarkup(kb)

def districts_keyboard(region_idx, prefix="dist_", back_callback="back_region"):
    region_name = REG_KEYS[int(region_idx)]
    districts = REGIONS.get(region_name, [])
    kb = []
    row = []
    for d_idx, d in enumerate(districts):
        row.append(InlineKeyboardButton(d, callback_data=f"{prefix}{d_idx}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    kb.append([InlineKeyboardButton("🔙 Orqaga / Назад", callback_data=back_callback)])
    return InlineKeyboardMarkup(kb)

# ===================== START QISMI =====================
async def start(update: Update, context):
    uid = update.effective_user.id
    msg = update.message if update.message else update.callback_query.message
    
    if uid in workers:
        w = workers[uid]
        lang = w.get("lang", "uz")
        context.user_data["lang"] = lang 
        
        if w.get("approved"):
            if lang == "uz":
                await msg.reply_text("<b>Xush kelibsiz, haydovchi!</b>\nSiz tizimda mavjudsiz. Balans va hisobingiz tiklandi.", reply_markup=driver_menu_keyboard("uz"), parse_mode="HTML")
            else:
                await msg.reply_text("<b>Добро пожаловать, водитель!</b>\nВы уже есть в системе. Ваш баланс и данные восстановлены.", reply_markup=driver_menu_keyboard("ru"), parse_mode="HTML")
            return ConversationHandler.END
        else:
            if lang == "uz":
                await msg.reply_text("<b>Sizning arizangiz hali ko'rib chiqilmoqda.</b>\nAdmin tasdiqlashini kuting.", parse_mode="HTML")
            else:
                await msg.reply_text("<b>Ваша заявка все еще на рассмотрении.</b>\nПожалуйста, дождитесь подтверждения админа.", parse_mode="HTML")
            return ConversationHandler.END

    context.user_data.clear() 

    kb = [
        [InlineKeyboardButton("🇺🇿 O'ZBEKCHA", callback_data="lang_uz")],
        [InlineKeyboardButton("🇷🇺 РУССКИЙ", callback_data="lang_ru")]
    ]
    await msg.reply_text(
        "✨ <b>Labo yuk tashish xizmatiga xush kelibsiz! / Добро пожаловать в службу грузоперевозок Labo!</b>\n\n"
        "Davom etish uchun tilni tanlang:\nВыберите язык для продолжения:", 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode="HTML"
    )
    return LANG

async def select_lang(update: Update, context):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    context.user_data["lang"] = lang
    
    if lang == "uz":
        kb = [
            [InlineKeyboardButton("Mijoz (Yuk yuborish) 📦", callback_data="role_client")],
            [InlineKeyboardButton("Labochi (Haydovchi bo'lib ro'yxatdan o'tish) 🛺", callback_data="role_worker")],
        ]
        await query.edit_message_text("Botdan qanday maqsadda foydalanmoqchisiz? Tanlang:", reply_markup=InlineKeyboardMarkup(kb))
    else:
        kb = [
            [InlineKeyboardButton("Клиент (Отправить груз) 📦", callback_data="role_client")],
            [InlineKeyboardButton("Водитель (Регистрация как водитель) 🛺", callback_data="role_worker")],
        ]
        await query.edit_message_text("С какой целью вы используете бота? Выберите:", reply_markup=InlineKeyboardMarkup(kb))
    return ROLE

async def role_sel(update: Update, context):
    query = update.callback_query
    await query.answer()
    role = query.data.split("_")[1]
    context.user_data["role"] = role
    lang = context.user_data.get("lang", "uz")
    
    if role == "client":
        if lang == "uz":
            await context.bot.send_message(chat_id=query.from_user.id, text="Siz Mijoz menyusiga o'tdingiz. Pastdagi tugma orqali buyurtma berishingiz mumkin.", reply_markup=client_menu_keyboard("uz"))
            await query.edit_message_text("Yuk qayerdan olinadi? Viloyatni tanlang:", reply_markup=regions_keyboard("reg_"))
        else:
            await context.bot.send_message(chat_id=query.from_user.id, text="Вы перешли в меню Клиента. Вы можете оформить заказ с помощью кнопки ниже.", reply_markup=client_menu_keyboard("ru"))
            await query.edit_message_text("Откуда забрать груз? Выберите область:", reply_markup=regions_keyboard("reg_"))
        return C_REGION
    else:
        if lang == "uz":
            await query.edit_message_text("Haydovchi sifatida ro'yxatdan o'tish.\nSiz qaysi hududda yuk tashiysiz? Viloyatni tanlang:", reply_markup=regions_keyboard("wreg_"))
        else:
            await query.edit_message_text("Регистрация в качестве водителя.\nВ каком регионе вы перевозите грузы? Выберите область:", reply_markup=regions_keyboard("wreg_"))
        return W_REGION

# ===================== MIJOZ OQIMI =====================
async def start_client_order(update: Update, context):
    lang = context.user_data.get("lang", "uz")
    if lang == "uz":
        await update.message.reply_text("Yuk qayerdan olinadi? Viloyatni tanlang:", reply_markup=regions_keyboard("reg_"))
    else:
        await update.message.reply_text("Откуда забрать груз? Выберите область:", reply_markup=regions_keyboard("reg_"))
    return C_REGION

async def c_region(update: Update, context):
    query = update.callback_query
    await query.answer()
    reg_idx = query.data.replace("reg_", "")
    context.user_data["c_region_idx"] = reg_idx
    context.user_data["c_region"] = REG_KEYS[int(reg_idx)]
    lang = context.user_data.get("lang", "uz")
    
    if lang == "uz":
        await query.edit_message_text(f"Tanlangan viloyat: {context.user_data['c_region']}\nTumanni tanlang:", reply_markup=districts_keyboard(reg_idx, "dist_", "back_region"))
    else:
        await query.edit_message_text(f"Выбранная область: {context.user_data['c_region']}\nВыберите район:", reply_markup=districts_keyboard(reg_idx, "dist_", "back_region"))
    return C_DISTRICT

async def c_district(update: Update, context):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "uz")
    if query.data == "back_region":
        if lang == "uz":
            await query.edit_message_text("Yuk qayerdan olinadi? Viloyatni tanlang:", reply_markup=regions_keyboard("reg_"))
        else:
            await query.edit_message_text("Откуда забрать груз? Выберите область:", reply_markup=regions_keyboard("reg_"))
        return C_REGION
    d_idx = int(query.data.replace("dist_", ""))
    reg_idx = context.user_data["c_region_idx"]
    context.user_data["c_district"] = REGIONS[REG_KEYS[int(reg_idx)]][d_idx]
    
    if lang == "uz":
        await query.edit_message_text("🏁 <b>Aniq manzilni batafsil kiriting:</b>\n\nYuk qayerdan olinadi va qayerga boradi? (Yozib yuboring):", parse_mode="HTML")
    else:
        await query.edit_message_text("🏁 <b>Введите точный адрес подробно:</b>\n\nОткуда забрать груз и куда его доставить? (Отправьте текстом):", parse_mode="HTML")
    return C_TARGET

async def c_target(update: Update, context):
    lang = context.user_data.get("lang", "uz")
    if not update.message or not update.message.text:
        msg = "Iltimos, manzilni matn ko'rinishida yozing:" if lang == "uz" else "Пожалуйста, введите адрес в текстовом формате:"
        await update.message.reply_text(msg)
        return C_TARGET
    context.user_data["c_target"] = update.message.text
    
    if lang == "uz":
        kb = [[KeyboardButton("📺 Texnikalar"), KeyboardButton("🦮 Hayvonlar")], [KeyboardButton("🧱 Qurilish mollari"), KeyboardButton("📦 Boshqa narsalar")]]
        await update.message.reply_text("📦 Yukingiz qaysi turga kiradi?", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    else:
        kb = [[KeyboardButton("📺 Техника"), KeyboardButton("🦮 Животные")], [KeyboardButton("🧱 Стройматериалы"), KeyboardButton("📦 Другое")]]
        await update.message.reply_text("📦 К какому типу относится ваш груз?", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return C_DESC

async def c_desc(update: Update, context):
    lang = context.user_data.get("lang", "uz")
    if not update.message or not update.message.text:
        msg = "Yuk turini yozing yoki tanlang:" if lang == "uz" else "Выберите или введите тип груза:"
        await update.message.reply_text(msg)
        return C_DESC
    context.user_data["c_desc"] = update.message.text
    
    if lang == "uz":
        kb = [[KeyboardButton("⚡️ Hozir / Tezda")], [KeyboardButton("📅 Bugun kechroq"), KeyboardButton("📞 Kelishiladi")]]
        await update.message.reply_text("🕒 Yuk qachon olib ketilishi kerak?", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    else:
        kb = [[KeyboardButton("⚡️ Сейчас / Срочно")], [KeyboardButton("📅 Сегодня позже"), KeyboardButton("📞 По согласованию")]]
        await update.message.reply_text("🕒 Когда нужно забрать груз?", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return C_TIME

async def c_time(update: Update, context):
    lang = context.user_data.get("lang", "uz")
    if not update.message or not update.message.text:
        msg = "Iltimos, vaqtni kiriting:" if lang == "uz" else "Пожалуйста, введите время:"
        await update.message.reply_text(msg)
        return C_TIME
    context.user_data["c_time"] = update.message.text
    
    if lang == "uz":
        kb = [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]]
        await update.message.reply_text("📞 Telefon raqamingizni kiriting yoki pastdagi tugmani bosing:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    else:
        kb = [[KeyboardButton("📱 Отправить номер телефона", request_contact=True)]]
        await update.message.reply_text("📞 Введите ваш номер телефона или нажмите кнопку ниже:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return C_PHONE

async def c_phone(update: Update, context):
    lang = context.user_data.get("lang", "uz")
    if update.message.contact: 
        phone = update.message.contact.phone_number
    elif update.message.text: 
        phone = update.message.text
    else:
        msg = "Iltimos, telefon raqamni yuboring:" if lang == "uz" else "Пожалуйста, отправьте номер телефона:"
        await update.message.reply_text(msg)
        return C_PHONE
    context.user_data["c_phone"] = phone
    
    if lang == "uz":
        kb = [[KeyboardButton("📍 Joylashuvni yuborish", request_location=True)]]
        await update.message.reply_text("Yuk turgan joyning lokatsiyasini yuboring (yoki matn qilib yozing):", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    else:
        kb = [[KeyboardButton("📍 Отправить геолокацию", request_location=True)]]
        await update.message.reply_text("Отправьте геолокацию груза (или напишите текстом):", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return C_LOCATION

async def c_location(update: Update, context):
    lang = context.user_data.get("lang", "uz")
    if update.message.location:
        lat, lon = update.message.location.latitude, update.message.location.longitude
        context.user_data["c_location_text"] = f"https://maps.google.com/?q={lat},{lon}"
    elif update.message.text:
        context.user_data["c_location_text"] = update.message.text
    else:
        msg = "Iltimos, lokatsiya yuboring:" if lang == "uz" else "Пожалуйста, отправьте локацию:"
        await update.message.reply_text(msg)
        return C_LOCATION

    data = context.user_data
    if lang == "uz":
        text = (
            f"📋 <b>ARIZANGIZ TAYYOR:</b>\n\n"
            f"📍 Hudud: {data.get('c_region')}, {data.get('c_district')}\n"
            f"🏁 Aniq Manzil: {data.get('c_target')}\n"
            f"📦 Yuk turi: {data.get('c_desc')}\n"
            f"🕒 Vaqt: {data.get('c_time')}\n"
            f"📞 Telefon: {data.get('c_phone')}\n"
            f"🗺 Lokatsiya: {data.get('c_location_text')}\n\n"
            f"Arizani tasdiqlaysizmi?"
        )
        kb = [[InlineKeyboardButton("✅ Tasdiqlash", callback_data="c_confirm")], [InlineKeyboardButton("❌ Bekor qilish", callback_data="c_cancel")]]
    else:
        text = (
            f"📋 <b>ВАША ЗАЯВКА ГОТОВА:</b>\n\n"
            f"📍 Регион: {data.get('c_region')}, {data.get('c_district')}\n"
            f"🏁 Точный адрес: {data.get('c_target')}\n"
            f"📦 Тип груза: {data.get('c_desc')}\n"
            f"🕒 Время: {data.get('c_time')}\n"
            f"📞 Телефон: {data.get('c_phone')}\n"
            f"🗺 Локация: {data.get('c_location_text')}\n\n"
            f"Вы подтверждаете заявку?"
        )
        kb = [[InlineKeyboardButton("✅ Подтвердить", callback_data="c_confirm")], [InlineKeyboardButton("❌ Отменить", callback_data="c_cancel")]]
        
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    return C_CONFIRM

async def c_confirm(update: Update, context):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "uz")
    
    if query.data == "c_cancel":
        msg = "Ariza bekor qilindi." if lang == "uz" else "Заявка отменена."
        await query.edit_message_text(msg)
        return ConversationHandler.END

    uid = query.from_user.id
    data = context.user_data
    oid = int(order_counter[0]) 
    order_counter[0] += 1

    orders[oid] = {
        "id": oid, "client_id": uid, "region": data.get("c_region"), "district": data.get("c_district"),
        "desc": data.get("c_desc"), "target": data.get("c_target"), "time": data.get("c_time"), 
        "phone": data.get("c_phone"), "location_text": data.get("c_location_text"), 
        "status": "pending", "worker_id": None, "client_msg_id": None, "driver_msg_id": None, "driver_messages": []
    }
    save_data()

    if lang == "uz":
        kb = [[InlineKeyboardButton("❌ Buyurtmani bekor qilish", callback_data=f"client_cancel_{oid}")]]
        msg_text = f"⏳ <b>Ariza #{oid} haydovchilarga yuborildi!</b>\n\nHaydovchi qabul qilsa, uning ma'lumotlarini shu yerda ko'rasiz."
    else:
        kb = [[InlineKeyboardButton("❌ Отменить заказ", callback_data=f"client_cancel_{oid}")]]
        msg_text = f"⏳ <b>Заявка #{oid} отправлена водителям!</b>\n\nКак только водитель примет её, вы увидите его данные здесь."

    sent_msg = await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    orders[oid]["client_msg_id"] = sent_msg.message_id 

    for wid, w in workers.items():
        if w.get("approved") and data.get("c_region") == w.get("region") and w.get("district") == data.get("c_district"):
            if w.get("balance", 0) >= FIXED_COMMISSION:
                drv_lang = w.get("lang", "uz")
                btn_text = f"🛺 Qabul qilish ({FIXED_COMMISSION:,} so'm)" if drv_lang == "uz" else f"🛺 Принять ({FIXED_COMMISSION:,} сум)"
                drv_kb = [[InlineKeyboardButton(btn_text, callback_data=f"accept_{oid}")]]
                
                title = f"🔔 <b>YANGI BUYURTMA #{oid}!</b>" if drv_lang == "uz" else f"🔔 <b>НОВЫЙ ЗАКАЗ #{oid}!</b>"
                addr_label = "📍 Hudud:" if drv_lang == "uz" else "📍 Регион:"
                target_label = "🏁 Manzil:" if drv_lang == "uz" else "🏁 Адрес:"
                desc_label = "📦 Turi:" if drv_lang == "uz" else "📦 Тип:"
                time_label = "🕒 Vaqt:" if drv_lang == "uz" else "🕒 Время:"
                
                try:
                    d_msg = await context.bot.send_message(
                        wid,
                        f"{title}\n\n"
                        f"{addr_label} {data.get('c_region')}, {data.get('c_district')}\n"
                        f"{target_label} {data.get('c_target')}\n"
                        f"{desc_label} {data.get('c_desc')} | {time_label} {data.get('c_time')}",
                        reply_markup=InlineKeyboardMarkup(drv_kb), parse_mode="HTML"
                    )
                    orders[oid]["driver_messages"].append({"chat_id": int(wid), "message_id": d_msg.message_id})
                except Exception: pass
                
    save_data()
    return ConversationHandler.END

# ===================== QIDIRISH VA YANGILASH TIZIMI =====================
async def search_orders_cmd(update: Update, context):
    uid = update.effective_user.id
    if uid not in workers or not workers[uid].get("approved"):
        await update.message.reply_text("Siz tasdiqlangan haydovchi emassiz. / Вы не являетесь одобренным водителем.")
        return

    w = workers[uid]
    drv_lang = w.get("lang", "uz")
    hr_region = w.get("region")
    hr_district = w.get("district")

    found_orders = []
    for oid, o in orders.items():
        if o["status"] == "pending" and o["region"] == hr_region and o["district"] == hr_district:
            found_orders.append(o)

    if not found_orders:
        if drv_lang == "uz":
            kb = [[InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_search")]]
            text = f"📍 <b>{hr_region}, {hr_district}</b> hududida hozircha faol buyurtmalar topilmadi.\n\nYangi buyurtmalarni tekshirish uchun pastdagi tugmani bosing:"
        else:
            kb = [[InlineKeyboardButton("🔄 Обновить", callback_data="refresh_search")]]
            text = f"📍 В регионе <b>{hr_region}, {hr_district}</b> активных заказов пока не найдено.\n\nНажмите кнопку ниже, чтобы проверить новые заказы:"
            
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        return

    title = f"🔍 <b>Sizning hududingizdagi faol buyurtmalar ({len(found_orders)} ta):</b>" if drv_lang == "uz" else f"🔍 <b>Активные заказы в вашем регионе ({len(found_orders)} шт):</b>"
    await update.message.reply_text(title, parse_mode="HTML")
    
    for o in found_orders:
        btn_text = f"🛺 Qabul qilish ({FIXED_COMMISSION:,} so'm)" if drv_lang == "uz" else f"🛺 Принять ({FIXED_COMMISSION:,} сум)"
        drv_kb = [[InlineKeyboardButton(btn_text, callback_data=f"accept_{o['id']}")]]
        
        b_label = f"📦 <b>BUYURTMA #{o['id']}</b>" if drv_lang == "uz" else f"📦 <b>ЗАКАЗ #{o['id']}</b>"
        m_label = "🏁 Manzil:" if drv_lang == "uz" else "🏁 Адрес:"
        t_label = "📦 Turi:" if drv_lang == "uz" else "📦 Тип:"
        v_label = "🕒 Vaqt:" if drv_lang == "uz" else "🕒 Время:"
        
        await update.message.reply_text(
            f"{b_label}\n"
            f"{m_label} {o['target']}\n"
            f"{t_label} {o['desc']}\n"
            f"{v_label} {o['time']}",
            reply_markup=InlineKeyboardMarkup(drv_kb), parse_mode="HTML"
        )

async def refresh_search_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    w = workers.get(uid)
    if not w: return

    drv_lang = w.get("lang", "uz")
    hr_region = w.get("region")
    hr_district = w.get("district")

    found_orders = []
    for oid, o in orders.items():
        if o["status"] == "pending" and o["region"] == hr_region and o["district"] == hr_district:
            found_orders.append(o)

    if not found_orders:
        try:
            if drv_lang == "uz":
                kb = [[InlineKeyboardButton("🔄 Qayta yangilash", callback_data="refresh_search")]]
                text = f"⏳ Oxirgi tekshiruv: <b>Hozir</b>\n📍 Hudud: {hr_region}, {hr_district}\n\nHech qanday yangi buyurtma topilmadi. Kutishingiz yoki qayta urinib ko'rishingiz mumkin."
            else:
                kb = [[InlineKeyboardButton("🔄 Повторить обновление", callback_data="refresh_search")]]
                text = f"⏳ Последняя проверка: <b>Только что</b>\n📍 Регион: {hr_region}, {hr_district}\n\nНовых заказов не найдено. Вы можете подождать или попробовать еще раз."
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        except Exception: pass
        return

    success_msg = "✅ Yangi buyurtmalar topildi! Pastda ko'rishingiz mumkin:" if drv_lang == "uz" else "✅ Найдены новые заказы! Вы можете увидеть их ниже:"
    await query.edit_message_text(success_msg)
    
    for o in found_orders:
        btn_text = f"🛺 Qabul qilish ({FIXED_COMMISSION:,} so'm)" if drv_lang == "uz" else f"🛺 Принять ({FIXED_COMMISSION:,} сум)"
        drv_kb = [[InlineKeyboardButton(btn_text, callback_data=f"accept_{o['id']}")]]
        
        b_label = f"📦 <b>BUYURTMA #{o['id']}</b>" if drv_lang == "uz" else f"📦 <b>ЗАКАЗ #{o['id']}</b>"
        m_label = "🏁 Manzil:" if drv_lang == "uz" else "🏁 Адрес:"
        t_label = "📦 Turi:" if drv_lang == "uz" else "📦 Тип:"
        v_label = "🕒 Vaqt:" if drv_lang == "uz" else "🕒 Время:"
        
        await context.bot.send_message(
            chat_id=uid,
            text=f"{b_label}\n"
                 f"{m_label} {o['target']}\n"
                 f"{t_label} {o['desc']}\n"
                 f"{v_label} {o['time']}",
            reply_markup=InlineKeyboardMarkup(drv_kb), parse_mode="HTML"
        )

# ===================== BUYURTMANI QABUL QILISH =====================
async def accept_order(update: Update, context):
    query = update.callback_query
    await query.answer()
    oid = int(query.data.split("_")[1])
    uid = query.from_user.id

    if oid not in orders:
        await query.edit_message_text("Order not found / Buyurtma topilmadi.")
        return
    
    order = orders[oid]
    w = workers.get(uid)
    drv_lang = w.get("lang", "uz") if w else "uz"
    
    if order["status"] in ["cancelled_by_client", "cancelled_after_accept"]:
        msg = "Buyurtma bekor qilingan. 😔" if drv_lang == "uz" else "Заказ отменен. 😔"
        await query.edit_message_text(msg)
        return
    if order["status"] != "pending":
        msg = "Kechikdingiz, boshqa haydovchi qabul qildi." if drv_lang == "uz" else "Вы опоздали, другой водитель уже принял заказ."
        await query.edit_message_text(msg)
        return

    if not w or w.get("balance", 0) < FIXED_COMMISSION:
        try:
            msg = f"❌ <b>Sizda yetarli mablag' yo'q!</b>\n\nBalansingiz: {w.get('balance', 0):,} so'm." if drv_lang == "uz" else f"❌ <b>Недостаточно средств!</b>\n\nВаш баланс: {w.get('balance', 0):,} сум."
            await context.bot.send_message(uid, msg, parse_mode="HTML")
        except Exception: pass
        return

    order["status"] = "accepted"
    order["worker_id"] = uid
    w["balance"] -= FIXED_COMMISSION 
    w["total_orders"] += 1
    save_data()

    btn_text = "❌ Buyurtmani bekor qilish (Voz kechish)" if drv_lang == "uz" else "❌ Отменить заказ (Отказ)"
    drv_cancel_kb = [[InlineKeyboardButton(btn_text, callback_data=f"driver_cancel_{oid}")]]
    
    if drv_lang == "uz":
        drv_text = (
            f"🎉 <b>Buyurtma #{oid} sizniki!</b>\n💰 Balansdan 4,000 so'm yechildi.\n\n"
            f"📞 Mijoz: {order['phone']}\n"
            f"🏁 Manzil: {order['target']}\n"
            f"📍 <a href='{order['location_text']}'>Lokatsiya xaritasi</a>\n\n"
            f"⚠️ Agar bormasangiz yoki muammo bo'lsa, quyidagi tugma orqali bekor qiling (pul qaytadi)."
        )
    else:
        drv_text = (
            f"🎉 <b>Заказ #{oid} ваш!</b>\n💰 С баланса списано 4,000 сум.\n\n"
            f"📞 Клиент: {order['phone']}\n"
            f"🏁 Адрес: {order['target']}\n"
            f"📍 <a href='{order['location_text']}'>Карта локации</a>\n\n"
            f"⚠️ Если вы не сможете поехать или возникнет проблема, отмените заказ с помощью кнопки ниже (деньги вернутся)."
        )

    await query.edit_message_text(
        drv_text,
        reply_markup=InlineKeyboardMarkup(drv_cancel_kb), parse_mode="HTML", disable_web_page_preview=True
    )
    order["driver_msg_id"] = query.message.message_id

    for msg_info in order.get("driver_messages", []):
        if int(msg_info["chat_id"]) != uid:
            try:
                other_w = workers.get(int(msg_info["chat_id"]))
                other_lang = other_w.get("lang", "uz") if other_w else "uz"
                ref_text = f"🔕 Buyurtma #{oid} boshqa haydovchi tomonidan olindi." if other_lang == "uz" else f"🔕 Заказ #{oid} принят другим водителем."
                await context.bot.edit_message_text(chat_id=int(msg_info["chat_id"]), message_id=msg_info["message_id"], text=ref_text)
            except Exception: pass

    client_lang = context.user_data.get("lang", "uz") 
    c_btn = "❌ Buyurtmani bekor qilish" if client_lang == "uz" else "❌ Отменить заказ"
    client_cancel_kb = [[InlineKeyboardButton(c_btn, callback_data=f"client_cancel_{oid}")]]
    
    if client_lang == "uz":
        cl_text = (
            f"✅ <b>Haydovchi topildi!</b>\n\n"
            f"👤 Haydovchi: <b>{w['name']}</b>\n"
            f"🛺 Mashina rusumi: <b>{w.get('car_model', 'Labo')}</b>\n"
            f"🎨 Mashina rangi: <b>{w.get('car_color', 'Oq')}</b>\n"
            f"🚘 Davlat raqami: <b>{w['car_number']}</b>\n"
            f"📞 Telefon raqami: <b>{w['phone']}</b>\n\n"
            f"Haydovchi hozir sizga aloqaga chiqadi. Agar buyurtmani bekor qilmoqchi bo'lsangiz, pastdagi tugmani bosing:"
        )
    else:
        cl_text = (
            f"✅ <b>Водитель найден!</b>\n\n"
            f"👤 Водитель: <b>{w['name']}</b>\n"
            f"🛺 Марка машины: <b>{w.get('car_model', 'Labo')}</b>\n"
            f"🎨 Цвет машины: <b>{w.get('car_color', 'Белый')}</b>\n"
            f"🚘 Госмномер: <b>{w['car_number']}</b>\n"
            f"📞 Номер телефона: <b>{w['phone']}</b>\n\n"
            f"Водитель сейчас свяжется с вами. Если вы хотите отменить заказ, нажмите кнопку ниже:"
        )

    try:
        await context.bot.edit_message_text(
            chat_id=int(order["client_id"]), message_id=order["client_msg_id"],
            text=cl_text,
            reply_markup=InlineKeyboardMarkup(client_cancel_kb), parse_mode="HTML"
        )
    except Exception: pass
    save_data()

# ===================== BEKOR QILISHLAR =====================
async def client_cancel_order(update: Update, context):
    query = update.callback_query
    await query.answer()
    oid = int(query.data.split("_")[2])
    client_lang = context.user_data.get("lang", "uz")

    if oid not in orders:
        await query.edit_message_text("Error / Xato.")
        return

    order = orders[oid]
    if order["status"] in ["cancelled_by_client", "cancelled_after_accept"]:
        msg = "Buyurtma allaqachon bekor qilingan." if client_lang == "uz" else "Заказ уже отменен."
        await query.edit_message_text(msg)
        return

    old_status = order["status"]
    order["status"] = "cancelled_by_client"
    
    msg_cancel = "❌ Siz buyurtmani bekor qildingiz." if client_lang == "uz" else "❌ Вы отменили заказ."
    await query.edit_message_text(msg_cancel)

    if old_status == "accepted" and order["worker_id"]:
        wid = order["worker_id"]
        if wid in workers:
            workers[wid]["balance"] += FIXED_COMMISSION
            save_data()
            drv_lang = workers[wid].get("lang", "uz")
            try:
                if drv_lang == "uz":
                    txt_drv = f"🔴 <b>Buyurtma #{oid} mijoz tomonidan bekor qilindi!</b>\n\nBalansingizga {FIXED_COMMISSION:,} so'm qaytarildi."
                    txt_edit = f"🔴 <b>Buyurtma #{oid} mijoz tomonidan bekor qilindi. Pul qaytarildi.</b>"
                else:
                    txt_drv = f"🔴 <b>Заказ #{oid} отменен клиентом!</b>\n\nНа ваш баланс возвращено {FIXED_COMMISSION:,} сум."
                    txt_edit = f"🔴 <b>Заказ #{oid} отменен клиентом. Деньги возвращены.</b>"
                
                await context.bot.send_message(chat_id=int(wid), text=txt_drv, parse_mode="HTML")
                if order["driver_msg_id"]:
                    await context.bot.edit_message_text(chat_id=int(wid), message_id=order["driver_msg_id"], text=txt_edit, parse_mode="HTML")
            except Exception: pass
            
    elif old_status == "pending":
        for msg_info in order.get("driver_messages", []):
            try: 
                o_w = workers.get(int(msg_info["chat_id"]))
                o_l = o_w.get("lang", "uz") if o_w else "uz"
                txt_pnd = f"🔴 <b>Buyurtma #{oid} mijoz tomonidan bekor qilindi.</b>" if o_l == "uz" else f"🔴 <b>Заказ #{oid} отменен клиентом.</b>"
                await context.bot.edit_message_text(chat_id=int(msg_info["chat_id"]), message_id=msg_info["message_id"], text=txt_pnd, parse_mode="HTML")
            except Exception: pass
            
    save_data()

async def driver_cancel_order(update: Update, context):
    query = update.callback_query
    await query.answer()
    oid = int(query.data.split("_")[2])
    uid = query.from_user.id
    w = workers.get(uid)
    drv_lang = w.get("lang", "uz") if w else "uz"

    if oid not in orders:
        await query.edit_message_text("Order not found.")
        return

    order = orders[oid]
    if order["status"] != "accepted" or order["worker_id"] != uid:
        msg = "Siz bu buyurtmani bekor qila olmaysiz." if drv_lang == "uz" else "Вы не можете отменить этот заказ."
        await query.edit_message_text(msg)
        return

    order["status"] = "cancelled_after_accept"
    if uid in workers:
        workers[uid]["balance"] += FIXED_COMMISSION
        save_data()

    msg_ret = f"❌ Siz buyurtma #{oid} dan voz kechdingiz. {FIXED_COMMISSION:,} so'm balansingizga qaytarildi." if drv_lang == "uz" else f"❌ Вы отказались от заказа #{oid}. {FIXED_COMMISSION:,} сум возвращены на ваш баланс."
    await query.edit_message_text(msg_ret)

    client_lang = context.user_data.get("lang", "uz")
    if client_lang == "uz":
        c_btn_text = "🔄 Qayta buyurtma berish"
        c_txt = f"⚠️ <b>Haydovchi buyurtma #{oid} ni bekor qildi!</b>\n\nKechirasiz, haydovchi texnik sabablarga ko'ra buyurtmani bajara olmadi. Qayta buyurtma berishingiz mumkin."
    else:
        c_btn_text = "🔄 Заказать снова"
        c_txt = f"⚠️ <b>Водитель отменил заказ #{oid}!</b>\n\nИзвините, водитель не смог выполнить заказ по техническим причинам. Вы можете оформить заказ заново."

    try:
        await context.bot.edit_message_text(
            chat_id=int(order["client_id"]), 
            message_id=order["client_msg_id"],
            text=c_txt,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(c_btn_text, callback_data="re_order_start")]]),
            parse_mode="HTML"
        )
    except Exception: pass
    save_data()

async def re_order_start(update: Update, context):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "uz")
    msg = "Yuk qayerdan olinadi? Viloyatni tanlang:" if lang == "uz" else "Откуда забрать груз? Выберите область:"
    await query.message.reply_text(msg, reply_markup=regions_keyboard("reg_"))
    return C_REGION

# ===================== KABINET VA SOZLAMALAR =====================
async def profile_cmd(update: Update, context):
    msg = update.message if update.message else update.callback_query.message
    uid = update.effective_user.id
    if uid not in workers:
        await msg.reply_text("Siz haydovchi emassiz. / Вы не являетесь водителем.")
        return ConversationHandler.END
    w = workers[uid]
    drv_lang = w.get("lang", "uz")
    
    if drv_lang == "uz":
        text = (
            f"💳 <b>SHAXSIY KABINET (HAYDOVCHI)</b>\n\n"
            f"👤 Ism: <b>{w['name']}</b>\n"
            f"🛺 Mashina rusumi: <b>{w.get('car_model', 'Kiritilmagan')}</b>\n"
            f"🎨 Mashina rangi: <b>{w.get('car_color', 'Kiritilmagan')}</b>\n"
            f"🚘 Davlat raqami: <b>{w['car_number']}</b>\n"
            f"📞 Tel: <b>{w['phone']}</b>\n"
            f"📍 Hudud: <b>{w['region']}, {w['district']}</b>\n\n"
            f"💰 Balans: <b>{w['balance']:,} so'm</b>\n"
            f"🛺 Buyurtmalar: <b>{w['total_orders']} ta</b>"
        )
        kb = [
            [InlineKeyboardButton("📦 Faol buyurtmalarim", callback_data="my_active_orders")],
            [InlineKeyboardButton("💰 Hisobni to'ldirish", callback_data="deposit_money")],
            [InlineKeyboardButton("📍 Hududni o'zgartirish", callback_data="change_my_region")],
            [InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_profile")]
        ]
    else:
        text = (
            f"💳 <b>ЛИЧНЫЙ КАБИНЕТ (ВОДИТЕЛЬ)</b>\n\n"
            f"👤 Имя: <b>{w['name']}</b>\n"
            f"🛺 Марка авто: <b>{w.get('car_model', 'Не указано')}</b>\n"
            f"🎨 Цвет авто: <b>{w.get('car_color', 'Не указано')}</b>\n"
            f"🚘 Гономер: <b>{w['car_number']}</b>\n"
            f"📞 Тел: <b>{w['phone']}</b>\n"
            f"📍 Регион: <b>{w['region']}, {w['district']}</b>\n\n"
            f"💰 Баланс: <b>{w['balance']:,} сум</b>\n"
            f"🛺 Заказы: <b>{w['total_orders']} шт</b>"
        )
        kb = [
            [InlineKeyboardButton("📦 Мои активные заказы", callback_data="my_active_orders")],
            [InlineKeyboardButton("💰 Пополнить счет", callback_data="deposit_money")],
            [InlineKeyboardButton("📍 Изменить регион", callback_data="change_my_region")],
            [InlineKeyboardButton("🔄 Обновить", callback_data="refresh_profile")]
        ]
        
    await msg.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    return ConversationHandler.END

async def change_my_region(update: Update, context):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    drv_lang = workers[uid].get("lang", "uz") if uid in workers else "uz"
    msg = "Yangi viloyatingizni tanlang:" if drv_lang == "uz" else "Выберите новую область:"
    await query.edit_message_text(msg, reply_markup=regions_keyboard("chreg_"))
    return CH_REGION

async def ch_region(update: Update, context):
    query = update.callback_query
    await query.answer()
    reg_idx = query.data.replace("chreg_", "")
    context.user_data["ch_region_idx"] = reg_idx
    context.user_data["ch_region"] = REG_KEYS[int(reg_idx)]
    uid = query.from_user.id
    drv_lang = workers[uid].get("lang", "uz") if uid in workers else "uz"
    
    if drv_lang == "uz":
        await query.edit_message_text(f"Viloyat: {context.user_data['ch_region']}\nYangi tumanni tanlang:", reply_markup=districts_keyboard(reg_idx, "chdist_", "back_ch_region"))
    else:
        await query.edit_message_text(f"Область: {context.user_data['ch_region']}\nВыберите новый район:", reply_markup=districts_keyboard(reg_idx, "chdist_", "back_ch_region"))
    return CH_DISTRICT

async def ch_district(update: Update, context):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    drv_lang = workers[uid].get("lang", "uz") if uid in workers else "uz"
    
    if query.data == "back_ch_region":
        msg = "Yangi viloyatingizni tanlang:" if drv_lang == "uz" else "Выберите новую область:"
        await query.edit_message_text(msg, reply_markup=regions_keyboard("chreg_"))
        return CH_REGION
        
    d_idx = int(query.data.replace("chdist_", ""))
    reg_idx = context.user_data["ch_region_idx"]
    district_name = REGIONS[REG_KEYS[int(reg_idx)]][d_idx]
    
    if uid in workers:
        workers[uid]["region"] = context.user_data["ch_region"]
        workers[uid]["district"] = district_name
        save_data()
        
    success_text = f"✅ Hudud o'zgardi: <b>{context.user_data['ch_region']}, {district_name}</b>" if drv_lang == "uz" else f"✅ Регион изменен: <b>{context.user_data['ch_region']}, {district_name}</b>"
    await query.edit_message_text(success_text, parse_mode="HTML")
    return ConversationHandler.END

# ===================== HAYDOVCHI RO'YXATDAN O'TISH =====================
async def w_region(update: Update, context):
    query = update.callback_query
    await query.answer()
    reg_idx = query.data.replace("wreg_", "")
    context.user_data["w_region_idx"] = reg_idx
    context.user_data["w_region"] = REG_KEYS[int(reg_idx)]
    lang = context.user_data.get("lang", "uz")
    
    if lang == "uz":
        await query.edit_message_text(f"Viloyat: {context.user_data['w_region']}\nQaysi tumanda qatnaysiz?", reply_markup=districts_keyboard(reg_idx, "wdist_", "back_w_region"))
    else:
        await query.edit_message_text(f"Область: {context.user_data['w_region']}\nВ каком районе вы работаете?", reply_markup=districts_keyboard(reg_idx, "wdist_", "back_w_region"))
    return W_DISTRICT

async def w_district(update: Update, context):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "uz")
    if query.data == "back_w_region":
        msg = "Viloyatni tanlang:" if lang == "uz" else "Выберите область:"
        await query.edit_message_text(msg, reply_markup=regions_keyboard("wreg_"))
        return W_REGION
    d_idx = int(query.data.replace("wdist_", ""))
    reg_idx = context.user_data["w_region_idx"]
    context.user_data["w_district"] = REGIONS[REG_KEYS[int(reg_idx)]][d_idx]
    
    msg_name = "<b>Ism-familiyangizni kiriting:</b>" if lang == "uz" else "<b>Введите ваше имя и фамилию:</b>"
    await query.message.reply_text(msg_name, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    return W_NAME

async def w_name(update: Update, context):
    lang = context.user_data.get("lang", "uz")
    if not update.message or not update.message.text:
        msg = "Ismingizni kiriting:" if lang == "uz" else "Введите ваше имя:"
        await update.message.reply_text(msg)
        return W_NAME
    context.user_data["w_name"] = update.message.text
    
    if lang == "uz":
        kb = [[KeyboardButton("Labo"), KeyboardButton("Changan")], [KeyboardButton("Damas"), KeyboardButton("Porter")]]
        await update.message.reply_text("🚚 Yuk mashinangiz rusumini (modelini) kiriting yoki tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    else:
        kb = [[KeyboardButton("Labo"), KeyboardButton("Changan")], [KeyboardButton("Damas"), KeyboardButton("Porter")]]
        await update.message.reply_text("🚚 Введите или выберите марку вашего грузовика:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return W_CAR_MODEL

async def w_car_model(update: Update, context):
    lang = context.user_data.get("lang", "uz")
    if not update.message or not update.message.text:
        msg = "Mashina rusumini kiriting:" if lang == "uz" else "Введите марку машины:"
        await update.message.reply_text(msg)
        return W_CAR_MODEL
    context.user_data["w_car_model"] = update.message.text
    
    if lang == "uz":
        kb = [[KeyboardButton("Oq"), KeyboardButton("Kumush rang")], [KeyboardButton("Ko'k"), KeyboardButton("Qora")]]
        await update.message.reply_text("🎨 Mashinangiz rangini kiriting yoki tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    else:
        kb = [[KeyboardButton("Белый"), KeyboardButton("Серебристый")], [KeyboardButton("Синий"), KeyboardButton("Черный")]]
        await update.message.reply_text("🎨 Введите или выберите цвет вашей машины:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return W_CAR_COLOR

async def w_car_color(update: Update, context):
    lang = context.user_data.get("lang", "uz")
    if not update.message or not update.message.text:
        msg = "Mashina rangini kiriting:" if lang == "uz" else "Введите цвет машины:"
        await update.message.reply_text(msg)
        return W_CAR_COLOR
    context.user_data["w_car_color"] = update.message.text
    
    msg_num = "🔢 Mashinangiz davlat raqamini kiriting:\n(Masalan: 01 A 123 AB yoki 60 777 AAA)" if lang == "uz" else "🔢 Введите госномер вашей машины:\n(Например: 01 A 123 AB или 60 777 AAA)"
    await update.message.reply_text(msg_num, reply_markup=ReplyKeyboardRemove())
    return W_CAR_NUMBER

async def w_car_number(update: Update, context):
    lang = context.user_data.get("lang", "uz")
    if not update.message or not update.message.text:
        msg = "Iltimos, mashina raqamini kiriting:" if lang == "uz" else "Пожалуйста, введите номер машины:"
        await update.message.reply_text(msg)
        return W_CAR_NUMBER
    context.user_data["w_car_number"] = update.message.text.upper()
    
    msg_ph = "📞 Telefon raqamingizni kiriting:" if lang == "uz" else "📞 Введите ваш номер телефона:"
    await update.message.reply_text(msg_ph)
    return W_PHONE

async def w_phone(update: Update, context):
    lang = context.user_data.get("lang", "uz")
    if not update.message or not update.message.text:
        msg = "Telefon raqamni kiriting:" if lang == "uz" else "Введите номер телефона:"
        await update.message.reply_text(msg)
        return W_PHONE
    context.user_data["w_phone"] = update.message.text
    data = context.user_data
    
    if lang == "uz":
        text = (
            f"📋 <b>HAYDOVCHI MA'LUMOTLARI:</b>\n\n"
            f"👤 Ism: {data.get('w_name')}\n"
            f"🛺 Rusumi: {data.get('w_car_model')}\n"
            f"🎨 Rangi: {data.get('w_car_color')}\n"
            f"🚘 Raqami: {data.get('w_car_number')}\n"
            f"📞 Tel: {data.get('w_phone')}\n"
            f"📍 Hudud: {data.get('w_region')}, {data.get('w_district')}\n\n"
            f"Ma'lumotlar to'g'rimi?"
        )
        kb = [[InlineKeyboardButton("Ha, yuborilsin", callback_data="w_confirm")], [InlineKeyboardButton("Yo'q, bekor qilish", callback_data="w_cancel")]]
    else:
        text = (
            f"📋 <b>ДАННЫЕ ВОДИТЕЛЯ:</b>\n\n"
            f"👤 Имя: {data.get('w_name')}\n"
            f"🛺 Марка: {data.get('w_car_model')}\n"
            f"🎨 Цвет: {data.get('w_car_color')}\n"
            f"🚘 Номер: {data.get('w_car_number')}\n"
            f"📞 Тел: {data.get('w_phone')}\n"
            f"📍 Регион: {data.get('w_region')}, {data.get('w_district')}\n\n"
            f"Данные верны?"
        )
        kb = [[InlineKeyboardButton("Да, отправить", callback_data="w_confirm")], [InlineKeyboardButton("Нет, отменить", callback_data="w_cancel")]]
        
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    return W_CONFIRM

async def w_confirm(update: Update, context):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "uz")
    
    if query.data == "w_cancel":
        msg = "Ro'yxatdan o'tish bekor qilindi." if lang == "uz" else "Регистрация отменена."
        await query.edit_message_text(msg)
        return ConversationHandler.END

    uid = query.from_user.id
    data = context.user_data
    workers[uid] = {
        "name": data.get("w_name"), "car_model": data.get("w_car_model"), "car_color": data.get("w_car_color"),
        "car_number": data.get("w_car_number"), "phone": data.get("w_phone"), 
        "region": data.get("w_region"), "district": data.get("w_district"), 
        "approved": False, "balance": 0, "total_orders": 0, "lang": lang
    }
    save_data()

    kb = [[InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{uid}")]]
    try:
        await context.bot.send_message(
            ADMIN_ID, 
            f"🆕 <b>YANGI LABO HAYDOVCHISI ARIZASI:</b>\n\n"
            f"Ism: {data.get('w_name')}\n"
            f"Rusumi: {data.get('w_car_model')} | Rangi: {data.get('w_car_color')}\n"
            f"Mashina raqami: {data.get('w_car_number')}\n"
            f"Tel: {data.get('w_phone')}\nHudud: {data.get('w_region')} | Til: {lang}\nID: {uid}", 
            reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML"
        )
    except Exception: pass
    
    final_msg = "Arizangiz adminga yuborildi. Admin tasdiqlagach faoliyat boshlashingiz mumkin." if lang == "uz" else "Ваша заявка отправлена админу. Вы сможете начать работу после подтверждения."
    await query.edit_message_text(final_msg)
    return ConversationHandler.END

async def approve_driver(update: Update, context):
    query = update.callback_query
    await query.answer()
    uid = int(query.data.split("_")[1])
    if uid in workers:
        workers[uid]["approved"] = True
        workers[uid]["balance"] = 8000  # Bonus ball balansi kuymaydi
        save_data()
        await query.edit_message_text("Haydovchi tizimga muvaffaqiyatli qo'shildi!")
        
        drv_lang = workers[uid].get("lang", "uz")
        if drv_lang == "uz":
            m_text = "🎉 Arizangiz tasdiqlandi! Shaxsiy kabinetingiz va haydovchi menyusi ochildi."
        else:
            m_text = "🎉 Ваша заявка одобрена! Личный кабинет и меню водителя открыты."
            
        try: await context.bot.send_message(uid, m_text, reply_markup=driver_menu_keyboard(drv_lang))
        except Exception: pass

# ===================== BALANS TO'LDIRISH =====================
async def deposit_money(update: Update, context):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    drv_lang = workers[uid].get("lang", "uz") if uid in workers else "uz"
    
    if drv_lang == "uz":
        text = f"💳 Karta: <code>{KARTA_RAQAM}</code>\n👤 Ega si: <b>{KARTA_EGA_SI}</b>\n\n⚠️ Pul o'tkazgach, '✅ To'lov qildim' tugmasini bosing!"
        kb = [[InlineKeyboardButton("✅ To'lov qildim", callback_data="paid_notification")], [InlineKeyboardButton("🔙 Orqaga", callback_data="refresh_profile")]]
    else:
        text = f"💳 Карта: <code>{KARTA_RAQAM}</code>\n👤 Владелец: <b>{KARTA_EGA_SI}</b>\n\n⚠️ После перевода денег нажмите кнопку '✅ Я оплатил'!"
        kb = [[InlineKeyboardButton("✅ Я оплатил", callback_data="paid_notification")], [InlineKeyboardButton("🔙 Назад", callback_data="refresh_profile")]]
        
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def paid_notification(update: Update, context):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    drv_lang = workers[uid].get("lang", "uz") if uid in workers else "uz"
    msg = "💰 Qancha pul o'tkazganingizni yozing (Faqat raqamlarda):" if drv_lang == "uz" else "💰 Введите сумму перевода (Только цифрами):"
    await query.message.reply_text(msg)
    return PAY_AMOUNT

async def get_pay_amount(update: Update, context):
    uid = update.effective_user.id
    drv_lang = workers[uid].get("lang", "uz") if uid in workers else "uz"
    amount_text = update.message.text.replace(" ", "").replace(",", "").replace(".", "")
    if not amount_text.isdigit():
        msg = "Faqat raqam kiriting:" if drv_lang == "uz" else "Введите только цифры:"
        await update.message.reply_text(msg)
        return PAY_AMOUNT
    amount = int(amount_text)
    w = workers.get(uid)
    admin_kb = [[InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"payadd_{uid}_{amount}")], [InlineKeyboardButton("❌ Rad etish", callback_data=f"paydenied_{uid}")]]
    try:
        await context.bot.send_message(ADMIN_ID, f"💰 <b>Yangi to'lov:</b> {w['name']}\nID: {uid}\nSumma: <b>{amount:,} so'm</b>", reply_markup=InlineKeyboardMarkup(admin_kb), parse_mode="HTML")
    except Exception: pass
    
    success_send = "✅ Xabaringiz adminga yuborildi." if drv_lang == "uz" else "✅ Ваше сообщение отправлено админу."
    await update.message.reply_text(success_send, reply_markup=driver_menu_keyboard(drv_lang))
    return ConversationHandler.END

async def admin_payment_confirm(update: Update, context):
    query = update.callback_query
    await query.answer()
    data_parts = query.data.split("_")
    action, driver_id = data_parts[0], int(data_parts[1])
    if action == "payadd":
        amount = int(data_parts[2])
        if driver_id in workers:
            workers[driver_id]["balance"] += amount
            save_data()
            await query.edit_message_text(f"✅ ID: {driver_id} hisobiga {amount:,} so'm qo'shildi.")
            drv_lang = workers[driver_id].get("lang", "uz")
            msg_p = f"🚀 Balansingiz {amount:,} so'mga to'ldirildi!" if drv_lang == "uz" else f"🚀 Ваш баланс пополнен на {amount:,} сум!"
            try: await context.bot.send_message(driver_id, msg_p)
            except Exception: pass
    elif action == "paydenied":
        await query.edit_message_text("❌ To'lov rad etildi.")

async def my_active_orders(update: Update, context):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    drv_lang = workers[uid].get("lang", "uz") if uid in workers else "uz"
    found = False
    
    if drv_lang == "uz":
        text = "📂 <b>Siz qabul qilgan faol buyurtmalar:</b>\n\n"
        empty_text = "Faol buyurtmalar yo'q."
        back_btn = "🔙 Orqaga"
    else:
        text = "📂 <b>Принятые вами активные заказы:</b>\n\n"
        empty_text = "Активных заказов нет."
        back_btn = "🔙 Назад"
        
    for oid, o in orders.items():
        if o["worker_id"] == uid and o["status"] == "accepted":
            found = True
            if drv_lang == "uz":
                text += f"🆔 <b>Buyurtma #{oid}:</b>\n📞 Tel: {o['phone']}\n🏁 Manzil: {o['target']}\n📍 <a href='{o['location_text']}'>Lokatsiya</a>\n\n"
            else:
                text += f"🆔 <b>Заказ #{oid}:</b>\n📞 Тел: {o['phone']}\n🏁 Адрес: {o['target']}\n📍 <a href='{o['location_text']}'>Локация</a>\n\n"
                
    if not found: text += empty_text
    kb = [[InlineKeyboardButton(back_btn, callback_data="refresh_profile")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML", disable_web_page_preview=True)

async def refresh_profile(update: Update, context):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    w = workers.get(uid)
    if not w: return
    drv_lang = w.get("lang", "uz")
    
    if drv_lang == "uz":
        text = (
            f"💳 <b>SHAXSIY KABINET (HAYDOVCHI)</b>\n\n"
            f"👤 Ism: <b>{w['name']}</b>\n"
            f"🛺 Mashina rusumi: <b>{w.get('car_model', 'Kiritilmagan')}</b>\n"
            f"🎨 Rangi: <b>{w.get('car_color', 'Kiritilmagan')}</b>\n"
            f"🚘 Raqam: <b>{w['car_number']}</b>\n"
            f"📞 Tel: <b>{w['phone']}</b>\n"
            f"📍 Hudud: <b>{w['region']}, {w['district']}</b>\n\n"
            f"💰 Balans: <b>{w['balance']:,} so'm</b>"
        )
        kb = [[InlineKeyboardButton("📦 Faol buyurtmalarim", callback_data="my_active_orders")], [InlineKeyboardButton("💰 Hisobni to'ldirish", callback_data="deposit_money")], [InlineKeyboardButton("📍 Hududni o'zgartirish", callback_data="change_my_region")], [InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_profile")]]
    else:
        text = (
            f"💳 <b>ЛИЧНЫЙ КАБИНЕТ (ВОДИТЕЛЬ)</b>\n\n"
            f"👤 Имя: <b>{w['name']}</b>\n"
            f"🛺 Марка авто: <b>{w.get('car_model', 'Не указано')}</b>\n"
            f"🎨 Цвет: <b>{w.get('car_color', 'Не указано')}</b>\n"
            f"🚘 Номер: <b>{w['car_number']}</b>\n"
            f"📞 Тел: <b>{w['phone']}</b>\n"
            f"📍 Регион: <b>{w['region']}, {w['district']}</b>\n\n"
            f"💰 Баланс: <b>{w['balance']:,} сум</b>"
        )
        kb = [[InlineKeyboardButton("📦 Мои активные заказы", callback_data="my_active_orders")], [InlineKeyboardButton("💰 Пополнить счет", callback_data="deposit_money")], [InlineKeyboardButton("📍 Изменить регион", callback_data="change_my_region")], [InlineKeyboardButton("🔄 Обновить", callback_data="refresh_profile")]]
        
    try: await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    except Exception: pass

async def help_cmd(update: Update, context):
    uid = update.effective_user.id
    lang = "uz"
    if uid in workers: lang = workers[uid].get("lang", "uz")
    elif context.user_data.get("lang"): lang = context.user_data.get("lang")
    
    if lang == "uz":
        msg = "<b>Yordam bo'limi:</b>\nMijoz yuk buyurtma qilishi, haydovchi esa uni qabul qilishi mumkin."
    else:
        msg = "<b>Раздел помощи:</b>\nКлиент может заказать перевозку груза, а водитель может принять этот заказ."
        
    if update.message: await update.message.reply_text(msg, parse_mode="HTML")

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "Botni boshlash / Запустить бота"),
        BotCommand("profile", "Shaxsiy kabinet / Личный кабинет"),
        BotCommand("help", "Yordam / Помощь")
    ])

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    text_filter = filters.TEXT & ~filters.COMMAND & ~filters.Regex("^(🚀 Botni boshlash / Rol tanlash|🚀 Запустить бота / Выбор роли|📦 Yuk yuborish \(Buyurtma\)|📦 Отправить груз \(Заказ\)|💳 Shaxsiy Kabinet \(Haydovchilar\)|💳 Личный кабинет \(Водители\)|ℹ️ Yordam / Ma'lumot|ℹ️ Помощь / Информация|🔍 Buyurtmalarni qidirish|🔍 Поиск заказов)$")

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^(🚀 Botni boshlash / Rol tanlash|🚀 Запустить бота / Выбор роли)$"), start),
            MessageHandler(filters.Regex("^(📦 Yuk yuborish \(Buyurtma\)|📦 Отправить груз \(Заказ\))$"), start_client_order),
            MessageHandler(filters.Regex("^(💳 Shaxsiy Kabinet \(Haydovchilar\)|💳 Личный кабинет \(Водители\))$"), profile_cmd),
            CallbackQueryHandler(deposit_money, pattern="^deposit_money$"),
            CallbackQueryHandler(paid_notification, pattern="^paid_notification$"),
            CallbackQueryHandler(change_my_region, pattern="^change_my_region$"),
            CallbackQueryHandler(re_order_start, pattern="^re_order_start$")
        ],
        states={
            LANG: [CallbackQueryHandler(select_lang, pattern="^lang_")],
            ROLE: [CallbackQueryHandler(role_sel, pattern="^role_")],
            C_REGION: [CallbackQueryHandler(c_region, pattern="^reg_")],
            C_DISTRICT: [CallbackQueryHandler(c_district, pattern="^(dist_|back_region)")],
            C_TARGET: [MessageHandler(text_filter, c_target)],
            C_DESC: [MessageHandler(text_filter, c_desc)], 
            C_TIME: [MessageHandler(text_filter, c_time)], 
            C_PHONE: [MessageHandler((text_filter | filters.CONTACT), c_phone)], # MA LI SINTAKSIS TOʻGʻRILANDI
            C_LOCATION: [MessageHandler((filters.LOCATION | text_filter), c_location)],
            C_CONFIRM: [CallbackQueryHandler(c_confirm, pattern="^c_(confirm|cancel)")],
            W_REGION: [CallbackQueryHandler(w_region, pattern="^wreg_")],
            W_DISTRICT: [CallbackQueryHandler(w_district, pattern="^(wdist_|back_w_region)")],
            W_NAME: [MessageHandler(text_filter, w_name)],
            W_CAR_MODEL: [MessageHandler(text_filter, w_car_model)], 
            W_CAR_COLOR: [MessageHandler(text_filter, w_car_color)], 
            W_CAR_NUMBER: [MessageHandler(text_filter, w_car_number)],
            W_PHONE: [MessageHandler(text_filter, w_phone)],
            W_CONFIRM: [CallbackQueryHandler(w_confirm, pattern="^w_(confirm|cancel)")],
            PAY_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pay_amount)],
            CH_REGION: [CallbackQueryHandler(ch_region, pattern="^chreg_")],
            CH_DISTRICT: [CallbackQueryHandler(ch_district, pattern="^(chdist_|back_ch_region)")]
        },
        fallbacks=[
            CommandHandler("start", start), 
            MessageHandler(filters.Regex("^(💳 Shaxsiy Kabinet \(Haydovchilar\)|💳 Личный кабинет \(Водители\))$"), profile_cmd)
        ],
        allow_reentry=True
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Regex("^(🔍 Buyurtmalarni qidirish|🔍 Поиск заказов)$"), search_orders_cmd))
    app.add_handler(CallbackQueryHandler(refresh_search_callback, pattern="^refresh_search$"))
    
    app.add_handler(CallbackQueryHandler(accept_order, pattern="^accept_"))
    app.add_handler(CallbackQueryHandler(client_cancel_order, pattern="^client_cancel_"))
    app.add_handler(CallbackQueryHandler(driver_cancel_order, pattern="^driver_cancel_"))
    app.add_handler(CallbackQueryHandler(approve_driver, pattern="^approve_"))
    app.add_handler(CallbackQueryHandler(admin_payment_confirm, pattern="^pay(add|denied)_"))
    app.add_handler(CallbackQueryHandler(my_active_orders, pattern="^my_active_orders$"))
    app.add_handler(CallbackQueryHandler(refresh_profile, pattern="^refresh_profile$"))
    
    app.add_handler(MessageHandler(filters.Regex("^(ℹ️ Yordam / Ma'lumot|ℹ️ Помощь / Информация)$"), help_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    
    app.run_polling()

if __name__ == "__main__":
    main()
