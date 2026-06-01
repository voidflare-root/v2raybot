import base64
import json
import requests
import asyncio
import time
import re
import html
import urllib.parse

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode

# =========================================================
# CONFIG
# =========================================================
TOKEN = "BOT_TOKEN"
CHANNEL_ID = "@PIYUSHxTG"
CHANNEL_LINK = "https://t.me/PIYUSHxTG"
OWNER_ID = 6493515932
OWNER_USERNAME = "@PIYUSHxTG"

ADMINS = {OWNER_ID}
RESTRICTED_USERS = set()

LINKS = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity",
    "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/master/v2ray-subscribe.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no1.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no2.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no3.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no4.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no5.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no6.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no7.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no8.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no9.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no10.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub2.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub3.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub4.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub5.txt",
    "https://raw.githubusercontent.com/MatinGhanbari/V2Ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
]

CACHE_DURATION = 900
config_cache = []
cache_time = 0.0

SPINNER = ["◐", "◓", "◑", "◒"]

COUNTRY_KEYWORDS = {
    "IN": {"name": "INDIA", "flag": "🇮🇳", "keywords": ["india", "in-", "mumbai", "delhi", "bangalore", "chennai", "kolkata"]},
    "US": {"name": "USA", "flag": "🇺🇸", "keywords": ["usa", "us-", "america", "new york", "los angeles", "chicago"]},
    "GB": {"name": "UK", "flag": "🇬🇧", "keywords": ["uk", "gb-", "london", "britain", "manchester"]},
    "DE": {"name": "GERMANY", "flag": "🇩🇪", "keywords": ["germany", "de-", "frankfurt", "berlin", "munich"]},
    "SG": {"name": "SINGAPORE", "flag": "🇸🇬", "keywords": ["singapore", "sg-"]},
    "JP": {"name": "JAPAN", "flag": "🇯🇵", "keywords": ["japan", "jp-", "tokyo", "osaka"]},
    "CA": {"name": "CANADA", "flag": "🇨🇦", "keywords": ["canada", "ca-", "toronto", "vancouver"]},
    "NL": {"name": "NETHERLANDS", "flag": "🇳🇱", "keywords": ["netherlands", "nl-", "amsterdam"]},
    "FR": {"name": "FRANCE", "flag": "🇫🇷", "keywords": ["france", "fr-", "paris", "lyon"]},
    "AU": {"name": "AUSTRALIA", "flag": "🇦🇺", "keywords": ["australia", "au-", "sydney", "melbourne"]},
    "BR": {"name": "BRAZIL", "flag": "🇧🇷", "keywords": ["brazil", "br-", "sao paulo"]},
    "RU": {"name": "RUSSIA", "flag": "🇷🇺", "keywords": ["russia", "ru-", "moscow"]},
}

PROTOCOL_PATTERNS = {
    "VMESS": re.compile(r"^vmess://", re.I),
    "VLESS": re.compile(r"^vless://", re.I),
    "TROJAN": re.compile(r"^trojan://", re.I),
    "SS": re.compile(r"^ss://", re.I),
}

TYPE_SYMBOL = {
    "VMESS": "◇",
    "VLESS": "◆",
    "TROJAN": "◈",
    "SS": "◉",
}


# =========================================================
# HELPERS
# =========================================================
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS


def decode_base64(data: str) -> str:
    try:
        data = data.strip().replace("\n", "").replace("\r", "").replace(" ", "")
        missing = len(data) % 4
        if missing:
            data += "=" * (4 - missing)
        return base64.b64decode(data).decode("utf-8", errors="ignore")
    except Exception:
        try:
            data = data.replace("-", "+").replace("_", "/")
            missing = len(data) % 4
            if missing:
                data += "=" * (4 - missing)
            return base64.b64decode(data).decode("utf-8", errors="ignore")
        except Exception:
            return data


