import os, base64, json, requests, asyncio, time, re, html, urllib.parse
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

TOKEN = os.getenv("BOT_TOKEN", "BOT_TOKEN_HERE")

CHANNEL_ID = "@PIYUSHxTG"
CHANNEL_LINK = "https://t.me/ABOUTM3TG"
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
    "IN": {"flag": "🇮🇳", "keywords": ["india", "mumbai", "delhi", "bangalore", "chennai", "kolkata"]},
    "US": {"flag": "🇺🇸", "keywords": ["usa", "america", "new york", "los angeles", "chicago"]},
    "GB": {"flag": "🇬🇧", "keywords": ["uk", "london", "britain"]},
    "DE": {"flag": "🇩🇪", "keywords": ["germany", "frankfurt", "berlin"]},
    "SG": {"flag": "🇸🇬", "keywords": ["singapore"]},
    "JP": {"flag": "🇯🇵", "keywords": ["japan", "tokyo"]},
    "CA": {"flag": "🇨🇦", "keywords": ["canada", "toronto"]},
    "NL": {"flag": "🇳🇱", "keywords": ["netherlands", "amsterdam"]},
    "FR": {"flag": "🇫🇷", "keywords": ["france", "paris"]},
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
    except:
        return set()


RESTRICTED_USERS = load_restricted()


def save_restricted():
    with open(RESTRICT_FILE, "w") as f:
        json.dump(list(RESTRICTED_USERS), f)


def is_admin(user_id):
    return user_id in ADMINS


def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["◇ VMESS", "◆ VLESS"],
            ["◈ TROJAN", "◉ SS"],
            ["ℹ️ ABOUT", "⚙️ ADMIN"],
            ["🔄 START"]
        ],
        resize_keyboard=True
    )


def region_menu():
    return ReplyKeyboardMarkup(
        [
            ["🇮🇳 IN", "🇺🇸 US", "🇬🇧 GB"],
            ["🇩🇪 DE", "🇸🇬 SG", "🇯🇵 JP"],
            ["🇨🇦 CA", "🇳🇱 NL", "🇫🇷 FR"],
            ["🌍 ALL", "🔙 BACK"]
        ],
        resize_keyboard=True
    )


def admin_menu():
    return ReplyKeyboardMarkup(
        [
            ["🚫 RESTRICT USER", "✅ UNRESTRICT USER"],
            ["📋 LIST BLOCKED", "🔙 BACK"]
        ],
        resize_keyboard=True
    )


def decode_base64(data):
    try:
        data = data.strip().replace("\n", "").replace("\r", "").replace(" ", "")
        data += "=" * (-len(data) % 4)
        return base64.b64decode(data).decode("utf-8", errors="ignore")
    except:
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
    except:
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
    except:
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
    except:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu"] = "main"

    await update.message.reply_text(
        f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃    V2RAY PRO BOT   ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"Status : Online\n"
        f"Mode   : Reply Keyboard Menu\n\n"
        f"Typing box ke upar button select karo.",
        reply_markup=main_menu()
    )


