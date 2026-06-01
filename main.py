import os
import base64
import json
import requests
import asyncio
import time
import re
import html
import urllib.parse

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

TOKEN = os.getenv("BOT_TOKEN", "BOT_TOKEN_HERE")

CHANNEL_ID = "@PIYUSHxTG"
CHANNEL_LINK = "https://t.me/PIYUSHxTG"
OWNER_ID = 6493515932
OWNER_USERNAME = "PIYUSHxTG"

ADMINS = {OWNER_ID}
RESTRICT_FILE = "restricted_users.json"

LINKS = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity",
    "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/master/v2ray-subscribe.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub2.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub3.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub4.txt",
    "https://raw.githubusercontent.com/MatinGhanbari/V2Ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
]

CACHE_DURATION = 900
config_cache = []
cache_time = 0.0

COUNTRY_KEYWORDS = {
    "IN": {"name": "INDIA", "flag": "🇮🇳", "keywords": ["india", "mumbai", "delhi", "bangalore", "chennai", "kolkata"]},
    "US": {"name": "USA", "flag": "🇺🇸", "keywords": ["usa", "america", "new york", "los angeles", "chicago"]},
    "GB": {"name": "UK", "flag": "🇬🇧", "keywords": ["uk", "london", "britain"]},
    "DE": {"name": "GERMANY", "flag": "🇩🇪", "keywords": ["germany", "frankfurt", "berlin"]},
    "SG": {"name": "SINGAPORE", "flag": "🇸🇬", "keywords": ["singapore"]},
    "JP": {"name": "JAPAN", "flag": "🇯🇵", "keywords": ["japan", "tokyo"]},
    "CA": {"name": "CANADA", "flag": "🇨🇦", "keywords": ["canada", "toronto"]},
    "NL": {"name": "NETHERLANDS", "flag": "🇳🇱", "keywords": ["netherlands", "amsterdam"]},
    "FR": {"name": "FRANCE", "flag": "🇫🇷", "keywords": ["france", "paris"]},
}

PROTOCOLS = {
    "VMESS": "vmess://",
    "VLESS": "vless://",
    "TROJAN": "trojan://",
    "SS": "ss://",
}

TYPE_SYMBOL = {
    "VMESS": "◇",
    "VLESS": "◆",
    "TROJAN": "◈",
    "SS": "◉",
}


def load_restricted():
    try:
        with open(RESTRICT_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_restricted():
    with open(RESTRICT_FILE, "w") as f:
        json.dump(list(RESTRICTED_USERS), f)


RESTRICTED_USERS = load_restricted()


def is_admin(user_id):
    return user_id in ADMINS


def decode_base64(data):
    try:
        data = data.strip().replace("\n", "").replace("\r", "").replace(" ", "")
        data += "=" * (-len(data) % 4)
        return base64.b64decode(data).decode("utf-8", errors="ignore")
    except Exception:
        return data


def detect_country_code(text):
    text = text.lower()
    for code, info in COUNTRY_KEYWORDS.items():
        for kw in info["keywords"]:
            if kw in text:
                return code
    return None


def detect_country_flag(text):
    code = detect_country_code(text)
    return COUNTRY_KEYWORDS[code]["flag"] if code else "🌍"


def extract_name(line, ctype):
    try:
        if "#" in line:
            name = urllib.parse.unquote(line.split("#")[-1])
            name = re.sub(r"[^\w\s@.\-\u0900-\u097F]", "", name).strip()
            if name:
                return name[:40]

        if ctype == "VMESS":
            raw = decode_base64(line.replace("vmess://", "", 1))
            obj = json.loads(raw)
            return str(obj.get("ps", ctype))[:40]

        m = re.search(r"@([^:/?#]+)", line)
        if m:
            return f"{ctype}@{m.group(1)[:30]}"

        return ctype
    except Exception:
        return ctype


def parse_config(line):
    line = line.strip()
    for ctype, prefix in PROTOCOLS.items():
        if line.lower().startswith(prefix):
            name = extract_name(line, ctype)
            full = f"{name} {line}"
            return {
                "type": ctype,
                "symbol": TYPE_SYMBOL.get(ctype, "•"),
                "raw": line,
                "name": name,
                "flag": detect_country_flag(full),
                "code": detect_country_code(full),
            }
    return None


async def fetch_url_text(url):
    def get():
        return requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})

    try:
        r = await asyncio.to_thread(get)
        if r.status_code == 200:
            return r.text.strip()
    except Exception:
        return None
    return None


