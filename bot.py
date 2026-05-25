import logging
import os
import json
import asyncio
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Update,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)
from telegram.error import TelegramError

# Logging sozlamalari (Muammolarni tezkor aniqlash uchun)
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===================== SOZLAMALAR =====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8932867764:AAFd-2yHxCqWBcnjQoK3Wy03T2hx3S04iCE")
ADMIN_ID = 692744901

KARTA_RAQAM = "9860 3566 1848 3396"
KARTA_EGA_SI = "Bot Admini"
FIXED_COMMISSION = 4000 

REGIONS = {
    "Andijon viloyati": {
        "Andijon shahar": ["Markaz", "Sanoat zonasi", "Yangi shahar"],
        "Andijon tumani": ["Kuyganyor sh.", "Og'ullik", "Xartum", "Chunbosh"],
        "Asaka tumani": ["Asaka sh.", "Kujgan", "Navkan", "Toshkan"],
        "Buloqboshi tumani": [
            "Buloqboshi sh. (Markaz)", "Andijon MFY", "Uchtepa MFY", "Kullas MFY", 
            "Shirmonbuloq q.", "Nayman MFY", "Keltepa MFY", "Sarvontepa MFY", "Tog'liq MFY"
        ],
        "Xo'jaobod tumani": [
            "Xo'jaobod sh. (Markaz)", "Karnaychi MFY", "Qorabuloq MFY", "Uchko'cha MFY", 
            "Mustahkam MFY", "Baxrin MFY", "Dilkushod ShFY", "Guliston sh.", "Ko'tarma sh."
        ]
    },
    "Toshkent shahri": {
        "Chilonzor tumani": ["Oqtepa", "Algoritm", "Chilonzor massivi"],
        "Yunusobod tumani": ["Yunusobod 1-19 kvartal", "Bodomzor", "Shahriston"]
    }
}

REG_KEYS = list(REGIONS.keys())

# CONVERSATION HOLATLARI
(
    LANG, ROLE,
    C_REGION, C_DISTRICT, C_SUB_DISTRICT, C_TARGET, C_DESC, C_TIME, C_PHONE, C_LOCATION, C_CONFIRM,
    W_REGION, W_DISTRICT, W_SUB_DISTRICT, W_NAME, W_CAR_MODEL, W_CAR_COLOR, W_CAR_NUMBER, W_PHONE, W_CONFIRM
) = range(20)

DATA_FILE = "bot_data.json"

# ===================== FAYL BILAN ISHLASH (XAVFSIZ) =====================
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
            logger.error(f"⚠️ Kritik xato: JSON o'qilmadi, zaxira yaratilmoqda: {e}")
            return {}, {}, [1]
    return {}, {}, [1]

def save_data():
    global workers, orders, order_counter
    try:
        # Ma'lumotlarni xavfsiz vaqtinchalik faylga yozib keyin almashtiramiz (Crash-proof)
        temp_file = DATA_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump({"workers": workers, "orders": orders, "order_counter": order_counter}, f, ensure_ascii=False, indent=4)
        if os.path.exists(temp_file):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            os.rename(temp_file, DATA_FILE)
    except Exception as e:
        logger.error(f"⚠️ Ma'lumotlarni yozishda xato: {e}")

workers, orders, order_counter = load_data()

# ===================== SILLIQ KLAVIATURALAR =====================
def client_menu_keyboard(lang="uz"):
    if lang == "uz":
        return ReplyKeyboardMarkup([[KeyboardButton("📦 Yuk yuborish (Buyurtma)")], [KeyboardButton("ℹ️ Yordam / Ma'lumot")]], resize_keyboard=True)
    return ReplyKeyboardMarkup([[KeyboardButton("📦 Отправить груз (Заказ)")], [KeyboardButton("ℹ️ Помощь / Информация")]], resize_keyboard=True)

