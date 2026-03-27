"""
OLX.UZ Telegram Bot
Foydalanuvchilar Telegram orqali ro'yxatdan o'tadi va JWT token oladi.

Ishga tushirish:
    python telegram_bot/bot.py
"""

import logging
import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from decouple import config

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Sozlamalar
BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
BACKEND_URL = config('BACKEND_URL', default='http://127.0.0.1:8000')
API_BASE = f"{BACKEND_URL}/api/v1"


# ──────────────────────────────────────────────
# Backend bilan ishlash
# ──────────────────────────────────────────────

async def telegram_login(user_data: dict) -> dict | None:
    """
    Backend ga telegram-login so'rovi yuborish.
    Muvaffaqiyatli bo'lsa access/refresh token + user ma'lumotlarini qaytaradi.
    """
    payload = {
        "telegram_id": user_data["id"],
        "username":    user_data.get("username") or f"user_{user_data['id']}",
        "first_name":  user_data.get("first_name", ""),
        "last_name":   user_data.get("last_name", ""),
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE}/auth/telegram-login/",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                logger.error("Backend xato: %s", await resp.text())
                return None
    except Exception as e:
        logger.error("Backend ga ulanib bo'lmadi: %s", e)
        return None


async def get_my_profile(access_token: str) -> dict | None:
    """Token orqali foydalanuvchi profilini olish."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE}/users/me/",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception as e:
        logger.error("Profil olishda xato: %s", e)
        return None


async def get_products(access_token: str = None, search: str = "") -> list:
    """Aktiv mahsulotlar ro'yxatini olish."""
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    params = {}
    if search:
        params["search"] = search

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE}/products/",
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("results", data) if isinstance(data, dict) else data
                return []
    except Exception as e:
        logger.error("Mahsulotlar olishda xato: %s", e)
        return []