def extract_config_name(line: str, ctype: str) -> str:
    try:
        if "#" in line:
            name = line.split("#")[-1]
            if "%" in name:
                name = urllib.parse.unquote(name)
            name = re.sub(r"[^\w\s\u0900-\u097F@.\-]", "", name).strip()
            if name and len(name) > 1:
                return name[:40]

        if ctype == "VMESS" and line.startswith("vmess://"):
            decoded = decode_base64(line[8:])
            if decoded:
                try:
                    obj = json.loads(decoded)
                    ps = str(obj.get("ps", "")).strip()
                    if ps:
                        return ps[:40]
                except Exception:
                    m = re.search(r'"ps"\s*:\s*"([^"]+)"', decoded)
                    if m:
                        return m.group(1)[:40]

        ip_match = re.search(r"@([0-9.]+):", line)
        if ip_match:
            return f"{ctype}@{ip_match.group(1)}"

        domain_match = re.search(r"@([a-zA-Z0-9.\-]+):", line)
        if domain_match:
            return f"{ctype}@{domain_match.group(1)[:30]}"

        return ctype
    except Exception:
        return ctype


def detect_country_code(text: str):
    if not text:
        return None
    t = text.lower()
    for code, info in COUNTRY_KEYWORDS.items():
        for kw in info["keywords"]:
            if kw in t:
                return code
    return None


def detect_country_flag(text: str) -> str:
    code = detect_country_code(text)
    if code and code in COUNTRY_KEYWORDS:
        return COUNTRY_KEYWORDS[code]["flag"]
    return "🌍"


def parse_config(line: str):
    line = line.strip()
    if not line:
        return None

    try:
        ctype = None
        for t, pat in PROTOCOL_PATTERNS.items():
            if pat.match(line):
                ctype = t
                break

        if not ctype:
            return None

        name = extract_config_name(line, ctype)
        full = f"{name} {line}"

        return {
            "type": ctype,
            "symbol": TYPE_SYMBOL.get(ctype, "•"),
            "raw": line,
            "name": name,
            "flag": detect_country_flag(full),
            "code": detect_country_code(full),
            "search": full.lower(),
        }
    except Exception:
        return None


async def fetch_url_text(url: str):
    def _get():
        return requests.get(url, timeout=15)

    try:
        r = await asyncio.to_thread(_get)
        if r.status_code == 200:
            return r.text.strip()
    except Exception:
        return None
    return None


async def fetch_configs(progress_cb=None):
    global config_cache, cache_time

    now = time.time()
    if config_cache and (now - cache_time) < CACHE_DURATION:
        if progress_cb:
            await progress_cb(100.0, "Using cache")
        return config_cache

    all_configs = []
    seen = set()
    total_links = len(LINKS)

    for idx, link in enumerate(LINKS, start=1):
        try:
            if progress_cb:
                base_pct = ((idx - 1) / total_links) * 80.0
                await progress_cb(base_pct, f"Opening source {idx}/{total_links}")

            content = await fetch_url_text(link)
            if not content or len(content) < 20:
                continue

            if "public class" in content[:200] or "package " in content[:200] or ".class" in content[:200]:
                continue

            if not any(content.startswith(p) for p in ["vmess://", "vless://", "trojan://", "ss://"]):
                decoded = decode_base64(content)
                if decoded and len(decoded) > 50 and any(
                    p in decoded[:500] for p in ["vmess://", "vless://", "trojan://", "ss://"]
                ):
                    content = decoded

            lines = content.splitlines()
            line_total = max(len(lines), 1)

            for li, raw_line in enumerate(lines, start=1):
                line = raw_line.strip()
                if not line or line in seen:
                    continue
                if not any(line.startswith(p) for p in ["vmess://", "vless://", "trojan://", "ss://"]):
                    continue

                cfg = parse_config(line)
                if cfg:
                    seen.add(line)
                    all_configs.append(cfg)

                if progress_cb and li % 40 == 0:
                    inner = li / line_total
                    pct = ((idx - 1 + inner) / total_links) * 80.0
                    await progress_cb(pct, f"Parsing source {idx}/{total_links}")

        except Exception:
            continue

    if progress_cb:
        await progress_cb(85.0, "Filtering results")

    config_cache = all_configs
    cache_time = now

    if progress_cb:
        await progress_cb(100.0, "Completed")

    return all_configs