def driver_menu_keyboard(lang="uz"):
    if lang == "uz":
        return ReplyKeyboardMarkup([
            [KeyboardButton("🔍 Buyurtmalarni qidirish")],
            [KeyboardButton("💳 Shaxsiy Kabinet"), KeyboardButton("ℹ️ Yordam / Ma'lumot")]
        ], resize_keyboard=True)
    return ReplyKeyboardMarkup([
        [KeyboardButton("🔍 Поиск заказов")],
        [KeyboardButton("💳 Личный кабинет"), KeyboardButton("ℹ️ Помощь / Информация")],
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
    try:
        region_name = REG_KEYS[int(region_idx)]
        districts = list(REGIONS.get(region_name, {}).keys())
        kb = []
        row = []
        for d_idx, d in enumerate(districts):
            row.append(InlineKeyboardButton(d, callback_data=f"{prefix}{d_idx}"))
            if len(row) == 2:
                kb.append(row)
                row = []
        if row: kb.append(row)
        kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data=back_callback)])
        return InlineKeyboardMarkup(kb)
    except Exception:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=back_callback)]])

def sub_districts_keyboard(region_name, district_name, prefix="sub_", back_callback="back_dist"):
    try:
        sub_districts = REGIONS.get(region_name, {}).get(district_name, [])
        kb = []
        row = []
        for s_idx, s in enumerate(sub_districts):
            row.append(InlineKeyboardButton(s, callback_data=f"{prefix}{s_idx}"))
            if len(row) == 2:
                kb.append(row)
                row = []
        if row: kb.append(row)
        kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data=back_callback)])
        return InlineKeyboardMarkup(kb)
    except Exception:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=back_callback)]])