async def fetch_configs():
    global config_cache, cache_time

    now = time.time()
    if config_cache and now - cache_time < CACHE_DURATION:
        return config_cache

    all_configs = []
    seen = set()

    for link in LINKS:
        content = await fetch_url_text(link)
        if not content:
            continue

        if not any(p in content[:500] for p in PROTOCOLS.values()):
            decoded = decode_base64(content)
            if any(p in decoded[:1000] for p in PROTOCOLS.values()):
                content = decoded

        for line in content.splitlines():
            line = line.strip()
            if not line or line in seen:
                continue

            cfg = parse_config(line)
            if cfg:
                seen.add(line)
                all_configs.append(cfg)

    config_cache = all_configs
    cache_time = now
    return all_configs


async def strong_join_check(user_id, context):
    if user_id in RESTRICTED_USERS:
        return False

    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◇ VMESS", callback_data="TYPE_VMESS")],
        [InlineKeyboardButton("◆ VLESS", callback_data="TYPE_VLESS")],
        [InlineKeyboardButton("◈ TROJAN", callback_data="TYPE_TROJAN")],
        [InlineKeyboardButton("◉ SHADOWSOCKS", callback_data="TYPE_SS")],
        [InlineKeyboardButton("┆ ABOUT", callback_data="ABOUT")],
        [InlineKeyboardButton("┆ ADMIN PANEL", callback_data="ADMIN_PANEL")],
    ])


def country_keyboard():
    rows = []
    row = []
    for code, info in COUNTRY_KEYWORDS.items():
        row.append(InlineKeyboardButton(f"{info['flag']} {code}", callback_data=f"COUNTRY_{code}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    rows.append([InlineKeyboardButton("🌍 ALL", callback_data="COUNTRY_ALL")])
    rows.append([InlineKeyboardButton("┆ BACK", callback_data="BACK_HOME")])
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in RESTRICTED_USERS:
        await update.message.reply_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n┃    ACCESS DENIED   ┃\n┗━━━━━━━━━━━━━━━━━━━━┛\n\nContact: @{OWNER_USERNAME}"
        )
        return

    if not await strong_join_check(user_id, context):
        await update.message.reply_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n┃    JOIN REQUIRED   ┃\n┗━━━━━━━━━━━━━━━━━━━━┛\n\nChannel: {CHANNEL_ID}\nJoin first, then send /start",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("┆ JOIN CHANNEL", url=CHANNEL_LINK)]]),
            disable_web_page_preview=True,
        )
        return

    await update.message.reply_text(
        f"┏━━━━━━━━━━━━━━━━━━━━┓\n┃    V2RAY PRO BOT   ┃\n┗━━━━━━━━━━━━━━━━━━━━┛\n\nStatus: Online\nSources: {len(LINKS)}\n\nSelect Config Type:",
        reply_markup=main_menu_keyboard(),
    )


async def show_admin_panel(query):
    text = "┏━━━━━━━━━━━━━━━━━━━━┓\n┃     ADMIN PANEL    ┃\n┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
    text += f"Owner: @{OWNER_USERNAME}\nBlocked: {len(RESTRICTED_USERS)}\n\n"

    if RESTRICTED_USERS:
        for uid in sorted(RESTRICTED_USERS):
            text += f"• <code>{uid}</code>\n"
    else:
        text += "No restricted users"

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("┆ RESTRICT USER", callback_data="RESTRICT_SHOW")],
            [InlineKeyboardButton("┆ UNRESTRICT USER", callback_data="UNRESTRICT_SHOW")],
            [InlineKeyboardButton("┆ BACK", callback_data="BACK_HOME")],
        ])
    )


async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    action = context.user_data.get("admin_action")
    if not action:
        return

    try:
        target_id = int(update.message.text.strip())

        if action == "restrict":
            RESTRICTED_USERS.add(target_id)
            save_restricted()
            await update.message.reply_text(f"User restricted: <code>{target_id}</code>", parse_mode=ParseMode.HTML)

        elif action == "unrestrict":
            RESTRICTED_USERS.discard(target_id)
            save_restricted()
            await update.message.reply_text(f"User unrestricted: <code>{target_id}</code>", parse_mode=ParseMode.HTML)

        context.user_data["admin_action"] = None

    except Exception:
        await update.message.reply_text("Invalid ID. Example: 123456789")


