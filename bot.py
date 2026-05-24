import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)

# ===================== SOZLAMALAR =====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8932867764:AAFd-2yHxCqWBcnjQoK3Wy03T2hx3S04iCE")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "692744901"))

# Komissiya jadval (narxga qarab)
COMMISSION_TABLE = [
    (0, 50000, 3000),
    (50001, 100000, 5000),
    (100001, 200000, 10000),
    (200001, 500000, 20000),
    (500001, 99999999, 40000),
]

# Payme/Click (keyinchalik to'ldiring)
PAYME_MERCHANT_ID = os.environ.get("PAYME_MERCHANT_ID", "YOUR_PAYME_MERCHANT_ID")
CLICK_MERCHANT_ID = os.environ.get("CLICK_MERCHANT_ID", "YOUR_CLICK_MERCHANT_ID")
CLICK_SERVICE_ID = os.environ.get("CLICK_SERVICE_ID", "YOUR_CLICK_SERVICE_ID")

# ===================== HUDUDLAR =====================
REGIONS = {
    "Toshkent shahri": ["Yunusobod", "Chilonzor", "Mirzo Ulugbek", "Shayxontohur", "Uchtepa", "Yakkasaroy", "Olmazar"],
    "Toshkent viloyati": ["Angren", "Bekobod", "Bostonliq", "Chinoz", "Qibray", "Ohangaron", "Parkent", "Piskent", "Zangiota"],
    "Samarqand": ["Samarqand sh.", "Bulungur", "Ishtixon", "Jomboy", "Kattaqorgon", "Narpay", "Oqdaryo", "Paxtachi", "Payariq"],
    "Buxoro": ["Buxoro sh.", "Gijduvon", "Jondor", "Kogon", "Qorovulbozor", "Olot", "Peshku", "Romitan", "Shofirkon"],
    "Fargona": ["Fargona sh.", "Qoqon", "Margilan", "Beshariq", "Bogdod", "Dangara", "Furqat", "Oltiariq", "Rishton", "Toshloq", "Uchkoprik", "Yozyovon"],
    "Andijon": ["Andijon sh.", "Asaka", "Baliqchi", "Boz", "Buloqboshi", "Hojaobod", "Jalaquduq", "Izboskan", "Qorgontepa", "Marhamat", "Oltinkol", "Paxtaobod", "Shahrixon", "Ulognor"],
    "Namangan": ["Namangan sh.", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq", "Norin", "Pop", "Toraqorgon", "Uychi", "Yangiqorgon"],
    "Qashqadaryo": ["Qarshi sh.", "Chiroqchi", "Dehqonobod", "Guzor", "Kasbi", "Kitob", "Koson", "Mirishkor", "Muborak", "Nishon", "Shahrisabz", "Yakkabog"],
    "Surxondaryo": ["Termiz sh.", "Angor", "Bandixon", "Boysun", "Denov", "Jarqorgon", "Qiziriq", "Qumqorgon", "Muzrabot", "Oltinsoy", "Sariosiyo", "Sherobod", "Shurchi", "Uzun"],
    "Xorazm": ["Urganch sh.", "Bogot", "Gurlan", "Xiva", "Xonqa", "Qoshkopir", "Shovot", "Tuproqqala", "Yangiariq", "Yangibozor"],
    "Navoiy": ["Navoiy sh.", "Karmana", "Konimex", "Navbahor", "Nurota", "Qiziltepa", "Tomdi", "Uchquduq", "Xatirchi"],
    "Jizzax": ["Jizzax sh.", "Arnasoy", "Baxmal", "Dostlik", "Forish", "Gallaorol", "Mirzachol", "Paxtakor", "Sharof Rashidov", "Yangiobod", "Zarbdor", "Zafarobod", "Zomin"],
    "Sirdaryo": ["Guliston sh.", "Boyovut", "Mirzaobod", "Oqoltin", "Sardoba", "Sayxunobod", "Shirin", "Xavast"],
    "Qoraqalpogiston": ["Nukus sh.", "Amudaryo", "Beruniy", "Chimboy", "Ellikkala", "Kegeyli", "Moynoq", "Qanlikol", "Qongrot", "Qoraozak", "Shumanay", "Taxtakopir", "Tortkol", "Xojayli"],
}

# ===================== STATES =====================
(
    LANG, ROLE,
    C_REGION, C_DISTRICT, C_DESC, C_PRICE, C_PHONE, C_PAYMENT, C_CONFIRM,
    W_REGION, W_DISTRICT, W_NAME, W_PHONE, W_CONFIRM,
) = range(14)

# ===================== MALUMOTLAR =====================
users = {}
workers = {}
orders = {}
order_counter = [1]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== YORDAMCHI FUNKSIYALAR =====================

def get_commission(price):
    for mn, mx, comm in COMMISSION_TABLE:
        if mn <= price <= mx:
            return comm
    return 0

def make_payme_link(order_id, amount):
    import base64
    params = f"m={PAYME_MERCHANT_ID};ac.order_id={order_id};a={amount * 100}"
    encoded = base64.b64encode(params.encode()).decode()
    return f"https://checkout.paycom.uz/{encoded}"

def make_click_link(order_id, amount):
    return (
        f"https://my.click.uz/services/pay?"
        f"service_id={CLICK_SERVICE_ID}"
        f"&merchant_id={CLICK_MERCHANT_ID}"
        f"&amount={amount}"
        f"&transaction_param={order_id}"
    )

def regions_keyboard():
    kb = []
    row = []
    for region in REGIONS.keys():
        row.append(InlineKeyboardButton(region, callback_data=f"reg_{region}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    return InlineKeyboardMarkup(kb)

def districts_keyboard(region):
    districts = REGIONS.get(region, [])
    kb = []
    row = []
    for d in districts:
        row.append(InlineKeyboardButton(d, callback_data=f"dist_{d}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton("Orqaga", callback_data="back_region")])
    return InlineKeyboardMarkup(kb)

# ===================== START =====================

async def start(update: Update, context):
    kb = [
        [InlineKeyboardButton("Uzbek", callback_data="lang_uz"),
         InlineKeyboardButton("Русский", callback_data="lang_ru")]
    ]
    await update.message.reply_text(
        "Tilni tanlang / Выберите язык:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return LANG

async def select_lang(update: Update, context):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    uid = query.from_user.id
    users[uid] = {"lang": lang}
    context.user_data["lang"] = lang
    kb = [
        [InlineKeyboardButton("Mijoz", callback_data="role_client")],
        [InlineKeyboardButton("Labochi", callback_data="role_worker")],
    ]
    text = "Rolingizni tanlang:" if lang == "uz" else "Выберите роль:"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    return ROLE

async def role_sel(update: Update, context):
    query = update.callback_query
    await query.answer()
    role = query.data.split("_")[1]
    context.user_data["role"] = role
    if role == "client":
        await query.edit_message_text("Hududingizni tanlang:", reply_markup=regions_keyboard())
        return C_REGION
    else:
        uid = query.from_user.id
        if uid in workers and workers[uid].get("approved"):
            await query.edit_message_text("Siz allaqachon tasdiqlangansiz!\n/orders - arizalarni koring")
            return ConversationHandler.END
        await query.edit_message_text("Ishlaydigan hududingizni tanlang:", reply_markup=regions_keyboard())
        return W_REGION

# ===================== MIJOZ FLOW =====================

async def c_region(update: Update, context):
    query = update.callback_query
    await query.answer()
    region = query.data.replace("reg_", "")
    context.user_data["c_region"] = region
    await query.edit_message_text(
        f"{region}\nTumanni tanlang:",
        reply_markup=districts_keyboard(region)
    )
    return C_DISTRICT

async def c_district(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "back_region":
        await query.edit_message_text("Hududingizni tanlang:", reply_markup=regions_keyboard())
        return C_REGION
    district = query.data.replace("dist_", "")
    context.user_data["c_district"] = district
    await query.edit_message_text(
        f"{context.user_data['c_region']}, {district}\n\n"
        f"Xizmat haqida batafsil yozing:\n"
        f"(Masalan: Mashina moyini almashtirishim kerak)"
    )
    return C_DESC

async def c_desc(update: Update, context):
    context.user_data["c_desc"] = update.message.text
    await update.message.reply_text("Taxminiy narxni kiriting (somda):\nMasalan: 50000")
    return C_PRICE

async def c_price(update: Update, context):
    try:
        price = int(update.message.text.replace(" ", "").replace(",", ""))
        if price < 10000:
            await update.message.reply_text("Minimal narx 10,000 som")
            return C_PRICE
        context.user_data["c_price"] = price
        comm = get_commission(price)
        context.user_data["c_commission"] = comm
        await update.message.reply_text(
            f"Narx: {price:,} som\n"
            f"Xizmat komissiyasi: {comm:,} som\n\n"
            f"Telefon raqamingizni kiriting:\nMasalan: +998901234567"
        )
        return C_PHONE
    except ValueError:
        await update.message.reply_text("Faqat raqam kiriting. Masalan: 50000")
        return C_PRICE

async def c_phone(update: Update, context):
    context.user_data["c_phone"] = update.message.text
    data = context.user_data
    price = data["c_price"]
    comm = data["c_commission"]
    text = (
        f"ARIZA MALUMOTLARI:\n\n"
        f"Hudud: {data['c_region']}, {data['c_district']}\n"
        f"Xizmat: {data['c_desc']}\n"
        f"Narx: {price:,} som\n"
        f"Komissiya: {comm:,} som\n"
        f"Telefon: {data['c_phone']}\n\n"
        f"Tasdiqlaysizmi?"
    )
    kb = [
        [InlineKeyboardButton("Tasdiqlash", callback_data="c_confirm")],
        [InlineKeyboardButton("Bekor qilish", callback_data="c_cancel")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    return C_CONFIRM

async def c_confirm(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "c_cancel":
        await query.edit_message_text("Bekor qilindi. /start dan qaytadan boshlang.")
        return ConversationHandler.END
    uid = query.from_user.id
    data = context.user_data
    oid = order_counter[0]
    order_counter[0] += 1
    orders[oid] = {
        "id": oid,
        "client_id": uid,
        "region": data["c_region"],
        "district": data["c_district"],
        "desc": data["c_desc"],
        "price": data["c_price"],
        "commission": data["c_commission"],
        "phone": data["c_phone"],
        "status": "pending",
        "worker_id": None,
    }
    price = data["c_price"]
    payme_link = make_payme_link(oid, price)
    click_link = make_click_link(oid, price)
    kb = [
        [InlineKeyboardButton("Payme orqali tolash", url=payme_link)],
        [InlineKeyboardButton("Click orqali tolash", url=click_link)],
        [InlineKeyboardButton("Tolov qildim", callback_data=f"paid_{oid}")],
    ]
    await query.edit_message_text(
        f"Ariza #{oid} yaratildi!\n\n"
        f"Tolov summasi: {price:,} som\n\n"
        f"Tolov usulini tanlang:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return ConversationHandler.END

async def payment_done(update: Update, context):
    query = update.callback_query
    await query.answer()
    oid = int(query.data.split("_")[1])
    if oid not in orders:
        await query.edit_message_text("Ariza topilmadi")
        return
    orders[oid]["status"] = "paid"
    region = orders[oid]["region"]
    district = orders[oid]["district"]
    sent = 0
    for wid, w in workers.items():
        if w.get("approved") and w.get("region") == region and w.get("district") == district:
            kb = [[InlineKeyboardButton("Qabul qilish", callback_data=f"accept_{oid}")]]
            try:
                await context.bot.send_message(
                    wid,
                    f"YANGI ARIZA #{oid}\n\n"
                    f"{region}, {district}\n"
                    f"{orders[oid]['desc']}\n"
                    f"{orders[oid]['price']:,} som\n"
                    f"{orders[oid]['phone']}",
                    reply_markup=InlineKeyboardMarkup(kb)
                )
                sent += 1
            except Exception:
                pass
    await query.edit_message_text(
        f"Tolov qabul qilindi!\n"
        f"{sent} ta labochiga yuborildi.\n\n"
        f"Tez orada siz bilan boglanishadi."
    )

# ===================== LABOCHI FLOW =====================

async def w_region(update: Update, context):
    query = update.callback_query
    await query.answer()
    region = query.data.replace("reg_", "")
    context.user_data["w_region"] = region
    await query.edit_message_text(
        f"{region}\nTumanni tanlang:",
        reply_markup=districts_keyboard(region)
    )
    return W_DISTRICT

async def w_district(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "back_region":
        await query.edit_message_text("Hududingizni tanlang:", reply_markup=regions_keyboard())
        return W_REGION
    district = query.data.replace("dist_", "")
    context.user_data["w_district"] = district
    await query.edit_message_text(f"{context.user_data['w_region']}, {district}\n\nIsmingizni kiriting:")
    return W_NAME

async def w_name(update: Update, context):
    context.user_data["w_name"] = update.message.text
    await update.message.reply_text("Telefon raqamingizni kiriting:")
    return W_PHONE

async def w_phone(update: Update, context):
    context.user_data["w_phone"] = update.message.text
    data = context.user_data
    text = (
        f"ROYXATDAN OTISH:\n\n"
        f"Ism: {data['w_name']}\n"
        f"Telefon: {data['w_phone']}\n"
        f"Hudud: {data['w_region']}, {data['w_district']}\n\n"
        f"Tasdiqlaysizmi?"
    )
    kb = [
        [InlineKeyboardButton("Tasdiqlash", callback_data="w_confirm")],
        [InlineKeyboardButton("Bekor qilish", callback_data="w_cancel")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    return W_CONFIRM

async def w_confirm(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "w_cancel":
        await query.edit_message_text("Bekor qilindi.")
        return ConversationHandler.END
    uid = query.from_user.id
    data = context.user_data
    workers[uid] = {
        "name": data["w_name"],
        "phone": data["w_phone"],
        "region": data["w_region"],
        "district": data["w_district"],
        "approved": False,
        "balance": 0,
    }
    kb = [
        [InlineKeyboardButton("Tasdiqlash", callback_data=f"approve_{uid}")],
        [InlineKeyboardButton("Rad etish", callback_data=f"reject_{uid}")],
    ]
    await context.bot.send_message(
        ADMIN_ID,
        f"YANGI LABOCHI:\n\n"
        f"Ism: {data['w_name']}\n"
        f"Telefon: {data['w_phone']}\n"
        f"Hudud: {data['w_region']}, {data['w_district']}\n"
        f"Telegram ID: {uid}",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    await query.edit_message_text(
        "Arizangiz yuborildi!\n"
        "Admin tekshirib tasdiqlagach xabar beramiz."
    )
    return ConversationHandler.END

# ===================== ADMIN =====================

async def approve_driver(update: Update, context):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 1)
    action = parts[0]
    uid = int(parts[1])
    if uid not in workers:
        await query.edit_message_text("Labochi topilmadi")
        return
    if action == "approve":
        workers[uid]["approved"] = True
        await query.edit_message_text(f"{workers[uid]['name']} tasdiqlandi!")
        await context.bot.send_message(
            uid,
            "Tabriklaymiz! Hisobingiz tasdiqlandi.\n"
            "/orders - mavjud arizalarni koring"
        )
    else:
        del workers[uid]
        await query.edit_message_text("Labochi rad etildi")
        await context.bot.send_message(uid, "Afsuski, arizangiz rad etildi.")

async def accept_order(update: Update, context):
    query = update.callback_query
    await query.answer()
    oid = int(query.data.split("_")[1])
    uid = query.from_user.id
    if oid not in orders:
        await query.edit_message_text("Ariza topilmadi")
        return
    if orders[oid]["status"] != "paid":
        await query.edit_message_text("Bu ariza hali tolanmagan yoki qabul qilingan")
        return
    if uid not in workers or not workers[uid].get("approved"):
        await query.edit_message_text("Siz tasdiqlangan labochi emassiz")
        return
    orders[oid]["status"] = "accepted"
    orders[oid]["worker_id"] = uid
    comm = orders[oid]["commission"]
    workers[uid]["balance"] = workers[uid].get("balance", 0) - comm
    await query.edit_message_text(
        f"Ariza #{oid} qabul qilindi!\n"
        f"Mijoz telefoni: {orders[oid]['phone']}\n"
        f"Komissiya: {comm:,} som"
    )
    w = workers[uid]
    await context.bot.send_message(
        orders[oid]["client_id"],
        f"Ariza #{oid} qabul qilindi!\n\n"
        f"Labochi: {w['name']}\n"
        f"Telefon: {w['phone']}"
    )

async def orders_cmd(update: Update, context):
    uid = update.effective_user.id
    if uid not in workers or not workers[uid].get("approved"):
        await update.message.reply_text("Hisobingiz tasdiqlanmagan.")
        return
    w = workers[uid]
    pending = [
        o for o in orders.values()
        if o["status"] == "paid"
        and o["region"] == w["region"]
        and o["district"] == w["district"]
    ]
    if not pending:
        await update.message.reply_text("Hozircha sizning hududingizda ariza yoq.")
        return
    for o in pending:
        kb = [[InlineKeyboardButton("Qabul qilish", callback_data=f"accept_{o['id']}")]]
        await update.message.reply_text(
            f"Ariza #{o['id']}\n"
            f"{o['region']}, {o['district']}\n"
            f"{o['desc']}\n"
            f"{o['price']:,} som\n"
            f"{o['phone']}",
            reply_markup=InlineKeyboardMarkup(kb)
        )

async def stats_cmd(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    total_orders = len(orders)
    total_paid = sum(1 for o in orders.values() if o["status"] in ("paid", "accepted", "done"))
    total_commission = sum(o["commission"] for o in orders.values() if o["status"] in ("accepted", "done"))
    total_workers = len(workers)
    approved_workers = sum(1 for w in workers.values() if w.get("approved"))
    await update.message.reply_text(
        f"STATISTIKA:\n\n"
        f"Jami arizalar: {total_orders}\n"
        f"Tolangan: {total_paid}\n"
        f"Jami komissiya: {total_commission:,} som\n"
        f"Jami labochlar: {total_workers}\n"
        f"Tasdiqlangan: {approved_workers}"
    )

# ===================== MAIN =====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [CallbackQueryHandler(select_lang, pattern="^lang_")],
            ROLE: [CallbackQueryHandler(role_sel, pattern="^role_")],
            C_REGION: [CallbackQueryHandler(c_region, pattern="^reg_")],
            C_DISTRICT: [CallbackQueryHandler(c_district, pattern="^(dist_|back_region)")],
            C_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_desc)],
            C_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_price)],
            C_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_phone)],
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
    app.add_handler(CallbackQueryHandler(approve_driver, pattern="^(approve|reject)_"))
    app.add_handler(CallbackQueryHandler(payment_done, pattern="^paid_"))
    app.add_handler(CommandHandler("orders", orders_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    print("Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