async def send_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE, country):
    user_id = update.effective_user.id
    config_type = context.user_data.get("type", "VMESS")

    if user_id in RESTRICTED_USERS:
        await update.message.reply_text("Access denied.", reply_markup=main_menu())
        return

    if not await strong_join_check(user_id, context):
        await update.message.reply_text(
            f"Join channel first:\n{CHANNEL_LINK}\n\nJoin ke baad /start send karo.",
            reply_markup=main_menu(),
            disable_web_page_preview=True
        )
        return

    msg = await update.message.reply_text(
        f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃     UPLOADING      ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"Type   : {config_type}\n"
        f"Region : {country}\n\n"
        f"▰▱▱▱▱▱▱▱▱▱ 10%\n"
        f"Collecting accounts..."
    )

    try:
        await asyncio.sleep(0.4)
        await msg.edit_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃     UPLOADING      ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"▰▰▰▱▱▱▱▱▱▱ 35%\n"
            f"Checking sources..."
        )

        all_configs = await fetch_configs()

        await asyncio.sleep(0.4)
        await msg.edit_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃     UPLOADING      ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"▰▰▰▰▰▰▱▱▱▱ 65%\n"
            f"Filtering accounts..."
        )

        filtered = [c for c in all_configs if c["type"] == config_type]

        if country != "ALL":
            filtered = [c for c in filtered if c["code"] == country]

        if not filtered:
            await msg.edit_text(f"No {config_type} account found for {country}.")
            return

        await asyncio.sleep(0.4)
        await msg.edit_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃    ACCOUNTS FOUND  ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"Total  : {len(filtered)}\n"
            f"Type   : {config_type}\n"
            f"Region : {country}\n\n"
            f"Sending accounts..."
        )

        max_send = min(len(filtered), 25)

        for i, cfg in enumerate(filtered[:max_send], start=1):
            safe_name = html.escape(cfg["name"][:40])
            safe_raw = html.escape(cfg["raw"])

            text = (
                f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
                f"┃ {cfg['symbol']} {cfg['type']} ACCOUNT {cfg['flag']}\n"
                f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
                f"ID     : #{i}\n"
                f"Name   : {safe_name}\n"
                f"Region : {country}\n\n"
                f"<code>{safe_raw}</code>\n\n"
                f"Copy: config par tap/hold karo."
            )

            await update.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=main_menu()
            )

            await asyncio.sleep(0.2)

        await update.message.reply_text(
            f"✅ Done: {max_send} accounts sent\nType: {config_type}",
            reply_markup=main_menu()
        )

    except Exception as e:
        await msg.edit_text(f"Error:\n<code>{html.escape(str(e)[:300])}</code>", parse_mode=ParseMode.HTML)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text == "🔄 START":
        await start(update, context)
        return

    if text == "🔙 BACK":
        context.user_data["menu"] = "main"
        await update.message.reply_text("Main menu:", reply_markup=main_menu())
        return

    if text == "ℹ️ ABOUT":
        await update.message.reply_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃       ABOUT        ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"Owner   : @{OWNER_USERNAME}\n"
            f"Channel : {CHANNEL_ID}",
            reply_markup=main_menu()
        )
        return

    if text == "⚙️ ADMIN":
        if not is_admin(user_id):
            await update.message.reply_text("Only admin can use this.", reply_markup=main_menu())
            return

        context.user_data["menu"] = "admin"
        await update.message.reply_text("Admin Menu:", reply_markup=admin_menu())
        return

    if text == "🚫 RESTRICT USER":
        if is_admin(user_id):
            context.user_data["admin_action"] = "restrict"
            await update.message.reply_text("User ID send karo:", reply_markup=admin_menu())
        return

    if text == "✅ UNRESTRICT USER":
        if is_admin(user_id):
            context.user_data["admin_action"] = "unrestrict"
            await update.message.reply_text("User ID send karo:", reply_markup=admin_menu())
        return

    if text == "📋 LIST BLOCKED":
        if is_admin(user_id):
            if RESTRICTED_USERS:
                data = "\n".join([str(x) for x in RESTRICTED_USERS])
            else:
                data = "No blocked users"
            await update.message.reply_text(data, reply_markup=admin_menu())
        return

    action = context.user_data.get("admin_action")
    if action and is_admin(user_id):
        try:
            target = int(text)
            if action == "restrict":
                RESTRICTED_USERS.add(target)
                save_restricted()
                await update.message.reply_text(f"Restricted: {target}", reply_markup=admin_menu())
            elif action == "unrestrict":
                RESTRICTED_USERS.discard(target)
                save_restricted()
                await update.message.reply_text(f"Unrestricted: {target}", reply_markup=admin_menu())

            context.user_data["admin_action"] = None
        except:
            await update.message.reply_text("Invalid ID.", reply_markup=admin_menu())
        return

    if text == "◇ VMESS":
        context.user_data["type"] = "VMESS"
        await update.message.reply_text("Region select karo:", reply_markup=region_menu())
        return

    if text == "◆ VLESS":
        context.user_data["type"] = "VLESS"
        await update.message.reply_text("Region select karo:", reply_markup=region_menu())
        return

    if text == "◈ TROJAN":
        context.user_data["type"] = "TROJAN"
        await update.message.reply_text("Region select karo:", reply_markup=region_menu())
        return

    if text == "◉ SS":
        context.user_data["type"] = "SS"
        await update.message.reply_text("Region select karo:", reply_markup=region_menu())
        return

    country_map = {
        "🇮🇳 IN": "IN",
        "🇺🇸 US": "US",
        "🇬🇧 GB": "GB",
        "🇩🇪 DE": "DE",
        "🇸🇬 SG": "SG",
        "🇯🇵 JP": "JP",
        "🇨🇦 CA": "CA",
        "🇳🇱 NL": "NL",
        "🇫🇷 FR": "FR",
        "🌍 ALL": "ALL",
    }

    if text in country_map:
        await send_accounts(update, context, country_map[text])
        return

    await update.message.reply_text("Menu button use karo.", reply_markup=main_menu())


def main():
    if TOKEN in ["BOT_TOKEN_HERE", "BOT_TOKEN", ""]:
        print("ERROR: BOT_TOKEN set nahi hai.")
        return

    print("V2RAY BOT RUNNING | REPLY KEYBOARD ONLY")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()


if __name__ == "__main__":
    main()