async def get_categories() -> list:
    """Kategoriyalar ro'yxatini olish."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE}/categories/",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("results", data) if isinstance(data, dict) else data
                return []
    except Exception as e:
        logger.error("Kategoriyalar olishda xato: %s", e)
        return []


# ──────────────────────────────────────────────
# Bot handlerlar
# ──────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start komandasi — foydalanuvchini avtomatik ro'yxatdan o'tkazadi.
    """
    user = update.effective_user
    tg_data = {
        "id":         user.id,
        "username":   user.username,
        "first_name": user.first_name,
        "last_name":  user.last_name or "",
    }

    # Yuklanmoqda xabari
    msg = await update.message.reply_text("⏳ Tizimga kirilmoqda...")

    # Backend ga login so'rovi
    result = await telegram_login(tg_data)

    if not result:
        await msg.edit_text(
            "❌ Server bilan bog'lanishda xato.\n"
            "Iltimos, keyinroq qayta urinib ko'ring."
        )
        return

    # Tokenlarni context ga saqlash (session davomida)
    context.user_data["access_token"]  = result["access"]
    context.user_data["refresh_token"] = result["refresh"]
    context.user_data["user"]          = result["user"]

    role    = result["user"].get("role", "customer")
    created = result.get("created", False)

    greeting = "🎉 Xush kelibsiz!" if created else "👋 Qaytib keldingiz!"
    role_text = "🛍 Xaridor" if role == "customer" else "🏪 Sotuvchi"

    keyboard = main_menu_keyboard(role)

    await msg.edit_text(
        f"{greeting}\n\n"
        f"👤 Ism: *{user.first_name}*\n"
        f"🔖 Rol: {role_text}\n\n"
        f"Nima qilmoqchisiz?",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


def main_menu_keyboard(role: str) -> InlineKeyboardMarkup:
    """Asosiy menyu — rolga qarab."""
    buttons = [
        [InlineKeyboardButton("🔍 Mahsulotlar", callback_data="products")],
        [InlineKeyboardButton("📂 Kategoriyalar", callback_data="categories")],
        [InlineKeyboardButton("❤️ Sevimlilar", callback_data="favorites")],
        [InlineKeyboardButton("📦 Buyurtmalarim", callback_data="orders")],
        [InlineKeyboardButton("👤 Profilim", callback_data="profile")],
    ]
    if role == "seller":
        buttons.insert(2, [InlineKeyboardButton("➕ E'lon qo'shish", callback_data="add_product")])
    else:
        buttons.append([InlineKeyboardButton("🏪 Sotuvchi bo'lish", callback_data="become_seller")])

    return InlineKeyboardMarkup(buttons)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help komandasi."""
    await update.message.reply_text(
        "📖 *OLX.UZ Bot — Yordam*\n\n"
        "/start — Tizimga kirish\n"
        "/menu — Asosiy menyu\n"
        "/profile — Profilim\n"
        "/products — Mahsulotlar\n"
        "/search — Mahsulot qidirish\n"
        "/categories — Kategoriyalar\n"
        "/help — Yordam\n",
        parse_mode="Markdown"
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/menu komandasi."""
    if not context.user_data.get("access_token"):
        await update.message.reply_text("Avval /start bilan kiring.")
        return

    role = context.user_data.get("user", {}).get("role", "customer")
    await update.message.reply_text(
        "📋 Asosiy menyu:",
        reply_markup=main_menu_keyboard(role)
    )


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/profile komandasi."""
    token = context.user_data.get("access_token")
    if not token:
        await update.message.reply_text("Avval /start bilan kiring.")
        return

    profile = await get_my_profile(token)
    if not profile:
        await update.message.reply_text("❌ Profil ma'lumotlarini olishda xato.")
        return

    role_text = "🏪 Sotuvchi" if profile.get("role") == "seller" else "🛍 Xaridor"
    seller_info = ""
    if profile.get("has_seller_profile"):
        seller_info = "\n🏪 Do'kon profili: mavjud"

    await update.message.reply_text(
        f"👤 *Profilim*\n\n"
        f"Ism: {profile.get('first_name', '')} {profile.get('last_name', '')}\n"
        f"Username: @{profile.get('username', '')}\n"
        f"Telefon: {profile.get('phone_number') or 'kiritilmagan'}\n"
        f"Rol: {role_text}"
        f"{seller_info}",
        parse_mode="Markdown"
    )


async def products_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/products komandasi — mahsulotlar ro'yxati."""
    token = context.user_data.get("access_token")
    products = await get_products(token)

    if not products:
        await update.message.reply_text("📭 Hozircha mahsulot yo'q.")
        return

    text = "🛒 *Aktiv mahsulotlar:*\n\n"
    for p in products[:8]:
        price = f"{int(float(p.get('price', 0))):,} so'm"
        text += (
            f"• *{p['title']}*\n"
            f"  💰 {price} | 📍 {p.get('region', '')}\n"
            f"  👁 {p.get('view_count', 0)} ko'rish | "
            f"❤️ {p.get('favorite_count', 0)}\n\n"
        )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Qidirish", callback_data="search_products")],
        [InlineKeyboardButton("🔙 Menyu", callback_data="main_menu")]
    ])

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/categories komandasi."""
    categories = await get_categories()

    if not categories:
        await update.message.reply_text("📭 Kategoriyalar topilmadi.")
        return

    text = "📂 *Kategoriyalar:*\n\n"
    for c in categories[:10]:
        children = c.get("children", [])
        children_text = ""
        if children:
            names = ", ".join(ch["name"] for ch in children[:3])
            children_text = f"\n  └ {names}"
        text += f"• *{c['name']}*{children_text}\n"

    await update.message.reply_text(text, parse_mode="Markdown")


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/search komandasi — qidiruv."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "🔍 Qidirish uchun:\n`/search iphone`\n`/search samsung galaxy`",
            parse_mode="Markdown"
        )
        return

    query = " ".join(args)
    token = context.user_data.get("access_token")

    await update.message.reply_text(f"🔍 *{query}* qidirilmoqda...", parse_mode="Markdown")

    products = await get_products(token, search=query)

    if not products:
        await update.message.reply_text(f"😔 *{query}* bo'yicha hech narsa topilmadi.")
        return

    text = f"🔍 *\"{query}\"* bo'yicha natijalar ({len(products)} ta):\n\n"
    for p in products[:5]:
        price = f"{int(float(p.get('price', 0))):,} so'm"
        text += (
            f"• *{p['title']}*\n"
            f"  💰 {price} | 📍 {p.get('region', '')}\n\n"
        )

    await update.message.reply_text(text, parse_mode="Markdown")


# ──────────────────────────────────────────────
# Callback query handler (tugmalar)
# ──────────────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inline tugmalar uchun handler."""
    query = update.callback_query
    await query.answer()

    data  = query.data
    token = context.user_data.get("access_token")
    role  = context.user_data.get("user", {}).get("role", "customer")

    if data == "main_menu":
        await query.edit_message_text(
            "📋 Asosiy menyu:",
            reply_markup=main_menu_keyboard(role)
        )

    elif data == "profile":
        if not token:
            await query.edit_message_text("Avval /start bilan kiring.")
            return
        profile = await get_my_profile(token)
        if profile:
            role_text = "🏪 Sotuvchi" if profile.get("role") == "seller" else "🛍 Xaridor"
            await query.edit_message_text(
                f"👤 *Profilim*\n\n"
                f"Ism: {profile.get('first_name','')} {profile.get('last_name','')}\n"
                f"Username: @{profile.get('username','')}\n"
                f"Rol: {role_text}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")]
                ])
            )

    elif data == "products":
        products = await get_products(token)
        if not products:
            await query.edit_message_text(
                "📭 Hozircha mahsulot yo'q.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")]
                ])
            )
            return
        text = "🛒 *Mahsulotlar:*\n\n"
        for p in products[:6]:
            price = f"{int(float(p.get('price', 0))):,} so'm"
            text += f"• *{p['title']}*\n  💰 {price} | 📍 {p.get('region','')}\n\n"
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Qidirish", callback_data="search_products")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")]
            ])
        )

    elif data == "categories":
        cats = await get_categories()
        if not cats:
            await query.edit_message_text("📭 Kategoriya topilmadi.")
            return
        text = "📂 *Kategoriyalar:*\n\n"
        for c in cats[:8]:
            text += f"• {c['name']}\n"
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")]
            ])
        )

    elif data == "search_products":
        context.user_data["waiting_for_search"] = True
        await query.edit_message_text(
            "🔍 Qidirmoqchi bo'lgan mahsulot nomini yozing:\n\n"
            "_Masalan: iPhone, Samsung, velosiped..._",
            parse_mode="Markdown"
        )

    elif data == "favorites":
        if not token:
            await query.edit_message_text("Avval /start bilan kiring.")
            return
        await query.edit_message_text(
            "❤️ Sevimlilar ro'yxatini ko'rish uchun:\n"
            f"`GET {API_BASE}/favorites/`\n\n"
            "Token bilan so'rov yuboring.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")]
            ])
        )

    elif data == "orders":
        if not token:
            await query.edit_message_text("Avval /start bilan kiring.")
            return
        await query.edit_message_text(
            "📦 Buyurtmalar ro'yxatini ko'rish uchun:\n"
            f"`GET {API_BASE}/orders/`\n\n"
            "Token bilan so'rov yuboring.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")]
            ])
        )

    elif data == "become_seller":
        if not token:
            await query.edit_message_text("Avval /start bilan kiring.")
            return
        context.user_data["waiting_for_shop_name"] = True
        await query.edit_message_text(
            "🏪 *Sotuvchi bo'lish*\n\n"
            "Do'kon nomingizni yozing:\n"
            "_Masalan: Ali's Electronics_",
            parse_mode="Markdown"
        )

    elif data == "add_product":
        await query.edit_message_text(
            "➕ *Yangi e'lon qo'shish*\n\n"
            "E'lon qo'shish uchun API ga to'g'ridan-to'g'ri murojaat qiling:\n"
            f"`POST {API_BASE}/products/`\n\n"
            "Yoki Swagger orqali:\n"
            f"`{BACKEND_URL}/api/docs/`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")]
            ])
        )


