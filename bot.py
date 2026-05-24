import logging
import os
import json
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Update,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "8932867764:AAFd-2yHxCqWBcnjQoK3Wy03T2hx3S04iCE"
ADMIN_ID = 692744901

FIXED_COMMISSION = 4000 

REGIONS = {
    "Toshkent shahri": ["Yunusobod", "Chilonzor", "Mirzo Ulugbek", "Shayxontohur", "Uchtepa", "Yakkasaroy", "Olmazor"],
    "Toshkent viloyati": ["Angren", "Bekobod", "Bostonliq", "Chinoz", "Qibray", "Ohangaron", "Parkent"],
    "Qoraqalpogiston": ["Nukus sh.", "Amudaryo", "Beruniy", "Chimboy", "Ellikkala", "Xojayli"]
}

# STATES
(
    LANG, ROLE,
    C_REGION, C_DISTRICT, C_TARGET, C_DESC, C_TIME, C_PHONE, C_LOCATION, C_CONFIRM,
    W_REGION, W_DISTRICT, W_NAME, W_PHONE, W_CONFIRM
) = range(15)

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
        except Exception:
            return {}, {}, [1]
    return {}, {}, [1]

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"workers": workers, "orders": orders, "order_counter": order_counter}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Bazaga yozishda xato: {e}")

workers, orders, order_counter = load_data()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===================== YORDAMCHI FUNKSIYALAR =====================