# ===================== ASOSIY LOXIKA =====================
async def start(update: Update, context):
    try:
        global workers
        uid = update.effective_user.id
        msg = update.message if update.message else update.callback_query.message
        
        if uid in workers:
            w = workers[uid]
            lang = w.get("lang", "uz")
            context.user_data["lang"] = lang 
            
            if w.get("approved"):
                await msg.reply_text(
                    f"<b>Xush kelibsiz, {w['name']}!</b>\n\nTizim sizni tanidi. Haydovchi rejimingiz faol.", 
                    reply_markup=driver_menu_keyboard(lang), parse_mode="HTML"
                )
            else:
                await msg.reply_text(
                    "<b>Sizning arizangiz kutilmoqda.</b>\nAdmin tasdiqlashi bilan buyurtmalarni olishingiz mumkin.", 
                    reply_markup=driver_menu_keyboard(lang), parse_mode="HTML"
                )
            return ConversationHandler.END

        context.user_data.clear() 
        kb = [[InlineKeyboardButton("🇺🇿 O'ZBEKCHA", callback_data="lang_uz")], [InlineKeyboardButton("🇷🇺 РУССКИЙ", callback_data="lang_ru")]]
        await msg.reply_text("✨ <b>Xush kelibsiz!</b>\nTilni tanlang / Выберите язык:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        return LANG
    except Exception as e:
        logger.error(f"Start xatosi: {e}")
        return ConversationHandler.END

async def select_lang(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        lang = query.data.split("_")[1]
        context.user_data["lang"] = lang
        
        kb = [
            [InlineKeyboardButton("Mijoz (Yuk yuborish) 📦" if lang=="uz" else "Клиент 📦", callback_data="role_client")],
            [InlineKeyboardButton("Haydovchi (Ro'yxatdan o'tish) 🛺" if lang=="uz" else "Водитель 🛺", callback_data="role_worker")]
        ]
        await query.edit_message_text("Botdan foydalanish rolini tanlang:", reply_markup=InlineKeyboardMarkup(kb))
        return ROLE
    except Exception as e:
        logger.error(f"Til tanlash xatosi: {e}")
        return ConversationHandler.END

async def role_sel(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        role = query.data.split("_")[1]
        context.user_data["role"] = role
        lang = context.user_data.get("lang", "uz")
        
        if role == "client":
            await context.bot.send_message(chat_id=query.from_user.id, text="Mijoz menyusi faollashdi.", reply_markup=client_menu_keyboard(lang))
            await query.edit_message_text("Yuk qayerdan olinadi? Viloyatni tanlang:", reply_markup=regions_keyboard("reg_"))
            return C_REGION
        else:
            await query.edit_message_text("Haydovchi ro'yxatdan o'tish oynasi.\nViloyatni tanlang:", reply_markup=regions_keyboard("wreg_"))
            return W_REGION
    except Exception as e:
        logger.error(f"Rol tanlash xatosi: {e}")
        return ConversationHandler.END

# ===================== MIJOZ ZANJIRI (XATOlarsiz) =====================
async def start_client_order(update: Update, context):
    try:
        lang = context.user_data.get("lang", "uz")
        context.user_data.clear()
        context.user_data["lang"] = lang
        await update.message.reply_text("Yuk qayerdan olinadi? Viloyatni tanlang:", reply_markup=regions_keyboard("reg_"))
        return C_REGION
    except Exception as e:
        logger.error(f"Mijoz buyurtma start xatosi: {e}")
        return ConversationHandler.END

async def c_region(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        reg_idx = query.data.replace("reg_", "")
        context.user_data["c_region_idx"] = reg_idx
        context.user_data["c_region"] = REG_KEYS[int(reg_idx)]
        
        await query.edit_message_text(f"Viloyat: {context.user_data['c_region']}\nTumanni tanlang:", reply_markup=districts_keyboard(reg_idx, "dist_", "back_region"))
        return C_DISTRICT
    except Exception as e:
        logger.error(f"C_region xatosi: {e}")
        return ConversationHandler.END

async def c_district(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        if query.data == "back_region":
            await query.edit_message_text("Viloyatni tanlang:", reply_markup=regions_keyboard("reg_"))
            return C_REGION
            
        d_idx = int(query.data.replace("dist_", ""))
        reg_name = context.user_data["c_region"]
        dist_name = list(REGIONS[reg_name].keys())[d_idx]
        context.user_data["c_district"] = dist_name
        
        await query.edit_message_text(f"Tuman: {dist_name}\n🏠 Qishloq, shaharcha yoki mahallani tanlang:", reply_markup=sub_districts_keyboard(reg_name, dist_name, "csub_", "back_dist"))
        return C_SUB_DISTRICT
    except Exception as e:
        logger.error(f"C_district xatosi: {e}")
        return ConversationHandler.END

async def c_sub_district(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        if query.data == "back_dist":
            reg_idx = context.user_data["c_region_idx"]
            await query.edit_message_text("Tumanni tanlang:", reply_markup=districts_keyboard(reg_idx, "dist_", "back_region"))
            return C_DISTRICT
            
        s_idx = int(query.data.replace("csub_", ""))
        reg_name = context.user_data["c_region"]
        dist_name = context.user_data["c_district"]
        sub_name = REGIONS[reg_name][dist_name][s_idx]
        context.user_data["c_sub_district"] = sub_name
        
        await query.edit_message_text("🏁 <b>Aniq manzilni batafsil kiriting:</b>\n\nYuk qayerdan olinadi va qayerga boradi? (Yozib yuboring):", parse_mode="HTML")
        return C_TARGET
    except Exception as e:
        logger.error(f"C_sub_district xatosi: {e}")
        return ConversationHandler.END

async def c_target(update: Update, context):
    context.user_data["c_target"] = update.message.text if update.message.text else "Ko'rsatilmagan"
    kb = [[KeyboardButton("📺 Texnikalar"), KeyboardButton("🦮 Hayvonlar")], [KeyboardButton("🧱 Qurilish mollari"), KeyboardButton("📦 Boshqa narsalar")]]
    await update.message.reply_text("📦 Yukingiz qaysi turga kiradi?", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return C_DESC

async def c_desc(update: Update, context):
    context.user_data["c_desc"] = update.message.text if update.message.text else "Boshqa"
    kb = [[KeyboardButton("⚡️ Hozir / Tezda")], [KeyboardButton("📅 Bugun kechroq"), KeyboardButton("📞 Kelishiladi")]]
    await update.message.reply_text("🕒 Yuk qachon olib ketilishi kerak?", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return C_TIME

async def c_time(update: Update, context):
    context.user_data["c_time"] = update.message.text if update.message.text else "Kelishiladi"
    kb = [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]]
    await update.message.reply_text("📞 Telefon raqamingizni yuboring yoki kiriting:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return C_PHONE

async def c_phone(update: Update, context):
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    context.user_data["c_phone"] = phone
    kb = [[KeyboardButton("📍 Joylashuvni yuborish", request_location=True)]]
    await update.message.reply_text("Yuk lokatsiyasini yuboring (yoki matn ko'rinishida yozing):", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return C_LOCATION

async def c_location(update: Update, context):
    if update.message.location:
        lat, lon = update.message.location.latitude, update.message.location.longitude
        context.user_data["c_location_text"] = f"http://maps.google.com/?q={lat},{lon}"
    else:
        context.user_data["c_location_text"] = update.message.text if update.message.text else "Lokatsiya berilmagan"

    data = context.user_data
    text = (
        f"📋 <b>ARIZANGIZ TAYYOR:</b>\n\n"
        f"📍 Hudud: {data.get('c_region')}, {data.get('c_district')}, {data.get('c_sub_district')}\n"
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

# ASINXRON FONDA XABAR TARQATISH (BOT QATMASLIGI UCHUN ENG MUHIM JOYI)
async def broadcast_order_to_drivers(bot, oid, data):
    global workers
    for wid, w in list(workers.items()):
        if w.get("approved") and data.get("c_region") == w.get("region") and w.get("district") == data.get("c_district") and data.get("c_sub_district") == w.get("sub_district"):
            if w.get("balance", 0) >= FIXED_COMMISSION:
                drv_kb = [[InlineKeyboardButton(f"🛺 Qabul qilish ({FIXED_COMMISSION:,} so'm)", callback_data=f"accept_{oid}")]]
                try:
                    d_msg = await bot.send_message(
                        wid,
                        f"🔔 <b>YANGI HUDUDIY BUYURTMA #{oid}!</b>\n\n"
                        f"📍 {data.get('c_region')}, {data.get('c_district')}\n"
                        f"🏡 Qishloq/Mahalla: {data.get('c_sub_district')}\n"
                        f"🏁 Manzil: {data.get('c_target')}\n"
                        f"📦 Turi: {data.get('c_desc')} | {data.get('c_time')}",
                        reply_markup=InlineKeyboardMarkup(drv_kb), parse_mode="HTML"
                    )
                    orders[oid]["driver_messages"].append({"chat_id": int(wid), "message_id": d_msg.message_id})
                except TelegramError:
                    pass # Agar haydovchi botni block qilgan bo'lsa bot to'xtab qolmaydi
    save_data()

async def c_confirm(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        global order_counter, orders
        
        if query.data == "c_cancel":
            await query.edit_message_text("Ariza bekor qilindi.")
            return ConversationHandler.END

        uid = query.from_user.id
        data = context.user_data
        oid = int(order_counter[0]) 
        order_counter[0] += 1

        orders[oid] = {
            "id": oid, "client_id": uid, "region": data.get("c_region"), "district": data.get("c_district"), "sub_district": data.get("c_sub_district"),
            "desc": data.get("c_desc"), "target": data.get("c_target"), "time": data.get("c_time"), 
            "phone": data.get("c_phone"), "location_text": data.get("c_location_text"), 
            "status": "pending", "worker_id": None, "client_msg_id": None, "driver_messages": [], "client_lang": data.get("lang", "uz")
        }
        save_data()

        kb = [[InlineKeyboardButton("❌ Buyurtmani bekor qilish", callback_data=f"client_cancel_{oid}")]]
        sent_msg = await query.edit_message_text(f"⏳ <b>Ariza #{oid} haydovchilarga yuborildi!</b>\n\nAynan siz tanlagan qishloq/mahalla haydovchilariga bildirishnoma ketdi.", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        orders[oid]["client_msg_id"] = sent_msg.message_id 

        # Fon oqimiga topshiramiz, bot keyingi foydalanuvchiga silliq javob beraveradi
        asyncio.create_task(broadcast_order_to_drivers(context.bot, oid, data))

        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Tasdiqlash xatosi: {e}")
        return ConversationHandler.END

# ===================== HAYDOVCHILAR QISMI (XAVFSIZ) =====================
async def search_orders_cmd(update: Update, context):
    try:
        global orders, workers
        uid = update.effective_user.id
        if uid not in workers: return

        w = workers[uid]
        if not w.get("approved"):
            await update.message.reply_text("⚠️ Arizangiz hali admin tomonidan tasdiqlanmagan.")
            return

        hr_sub = w.get("sub_district")
        found_orders = [o for o in list(orders.values()) if o["status"] == "pending" and o["region"] == w["region"] and o["district"] == w["district"] and o.get("sub_district") == hr_sub]

        if not found_orders:
            kb = [[InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_search")]]
            await update.message.reply_text(f"📍 <b>{hr_sub}</b> hududida faol buyurtmalar yo'q.", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
            return

        await update.message.reply_text(f"🔍 <b>Sizning qishlog'ingizdagi buyurtmalar ({len(found_orders)} ta):</b>", parse_mode="HTML")
        for o in found_orders:
            drv_kb = [[InlineKeyboardButton(f"🛺 Qabul qilish", callback_data=f"accept_{o['id']}")]]
            await update.message.reply_text(f"📦 <b>BUYURTMA #{o['id']} ({o.get('sub_district')})</b>\n🏁 Manzil: {o['target']}\n📦 Turi: {o['desc']}", reply_markup=InlineKeyboardMarkup(drv_kb), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Qidiruv xatosi: {e}")

async def refresh_search_callback(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        global orders, workers
        uid = query.from_user.id
        w = workers.get(uid)
        if not w or not w.get("approved"): return

        found_orders = [o for o in list(orders.values()) if o["status"] == "pending" and o["region"] == w["region"] and o["district"] == w["district"] and o.get("sub_district") == w["sub_district"]]

        if not found_orders:
            kb = [[InlineKeyboardButton("🔄 Qayta yangilash", callback_data="refresh_search")]]
            await query.edit_message_text(f"⏳ Hozircha yangi buyurtma yo'q.\nHudud: {w['sub_district']}", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
            return

        await query.edit_message_text("✅ Yangi buyurtmalar bor!")
        for o in found_orders:
            drv_kb = [[InlineKeyboardButton("🛺 Qabul qilish", callback_data=f"accept_{o['id']}")]]
            await context.bot.send_message(chat_id=uid, text=f"📦 <b>#{o['id']}</b>\n Manzil: {o['target']}", reply_markup=InlineKeyboardMarkup(drv_kb))
    except Exception as e:
        logger.error(f"Yangilash xatosi: {e}")

async def accept_order(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        global orders, workers
        oid = int(query.data.split("_")[1])
        uid = query.from_user.id

        if oid not in orders: return
        order = orders[oid]
        w = workers.get(uid)
        
        if order["status"] != "pending":
            await query.edit_message_text("Kechikdingiz, buyurtma allaqachon olingan.")
            return

        if not w or w.get("balance", 0) < FIXED_COMMISSION:
            await context.bot.send_message(uid, "❌ Balansda mablag' yetarli emas!")
            return

        order["status"] = "accepted"
        order["worker_id"] = uid
        w["balance"] -= FIXED_COMMISSION 
        w["total_orders"] += 1
        save_data()

        drv_cancel_kb = [[InlineKeyboardButton("❌ Voz kechish", callback_data=f"driver_cancel_{oid}")]]
        await query.edit_message_text(f"🎉 <b>Buyurtma sizniki!</b>\n\n📞 Mijoz: {order['phone']}\n🏁 Manzil: {order['target']}\n📍 <a href='{order['location_text']}'>Lokatsiya</a>", reply_markup=InlineKeyboardMarkup(drv_cancel_kb), parse_mode="HTML")

        # Boshqa haydovchilardagi xabarlarni tozalash (Xavfsiz asinxron oqimda)
        for msg_info in order.get("driver_messages", []):
            if int(msg_info["chat_id"]) != uid:
                try: await context.bot.edit_message_text(chat_id=int(msg_info["chat_id"]), message_id=msg_info["message_id"], text=f"🔕 Buyurtma #{oid} boshqa haydovchi tomonidan olindi.")
                except Exception: pass

        client_cancel_kb = [[InlineKeyboardButton("❌ Bekor qilish", callback_data=f"client_cancel_{oid}")]]
        cl_text = f"✅ <b>Haydovchi topildi!</b>\n\n🛺 Ismi: {w['name']}\n📞 Telefon: {w['phone']}\n🚗 Mashina: {w['car_color']} {w['car_model']} ({w['car_number']})"
        try: await context.bot.edit_message_text(chat_id=order["client_id"], message_id=order["client_msg_id"], text=cl_text, reply_markup=InlineKeyboardMarkup(client_cancel_kb), parse_mode="HTML")
        except Exception: pass
    except Exception as e:
        logger.error(f"Buyurtma qabul xatosi: {e}")

async def client_cancel_order(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        global orders, workers
        oid = int(query.data.split("_")[-1])
        if oid not in orders: return
        order = orders[oid]
        
        if order["status"] == "cancelled_by_client": return

        order["status"] = "cancelled_by_client"
        wid = order["worker_id"]
        if wid and wid in workers:
            workers[wid]["balance"] += FIXED_COMMISSION
            try: await context.bot.send_message(wid, f"🔕 Buyurtma #{oid} mijoz tomonidan bekor qilindi. Pul balansingizga qaytarildi.")
            except Exception: pass
        save_data()
        await query.edit_message_text("Buyurtmangiz muvaffaqiyatli bekor qilindi.")
    except Exception as e:
        logger.error(f"Mijoz bekor qilish xatosi: {e}")

async def driver_cancel_order(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        global orders, workers
        oid = int(query.data.split("_")[-1])
        uid = query.from_user.id
        if oid not in orders: return
        order = orders[oid]
        
        order["status"] = "pending"
        order["worker_id"] = None
        if uid in workers:
            workers[uid]["balance"] += FIXED_COMMISSION
        save_data()
        await query.edit_message_text("Siz buyurtmadan voz kechdingiz. Pul balansingizga qaytarildi.")
        try: await context.bot.send_message(order["client_id"], "⚠️ Haydovchi buyurtmani bekor qildi. Tizim qayta qidirmoqda...")
        except Exception: pass
    except Exception as e:
        logger.error(f"Haydovchi voz kechish xatosi: {e}")

# ===================== HAYDOVCHI REGISTRATSIYA (MUTLAQ HIMOYA) =====================
async def w_region(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        reg_idx = query.data.replace("wreg_", "")
        context.user_data["w_region_idx"] = reg_idx
        context.user_data["w_region"] = REG_KEYS[int(reg_idx)]
        await query.edit_message_text(f"Viloyat: {context.user_data['w_region']}\nTumaningizni tanlang:", reply_markup=districts_keyboard(reg_idx, "wdist_", "wback_region"))
        return W_DISTRICT
    except Exception as e:
        logger.error(f"W_region xatosi: {e}")
        return ConversationHandler.END

async def w_district(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        if query.data == "wback_region":
            await query.edit_message_text("Viloyatni tanlang:", reply_markup=regions_keyboard("wreg_"))
            return W_REGION
            
        d_idx = int(query.data.replace("wdist_", ""))
        reg_name = context.user_data["w_region"]
        dist_name = list(REGIONS[reg_name].keys())[d_idx]
        context.user_data["w_district"] = dist_name
        
        await query.edit_message_text(f"Tuman: {dist_name}\n🏠 Asosiy ish joyingiz (Qishloq/Shaharacha/Mahalla):", reply_markup=sub_districts_keyboard(reg_name, dist_name, "wsub_", "wback_dist"))
        return W_SUB_DISTRICT
    except Exception as e:
        logger.error(f"W_district xatosi: {e}")
        return ConversationHandler.END

async def w_sub_district(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        if query.data == "wback_dist":
            reg_idx = context.user_data["w_region_idx"]
            await query.edit_message_text("Tumaningizni tanlang:", reply_markup=districts_keyboard(reg_idx, "wdist_", "wback_region"))
            return W_DISTRICT
            
        s_idx = int(query.data.replace("wsub_", ""))
        reg_name = context.user_data["w_region"]
        dist_name = context.user_data["w_district"]
        sub_name = REGIONS[reg_name][dist_name][s_idx]
        context.user_data["w_sub_district"] = sub_name
        
        await context.bot.send_message(chat_id=query.from_user.id, text="Ism va familiyangizni kiriting:", reply_markup=ReplyKeyboardRemove())
        return W_NAME
    except Exception as e:
        logger.error(f"W_sub xatosi: {e}")
        return ConversationHandler.END

async def w_name(update: Update, context):
    context.user_data["w_name"] = update.message.text
    await update.message.reply_text("Mashinangiz modeli (Masalan: Labo, Damas):")
    return W_CAR_MODEL

async def w_car_model(update: Update, context):
    context.user_data["w_car_model"] = update.message.text
    await update.message.reply_text("Mashina rangi:")
    return W_CAR_COLOR

async def w_car_color(update: Update, context):
    context.user_data["w_car_color"] = update.message.text
    await update.message.reply_text("Mashina davlat raqami (Masalan: 01 A 777 AA):")
    return W_CAR_NUMBER

async def w_car_number(update: Update, context):
    context.user_data["w_car_number"] = update.message.text
    kb = [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]]
    await update.message.reply_text("Telefon raqamingizni yuboring:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return W_PHONE

async def w_phone(update: Update, context):
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    context.user_data["w_phone"] = phone
    
    data = context.user_data
    text = (
        f"🚖 <b>HAYDOVCHI ANKETASI:</b>\n\n"
        f"👤 Ism: {data.get('w_name')}\n"
        f"📍 Hudud: {data.get('w_region')}, {data.get('w_district')}, {data.get('w_sub_district')}\n"
        f"🚗 Mashina: {data.get('w_car_color')} {data.get('w_car_model')}\n"
        f"🔢 Nomer: {data.get('w_car_number')}\n"
        f"📞 Telefon: {data.get('w_phone')}\n\n"
        f"Ma'lumotlar to'g'rimi?"
    )
    kb = [[InlineKeyboardButton("✅ Ha, yuborish", callback_data="w_confirm")], [InlineKeyboardButton("❌ Qayta to'ldirish", callback_data="w_cancel")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    return W_CONFIRM

async def w_confirm(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        global workers
        if query.data == "w_cancel":
            await query.edit_message_text("Ro'yxatdan o'tish bekor qilindi. Qayta boshlash: /start")
            return ConversationHandler.END
            
        uid = query.from_user.id
        data = context.user_data
        
        workers[uid] = {
            "id": uid, "name": data.get("w_name"), "region": data.get("w_region"), "district": data.get("w_district"), "sub_district": data.get("w_sub_district"),
            "car_model": data.get("w_car_model"), "car_color": data.get("w_car_color"), "car_number": data.get("w_car_number"),
            "phone": data.get("w_phone"), "approved": False, "balance": 0, "total_orders": 0, "lang": data.get("lang", "uz")
        }
        save_data()
        
        await context.bot.send_message(chat_id=uid, text="✅ Arizangiz adminga yuborildi.", reply_markup=driver_menu_keyboard(data.get("lang", "uz")))
        
        admin_txt = f"🆕 <b>YANGI HAYDOVCHI:</b>\n\nID: <code>{uid}</code>\n👤 Ism: {data.get('w_name')}\n📍 Hudud: {data.get('w_region')}, {data.get('w_district')}, {data.get('w_sub_district')}"
        kb = [[InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin_approve_{uid}")], [InlineKeyboardButton("❌ Rad etish", callback_data=f"admin_reject_{uid}")]]
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"W_confirm xatosi: {e}")
        return ConversationHandler.END

# ===================== ADMIN PANEL (HAYDOVCHINI TASDIQLASH) =====================
async def admin_callback(update: Update, context):
    query = update.callback_query
    try:
        await query.answer()
        global workers
        act = query.data.split("_")[1]
        target_id = int(query.data.split("_")[2])
        
        if act == "approve":
            if target_id in workers:
                workers[target_id]["approved"] = True
                save_data()
                await query.edit_message_text(f"✅ Haydovchi (ID: {target_id}) tasdiqlandi.")
                try: await context.bot.send_message(target_id, "🎉 Arizangiz tasdiqlandi!", reply_markup=driver_menu_keyboard(workers[target_id]["lang"]))
                except Exception: pass
        elif act == "reject":
            if target_id in workers:
                del workers[target_id]
                save_data()
                await query.edit_message_text(f"❌ Arizasi rad etildi.")
    except Exception as e:
        logger.error(f"Admin callback xatosi: {e}")

# ===================== SINF VA PANELLAR =====================
async def shaxsiy_kabinet(update: Update, context):
    global workers
    uid = update.effective_user.id
    if uid not in workers: return
    w = workers[uid]
    status = "Aktiv ✅" if w.get("approved") else "Kutilmoqda ⏳"
    text = f"💳 <b>SHAXSIY KABINET</b>\n\n👤 Ism: {w['name']}\n🏠 Ish hududi: {w['sub_district']}\n📊 Holati: {status}\n💰 Balans: {w['balance']:,} so'm\n🛺 Jami buyurtmalar: {w['total_orders']} ta\n\n💵 Karta: <code>{KARTA_RAQAM}</code>\nEga si: {KARTA_EGA_SI}"
    await update.message.reply_text(text, parse_mode="HTML")

async def yordam_info(update: Update, context):
    await update.message.reply_text("ℹ️ Hududiy Yuk Tashish Logistika Xizmati Bot Tizimi.")

async def cancel(update: Update, context):
    await update.message.reply_text("Jarayon bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ===================== ASOSIY MATOR (RUN ENGINE) =====================
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^(📦 Yuk yuborish \(Buyurtma\)|📦 Отправить груз \(Заказ\))"), start_client_order)
        ],
        states={
            LANG: [CallbackQueryHandler(select_lang, pattern="^lang_")],
            ROLE: [CallbackQueryHandler(role_sel, pattern="^role_")],
            C_REGION: [CallbackQueryHandler(c_region, pattern="^reg_")],
            C_DISTRICT: [CallbackQueryHandler(c_district, pattern="^(dist_|back_region)")],
            C_SUB_DISTRICT: [CallbackQueryHandler(c_sub_district, pattern="^(csub_|back_dist)")],
            C_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_target)],
            C_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_desc)],
            C_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_time)],
            C_PHONE: [MessageHandler((filters.TEXT | filters.CONTACT) & ~filters.COMMAND, c_phone)],
            C_LOCATION: [MessageHandler((filters.TEXT | filters.LOCATION) & ~filters.COMMAND, c_location)],
            C_CONFIRM: [CallbackQueryHandler(c_confirm, pattern="^(c_confirm|c_cancel)")],
            
            W_REGION: [CallbackQueryHandler(w_region, pattern="^wreg_")],
            W_DISTRICT: [CallbackQueryHandler(w_district, pattern="^(wdist_|wback_region)")],
            W_SUB_DISTRICT: [CallbackQueryHandler(w_sub_district, pattern="^(wsub_|wback_dist)")],
            W_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, w_name)],
            W_CAR_MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, w_car_model)],
            W_CAR_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, w_car_color)],
            W_CAR_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, w_car_number)],
            W_PHONE: [MessageHandler((filters.TEXT | filters.CONTACT) & ~filters.COMMAND, w_phone)],
            W_CONFIRM: [CallbackQueryHandler(w_confirm, pattern="^(w_confirm|w_cancel)")]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.Regex("^(🔍 Buyurtmalarni qidirish|🔍 Поиск заказов)"), search_orders_cmd))
    application.add_handler(MessageHandler(filters.Regex("^(💳 Shaxsiy Kabinet|💳 Личный кабинет)"), shaxsiy_kabinet))
    application.add_handler(MessageHandler(filters.Regex("^(ℹ️ Yordam / Ma'lumot|ℹ️ Помощь / Информация)"), yordam_info))
    
    application.add_handler(CallbackQueryHandler(refresh_search_callback, pattern="^refresh_search$"))
    application.add_handler(CallbackQueryHandler(accept_order, pattern="^accept_"))
    application.add_handler(CallbackQueryHandler(client_cancel_order, pattern="^client_cancel_"))
    application.add_handler(CallbackQueryHandler(driver_cancel_order, pattern="^driver_cancel_"))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))

    logger.info("Muzlamaydigan xavfsiz bot tizimi muvaffaqiyatli yoqildi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