def build_progress_bar(percent: float, width: int = 20) -> str:
    filled = int((percent / 100.0) * width)
    return "━" * filled + "─" * (width - filled)


async def live_progress_editor(message, state):
    last_text = None

    while not state["done"]:
        pct = state["percent"]
        stage = state["stage"]
        spin = SPINNER[int(time.time() * 4) % len(SPINNER)]
        bar = build_progress_bar(pct)

        text = (
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃     PROCESSING     ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"{spin} {pct:05.1f}%\n"
            f"[{bar}]\n\n"
            f"Type   : {html.escape(state['type'])}\n"
            f"Region : {html.escape(state['country'])}\n"
            f"Stage  : {html.escape(stage)}"
        )

        if text != last_text:
            try:
                await message.edit_text(text, parse_mode=ParseMode.HTML)
                last_text = text
            except Exception:
                pass

        await asyncio.sleep(0.6)

    try:
        final_text = (
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃     PROCESSING     ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"{SPINNER[1]} 100.0%\n"
            f"[{build_progress_bar(100.0)}]\n\n"
            f"Type   : {html.escape(state['type'])}\n"
            f"Region : {html.escape(state['country'])}\n"
            f"Stage  : Completed"
        )
        await message.edit_text(final_text, parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def strong_join_check(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if user_id in RESTRICTED_USERS:
        return False

    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("◇ VMESS", callback_data="TYPE_VMESS")],
        [InlineKeyboardButton("◆ VLESS", callback_data="TYPE_VLESS")],
        [InlineKeyboardButton("◈ TROJAN", callback_data="TYPE_TROJAN")],
        [InlineKeyboardButton("◉ SHADOWSOCKS", callback_data="TYPE_SS")],
        [InlineKeyboardButton("┆ ABOUT", callback_data="ABOUT")],
        [InlineKeyboardButton("┆ ADMIN PANEL", callback_data="ADMIN_PANEL")],
    ]
    return InlineKeyboardMarkup(keyboard)


def country_keyboard():
    keys = []
    row = []
    for code, info in COUNTRY_KEYWORDS.items():
        row.append(InlineKeyboardButton(f"{info['flag']} {code}", callback_data=f"COUNTRY_{code}"))
        if len(row) == 3:
            keys.append(row)
            row = []
    if row:
        keys.append(row)
    keys.append([InlineKeyboardButton("┆ ALL", callback_data="COUNTRY_ALL")])
    keys.append([InlineKeyboardButton("┆ BACK", callback_data="BACK_HOME")])
    return InlineKeyboardMarkup(keys)