# ──────────────────────────────────────────────
# Matn xabarlar (foydalanuvchi yozganda)
# ──────────────────────────────────────────────

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi matn yozganda — holatga qarab ishlov berish."""
    text  = update.message.text
    token = context.user_data.get("access_token")

    # Qidiruv holati
    if context.user_data.get("waiting_for_search"):
        context.user_data["waiting_for_search"] = False
        await update.message.reply_text(f"🔍 *{text}* qidirilmoqda...", parse_mode="Markdown")
        products = await get_products(token, search=text)
        if not products:
            await update.message.reply_text(f"😔 *{text}* bo'yicha hech narsa topilmadi.")
            return
        result = f"🔍 *\"{text}\"* natijalari ({len(products)} ta):\n\n"
        for p in products[:5]:
            price = f"{int(float(p.get('price', 0))):,} so'm"
            result += f"• *{p['title']}*\n  💰 {price} | 📍 {p.get('region','')}\n\n"
        await update.message.reply_text(result, parse_mode="Markdown")
        return

    # Do'kon nomi holati (sotuvchi bo'lish)
    if context.user_data.get("waiting_for_shop_name"):
        context.user_data["waiting_for_shop_name"] = False
        context.user_data["shop_name_temp"] = text
        context.user_data["waiting_for_region"] = True
        await update.message.reply_text(
            f"✅ Do'kon nomi: *{text}*\n\nViloyatingizni yozing:\n_Masalan: Toshkent_",
            parse_mode="Markdown"
        )
        return

    # Viloyat holati
    if context.user_data.get("waiting_for_region"):
        context.user_data["waiting_for_region"] = False
        shop_name = context.user_data.get("shop_name_temp", "")
        region    = text

        # Backend ga so'rov
        payload = {
            "shop_name": shop_name,
            "region":    region,
            "district":  "Noma'lum",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_BASE}/users/me/upgrade-to-seller/",
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 201:
                        context.user_data["user"]["role"] = "seller"
                        await update.message.reply_text(
                            f"🎉 Tabriklaymiz! Siz endi sotuvchisiz!\n\n"
                            f"🏪 Do'kon: *{shop_name}*\n"
                            f"📍 Viloyat: *{region}*",
                            parse_mode="Markdown",
                            reply_markup=main_menu_keyboard("seller")
                        )
                    else:
                        err = await resp.json()
                        await update.message.reply_text(
                            f"❌ Xato: {err}\n\nQaytadan urinib ko'ring."
                        )
        except Exception as e:
            await update.message.reply_text(f"❌ Server xatosi: {e}")
        return

    # Boshqa matnlar
    if not token:
        await update.message.reply_text(
            "Boshlash uchun /start ni yuboring."
        )
    else:
        role = context.user_data.get("user", {}).get("role", "customer")
        await update.message.reply_text(
            "Menyu orqali davom eting:",
            reply_markup=main_menu_keyboard(role)
        )


# ──────────────────────────────────────────────
# Botni ishga tushirish
# ──────────────────────────────────────────────

def main() -> None:
    """Botni ishga tushirish."""
    app = Application.builder().token(BOT_TOKEN).build()

    # Komandalar
    app.add_handler(CommandHandler("start",      start))
    app.add_handler(CommandHandler("help",       help_command))
    app.add_handler(CommandHandler("menu",       menu_command))
    app.add_handler(CommandHandler("profile",    profile_command))
    app.add_handler(CommandHandler("products",   products_command))
    app.add_handler(CommandHandler("categories", categories_command))
    app.add_handler(CommandHandler("search",     search_command))

    # Tugmalar
    app.add_handler(CallbackQueryHandler(button_handler))

    # Matn xabarlar
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    logger.info("OLX.UZ Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()