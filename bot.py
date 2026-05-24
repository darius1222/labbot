import logging
import os
import json
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Update,
    KeyboardButton, ReplyKeyboardMarkup, BotCommand
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

# --- SIZNING HAQIQIY KARTA MA'LUMOTLARINGIZ ---
KARTA_RAQAM = "9860 3566 1848 3396"
KARTA_EGA_SI = "Bot Admini"

# --- HAR BIR BUYURTMA UCHUN KOMISSIYA (XIZMAT HAQI) ---
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

# Conversation States
(
    LANG, ROLE,
    C_REGION, C_DISTRICT, C_TARGET, C_DESC, C_TIME, C_PHONE, C_LOCATION, C_CONFIRM,
    W_REGION, W_DISTRICT, W_NAME, W_PHONE, W_CONFIRM,
    PAY_AMOUNT
) = range(16)

# ===================== JSON BAZA TIZIMI =====================
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

# ===================== KEYBOARDS =====================
def main_menu_keyboard():
    kb = [
        [KeyboardButton("🚀 Buyurtma berish / Ro'yxatdan o'tish")],
        [KeyboardButton("💳 Shaxsiy Kabinet (Haydovchilar)"), KeyboardButton("ℹ️ Yordam / Ma'lumot")]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def regions_keyboard():
    kb = []
    row = []
    for idx, region in enumerate(REG_KEYS):
        row.append(InlineKeyboardButton(region, callback_data=f"reg_{idx}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    return InlineKeyboardMarkup(kb)

def districts_keyboard(region_idx):
    region_name = REG_KEYS[int(region_idx)]
    districts = REGIONS.get(region_name, [])
    kb = []
    row = []
    for d_idx, d in enumerate(districts):
        row.append(InlineKeyboardButton(d, callback_data=f"dist_{d_idx}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_region")])
    return InlineKeyboardMarkup(kb)

# ===================== START FUNCTION =====================
async def start(update: Update, context):
    context.user_data.clear() 
    kb = [[InlineKeyboardButton("O'zbekcha 🇺🇿", callback_data="lang_uz")]]
    
    msg = update.message if update.message else update.callback_query.message
    await msg.reply_text(
        "<b>Labo yuk tashish xizmatiga xush kelibsiz!</b>\n\nKerakli xizmatni tanlash uchun pastdagi menyudan foydalaning yoki tilni sozlang:", 
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )
    await msg.reply_text("Tilni tanlang:", reply_markup=InlineKeyboardMarkup(kb))
    return LANG

async def select_lang(update: Update, context):
    query = update.callback_query
    await query.answer()
    kb = [
        [InlineKeyboardButton("Mijoz (Yuk yuborish) 📦", callback_data="role_client")],
        [InlineKeyboardButton("Labochi (Haydovchi) 🛺", callback_data="role_worker")],
    ]
    await query.edit_message_text("Rolingizni tanlang:", reply_markup=InlineKeyboardMarkup(kb))
    return ROLE

async def role_sel(update: Update, context):
    query = update.callback_query
    await query.answer()
    role = query.data.split("_")[1]
    context.user_data["role"] = role
    
    if role == "client":
        await query.edit_message_text("Yuk qayerdan olinadi? Viloyatni tanlang:", reply_markup=regions_keyboard())
        return C_REGION
    else:
        uid = query.from_user.id
        if uid in workers and workers[uid].get("approved"):
            await query.edit_message_text("Siz allaqachon ro'yxatdan o'tgansiz. 'Shaxsiy Kabinet' menyusi orqali balansingizni ko'rishingiz mumkin.")
            return ConversationHandler.END
        await query.edit_message_text("Siz qaysi hududda yuk tashiysiz? Viloyatni tanlang:", reply_markup=regions_keyboard())
        return W_REGION

# ===================== MIJOZ OQIMI (FLOW) =====================
async def c_region(update: Update, context):
    query = update.callback_query
    await query.answer()
    reg_idx = query.data.replace("reg_", "")
    context.user_data["c_region_idx"] = reg_idx
    context.user_data["c_region"] = REG_KEYS[int(reg_idx)]
    
    await query.edit_message_text(f"Tanlangan viloyat: {context.user_data['c_region']}\nTumanni tanlang:", reply_markup=districts_keyboard(reg_idx))
    return C_DISTRICT

async def c_district(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "back_region":
        await query.edit_message_text("Yuk qayerdan olinadi? Viloyatni tanlang:", reply_markup=regions_keyboard())
        return C_REGION
        
    d_idx = int(query.data.replace("dist_", ""))
    reg_idx = context.user_data["c_region_idx"]
    district_name = REGIONS[REG_KEYS[int(reg_idx)]][d_idx]
    context.user_data["c_district"] = district_name
    
    await query.edit_message_text("🏁 <b>Aniq manzilni batafsil kiriting:</b>\n\nYuk qaysi qishloq/mahalladan olinadi va qayerga boradi? (Matn ko'rinishida yozing):", parse_mode="HTML")
    return C_TARGET

async def c_target(update: Update, context):
    if not update.message or not update.message.text:
        await update.message.reply_text("Iltimos, manzilni matn ko'rinishida yozib yuboring:")
        return C_TARGET
    context.user_data["c_target"] = update.message.text
    kb = [
        [KeyboardButton("📺 Texnikalar"), KeyboardButton("🦮 Hayvonlar")],
        [KeyboardButton("🧱 Qurilish mollari"), KeyboardButton("📦 Boshqa narsalar")]
    ]
    await update.message.reply_text("📦 Yukingiz qaysi turga kiradi?", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return C_DESC

async def c_desc(update: Update, context):
    if not update.message or not update.message.text:
        await update.message.reply_text("Ro'yxatdan tanlang yoki yuk turini yozing:")
        return C_DESC
    context.user_data["c_desc"] = update.message.text
    kb = [[KeyboardButton("⚡️ Hozir / Tezda")], [KeyboardButton("📅 Bugun kechroq"), KeyboardButton("📞 Kelishiladi")]]
    await update.message.reply_text("🕒 Yuk qachon olib ketilishi kerak?", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return C_TIME

async def c_time(update: Update, context):
    if not update.message or not update.message.text:
        await update.message.reply_text("Iltimos, vaqtni kiriting:")
        return C_TIME
    context.user_data["c_time"] = update.message.text
    kb = [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]]
    await update.message.reply_text("📞 Telefon raqamingizni kiriting yoki pastdagi tugmani bosing:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return C_PHONE

async def c_phone(update: Update, context):
    if update.message.contact:
        phone = update.message.contact.phone_number
    elif update.message.text:
        phone = update.message.text
    else:
        await update.message.reply_text("Iltimos, telefon raqamni yozing yoki tugmani bosing:")
        return C_PHONE
        
    context.user_data["c_phone"] = phone
    kb = [[KeyboardButton("📍 Joylashuvni yuborish", request_location=True)]]
    await update.message.reply_text("Yuk turgan joyning aniq lokatsiyasini yuboring (yoki matn qilib yozing):", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return C_LOCATION

async def c_location(update: Update, context):
    if update.message.location:
        lat, lon = update.message.location.latitude, update.message.location.longitude
        context.user_data["c_location_text"] = f"http://maps.google.com/?q={lat},{lon}"
    elif update.message.text:
        context.user_data["c_location_text"] = update.message.text
    else:
        await update.message.reply_text("Iltimos, lokatsiya ulashing yoki matn qilib yozing:")
        return C_LOCATION

    data = context.user_data
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
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    return C_CONFIRM

async def c_confirm(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "c_cancel":
        await query.edit_message_text("Ariza bekor qilindi.")
        return ConversationHandler.END

    uid = query.from_user.id
    data = context.user_data
    oid = int(order_counter[0]) 
    order_counter[0] += 1

    orders[oid] = {
        "id": oid, "client_id": uid, "region": data.get("c_region"), "district": data.get("c_district"),
        "desc": data.get("c_desc"), "target": data.get("c_target"), "time": data.get("c_time"), 
        "phone": data.get("c_phone"), "location_text": data.get("c_location_text"), 
        "status": "pending", "worker_id": None, "client_msg_id": None, "driver_messages": []
    }
    save_data()

    kb = [[InlineKeyboardButton("❌ Buyurtmani bekor qilish", callback_data=f"client_cancel_{oid}")]]
    sent_msg = await query.edit_message_text(
        f"⏳ <b>Ariza #{oid} haydovchilarga yuborildi!</b>\n\n"
        f"Haydovchi topilsa sizga darhol xabar beramiz. Istasangiz pastdagi tugma orqali arizani bekor qilishingiz mumkin.",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="HTML"
    )
    orders[oid]["client_msg_id"] = sent_msg.message_id 

    for wid, w in workers.items():
        if w.get("approved") and data.get("c_region") == w.get("region") and w.get("district") == data.get("c_district"):
            if w.get("balance", 0) >= FIXED_COMMISSION:
                drv_kb = [[InlineKeyboardButton(f"🛺 Qabul qilish ({FIXED_COMMISSION:,} so'm)", callback_data=f"accept_{oid}")]]
                try:
                    d_msg = await context.bot.send_message(
                        wid,
                        f"🔔 <b>YANGI BUYURTMA #{oid}!</b>\n\n"
                        f"📍 {data.get('c_region')}, {data.get('c_district')}\n"
                        f"🏁 Manzil: {data.get('c_target')}\n"
                        f"📦 Turi: {data.get('c_desc')} | 🕒 Vaqt: {data.get('c_time')}",
                        reply_markup=InlineKeyboardMarkup(drv_kb),
                        parse_mode="HTML"
                    )
                    orders[oid]["driver_messages"].append({"chat_id": int(wid), "message_id": d_msg.message_id})
                except Exception: pass
                
    save_data()
    return ConversationHandler.END

async def client_cancel_order(update: Update, context):
    query = update.callback_query
    await query.answer()
    oid = int(query.data.split("_")[2])

    if oid not in orders:
        await query.edit_message_text("Buyurtma topilmadi.")
        return

    order = orders[oid]
    if order["status"] == "accepted":
        await query.edit_message_text("⚠️ Kechirasiz, buyurtmani allaqachon haydovchi qabul qildi. Uni bekor qila olmaysiz.")
        return

    order["status"] = "cancelled_by_client"
    await query.edit_message_text("❌ Siz buyurtmani bekor qildingiz.")

    for msg_info in order.get("driver_messages", []):
        try:
            await context.bot.edit_message_text(
                chat_id=int(msg_info["chat_id"]),
                message_id=msg_info["message_id"],
                text=f"🔴 <b>Buyurtma #{oid} mijoz tomonidan bekor qilindi.</b>",
                parse_mode="HTML"
            )
        except Exception: pass
    save_data()

# ===================== BUYURTMANI QABUL QILISH =====================
async def accept_order(update: Update, context):
    query = update.callback_query
    await query.answer()
    oid = int(query.data.split("_")[1])
    uid = query.from_user.id

    if oid not in orders:
        await query.edit_message_text("Bu buyurtma topilmadi.")
        return
    
    order = orders[oid]
    if order["status"] == "cancelled_by_client":
        await query.edit_message_text("Mijoz buyurtmani bekor qilib bo'lgan. 😔")
        return
    if order["status"] != "pending":
        await query.edit_message_text("Kechikdingiz, boshqa haydovchi qabul qildi.")
        return

    w = workers.get(uid)
    if not w or w.get("balance", 0) < FIXED_COMMISSION:
        try:
            await context.bot.send_message(
                chat_id=uid, 
                text=f"❌ <b>Sizda yetarli mablag' yo'q!</b>\n\nBuyurtma komissiyasi: <b>{FIXED_COMMISSION:,} so'm</b>.\n"
                     f"Sizning balansingiz: {w.get('balance', 0):,} so'm.\n"
                     f"Iltimos, hisobingizni to'ldiring.",
                parse_mode="HTML"
            )
        except Exception: pass
        return

    order["status"] = "accepted"
    order["worker_id"] = uid
    w["balance"] -= FIXED_COMMISSION 
    w["total_orders"] += 1
    save_data()

    await query.edit_message_text(
        f"🎉 <b>Buyurtma #{oid} sizniki!</b>\n"
        f"💰 Balansingizdan <b>{FIXED_COMMISSION:,} so'm</b> yechildi.\n\n"
        f"📞 Mijoz: {order['phone']}\n"
        f"🏁 Manzil: {order['target']}\n"
        f"📍 Lokatsiya: {order['location_text']}\n\n"
        f"📞 Tezda aloqaga chiqib yo'lga chiqing!",
        parse_mode="HTML"
    )

    for msg_info in order.get("driver_messages", []):
        if int(msg_info["chat_id"]) != uid:
            try:
                await context.bot.edit_message_text(chat_id=int(msg_info["chat_id"]), message_id=msg_info["message_id"], text=f"🔕 Buyurtma #{oid} boshqa haydovchi tomonidan olindi.")
            except Exception: pass

    try:
        await context.bot.edit_message_text(
            chat_id=int(order["client_id"]), message_id=order["client_msg_id"],
            text=f"✅ <b>Haydovchi topildi!</b>\n\n🛺 {w['name']}\n📞 Tel: {w['phone']}\nHozir sizga aloqaga chiqadi.",
            parse_mode="HTML"
        )
    except Exception: pass

# ===================== HAYDOVCHILAR KABINETI TIZIMI =====================
async def profile_cmd(update: Update, context):
    if context.fsm_context if hasattr(context, 'fsm_context') else True:
        context.user_data.clear() 
    msg = update.message if update.message else update.callback_query.message
    uid = update.effective_user.id
    if uid not in workers:
        await msg.reply_text("Siz tizimda haydovchi sifatida ro'yxatdan o'tmagansiz!", reply_markup=main_menu_keyboard())
        return ConversationHandler.END
    w = workers[uid]
    
    text = f"💳 <b>SHAXSIY KABINET</b>\n\n💰 Elektron balans: {w['balance']:,} so'm\n🛺 Jami buyurtmalar: {w['total_orders']} ta\n🆔 Sizning ID: <code>{uid}</code>"
    kb = [
        [InlineKeyboardButton("🗂 Faol buyurtmalarim", callback_data="my_active_orders")],
        [InlineKeyboardButton("💰 Hisobni to'ldirish", callback_data="deposit_money")],
        [InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_profile")]
    ]
    await msg.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    return ConversationHandler.END

async def deposit_money(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    text = (
        f"💰 <b>HISOBNI TO'LDIRISH</b>\n\n"
        f"Elektron balansingizni to'ldirish uchun quyidagi plastik kartaga pul o'tkazing:\n\n"
        f"💳 Karta: <code>{KARTA_RAQAM}</code>\n"
        f"👤 Ega si: <b>{KARTA_EGA_SI}</b>\n\n"
        f"⚠️ <b>MUHIM:</b> Pul o'tkazgach, pastdagi '✅ To'lov qildim' tugmasini bosing!"
    )
    kb = [
        [InlineKeyboardButton("✅ To'lov qildim", callback_data="paid_notification")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="refresh_profile")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def paid_notification(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("💰 Qancha pul o'tkazganingizni yozing:\n(Faqat raqamlarda, masalan: 50000)")
    return PAY_AMOUNT

async def get_pay_amount(update: Update, context):
    uid = update.effective_user.id
    if not update.message or not update.message.text:
        await update.message.reply_text("❌ Summani to'g'ri ko'rinishda kiriting:")
        return PAY_AMOUNT
        
    amount_text = update.message.text.replace(" ", "").replace(",", "").replace(".", "")
    
    if not amount_text.isdigit():
        await update.message.reply_text("❌ Iltimos, faqat raqamlarda kiriting! Masalan: 50000")
        return PAY_AMOUNT
        
    amount = int(amount_text)
    w = workers.get(uid)
    
    admin_kb = [
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"payadd_{uid}_{amount}")],
        [InlineKeyboardButton("❌ Rad etish", callback_data=f"paydenied_{uid}")]
    ]
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💰 <b>YANGI TO'LOV BILDIRISHNOMASI!</b>\n\n"
                 f"👤 Haydovchi: {w['name']}\n"
                 f"📞 Tel: {w['phone']}\n"
                 f"🆔 ID: <code>{uid}</code>\n"
                 f"💵 Summa: <b>{amount:,} so'm</b>\n\n"
                 f"Kartangizni tekshirib, tasdiqlang:",
            reply_markup=InlineKeyboardMarkup(admin_kb),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Adminga xabar yuborishda xato: {e}")
    
    await update.message.reply_text(
        "✅ <b>Xabaringiz adminga yuborildi!</b>\n\nTo'lov tekshirilgach, balansingiz tez orada to'ldiriladi.",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END

async def admin_payment_confirm(update: Update, context):
    query = update.callback_query
    await query.answer()
    data_parts = query.data.split("_")
    action = data_parts[0]
    driver_id = int(data_parts[1])
    
    if action == "payadd":
        amount = int(data_parts[2])
        if driver_id in workers:
            workers[driver_id]["balance"] += amount
            save_data()
            
            await query.edit_message_text(f"✅ ID: {driver_id} hisobiga {amount:,} so'm qo'shildi.")
            try:
                await context.bot.send_message(
                    chat_id=driver_id,
                    text=f"🚀 <b>To'lovingiz tasdiqlandi!</b>\n\nHisobingizga <b>{amount:,} so'm</b> o'tkazildi. Buyurtmalarni qabul qilishingiz mumkin!"
                )
            except Exception: pass
    elif action == "paydenied":
        await query.edit_message_text("❌ To'lov rad etildi.")
        try:
            await context.bot.send_message(
                chat_id=driver_id,
                text="❌ <b>To'lovingiz bekor qilindi!</b>\n\nMuvaffaqiyatsiz bo'lsa adminga murojaat qiling."
            )
        except Exception: pass

async def my_active_orders(update: Update, context):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    
    found = False
    text = "📂 <b>Siz qabul qilgan faol buyurtmalar:</b>\n\n"
    for oid, o in orders.items():
        if o["worker_id"] == uid and o["status"] == "accepted":
            found = True
            text += f"🆔 <b>Buyurtma #{oid}:</b>\n📞 Tel: {o['phone']}\n🏁 Manzil: {o['target']}\n📍 <a href='{o['location_text']}'>Lokatsiya havolasi</a>\n\n"
    
    if not found:
        text += "Sizda hozircha faol bajarilayotgan buyurtmalar yo'q."
        
    kb = [[InlineKeyboardButton("🔙 Orqaga", callback_data="refresh_profile")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML", disable_web_page_preview=True)

async def refresh_profile(update: Update, context):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    w = workers.get(uid)
    if not w: return
    text = f"💳 <b>SHAXSIY KABINET</b>\n\n💰 Elektron balans: {w['balance']:,} so'm\n🛺 Jami buyurtmalar: {w['total_orders']} ta\n🆔 Sizning ID: <code>{uid}</code>"
    kb = [
        [InlineKeyboardButton("🗂 Faol buyurtmalarim", callback_data="my_active_orders")],
        [InlineKeyboardButton("💰 Hisobni to'ldirish", callback_data="deposit_money")],
        [InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_profile")]
    ]
    try: await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    except Exception: pass

# ===================== RO'YXATDAN O'TISH OQIMI =====================
async def w_region(update: Update, context):
    query = update.callback_query
    await query.answer()
    reg_idx = query.data.replace("reg_", "")
    context.user_data["w_region_idx"] = reg_idx
    context.user_data["w_region"] = REG_KEYS[int(reg_idx)]
    
    await query.edit_message_text(f"Viloyat: {context.user_data['w_region']}\nQaysi tumanda qatnaysiz?", reply_markup=districts_keyboard(reg_idx))
    return W_DISTRICT

async def w_district(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "back_region":
        await query.edit_message_text("Viloyatni tanlang:", reply_markup=regions_keyboard())
        return W_REGION
        
    d_idx = int(query.data.replace("dist_", ""))
    reg_idx = context.user_data["w_region_idx"]
    district_name = REGIONS[REG_KEYS[int(reg_idx)]][d_idx]
    context.user_data["w_district"] = district_name
    
    await query.edit_message_text("Ism-familiyangizni kiriting:")
    return W_NAME

async def w_name(update: Update, context):
    if not update.message or not update.message.text:
        await update.message.reply_text("Iltimos, ismingizni matn qilib yozing:")
        return W_NAME
    context.user_data["w_name"] = update.message.text
    await update.message.reply_text("Telefon raqamingizni kiriting:")
    return W_PHONE

async def w_phone(update: Update, context):
    if not update.message or not update.message.text:
        await update.message.reply_text("Iltimos, telefon raqamingizni kiriting:")
        return W_PHONE
    context.user_data["w_phone"] = update.message.text
    data = context.user_data
    text = f"Haydovchi: {data.get('w_name')}\nTel: {data.get('w_phone')}\nHudud: {data.get('w_region')}, {data.get('w_district')}\n\nMa'lumotlar to'g'rimi?"
    kb = [[InlineKeyboardButton("Ha, yuborilsin", callback_data="w_confirm")], [InlineKeyboardButton("Yo'q, bekor qilish", callback_data="w_cancel")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    return W_CONFIRM

async def w_confirm(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "w_cancel":
        await query.edit_message_text("Ro'yxatdan o'tish bekor qilindi.")
        return ConversationHandler.END

    uid = query.from_user.id
    data = context.user_data
    workers[uid] = {
        "name": data.get("w_name"), "phone": data.get("w_phone"), "region": data.get("w_region"),
        "district": data.get("w_district"), "approved": False, "balance": 0, "total_orders": 0
    }
    save_data()

    kb = [[InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{uid}")]]
    try:
        await context.bot.send_message(ADMIN_ID, f"🆕 <b>YANGI LABO HAYDOVCHISI ARIZASI:</b>\n\nIsm: {data.get('w_name')}\nTel: {data.get('w_phone')}\nHudud: {data.get('w_region')}\nID: <code>{uid}</code>", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    except Exception: pass
    await query.edit_message_text("Arizangiz adminga yuborildi. Tez orada profil faollashadi.")
    return ConversationHandler.END

async def approve_driver(update: Update, context):
    query = update.callback_query
    await query.answer()
    uid = int(query.data.split("_")[1])
    if uid in workers:
        workers[uid]["approved"] = True
        workers[uid]["balance"] = 8000  # Bonus start uchun
        save_data()
        await query.edit_message_text("Haydovchi tizimga muvaffaqiyatli qo'shildi!")
        try: await context.bot.send_message(uid, "🎉 Arizangiz tasdiqlandi! Botdan to'liq foydalanishingiz mumkin.")
        except Exception: pass

async def admin_pay_driver(update: Update, context):
    if update.effective_user.id != ADMIN_ID: return
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Xato format! Ishlatish: /pay ID SUMMA")
            return
        driver_id, amount = int(args[0]), int(args[1])
        if driver_id in workers:
            workers[driver_id]["balance"] += amount
            save_data()
            await update.message.reply_text(f"✅ ID {driver_id} hisobiga {amount:,} so'm qo'shildi.")
            try: await context.bot.send_message(driver_id, f"💰 Hisobingiz admin tomonidan {amount:,} so'mga to'ldirildi!")
            except Exception: pass
        else:
            await update.message.reply_text("Bunday ID dagi haydovchi topilmadi.")
    except Exception as e: await update.message.reply_text(f"Xato yuz berdi: {e}")

async def help_cmd(update: Update, context):
    if update.message:
        await update.message.reply_text("<b>Yordam bo'limi:</b>\n\nBot orqali mijozlar Labo avtomashinalariga buyurtma berishlari, haydovchilar esa shaxsiy kabinetlari orqali hisoblarini elektron to'ldirib, buyurtmalarni qabul qilishlari mumkin.", parse_mode="HTML")

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "Botni ishga tushirish"),
        BotCommand("profile", "Shaxsiy kabinet (Balans)"),
        BotCommand("help", "Yordam / Ma'lumot")
    ])

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    text_filter = filters.TEXT & ~filters.COMMAND & ~filters.Regex("^(🚀 Buyurtma berish / Ro'yxatdan o'tish|💳 Shaxsiy Kabinet \(Haydovchilar\)|ℹ️ Yordam / Ma'lumot)$")

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🚀 Buyurtma berish / Ro'yxatdan o'tish$"), start),
            MessageHandler(filters.Regex("^💳 Shaxsiy Kabinet \(Haydovchilar\)$"), profile_cmd),
            CallbackQueryHandler(deposit_money, pattern="^deposit_money$"),
            CallbackQueryHandler(paid_notification, pattern="^paid_notification$")
        ],
        states={
            LANG: [CallbackQueryHandler(select_lang, pattern="^lang_")],
            ROLE: [CallbackQueryHandler(role_sel, pattern="^role_")],
            C_REGION: [CallbackQueryHandler(c_region, pattern="^reg_")],
            C_DISTRICT: [CallbackQueryHandler(c_district, pattern="^(dist_|back_region)")],
            C_TARGET: [MessageHandler(text_filter, c_target)],
            C_DESC: [MessageHandler(text_filter, c_desc)], 
            C_TIME: [MessageHandler(text_filter, c_time)], 
            C_PHONE: [MessageHandler((text_filter | filters.CONTACT), c_phone)],
            C_LOCATION: [MessageHandler((filters.LOCATION | text_filter), c_location)],
            C_CONFIRM: [CallbackQueryHandler(c_confirm, pattern="^c_(confirm|cancel)")],
            W_REGION: [CallbackQueryHandler(w_region, pattern="^reg_")],
            W_DISTRICT: [CallbackQueryHandler(w_district, pattern="^(dist_|back_region)")],
            W_NAME: [MessageHandler(text_filter, w_name)],
            W_PHONE: [MessageHandler(text_filter, w_phone)],
            W_CONFIRM: [CallbackQueryHandler(w_confirm, pattern="^w_(confirm|cancel)")],
            PAY_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pay_amount)]
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🚀 Buyurtma berish / Ro'yxatdan o'tish$"), start),
            MessageHandler(filters.Regex("^💳 Shaxsiy Kabinet \(Haydovchilar\)$"), profile_cmd)
        ],
        allow_reentry=True
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(accept_order, pattern="^accept_"))
    app.add_handler(CallbackQueryHandler(client_cancel_order, pattern="^client_cancel_"))
    app.add_handler(CallbackQueryHandler(approve_driver, pattern="^approve_"))
    
    app.add_handler(CallbackQueryHandler(admin_payment_confirm, pattern="^payadd_"))
    app.add_handler(CallbackQueryHandler(admin_payment_confirm, pattern="^paydenied_"))
    
    app.add_handler(CallbackQueryHandler(my_active_orders, pattern="^my_active_orders$"))
    app.add_handler(CallbackQueryHandler(refresh_profile, pattern="^refresh_profile$"))
    app.add_handler(CallbackQueryHandler(deposit_money, pattern="^deposit_money$"))
    app.add_handler(CallbackQueryHandler(paid_notification, pattern="^paid_notification$"))
    
    app.add_handler(MessageHandler(filters.Regex("^💳 Shaxsiy Kabinet \(Haydovchilar\)$"), profile_cmd))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Yordam / Ma'lumot$"), help_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("pay", admin_pay_driver))
    
    app.run_polling()

if __name__ == "__main__":
    main()