# =========================================================
# ADMIN
# =========================================================
async def show_admin_panel(query):
    user_id = query.from_user.id
    restricted_list = list(RESTRICTED_USERS)

    if restricted_list:
        restricted_text = ""
        for uid in restricted_list[:8]:
            restricted_text += f"• <code>{uid}</code>\n"
        if len(restricted_list) > 8:
            restricted_text += f"• +{len(restricted_list) - 8} more\n"
    else:
        restricted_text = "• No restricted users"

    note = "Authorized only" if is_admin(user_id) else "Visible to all | Restricted for non-admin"

    keyboard = [
        [InlineKeyboardButton("┆ RESTRICT USER", callback_data="RESTRICT_SHOW")],
        [InlineKeyboardButton("┆ UNRESTRICT USER", callback_data="UNRESTRICT_SHOW")],
        [InlineKeyboardButton("┆ LIST RESTRICTED", callback_data="LIST_RESTRICTED")],
        [InlineKeyboardButton("┆ BACK", callback_data="BACK_HOME")],
    ]

    await query.edit_message_text(
        f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃     ADMIN PANEL    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"Mode   : {html.escape(note)}\n"
        f"Owner  : @{OWNER_USERNAME}\n"
        f"Blocked: {len(restricted_list)}\n\n"
        f"{restricted_text}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML,
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

        if action == "waiting_restrict":
            RESTRICTED_USERS.add(target_id)
            await update.message.reply_text(
                f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
                f"┃   USER RESTRICTED  ┃\n"
                f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
                f"User ID : <code>{target_id}</code>",
                parse_mode=ParseMode.HTML,
            )
        elif action == "waiting_unrestrict":
            RESTRICTED_USERS.discard(target_id)
            await update.message.reply_text(
                f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
                f"┃ USER UNRESTRICTED  ┃\n"
                f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
                f"User ID : <code>{target_id}</code>",
                parse_mode=ParseMode.HTML,
            )

        context.user_data["admin_action"] = None
    except Exception:
        await update.message.reply_text(
            "Invalid user ID.\nExample:\n<code>123456789</code>",
            parse_mode=ParseMode.HTML,
        )


# =========================================================
# USER FLOW
# =========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in RESTRICTED_USERS:
        await update.message.reply_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃    ACCESS DENIED   ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"Status : Restricted\n"
            f"Contact: @{OWNER_USERNAME}",
            parse_mode=ParseMode.HTML,
        )
        return

    if not await strong_join_check(user_id, context):
        keyboard = [[InlineKeyboardButton("┆ JOIN CHANNEL", url=CHANNEL_LINK)]]
        await update.message.reply_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃    JOIN REQUIRED   ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"Channel : {html.escape(CHANNEL_ID)}\n"
            f"Action  : Join first, then send /start\n\n"
            f"Access remains locked until membership is confirmed.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    await update.message.reply_text(
        f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃    V2RAY PRO BOT   ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"Status  : Online\n"
        f"Sources : {len(LINKS)}\n"
        f"Cache   : {CACHE_DURATION}s\n\n"
        f"Select Config Type:",
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def select_country_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, country: str):
    query = update.callback_query
    config_type = context.user_data.get("type", "VMESS")

    msg = await query.edit_message_text(
        "Starting...",
        parse_mode=ParseMode.HTML
    )

    progress_state = {
        "percent": 0.0,
        "stage": "Initializing",
        "done": False,
        "type": config_type,
        "country": country
    }

    async def progress_cb(percent, stage):
        progress_state["percent"] = min(max(percent, 0.0), 100.0)
        progress_state["stage"] = stage

    progress_task = asyncio.create_task(live_progress_editor(msg, progress_state))

    try:
        all_configs = await asyncio.wait_for(fetch_configs(progress_cb=progress_cb), timeout=120)

        await progress_cb(88.0, "Filtering results")

        filtered = [c for c in all_configs if c["type"] == config_type]
        if country != "ALL":
            filtered = [c for c in filtered if c["code"] == country]

        await progress_cb(93.0, "Preparing messages")

        if not filtered:
            progress_state["done"] = True
            await progress_task
            await msg.edit_text(
                f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
                f"┃      NOT FOUND     ┃\n"
                f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
                f"No {html.escape(config_type)} configs for {html.escape(country)}.",
                parse_mode=ParseMode.HTML,
            )
            return

        progress_state["done"] = True
        await progress_task

        await msg.edit_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃    CONFIGS FOUND   ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"Total  : {len(filtered)}\n"
            f"Type   : {html.escape(config_type)}\n"
            f"Region : {html.escape(country)}\n\n"
            f"Sending all configs...",
            parse_mode=ParseMode.HTML
        )

        total_send = len(filtered)
        for i, cfg in enumerate(filtered, start=1):
            safe_name = html.escape(cfg["name"][:35])
            safe_raw = html.escape(cfg["raw"])

            header = (
                f"┌────────────────────┐\n"
                f"│ #{i}/{total_send} {cfg['symbol']} {cfg['type']} {cfg['flag']}\n"
                f"├────────────────────┤\n"
                f"│ {safe_name}\n"
                f"└────────────────────┘"
            )

            await update.effective_chat.send_message(
                header,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )

            chunk_size = 3500
            for start_idx in range(0, len(safe_raw), chunk_size):
                chunk = safe_raw[start_idx:start_idx + chunk_size]
                await update.effective_chat.send_message(
                    f"<code>{chunk}</code>",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )

            if i % 5 == 0:
                await asyncio.sleep(0.4)

        await update.effective_chat.send_message(
            f"────────────────────\n"
            f"Done    : {len(filtered)} configs sent\n"
            f"Channel : {html.escape(CHANNEL_ID)}",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    except asyncio.TimeoutError:
        progress_state["done"] = True
        await progress_task
        await msg.edit_text(
            "Timeout. Use /start again.",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        progress_state["done"] = True
        await progress_task
        await msg.edit_text(
            f"Error:\n<code>{html.escape(str(e)[:200])}</code>",
            parse_mode=ParseMode.HTML,
        )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    data = query.data

    if user_id in RESTRICTED_USERS:
        await query.answer("Access blocked", show_alert=True)
        return

    if data not in {"ADMIN_PANEL"} and not await strong_join_check(user_id, context):
        await query.answer("Join channel first", show_alert=True)
        return

    await query.answer()

    if data == "BACK_HOME":
        await query.edit_message_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃    V2RAY PRO BOT   ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"Status  : Online\n"
            f"Sources : {len(LINKS)}\n"
            f"Cache   : {CACHE_DURATION}s\n\n"
            f"Select Config Type:",
            reply_markup=main_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "ABOUT":
        await query.edit_message_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃       ABOUT        ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"Owner   : @{OWNER_USERNAME}\n\n"
            f"Team    :\n"
            f"• @NIKSHACKS\n"
            f"• @SAHILXTG_45\n"
            f"• @Vijayxtunnel\n"
            f"• @ADITYAXTG4\n\n"
            f"• @THE_MODS_KING\n\n"
            f"Channel : {html.escape(CHANNEL_ID)}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("┆ BACK", callback_data="BACK_HOME")]]),
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "ADMIN_PANEL":
        await show_admin_panel(query)
        return

    if data == "RESTRICT_SHOW":
        if not is_admin(user_id):
            await query.answer("Only authorized admin can use this", show_alert=True)
            return
        context.user_data["admin_action"] = "waiting_restrict"
        await query.edit_message_text(
            "Send user ID to restrict.\n\nExample:\n<code>123456789</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("┆ BACK", callback_data="ADMIN_PANEL")]]),
        )
        return

    if data == "UNRESTRICT_SHOW":
        if not is_admin(user_id):
            await query.answer("Only authorized admin can use this", show_alert=True)
            return
        context.user_data["admin_action"] = "waiting_unrestrict"
        await query.edit_message_text(
            "Send user ID to unrestrict.\n\nExample:\n<code>123456789</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("┆ BACK", callback_data="ADMIN_PANEL")]]),
        )
        return

    if data == "LIST_RESTRICTED":
        if not is_admin(user_id):
            await query.answer("Only authorized admin can use this", show_alert=True)
            return
        text = "Restricted Users\n━━━━━━━━━━━━━━━━━\n"
        if RESTRICTED_USERS:
            for uid in sorted(RESTRICTED_USERS):
                text += f"• <code>{uid}</code>\n"
        else:
            text += "• No restricted users"
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("┆ BACK", callback_data="ADMIN_PANEL")]]),
        )
        return

    if data.startswith("TYPE_"):
        config_type = data.replace("TYPE_", "")
        context.user_data["type"] = config_type

        await query.edit_message_text(
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃    SELECT REGION   ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"Type : {html.escape(config_type)}\n\n"
            f"Choose location:",
            reply_markup=country_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if data.startswith("COUNTRY_"):
        country = data.replace("COUNTRY_", "")
        await select_country_and_send(update, context, country)
        return


# =========================================================
# MAIN
# =========================================================
def main():
    print("╔══════════════════════════════════╗")
    print("║        V2RAY PRO BOT FINAL      ║")
    print("║   Strong Join | Admin Control   ║")
    print("║   Smooth Progress | Full Config ║")
    print("╚══════════════════════════════════╝")
    print(f"\nOwner   : @{OWNER_USERNAME}")
    print(f"Admins  : {len(ADMINS)}")
    print(f"Sources : {len(LINKS)}")
    print(f"Cache   : {CACHE_DURATION}s")
    print("\nBot Running...\n")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_text))
    app.add_handler(CallbackQueryHandler(on_callback))

    app.run_polling()


if __name__ == "__main__":
    main()