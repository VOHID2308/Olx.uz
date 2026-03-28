"""
OLX.UZ Telegram Bot
Foydalanuvchilar Telegram orqali ro'yxatdan o'tadi va Mini App ochiladi.

Ishga tushirish:
    python telegram_bot/bot.py
"""

import logging
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes,
)
from decouple import config

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN   = config('TELEGRAM_BOT_TOKEN')
BACKEND_URL = config('BACKEND_URL', default='http://127.0.0.1:8000')
MINIAPP_URL = config('MINIAPP_URL', default="https://gentlemanly-unrentable-burma.ngrok-free.dev")
API_BASE    = f"{BACKEND_URL}/api/v1"


async def telegram_login(user_data: dict) -> dict | None:
    """Backendga login so'rovi — token va user qaytaradi."""
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start — login + Mini App tugmasi."""
    tg_user = update.effective_user
    msg = await update.message.reply_text("⏳ Tizimga kirilmoqda...")

    result = await telegram_login({
        "id": tg_user.id, "username": tg_user.username,
        "first_name": tg_user.first_name, "last_name": tg_user.last_name or "",
    })

    if not result:
        await msg.edit_text("❌ Server bilan bog'lanishda xato. Keyinroq urinib ko'ring.")
        return

    context.user_data["access_token"]  = result["access"]
    context.user_data["refresh_token"] = result["refresh"]
    context.user_data["user"]          = result["user"]

    role      = result["user"].get("role", "customer")
    created   = result.get("created", False)
    greeting  = "🎉 Xush kelibsiz!" if created else "👋 Qaytib keldingiz!"
    role_text = "🛍 Xaridor" if role == "customer" else "🏪 Sotuvchi"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒  OLX.UZ ni ochish", web_app=WebAppInfo(url=MINIAPP_URL))],
        [
            InlineKeyboardButton("📦 Buyurtmalar", callback_data="orders"),
            InlineKeyboardButton("👤 Profil",      callback_data="profile"),
        ],
        [InlineKeyboardButton("🔍 Mahsulot qidirish", callback_data="search_prompt")],
    ])

    await msg.edit_text(
        f"{greeting}\n\n"
        f"👤 *{tg_user.first_name}*\n"
        f"🔖 Rol: {role_text}\n\n"
        f"Platformaga kirish uchun tugmani bosing 👇",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 *OLX.UZ Bot*\n\n"
        "/start — Platformaga kirish\n"
        "/search iphone — Mahsulot qidirish\n"
        "/help — Yordam\n",
        parse_mode="Markdown"
    )


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await update.message.reply_text("Foydalanish: `/search iphone`", parse_mode="Markdown")
        return

    query = " ".join(args)
    token = context.user_data.get("access_token")
    await update.message.reply_text(f"🔍 *{query}* qidirilmoqda...", parse_mode="Markdown")

    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE}/products/?search={query}", headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                data = await resp.json()
        products = data.get("results", data) if isinstance(data, dict) else data

        if not products:
            await update.message.reply_text(f"😔 *{query}* bo'yicha hech narsa topilmadi.")
            return

        text = f"🔍 *\"{query}\"* — {len(products)} ta natija:\n\n"
        for p in products[:5]:
            price = f"{int(float(p.get('price', 0))):,} so'm"
            text += f"• *{p['title']}*\n  💰 {price} | 📍 {p.get('region', '')}\n\n"

        await update.message.reply_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🛒 Platformada ko'rish", web_app=WebAppInfo(url=MINIAPP_URL))
            ]])
        )
    except Exception:
        await update.message.reply_text("❌ Qidirishda xato yuz berdi.")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    token = context.user_data.get("access_token")

    open_btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("🛒 Platformani ochish", web_app=WebAppInfo(url=MINIAPP_URL))
    ]])

    if query.data == "profile":
        if not token:
            await query.edit_message_text("Avval /start bilan kiring.")
            return
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_BASE}/users/me/",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    profile = await resp.json()
            role_text = "🏪 Sotuvchi" if profile.get("role") == "seller" else "🛍 Xaridor"
            await query.edit_message_text(
                f"👤 *Profil*\n\n"
                f"Ism: {profile.get('first_name','')} {profile.get('last_name','')}\n"
                f"Username: @{profile.get('username','')}\n"
                f"Telefon: {profile.get('phone_number') or 'kiritilmagan'}\n"
                f"Rol: {role_text}",
                parse_mode="Markdown", reply_markup=open_btn
            )
        except Exception:
            await query.edit_message_text("❌ Profil ma'lumotlarini olishda xato.")

    elif query.data == "orders":
        if not token:
            await query.edit_message_text("Avval /start bilan kiring.")
            return
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_BASE}/orders/",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    data_resp = await resp.json()
            orders = data_resp.get("results", data_resp) if isinstance(data_resp, dict) else data_resp
            if not orders:
                text = "📦 Hozircha buyurtma yo'q."
            else:
                STATUS = {'kutilyapti':'⏳','kelishilgan':'🤝','sotib olingan':'✅','bekor qilingan':'❌'}
                text = "📦 *Buyurtmalar:*\n\n"
                for o in orders[:5]:
                    icon  = STATUS.get(o.get("status",""), "📦")
                    price = f"{int(float(o.get('final_price', 0))):,} so'm"
                    title = o.get('product', {}).get('title', 'Mahsulot') if isinstance(o.get('product'), dict) else 'Mahsulot'
                    text += f"{icon} {title}\n  💰 {price}\n\n"
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=open_btn)
        except Exception:
            await query.edit_message_text("❌ Buyurtmalarni olishda xato.")

    elif query.data == "search_prompt":
        context.user_data["waiting_search"] = True
        await query.edit_message_text(
            "🔍 Qidirmoqchi bo'lgan mahsulotni yozing:\n\n"
            "_Masalan: iPhone, velosiped, kitob..._",
            parse_mode="Markdown"
        )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text  = update.message.text
    token = context.user_data.get("access_token")

    if context.user_data.get("waiting_search"):
        context.user_data["waiting_search"] = False
        context.args = text.split()
        await search_command(update, context)
        return

    if not token:
        await update.message.reply_text("Boshlash uchun /start yuboring.")
    else:
        await update.message.reply_text(
            "Platforma uchun quyidagi tugmani bosing:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🛒 OLX.UZ ni ochish", web_app=WebAppInfo(url=MINIAPP_URL))
            ]])
        )


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("help",   help_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    logger.info("OLX.UZ Bot ishga tushdi (Mini App rejimida)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()