def regions_keyboard():
    kb = []
    row = []
    for region in REGIONS.keys():
        row.append(InlineKeyboardButton(region, callback_data=f"reg_{region}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    return InlineKeyboardMarkup(kb)

def districts_keyboard(region_name):
    districts = REGIONS.get(region_name, [])
    kb = []
    row = []
    for d in districts:
        row.append(InlineKeyboardButton(d, callback_data=f"dist_{d}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_region")])
    return InlineKeyboardMarkup(kb)

# ===================== START & ROL TANLASH =====================

async def start(update: Update, context):
    if context.user_data:
        context.user_data.clear()
        
    kb = [[InlineKeyboardButton("O'zbekcha 🇺🇿", callback_data="lang_uz")]]
    await update.message.reply_text("Tilni tanlang / Выберите язык:", reply_markup=InlineKeyboardMarkup(kb))
    return LANG

async def select_lang(update: Update, context):
    query = update.callback_query
    await query.answer()
    kb = [
        [InlineKeyboardButton("Mijoz (Yuk yuborish) 📦", callback_data="role_client")],
        [InlineKeyboardButton("Labochi (Haydovchi) 🛺", callback_data="role_worker")],
    ]
    try:
        await query.edit_message_text("Rolingizni tanlang:", reply_markup=InlineKeyboardMarkup(kb))
    except Exception:
        await query.message.reply_text("Rolingizni tanlang:", reply_markup=InlineKeyboardMarkup(kb))
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
            await query.edit_message_text("Siz faol haydovchisiz! Profilingizni ko'rish uchun /profile buyrug'ini bosing.")
            return ConversationHandler.END
        await query.edit_message_text("Siz qaysi hududda yuk tashiysiz? Viloyatni tanlang:", reply_markup=regions_keyboard())
        return W_REGION

# ===================== MIJOZ FLOW =====================

async def c_region(update: Update, context):
    query = update.callback_query
    await query.answer()
    region = query.data.replace("reg_", "")
    context.user_data["c_region"] = region
    await query.edit_message_text(f"Tanlangan viloyat: {region}\nTumanni tanlang:", reply_markup=districts_keyboard(region))
    return C_DISTRICT

async def c_district(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "back_region":
        await query.edit_message_text("Yuk qayerdan olinadi? Viloyatni tanlang:", reply_markup=regions_keyboard())
        return C_REGION
    district = query.data.replace("dist_", "")
    context.user_data["c_district"] = district
    await query.edit_message_text("🏁 Yuk qayerga olib boriladi?\n(Boradigan shahar, tuman yoki aniq manzilni yozib yuboring):")
    return C_TARGET

async def c_target(update: Update, context):
    context.user_data["c_target"] = update.message.text if update.message.text else "Noma'lum manzil"
    
    kb = [
        [KeyboardButton("📺 Texnikalar"), KeyboardButton("🦮 Hayvonlar")],
        [KeyboardButton("🧱 Qurilish mollari"), KeyboardButton("📦 Boshqa narsalar")]
    ]
    await update.message.reply_text(
        "📦 Yukingiz qaysi turga kiradi?\nVariantlardan birini tanlang yoki o'zingiz yozib yuboring:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
    )
    return C_DESC

async def c_desc(update: Update, context):
    context.user_data["c_desc"] = update.message.text if update.message.text else "Boshqa narsalar"
    
    kb = [
        [KeyboardButton("⚡️ Hozir / Tezda")],
        [KeyboardButton("📅 Bugun kechroq"), KeyboardButton("📞 Kelishiladi")]
    ]
    await update.message.reply_text(
        "🕒 Yuk qachon olib ketilishi kerak?\nTugmalardan birini tanlang yoki vaqtini yozing:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
    )
    return C_TIME

async def c_time(update: Update, context):
    context.user_data["c_time"] = update.message.text if update.message.text else "Kelishiladi"
    await update.message.reply_text(
        "📞 Telefon raqamingizni kiriting (Haydovchi bog'lanishi uchun):",
        reply_markup=ReplyKeyboardRemove()
    )
    return C_PHONE

async def c_phone(update: Update, context):
    context.user_data["c_phone"] = update.message.text if update.message.text else "Kiritilmadi"
    kb = [[KeyboardButton("📍 Joylashuvni yuborish", request_location=True)]]
    await update.message.reply_text(
        "Yuk turgan joy lokatsiyasini yuboring (yoki matn ko'rinishida yozing):",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
    )
    return C_LOCATION

async def c_location(update: Update, context):
    if update.message.location:
        lat, lon = update.message.location.latitude, update.message.location.longitude
        context.user_data["c_location_text"] = f"https://maps.google.com/?q={lat},{lon}"
    elif update.message.text:
        context.user_data["c_location_text"] = update.message.text
    else:
        await update.message.reply_text("Iltimos, faqat joylashuv tugmasini bosing yoki matn ko'rinishida manzilni yozing:")
        return C_LOCATION

    data = context.user_data
    text = (
        f"📋 <b>ARIZANGIZ TAYYOR:</b>\n\n"
        f"📍 Qayerdan: {data.get('c_region', 'Noma\'lum')}, {data.get('c_district', 'Noma\'lum')}\n"
        f"🏁 Qayerga: {data.get('c_target', 'Noma\'lum')}\n"
        f"📦 Yuk turi: {data.get('c_desc', 'Noma\'lum')}\n"
        f"🕒 Olib ketish vaqti: {data.get('c_time', 'Noma\'lum')}\n"
        f"📞 Telefon: {data.get('c_phone', 'Noma\'lum')}\n"
        f"🗺 Lokatsiya: {data.get('c_location_text', 'Noma\'lum')}\n\n"
        f"Arizani tasdiqlaysizmi?"
    )
    kb = [
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data="c_confirm")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="c_cancel")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    return C_CONFIRM

async def c_confirm(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "c_cancel":
        await query.edit_message_text("Ariza bekor qilindi. Qaytadan boshlash: /start")
        context.user_data.clear()
        return ConversationHandler.END

    uid = query.from_user.id
    data = context.user_data
    oid = order_counter[0]
    order_counter[0] += 1

    orders[oid] = {
        "id": oid, "client_id": uid, "region": data.get("c_region"), "district": data.get("c_district"),
        "desc": data.get("c_desc"), "target": data.get("c_target"), "time": data.get("c_time"), 
        "phone": data.get("c_phone"), "location_text": data.get("c_location_text"), 
        "status": "pending", "worker_id": None, "client_msg_id": None
    }
    save_data()

    waiting_text = (
        f"⏳ <b>Ariza #{oid} Labochilarga yuborildi!</b>\n\n"
        f"📦 Yuk turi: {data.get('c_desc', 'Noma\'lum')}\n"
        f"🏁 Borish joyi: {data.get('c_target', 'Noma\'lum')}\n"
        f"🕒 Vaqti: {data.get('c_time', 'Noma\'lum')}\n\n"
        f"Haydovchilar arizangizni ko'rib chiqishmoqda. Iltimos kuting...\n"
    )
    sent_msg = await query.edit_message_text(waiting_text, parse_mode="HTML")
    orders[oid]["client_msg_id"] = sent_msg.message_id 
    save_data()

    for wid, w in workers.items():
        if w.get("approved") and data.get("c_region") == w.get("region") and data.get("c_district") == w.get("district"):
            if w.get("balance", 0) >= FIXED_COMMISSION:
                kb = [[InlineKeyboardButton(f"🛺 Buyurtmani olish ({FIXED_COMMISSION:,} so'm)", callback_data=f"accept_{oid}")]]
                try:
                    await context.bot.send_message(
                        wid,
                        f"🔔 <b>YANGI BUYURTMA #{oid}!</b>\n\n"
                        f"📍 Qayerdan: {data.get('c_region')}, {data.get('c_district')}\n"
                        f"🏁 Qayerga: {data.get('c_target')}\n"
                        f"📦 Yuk turi: {data.get('c_desc')}\n"
                        f"🕒 Vaqti: {data.get('c_time')}\n\n"
                        f"⚠️ Diqqat: Buyurtmani olsangiz hisobingizdan {FIXED_COMMISSION:,} so'm yechiladi.",
                        reply_markup=InlineKeyboardMarkup(kb),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
                    
    context.user_data.clear()
    return ConversationHandler.END

# ===================== BUYURTMANI QABUL QILISH =====================

async def accept_order(update: Update, context):
    query = update.callback_query
    await query.answer()
    oid = int(query.data.split("_")[1])
    uid = query.from_user.id

    if oid not in orders:
        await query.edit_message_text("Bu buyurtma tizimda topilmadi.")
        return
    
    order = orders[oid]
    # Race Condition oldini olish (Bir vaqtda ikki kishi bossa)
    if order["status"] != "pending":
        await query.edit_message_text("Kechikdingiz, bu buyurtmani boshqa haydovchi qabul qilib bo'ldi. 😔")
        return

    w = workers.get(uid)
    if not w or not w.get("approved"):
        await query.edit_message_text("Profilingiz hali tasdiqlanmagan.")
        return

    if w.get("balance", 0) < FIXED_COMMISSION:
        await query.message.reply_text(f"❌ Balansingizda mablag' yetarli emas! Sizda: {w['balance']:,} so'm.")
        return

    order["status"] = "accepted"
    order["worker_id"] = uid
    w["balance"] -= FIXED_COMMISSION
    w["total_orders"] += 1
    save_data()

    await query.edit_message_text(
        f"🎉 <b>Buyurtma muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"📞 Mijoz telefoni: {order['phone']}\n"
        f"🗺 Lokatsiya: {order['location_text']}\n"
        f"📦 Yuk turi: {order['desc']}\n"
        f"🕒 Vaqt: {order['time']}\n\n"
        f"📞 Tezda mijozga telefon qilib, kelishib oling!",
        parse_mode="HTML"
    )

    try:
        await context.bot.edit_message_text(
            chat_id=order["client_id"],
            message_id=order["client_msg_id"],
            text=(
                f"✅ <b>Xushxabar! Arizangiz qabul qilindi.</b>\n\n"
                f"🛺 <b>Haydovchi:</b> {w['name']}\n"
                f"📞 <b>Telefon:</b> {w['phone']}\n\n"
                f"Haydovchi hozir sizga telefon qilib, barcha tafsilotlarni kelishib oladi."
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Mijoz xabarini tahrirlashda xato: {e}")

# ===================== HAYDOVCHI PROFILI VA RO'YXATDAN O'TISH =====================

async def profile_cmd(update: Update, context):
    uid = update.effective_user.id
    if uid not in workers:
        await update.message.reply_text("Siz haydovchi emassiz. /start bosing.")
        return
    w = workers[uid]
    text = f"💳 <b>LABOCHI ELEKTRON SCHOTI</b>\n\n🆔 ID: <code>{uid}</code>\n💰 Balans: {w['balance']:,} so'm\n🛺 Zakazlar: {w['total_orders']} ta"
    kb = [[InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_profile")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def refresh_profile(update: Update, context):
    query = update.callback_query
    await query.answer("Yangilandi")
    uid = query.from_user.id
    w = workers[uid]
    text = f"💳 <b>LABOCHI ELEKTRON SCHOTI</b>\n\n🆔 ID: <code>{uid}</code>\n💰 Balans: {w['balance']:,} so'm\n🛺 Zakazlar: {w['total_orders']} ta"
    kb = [[InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_profile")]]
    try:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    except Exception:
        pass

async def w_region(update: Update, context):
    query = update.callback_query
    await query.answer()
    region = query.data.replace("reg_", "")
    context.user_data["w_region"] = region
    await query.edit_message_text(f"Tanlangan viloyat: {region}\nQaysi tumanda faoliyat ko'rsatasiz?", reply_markup=districts_keyboard(region))
    return W_DISTRICT

async def w_district(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "back_region":
        await query.edit_message_text("Siz qaysi hududda yuk tashiysiz? Viloyatni tanlang:", reply_markup=regions_keyboard())
        return W_REGION
    district = query.data.replace("dist_", "")
    context.user_data["w_district"] = district
    await query.edit_message_text("Ism-familiyangizni kiriting:")
    return W_NAME

async def w_name(update: Update, context):
    context.user_data["w_name"] = update.message.text if update.message.text else "Ismsiz haydovchi"
    await update.message.reply_text("Telefon raqamingizni kiriting:")
    return W_PHONE

async def w_phone(update: Update, context):
    context.user_data["w_phone"] = update.message.text if update.message.text else "Kiritilmadi"
    data = context.user_data
    text = f"Haydovchi: {data.get('w_name')}\nTel: {data.get('w_phone')}\nHudud: {data.get('w_region')}, {data.get('w_district')}\n\nYuborilsinmi?"
    kb = [[InlineKeyboardButton("Ha", callback_data="w_confirm")], [InlineKeyboardButton("Yo'q", callback_data="w_cancel")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    return W_CONFIRM

async def w_confirm(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "w_cancel":
        await query.edit_message_text("Bekor qilindi.")
        context.user_data.clear()
        return ConversationHandler.END

    uid = query.from_user.id
    data = context.user_data
    workers[uid] = {
        "name": data.get("w_name"), "phone": data.get("w_phone"), "region": data.get("w_region"),
        "district": data.get("w_district"), "approved": False, "balance": 0, "total_orders": 0
    }
    save_data()

    kb = [[InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{uid}")]]
    await context.bot.send_message(ADMIN_ID, f"🆕 <b>Yangi Labochi ro'yxatdan o'tdi:</b>\nIsmi: {data.get('w_name')}\nID: {uid}\nTel: {data.get('w_phone')}", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    await query.edit_message_text("Arizangiz adminga yuborildi. Yaqin orada faollashadi.")
    context.user_data.clear()
    return ConversationHandler.END

async def approve_driver(update: Update, context):
    query = update.callback_query
    await query.answer()
    uid = int(query.data.split("_")[1])
    if uid in workers:
        workers[uid]["approved"] = True
        workers[uid]["balance"] = 8000
        save_data()
        await query.edit_message_text("Haydovchi tasdiqlandi!")
        try:
            await context.bot.send_message(uid, "🎉 Profilingiz faollashdi! Botdan foydalanishingiz mumkin. Balansni tekshirish: /profile")
        except Exception:
            pass

async def admin_pay_driver(update: Update, context):
    if update.effective_user.id != ADMIN_ID: return
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Format xato! Ishlatish: /pay ID SUMMA")
            return
        driver_id = int(args[0])
        amount = int(args[1])
        if driver_id in workers:
            workers[driver_id]["balance"] += amount
            save_data()
            await update.message.reply_text(f"✅ ID {driver_id} schotiga {amount:,} so'm qo'shildi.")
            try:
                await context.bot.send_message(driver_id, f"💰 Hisobingiz admin tomonidan {amount:,} so'mga to'ldirildi!")
            except Exception: pass
        else:
            await update.message.reply_text("Haydovchi topilmadi.")
    except Exception as e:
        await update.message.reply_text(f"Xato: {e}")

# ===================== MAIN RUNNER =====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [CallbackQueryHandler(select_lang, pattern="^lang_")],
            ROLE: [CallbackQueryHandler(role_sel, pattern="^role_")],
            C_REGION: [CallbackQueryHandler(c_region, pattern="^reg_")],
            C_DISTRICT: [CallbackQueryHandler(c_district, pattern="^(dist_|back_region)")],
            C_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_target)],
            C_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_desc)], 
            C_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_time)], 
            C_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_phone)],
            C_LOCATION: [MessageHandler(filters.LOCATION | filters.TEXT & ~filters.COMMAND, c_location)],
            C_CONFIRM: [CallbackQueryHandler(c_confirm, pattern="^c_(confirm|cancel)")],
            W_REGION: [CallbackQueryHandler(w_region, pattern="^reg_")],
            W_DISTRICT: [CallbackQueryHandler(w_district, pattern="^(dist_|back_region)")],
            W_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, w_name)],
            W_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, w_phone)],
            W_CONFIRM: [CallbackQueryHandler(w_confirm, pattern="^w_(confirm|cancel)")],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(accept_order, pattern="^accept_"))
    app.add_handler(CallbackQueryHandler(approve_driver, pattern="^approve_"))
    app.add_handler(CallbackQueryHandler(refresh_profile, pattern="^refresh_profile$"))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("pay", admin_pay_driver))
    
    print("Bot 100% ideal holatda ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