async def select_country_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, country):
    query = update.callback_query
    config_type = context.user_data.get("type", "VMESS")

    msg = await query.edit_message_text(
        f"┏━━━━━━━━━━━━━━━━━━━━┓\n┃     PROCESSING     ┃\n┗━━━━━━━━━━━━━━━━━━━━┛\n\nType: {config_type}\nRegion: {country}\nPlease wait..."
    )

    try:
        all_configs = await fetch_configs()

        filtered = [c for c in all_configs if c["type"] == config_type]
        if country != "ALL":
            filtered = [c for c in filtered if c["code"] == country]

        if not filtered:
            await msg.edit_text(f"No {config_type} configs found for {country}.")
            return

        file_name = f"{config_type}_{country}_configs.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            for i, cfg in enumerate(filtered, 1):
                f.write(f"# {i} {cfg['type']} {cfg['flag']} {cfg['name']}\n")
                f.write(cfg["raw"] + "\n\n")

        await msg.edit_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n┃    CONFIGS FOUND   ┃\n┗━━━━━━━━━━━━━━━━━━━━┛\n\nTotal: {len(filtered)}\nType: {config_type}\nRegion: {country}\n\nSending file..."
        )

        await update.effective_chat.send_document(
            document=open(file_name, "rb"),
            filename=file_name,
            caption=f"{config_type} {country} configs\nTotal: {len(filtered)}\nChannel: {CHANNEL_ID}"
        )

        os.remove(file_name)

    except Exception as e:
        await msg.edit_text(f"Error:\n<code>{html.escape(str(e)[:300])}</code>", parse_mode=ParseMode.HTML)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    data = query.data

    await query.answer()

    if user_id in RESTRICTED_USERS:
        await query.answer("Access blocked", show_alert=True)
        return

    if data != "ADMIN_PANEL" and not await strong_join_check(user_id, context):
        await query.answer("Join channel first", show_alert=True)
        return

    if data == "BACK_HOME":
        await query.edit_message_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n┃    V2RAY PRO BOT   ┃\n┗━━━━━━━━━━━━━━━━━━━━┛\n\nSelect Config Type:",
            reply_markup=main_menu_keyboard(),
        )
        return

    if data == "ABOUT":
        await query.edit_message_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n┃       ABOUT        ┃\n┗━━━━━━━━━━━━━━━━━━━━┛\n\nOwner: @{OWNER_USERNAME}\nChannel: {CHANNEL_ID}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("┆ BACK", callback_data="BACK_HOME")]])
        )
        return

    if data == "ADMIN_PANEL":
        await show_admin_panel(query)
        return

    if data == "RESTRICT_SHOW":
        if not is_admin(user_id):
            await query.answer("Only admin", show_alert=True)
            return
        context.user_data["admin_action"] = "restrict"
        await query.edit_message_text("Send user ID to restrict:")
        return

    if data == "UNRESTRICT_SHOW":
        if not is_admin(user_id):
            await query.answer("Only admin", show_alert=True)
            return
        context.user_data["admin_action"] = "unrestrict"
        await query.edit_message_text("Send user ID to unrestrict:")
        return

    if data.startswith("TYPE_"):
        config_type = data.replace("TYPE_", "")
        context.user_data["type"] = config_type
        await query.edit_message_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n┃    SELECT REGION   ┃\n┗━━━━━━━━━━━━━━━━━━━━┛\n\nType: {config_type}",
            reply_markup=country_keyboard()
        )
        return

    if data.startswith("COUNTRY_"):
        country = data.replace("COUNTRY_", "")
        await select_country_and_send(update, context, country)
        return


def main():
    if TOKEN == "BOT_TOKEN_HERE" or TOKEN == "BOT_TOKEN":
        print("ERROR: BOT_TOKEN set nahi hai.")
        return

    print("V2RAY PRO BOT RUNNING...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_text))
    app.add_handler(CallbackQueryHandler(on_callback))

    app.run_polling()


if __name__ == "__main__":
    main()
