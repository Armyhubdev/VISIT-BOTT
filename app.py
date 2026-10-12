import asyncio
import json
import time
import os
import re as _re
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ==================================================
# CONFIG
# ==================================================

BOT_TOKEN = "8848812350:AAGKMSdHoTmwdSuwHFgDo2gGNz8eknvTEX4"

ADMIN_ID = 8786484736

API_URL = "https://rg-visitt-production.up.railway.app/visit"
PRIME_API_URL = "https://www.freefiremania.com.br/paginas/nivel-prime-check.php"
SENSI_API_URL = "https://www.freefiremania.com.br/paginas/gerar-sensibilidade.php"

MAX_REQUESTS = 100

TRIAL_KEY = "RG_iCjEouu1jxYLQTLbIfSuQ6Rf"
TRIAL_COOLDOWN = 24 * 60 * 60
TRIAL_REQUESTS = 1

DEV_HANDLE = "@rgdev404"
SUPPORT_HANDLE = "@rgdev404"
BUY_HANDLE = "@rgdev404"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRIAL_FILE = os.path.join(BASE_DIR, "trial_usage.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
ADMIN_FILE = os.path.join(BASE_DIR, "admin_settings.json")


# ==================================================
# TRANSLATION HELPERS
# ==================================================

def translate_prime_text(text):
    if not text:
        return text

    exact = {
        "Moldura de Avatar Prime": "Prime Avatar Frame",
        "Compartilhamento de Trajes": "Outfits Sharing",
        "Compartilhamento de Traje": "Outfit Sharing",
        "Emblema Prime": "Prime Emblem",
        "Insígnia Prime": "Prime Badge",
        "Recompensas Diárias": "Daily Rewards",
        "Sala VIP": "VIP Room",
        "O nível 1 do Prime Free Fire representa o primeiro nível do programa, oferecendo acesso a benefícios básicos como o símbolo Prime 1 dentro do jogo.":
            "Prime Level 1 of Free Fire represents the first tier of the program, offering access to basic benefits like the Prime Symbol 1 inside the game.",
        "O nível 2 do Prime Free Fire oferece benefícios progressivos, incluindo o símbolo Prime 2 e pequenos bônus dentro do jogo.":
            "Prime Level 2 of Free Fire offers progressive benefits, including the Prime Symbol 2 and small bonuses inside the game.",
        "O nível 3 do Prime Free Fire introduz vantagens exclusivas e o símbolo Prime 3, melhorando a experiência dentro do jogo.":
            "Prime Level 3 of Free Fire introduces exclusive advantages and the Prime Symbol 3, improving the in-game experience.",
        "O nível 4 do Prime Free Fire representa um passo intermediário, liberando o símbolo Prime 4 e benefícios adicionais.":
            "Prime Level 4 of Free Fire represents an intermediate step, unlocking the Prime Symbol 4 and additional benefits.",
        "O nível 5 do Prime Free Fire traz vantagens significativas e o símbolo Prime 5, marcando metade do caminho para o topo.":
            "Prime Level 5 of Free Fire brings significant advantages and the Prime Symbol 5, marking half-way to the top.",
        "O nível 6 do Prime Free Fire oferece benefícios premium, incluindo o símbolo Prime 6, para jogadores dedicados.":
            "Prime Level 6 of Free Fire offers premium benefits, including the Prime Symbol 6, for dedicated players.",
        "O nível 7 do Prime Free Fire libera vantagens quase máximas e o símbolo Prime 7, colocando o jogador entre os melhores.":
            "Prime Level 7 of Free Fire unlocks near-maximum advantages and the Prime Symbol 7, placing the player among the best.",
        "O nível 8 do Prime Free Fire representa o status máximo, liberando benefícios exclusivos como compartilhamento de trajes e reconhecimento premium dentro do jogo.":
            "Prime Level 8 of Free Fire represents the maximum status, unlocking exclusive benefits like outfit sharing and premium recognition in the game.",
    }

    if text in exact:
        return exact[text]

    text = _re.sub(r"Símbolo Prime (\d+)", r"Prime Symbol \1", text)
    text = _re.sub(r"Emblema Prime (\d+)", r"Prime Emblem \1", text)
    text = _re.sub(r"Insígnia Prime (\d+)", r"Prime Badge \1", text)
    text = _re.sub(r"O nível (\d+)", r"Level \1", text)
    text = _re.sub(r"nível (\d+)", r"Level \1", text)

    phrase_map = [
        ("do Prime Free Fire", "of Prime Free Fire"),
        ("status máximo", "maximum status"),
        ("liberando benefícios exclusivos como", "unlocking exclusive benefits like"),
        ("compartilhamento de trajes", "outfit sharing"),
        ("compartilhamento de traje", "outfit sharing"),
        ("reconhecimento premium dentro do jogo", "premium recognition inside the game"),
        ("dentro do jogo", "inside the game"),
        ("benefícios exclusivos", "exclusive benefits"),
        ("benefícios adicionais", "additional benefits"),
        ("benefícios premium", "premium benefits"),
        ("benefícios básicos", "basic benefits"),
        ("benefícios progressivos", "progressive benefits"),
        ("vantagens exclusivas", "exclusive advantages"),
        ("vantagens significativas", "significant advantages"),
        ("vantagens quase máximas", "near-maximum advantages"),
        ("oferecendo acesso a", "offering access to"),
        ("oferecendo", "offering"),
        ("oferece", "offers"),
        ("representa", "represents"),
        ("programa", "program"),
        ("jogadores dedicados", "dedicated players"),
        ("jogadores", "players"),
        ("jogador", "player"),
        ("melhores", "best"),
        ("pequenos bônus", "small bonuses"),
        ("bônus", "bonuses"),
        ("incluindo", "including"),
        ("introduz", "introduces"),
        ("melhorando a experiência", "improving the experience"),
        ("liberando", "unlocking"),
        ("traz", "brings"),
        ("marcando metade do caminho para o topo", "marking half-way to the top"),
        ("colocando o jogador entre os melhores", "placing the player among the best"),
        ("para jogadores dedicados", "for dedicated players"),
        ("exclusivas", "exclusive"),
        ("exclusivos", "exclusive"),
        ("Moldura de Avatar Prime", "Prime Avatar Frame"),
        ("Emblema Prime", "Prime Emblem"),
        ("Insígnia Prime", "Prime Badge"),
        ("Sala VIP", "VIP Room"),
        ("Recompensas Diárias", "Daily Rewards"),
    ]

    for pt, en in phrase_map:
        text = text.replace(pt, en)

    return text


def format_diamonds(value):
    if not value or value == "N/A":
        return value
    try:
        if isinstance(value, str):
            clean = value.replace(".", "").replace(",", ".")
            num = int(float(clean))
            return f"{num:,}"
    except Exception:
        pass
    return value


# ==================================================
# ADMIN SETTINGS
# ==================================================

DEFAULT_ADMIN_SETTINGS = {
    "maintenance": {
        "bot": False,
        "visit": False,
        "prime": False,
        "sensi": False,
    },
    "maintenance_msg": (
        "🔧 *Bot is under maintenance*\n\n"
        "Please try again later.\n"
        "We'll be back soon! 🚀"
    ),
    "trial_enabled": True,
    "banned_users": []
}


def load_admin_settings():
    try:
        with open(ADMIN_FILE, "r") as f:
            data = json.load(f)
        for k, v in DEFAULT_ADMIN_SETTINGS.items():
            if k not in data:
                data[k] = v
        if "maintenance" not in data:
            data["maintenance"] = DEFAULT_ADMIN_SETTINGS["maintenance"].copy()
        else:
            for k, v in DEFAULT_ADMIN_SETTINGS["maintenance"].items():
                if k not in data["maintenance"]:
                    data["maintenance"][k] = v
        return data
    except Exception:
        return json.loads(json.dumps(DEFAULT_ADMIN_SETTINGS))


def save_admin_settings(data):
    try:
        with open(ADMIN_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Save admin settings error:", e)


def is_maintenance(service):
    settings = load_admin_settings()
    if settings["maintenance"].get("bot", False):
        return True, settings.get("maintenance_msg", "Under maintenance")
    if service in settings["maintenance"] and settings["maintenance"][service]:
        return True, settings.get("maintenance_msg", "Under maintenance")
    return False, None


def is_banned(user_id):
    if user_id == ADMIN_ID:
        return False
    settings = load_admin_settings()
    return str(user_id) in settings.get("banned_users", [])


def is_trial_enabled():
    return load_admin_settings().get("trial_enabled", True)


# ==================================================
# USERS
# ==================================================

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_users(data):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print("Save users error:", e)


def add_user(user):
    if not user:
        return
    users = load_users()
    uid = str(user.id)
    users[uid] = {
        "name": user.first_name or "Unknown",
        "username": user.username or "",
        "last_seen": time.time()
    }
    save_users(users)


# ==================================================
# TRIAL
# ==================================================

def load_trials():
    try:
        with open(TRIAL_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_trials(data):
    try:
        with open(TRIAL_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print("Save trial error:", e)


def can_use_trial(user_id):
    if user_id == ADMIN_ID:
        return True, None
    if not is_trial_enabled():
        return False, "disabled"
    trials = load_trials()
    last = trials.get(str(user_id), 0)
    elapsed = time.time() - last
    if elapsed >= TRIAL_COOLDOWN:
        return True, None
    remaining = TRIAL_COOLDOWN - elapsed
    hours = int(remaining // 3600)
    minutes = int((remaining % 3600) // 60)
    return False, (hours, minutes)


def mark_trial_used(user_id):
    trials = load_trials()
    trials[str(user_id)] = time.time()
    save_trials(trials)


# ==================================================
# HELPERS
# ==================================================

def is_admin(update: Update):
    return update.effective_user and update.effective_user.id == ADMIN_ID


# ==================================================
# KEYBOARDS
# ==================================================

def cancel_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🛑 Cancel Process", callback_data="cancel_process")]]
    )


def welcome_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🚀 Start Visit", callback_data="start_visit")],
            [
                InlineKeyboardButton("👑 Prime Check", callback_data="start_prime"),
                InlineKeyboardButton("🎯 Sensitivity", callback_data="start_sensi")
            ],
            [
                InlineKeyboardButton("🔑 Buy Key", url=f"https://t.me/{BUY_HANDLE.lstrip('@')}"),
                InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_HANDLE.lstrip('@')}")
            ],
            [InlineKeyboardButton("ℹ️ How It Works", callback_data="how_it_works")]
        ]
    )


def trial_or_key_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎁 Use Free Trial", callback_data="use_trial")],
            [InlineKeyboardButton("🔑 Buy Premium Key", url=f"https://t.me/{BUY_HANDLE.lstrip('@')}")],
            [InlineKeyboardButton("🛑 Cancel", callback_data="cancel_process")]
        ]
    )


def again_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔁 Run Again", callback_data="start_visit")],
            [
                InlineKeyboardButton("👑 Prime Check", callback_data="start_prime"),
                InlineKeyboardButton("🎯 Sensitivity", callback_data="start_sensi")
            ],
            [
                InlineKeyboardButton("🔑 Buy Key", url=f"https://t.me/{BUY_HANDLE.lstrip('@')}"),
                InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_HANDLE.lstrip('@')}")
            ]
        ]
    )


def prime_again_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("👑 Check Another", callback_data="start_prime")],
            [
                InlineKeyboardButton("🚀 Visit", callback_data="start_visit"),
                InlineKeyboardButton("🎯 Sensitivity", callback_data="start_sensi")
            ],
            [
                InlineKeyboardButton("🔑 Buy Key", url=f"https://t.me/{BUY_HANDLE.lstrip('@')}"),
                InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_HANDLE.lstrip('@')}")
            ]
        ]
    )


def sensi_again_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎯 New Device", callback_data="start_sensi")],
            [
                InlineKeyboardButton("🚀 Visit", callback_data="start_visit"),
                InlineKeyboardButton("👑 Prime", callback_data="start_prime")
            ],
            [
                InlineKeyboardButton("🔑 Buy Key", url=f"https://t.me/{BUY_HANDLE.lstrip('@')}"),
                InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_HANDLE.lstrip('@')}")
            ]
        ]
    )


def back_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back", callback_data="back_home")]]
    )


def admin_keyboard():
    s = load_admin_settings()
    m = s["maintenance"]

    def btn(label, key, state):
        icon = "🟢" if not state else "🔴"
        return InlineKeyboardButton(f"{icon} {label}", callback_data=f"adm_toggle_{key}")

    trial_icon = "🟢" if s.get("trial_enabled", True) else "🔴"

    return InlineKeyboardMarkup(
        [
            [
                btn("Visit", "visit", m.get("visit", False)),
                btn("Prime", "prime", m.get("prime", False)),
            ],
            [
                btn("Sensi", "sensi", m.get("sensi", False)),
                btn("Bot", "bot", m.get("bot", False)),
            ],
            [
                InlineKeyboardButton(
                    f"{trial_icon} Free Trial", callback_data="adm_toggle_trial"
                )
            ],
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="adm_broadcast"),
                InlineKeyboardButton("📊 Stats", callback_data="adm_stats"),
            ],
            [
                InlineKeyboardButton("✏️ Edit Msg", callback_data="adm_edit_msg"),
                InlineKeyboardButton("🔄 Refresh", callback_data="adm_refresh"),
            ],
            [
                InlineKeyboardButton("🚫 Ban", callback_data="adm_ban"),
                InlineKeyboardButton("✅ Unban", callback_data="adm_unban"),
            ],
        ]
    )


# ==================================================
# ADMIN PANEL
# ==================================================

def admin_panel_text():
    s = load_admin_settings()
    m = s["maintenance"]

    def status(v):
        return "🔴 ON (maintenance)" if v else "🟢 OFF (working)"

    trial_status = "🟢 Enabled" if s.get("trial_enabled", True) else "🔴 Disabled"
    users = load_users()
    banned = s.get("banned_users", [])

    return (
        "╔══════════════════════════════╗\n"
        "     🛡️ *ADMIN CONTROL PANEL*\n"
        "╚══════════════════════════════╝\n\n"

        "🔧 *SERVICE STATUS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 Visit   : {status(m.get('visit', False))}\n"
        f"👑 Prime   : {status(m.get('prime', False))}\n"
        f"🎯 Sensi   : {status(m.get('sensi', False))}\n"
        f"🤖 Bot     : {status(m.get('bot', False))}\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚙️ *SETTINGS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 Free Trial : {trial_status}\n"
        f"👥 Total Users: `{len(users)}`\n"
        f"🚫 Banned     : `{len(banned)}`\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 *Tap buttons to toggle*\n"
        "🔴 = Maintenance ON\n"
        "🟢 = Normal (working)\n"
    )


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ Access Denied.")
        return

    context.user_data.clear()
    await update.message.reply_text(
        admin_panel_text(),
        parse_mode="Markdown",
        reply_markup=admin_keyboard()
    )


async def admin_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔄 Refreshed")
    try:
        await query.edit_message_text(
            admin_panel_text(),
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
    except Exception as e:
        print("refresh err:", e)


async def admin_toggle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "adm_toggle_trial":
        s = load_admin_settings()
        s["trial_enabled"] = not s.get("trial_enabled", True)
        save_admin_settings(s)
        state = "🟢 Enabled" if s["trial_enabled"] else "🔴 Disabled"
        await query.answer(f"Free Trial: {state}")
    else:
        key = data.replace("adm_toggle_", "")
        s = load_admin_settings()
        cur = s["maintenance"].get(key, False)
        s["maintenance"][key] = not cur
        save_admin_settings(s)
        state = "🔴 ON" if not cur else "🟢 OFF"
        await query.answer(f"{key.upper()}: {state}")

    try:
        await query.edit_message_text(
            admin_panel_text(),
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
    except Exception as e:
        print("toggle edit err:", e)


async def admin_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    users = load_users()
    trials = load_trials()
    s = load_admin_settings()

    now = time.time()
    active_trials = sum(1 for t in trials.values() if (now - t) < TRIAL_COOLDOWN)

    text = (
        "╔══════════════════════════════╗\n"
        "        📊 *BOT STATISTICS*\n"
        "╚══════════════════════════════╝\n\n"

        f"👥 Total Users     : `{len(users)}`\n"
        f"🎁 Trial Used (24h): `{active_trials}`\n"
        f"🚫 Banned Users    : `{len(s.get('banned_users', []))}`\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔧 *MAINTENANCE*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 Visit : `{s['maintenance'].get('visit', False)}`\n"
        f"👑 Prime : `{s['maintenance'].get('prime', False)}`\n"
        f"🎯 Sensi : `{s['maintenance'].get('sensi', False)}`\n"
        f"🤖 Bot   : `{s['maintenance'].get('bot', False)}`\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 *Recent Users*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    sorted_users = sorted(users.items(), key=lambda x: x[1].get("last_seen", 0), reverse=True)[:5]
    for uid, info in sorted_users:
        text += f"• `{info.get('name', 'Unknown')}` — `{uid}`\n"

    back_kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back", callback_data="adm_refresh")]]
    )

    try:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_kb)
    except Exception as e:
        print("stats edit err:", e)


async def admin_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_action"] = "broadcast"

    cancel_kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back", callback_data="adm_cancel_action")]]
    )

    try:
        await query.edit_message_text(
            "╔══════════════════════════════╗\n"
            "        📢 *BROADCAST*\n"
            "╚══════════════════════════════╝\n\n"
            "Send the message to broadcast\n"
            "to *all users*.\n\n"
            "_Markdown supported._\n\n"
            "📝 Send your message now:",
            parse_mode="Markdown",
            reply_markup=cancel_kb
        )
    except Exception as e:
        print("broadcast edit err:", e)


async def admin_edit_msg_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_action"] = "edit_msg"

    cancel_kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back", callback_data="adm_cancel_action")]]
    )

    current = load_admin_settings().get("maintenance_msg", "")

    try:
        await query.edit_message_text(
            "╔══════════════════════════════╗\n"
            "     ✏️ *EDIT MAINTENANCE MSG*\n"
            "╚══════════════════════════════╝\n\n"
            "📝 *Current Message:*\n"
            f"_{current}_\n\n"
            "Send your *new message* now:",
            parse_mode="Markdown",
            reply_markup=cancel_kb
        )
    except Exception as e:
        print("edit_msg err:", e)


async def admin_ban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_action"] = "ban"

    cancel_kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back", callback_data="adm_cancel_action")]]
    )

    try:
        await query.edit_message_text(
            "╔══════════════════════════════╗\n"
            "        🚫 *BAN USER*\n"
            "╚══════════════════════════════╝\n\n"
            "Send the *user ID* to ban:",
            parse_mode="Markdown",
            reply_markup=cancel_kb
        )
    except Exception as e:
        print("ban err:", e)


async def admin_unban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_action"] = "unban"

    cancel_kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back", callback_data="adm_cancel_action")]]
    )

    try:
        await query.edit_message_text(
            "╔══════════════════════════════╗\n"
            "        ✅ *UNBAN USER*\n"
            "╚══════════════════════════════╝\n\n"
            "Send the *user ID* to unban:",
            parse_mode="Markdown",
            reply_markup=cancel_kb
        )
    except Exception as e:
        print("unban err:", e)


async def admin_cancel_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Cancelled")
    context.user_data.pop("admin_action", None)

    try:
        await query.edit_message_text(
            admin_panel_text(),
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
    except Exception as e:
        print("cancel action err:", e)


# ==================================================
# ADMIN CALLBACK ROUTER
# ==================================================

async def admin_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    if not query.from_user or query.from_user.id != ADMIN_ID:
        await query.answer("❌ Access Denied.", show_alert=True)
        return

    data = query.data
    print(f"[ADMIN CALLBACK] {data}")

    try:
        if data == "adm_refresh":
            await admin_refresh_callback(update, context)
        elif data.startswith("adm_toggle_"):
            await admin_toggle_callback(update, context)
        elif data == "adm_stats":
            await admin_stats_callback(update, context)
        elif data == "adm_broadcast":
            await admin_broadcast_callback(update, context)
        elif data == "adm_edit_msg":
            await admin_edit_msg_callback(update, context)
        elif data == "adm_ban":
            await admin_ban_callback(update, context)
        elif data == "adm_unban":
            await admin_unban_callback(update, context)
        elif data == "adm_cancel_action":
            await admin_cancel_action_callback(update, context)
        else:
            await query.answer("⚠️ Unknown action")
    except Exception as e:
        print(f"[ADMIN ROUTER ERROR] {repr(e)}")
        try:
            await query.answer(f"❌ Error: {str(e)[:100]}", show_alert=True)
        except Exception:
            pass


# ==================================================
# START / WELCOME
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    add_user(user)

    if is_banned(user.id):
        await update.message.reply_text(
            "🚫 *You are banned from using this bot.*\n\n"
            f"Contact: {SUPPORT_HANDLE}",
            parse_mode="Markdown"
        )
        return

    context.user_data.clear()

    name = user.first_name if user else "User"

    welcome_text = (
        "╔══════════════════════════════╗\n"
        "     ⚡  *R G   V I S I T   B O T*  ⚡\n"
        "╚══════════════════════════════╝\n\n"

        f"👋 *Welcome, {name}!*\n\n"

        "🔥 Free Fire All-in-One Bot\n"
        "⚡ Fast • Reliable • Powerful\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 *FREE TRIAL*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ 1 Free Visit every 24 hours\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👑 *PRIME CHECK — FREE!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Check any player's Prime level\n"
        "✅ 100% Free — unlimited\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 *SENSITIVITY — FREE!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Auto-settings for your device\n"
        "✅ 100% Free — unlimited\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ *IMPORTANT NOTICE* ⚠️\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎮 Visits count hone ke liye tumhe\n"
        "*game ko restart* karna zaroori hai.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 *COMMANDS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🚀 /visit   —  Start visit process\n"
        "👑 /prime   —  Check Prime (FREE)\n"
        "🎯 /sensi   —  Sensitivity (FREE)\n"
        "🛑 /cancel  —  Cancel current process\n"
        "ℹ️ /help    —  How it works\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👨‍💻 Dev     : {DEV_HANDLE}\n"
        f"💬 Support : {SUPPORT_HANDLE}\n"
        f"🔑 Buy Key : {BUY_HANDLE}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "_Ready to boost? Tap below 👇_"
    )

    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=welcome_keyboard()
    )


# ==================================================
# HELP
# ==================================================

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    help_text = (
        "╔══════════════════════════════╗\n"
        "        ℹ️ *HOW IT WORKS*\n"
        "╚══════════════════════════════╝\n\n"

        "🚀 *VISIT*\n"
        "1️⃣ Start Visit\n"
        "2️⃣ UID → Server\n"
        "3️⃣ Trial or paid key\n"
        "4️⃣ Done!\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 *FREE TRIAL*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ 1 request / 24 hours\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👑 *PRIME CHECK (FREE)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Check any player's Prime level\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 *SENSITIVITY (FREE)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Auto-settings for your device\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔑 *PREMIUM KEY*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Up to `{MAX_REQUESTS}` requests\n"
        f"👉 Buy: {BUY_HANDLE}\n\n"

        "⚠️ *Game restart karo visits show karne ke liye*"
    )

    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )


# ==================================================
# CANCEL
# ==================================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["cancelled"] = True
    context.user_data.clear()

    await update.message.reply_text(
        "╔══════════════════════════════╗\n"
        "           🛑 *CANCELLED*\n"
        "╚══════════════════════════════╝\n\n"
        "Process has been stopped.\n\n"
        "👉 /visit to start again",
        parse_mode="Markdown"
    )


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    if not query:
        return

    await query.answer("🛑 Cancelling...")
    context.user_data["cancelled"] = True

    try:
        await query.edit_message_text(
            "╔══════════════════════════════╗\n"
            "           🛑 *CANCELLED*\n"
            "╚══════════════════════════════╝\n\n"
            "Process has been stopped.\n\n"
            "👉 /visit to start again",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
    except Exception:
        pass


# ==================================================
# USER CALLBACK ROUTER
# ==================================================

async def user_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    data = query.data

    if data == "cancel_process":
        await cancel_callback(update, context)
    elif data == "start_visit":
        await start_visit_callback(update, context)
    elif data == "start_prime":
        await start_prime_callback(update, context)
    elif data == "start_sensi":
        await start_sensi_callback(update, context)
    elif data == "use_trial":
        await use_trial_callback(update, context)
    elif data == "back_home":
        await back_home_callback(update, context)
    elif data == "how_it_works":
        await how_it_works_callback(update, context)


# ==================================================
# CALLBACKS
# ==================================================

async def back_home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()
    context.user_data.clear()

    user = query.from_user
    name = user.first_name if user else "User"

    welcome_text = (
        "╔══════════════════════════════╗\n"
        "     ⚡  *R G   V I S I T   B O T*  ⚡\n"
        "╚══════════════════════════════╝\n\n"
        f"👋 *Welcome back, {name}!*\n\n"
        "🎁 Free Trial: 1 request / 24 hours\n"
        "👑 Prime Check: 100% FREE\n"
        "🎯 Sensitivity: 100% FREE\n"
        f"🔑 Buy Premium: {BUY_HANDLE}\n\n"
        "_Tap below to continue 👇_"
    )

    try:
        await query.edit_message_text(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=welcome_keyboard()
        )
    except Exception:
        pass


async def how_it_works_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    help_text = (
        "╔══════════════════════════════╗\n"
        "        ℹ️ *HOW IT WORKS*\n"
        "╚══════════════════════════════╝\n\n"
        "🚀 *VISIT* — UID → Server → Key\n"
        "👑 *PRIME* — UID → Server (FREE)\n"
        "🎯 *SENSI* — Device Name (FREE)\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 Buy Premium: {BUY_HANDLE}\n"
        f"💬 Support: {SUPPORT_HANDLE}\n\n"
        "⚠️ *Game restart karo*"
    )

    try:
        await query.edit_message_text(
            help_text,
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
    except Exception:
        pass


async def start_visit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    add_user(query.from_user)

    if is_banned(query.from_user.id):
        await query.answer("🚫 You are banned!", show_alert=True)
        return

    mt, msg = is_maintenance("visit")
    if mt and query.from_user.id != ADMIN_ID:
        await query.answer("🔧 Visit under maintenance", show_alert=True)
        return

    await query.answer()
    context.user_data.clear()
    context.user_data["step"] = "uid"
    context.user_data["cancelled"] = False

    try:
        await query.edit_message_text(
            "╔══════════════════════════════╗\n"
            "        🆔 *STEP 1 / 3*\n"
            "╚══════════════════════════════╝\n\n"
            "Enter your *Free Fire UID*:\n\n"
            "📌 Example: `1234567890`",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
    except Exception:
        pass


async def start_prime_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    add_user(query.from_user)

    if is_banned(query.from_user.id):
        await query.answer("🚫 You are banned!", show_alert=True)
        return

    mt, msg = is_maintenance("prime")
    if mt and query.from_user.id != ADMIN_ID:
        await query.answer("🔧 Prime Check under maintenance", show_alert=True)
        return

    await query.answer()
    context.user_data.clear()
    context.user_data["prime_step"] = "uid"

    try:
        await query.edit_message_text(
            "╔══════════════════════════════╗\n"
            "        👑 *PRIME CHECK*\n"
            "╚══════════════════════════════╝\n\n"
            "🎉 *100% FREE — No Key Needed!*\n\n"
            "Enter your *Free Fire UID*:\n\n"
            "📌 Example: `1234567890`",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
    except Exception:
        pass


async def start_sensi_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    add_user(query.from_user)

    if is_banned(query.from_user.id):
        await query.answer("🚫 You are banned!", show_alert=True)
        return

    mt, msg = is_maintenance("sensi")
    if mt and query.from_user.id != ADMIN_ID:
        await query.answer("🔧 Sensitivity under maintenance", show_alert=True)
        return

    await query.answer()
    context.user_data.clear()
    context.user_data["sensi_step"] = "device"

    try:
        await query.edit_message_text(
            "╔══════════════════════════════╗\n"
            "      🎯 *SENSITIVITY GENERATOR*\n"
            "╚══════════════════════════════╝\n\n"
            "🎉 *100% FREE — No Key Needed!*\n\n"
            "Enter your *Device Name*:\n\n"
            "📌 Examples:\n"
            "• `Samsung Galaxy A12`\n"
            "• `Redmi Note 11`\n"
            "• `iPhone 13`\n"
            "• `POCO X3 Pro`",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
    except Exception:
        pass


# ==================================================
# COMMANDS
# ==================================================

async def prime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user)

    if is_banned(update.effective_user.id):
        await update.message.reply_text("🚫 You are banned.")
        return

    mt, msg = is_maintenance("prime")
    if mt and not is_admin(update):
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    context.user_data.clear()
    context.user_data["prime_step"] = "uid"

    await update.message.reply_text(
        "╔══════════════════════════════╗\n"
        "        👑 *PRIME CHECK*\n"
        "╚══════════════════════════════╝\n\n"
        "🎉 *100% FREE — No Key Needed!*\n\n"
        "Enter your *Free Fire UID*:\n\n"
        "📌 Example: `1234567890`",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )


async def sensi_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user)

    if is_banned(update.effective_user.id):
        await update.message.reply_text("🚫 You are banned.")
        return

    mt, msg = is_maintenance("sensi")
    if mt and not is_admin(update):
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    context.user_data.clear()
    context.user_data["sensi_step"] = "device"

    await update.message.reply_text(
        "╔══════════════════════════════╗\n"
        "      🎯 *SENSITIVITY GENERATOR*\n"
        "╚══════════════════════════════╝\n\n"
        "🎉 *100% FREE — No Key Needed!*\n\n"
        "Enter your *Device Name*:\n\n"
        "📌 Examples:\n"
        "• `Samsung Galaxy A12`\n"
        "• `Redmi Note 11`\n"
        "• `iPhone 13`\n"
        "• `POCO X3 Pro`",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )


async def visit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user)

    if is_banned(update.effective_user.id):
        await update.message.reply_text("🚫 You are banned.")
        return

    mt, msg = is_maintenance("visit")
    if mt and not is_admin(update):
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    context.user_data.clear()
    context.user_data["step"] = "uid"
    context.user_data["cancelled"] = False

    await update.message.reply_text(
        "╔══════════════════════════════╗\n"
        "        🆔 *STEP 1 / 3*\n"
        "╚══════════════════════════════╝\n\n"
        "Enter your *Free Fire UID*:\n\n"
        "📌 Example: `1234567890`",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )


# ==================================================
# USE TRIAL
# ==================================================

async def use_trial_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not is_trial_enabled() and query.from_user.id != ADMIN_ID:
        await query.answer("🎁 Free trial is disabled by admin", show_alert=True)
        return

    user_id = query.from_user.id
    allowed, remaining = can_use_trial(user_id)

    if not allowed:
        if remaining == "disabled":
            await query.answer("🎁 Free trial disabled", show_alert=True)
            return
        hours, minutes = remaining
        await query.answer(
            f"⏳ Trial used!\nWait {hours}h {minutes}m",
            show_alert=True
        )
        return

    await query.answer("🎁 Trial activated!")

    context.user_data["key"] = TRIAL_KEY
    context.user_data["requests"] = TRIAL_REQUESTS
    context.user_data["is_trial"] = True

    mark_trial_used(user_id)

    try:
        await query.edit_message_text(
            "╔══════════════════════════════╗\n"
            "     🎁 *FREE TRIAL ACTIVATED*\n"
            "╚══════════════════════════════╝\n\n"
            "✅ Trial key accepted\n"
            "📦 Requests: `1`\n\n"
            "⏳ Starting process...",
            parse_mode="Markdown"
        )
    except Exception:
        pass

    await run_visit_process_from_callback(query, context)


# ==================================================
# MESSAGE HANDLER
# ==================================================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    user = update.effective_user
    add_user(user)

    if is_banned(user.id):
        await update.message.reply_text("🚫 You are banned.")
        return

    text = update.message.text.strip()

    # ----------------------------------------------
    # ADMIN ACTIONS
    # ----------------------------------------------
    admin_action = context.user_data.get("admin_action")

    if admin_action and user.id == ADMIN_ID:
        if admin_action == "broadcast":
            context.user_data.pop("admin_action", None)
            await broadcast_message(update, context, text)
            return
        elif admin_action == "edit_msg":
            context.user_data.pop("admin_action", None)
            s = load_admin_settings()
            s["maintenance_msg"] = text
            save_admin_settings(s)
            await update.message.reply_text(
                "✅ *Maintenance message updated!*",
                parse_mode="Markdown",
                reply_markup=admin_keyboard()
            )
            return
        elif admin_action == "ban":
            context.user_data.pop("admin_action", None)
            await handle_ban(update, context, text)
            return
        elif admin_action == "unban":
            context.user_data.pop("admin_action", None)
            await handle_unban(update, context, text)
            return

    # ----------------------------------------------
    # PRIME FLOW
    # ----------------------------------------------
    if context.user_data.get("prime_step") == "uid":
        mt, msg = is_maintenance("prime")
        if mt and not is_admin(update):
            await update.message.reply_text(msg, parse_mode="Markdown")
            return
        context.user_data["prime_uid"] = text
        context.user_data["prime_step"] = "server"
        await update.message.reply_text(
            "╔══════════════════════════════╗\n"
            "        🌐 *PRIME SERVER*\n"
            "╚══════════════════════════════╝\n\n"
            "Enter your *Server Region*:\n\n"
            "📌 Examples: `IND`  `BD`  `PK`  `SG`",
            parse_mode="Markdown"
        )
        return

    elif context.user_data.get("prime_step") == "server":
        context.user_data["prime_server"] = text.upper()
        context.user_data["prime_step"] = None
        await run_prime_check(update, context)
        return

    # ----------------------------------------------
    # SENSI FLOW
    # ----------------------------------------------
    if context.user_data.get("sensi_step") == "device":
        mt, msg = is_maintenance("sensi")
        if mt and not is_admin(update):
            await update.message.reply_text(msg, parse_mode="Markdown")
            return
        context.user_data["sensi_device"] = text
        context.user_data["sensi_step"] = None
        await run_sensi_generator(update, context)
        return

    # ----------------------------------------------
    # VISIT FLOW
    # ----------------------------------------------
    step = context.user_data.get("step")

    if step == "uid":
        mt, msg = is_maintenance("visit")
        if mt and not is_admin(update):
            await update.message.reply_text(msg, parse_mode="Markdown")
            return
        context.user_data["uid"] = text
        context.user_data["step"] = "server"
        await update.message.reply_text(
            "╔══════════════════════════════╗\n"
            "        🌐 *STEP 2 / 3*\n"
            "╚══════════════════════════════╝\n\n"
            "Enter your *Server Region*:\n\n"
            "📌 Examples: `IND`  `BD`  `PK`  `SG`",
            parse_mode="Markdown"
        )

    elif step == "server":
        context.user_data["server"] = text.upper()
        context.user_data["step"] = "key"

        user_id = update.effective_user.id
        allowed, remaining = can_use_trial(user_id)

        if remaining == "disabled":
            trial_status = "🔴 *Disabled by admin*"
        elif allowed:
            trial_status = "✅ *Available* — tap below to use"
        else:
            hours, minutes = remaining
            trial_status = f"⏳ Next trial in: `{hours}h {minutes}m`"

        await update.message.reply_text(
            "╔══════════════════════════════╗\n"
            "        🔑 *STEP 3 / 3*\n"
            "╚══════════════════════════════╝\n\n"
            "Enter your *API Key*:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎁 *FREE TRIAL STATUS*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{trial_status}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 Buy premium: {BUY_HANDLE}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown",
            reply_markup=trial_or_key_keyboard()
        )

    elif step == "key":
        context.user_data["key"] = text

        if text.strip() == TRIAL_KEY:
            if not is_trial_enabled() and not is_admin(update):
                await update.message.reply_text(
                    "🎁 *Free trial is currently disabled.*",
                    parse_mode="Markdown"
                )
                return

            user_id = update.effective_user.id
            allowed, remaining = can_use_trial(user_id)

            if not allowed:
                if remaining == "disabled":
                    await update.message.reply_text(
                        "🎁 *Free trial is disabled.*",
                        parse_mode="Markdown"
                    )
                    return
                hours, minutes = remaining
                await update.message.reply_text(
                    "╔══════════════════════════════╗\n"
                    "        ⏳ *TRIAL COOLDOWN*\n"
                    "╚══════════════════════════════╝\n\n"
                    f"Next trial in: `{hours}h {minutes}m`\n\n"
                    f"🔑 Buy premium: {BUY_HANDLE}",
                    parse_mode="Markdown",
                    reply_markup=again_keyboard()
                )
                context.user_data.clear()
                return

            mark_trial_used(user_id)
            context.user_data["requests"] = TRIAL_REQUESTS
            context.user_data["is_trial"] = True
            await run_visit_process(update, context)
            return

        context.user_data["is_trial"] = False
        context.user_data["step"] = "requests"

        await update.message.reply_text(
            "╔══════════════════════════════╗\n"
            "        🔢 *REQUESTS COUNT*\n"
            "╚══════════════════════════════╝\n\n"
            "How many requests to send?\n\n"
            f"📦 Minimum: `1`\n"
            f"📦 Maximum: `{MAX_REQUESTS}`",
            parse_mode="Markdown"
        )

    elif step == "requests":
        try:
            requests_count = int(text)
        except ValueError:
            await update.message.reply_text(
                "❌ *Invalid input!*", parse_mode="Markdown"
            )
            return
        if requests_count < 1 or requests_count > MAX_REQUESTS:
            await update.message.reply_text(
                f"❌ *Range: 1 - {MAX_REQUESTS}*", parse_mode="Markdown"
            )
            return
        context.user_data["requests"] = requests_count
        await run_visit_process(update, context)


# ==================================================
# BROADCAST / BAN / UNBAN
# ==================================================

async def broadcast_message(update, context, text):
    users = load_users()
    total = len(users)
    sent = 0
    failed = 0

    status_msg = await update.message.reply_text(
        f"📢 *Broadcasting...*\n\n"
        f"👥 Total: `{total}`\n"
        f"✅ Sent: `0`\n"
        f"❌ Failed: `0`",
        parse_mode="Markdown"
    )

    for uid in list(users.keys()):
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=text,
                parse_mode="Markdown"
            )
            sent += 1
        except Exception:
            failed += 1

        if (sent + failed) % 10 == 0:
            try:
                await status_msg.edit_text(
                    f"📢 *Broadcasting...*\n\n"
                    f"👥 Total: `{total}`\n"
                    f"✅ Sent: `{sent}`\n"
                    f"❌ Failed: `{failed}`",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

        await asyncio.sleep(0.05)

    try:
        await status_msg.edit_text(
            f"✅ *Broadcast Complete!*\n\n"
            f"👥 Total: `{total}`\n"
            f"✅ Sent: `{sent}`\n"
            f"❌ Failed: `{failed}`",
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
    except Exception:
        pass


async def handle_ban(update, context, text):
    try:
        uid = int(text.strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return

    s = load_admin_settings()
    banned = s.get("banned_users", [])
    if str(uid) not in banned:
        banned.append(str(uid))
    s["banned_users"] = banned
    save_admin_settings(s)

    await update.message.reply_text(
        f"🚫 *User banned:* `{uid}`",
        parse_mode="Markdown",
        reply_markup=admin_keyboard()
    )


async def handle_unban(update, context, text):
    try:
        uid = int(text.strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return

    s = load_admin_settings()
    banned = s.get("banned_users", [])
    if str(uid) in banned:
        banned.remove(str(uid))
    s["banned_users"] = banned
    save_admin_settings(s)

    await update.message.reply_text(
        f"✅ *User unbanned:* `{uid}`",
        parse_mode="Markdown",
        reply_markup=admin_keyboard()
    )


# ==================================================
# PRIME CHECK
# ==================================================

async def run_prime_check(update, context):

    uid = context.user_data.get("prime_uid", "")
    server = context.user_data.get("prime_server", "")

    status_msg = await update.message.reply_text(
        "╔══════════════════════════════╗\n"
        "     👑 *CHECKING PRIME...*\n"
        "╚══════════════════════════════╝\n\n"
        f"🆔 UID    : `{uid}`\n"
        f"🌐 Server : `{server}`\n\n"
        "⏳ Please wait...",
        parse_mode="Markdown"
    )

    try:
        timeout = aiohttp.ClientTimeout(total=25)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.freefiremania.com.br/paginas/nivel-prime-check.php",
            "Origin": "https://www.freefiremania.com.br",
            "Accept": "application/json, text/plain, */*",
        }

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                PRIME_API_URL,
                data={"id": uid, "region": server.lower()},
                headers=headers
            ) as response:
                raw_text = await response.text()
                print(f"\n[PRIME] HTTP {response.status}\n{raw_text}")

                if response.status != 200:
                    await status_msg.edit_text(
                        f"❌ *Prime Check Failed*\nHTTP: `{response.status}`",
                        parse_mode="Markdown",
                        reply_markup=prime_again_keyboard()
                    )
                    context.user_data.clear()
                    return

                try:
                    data = json.loads(raw_text)
                except Exception:
                    data = {"raw": raw_text}

                if not data.get("ok", False):
                    await status_msg.edit_text(
                        "❌ *Player not found*\nInvalid UID/Region.",
                        parse_mode="Markdown",
                        reply_markup=prime_again_keyboard()
                    )
                    context.user_data.clear()
                    return

                nickname = data.get("nickname", "Unknown")
                region = data.get("region", server).upper()
                prime_info = data.get("prime", {}) or {}
                prime_level = prime_info.get("level", 0)
                prime_label = prime_info.get("label", "N/A")

                diamonds_req = format_diamonds(
                    prime_info.get("diamonds_required_formatted", "N/A")
                )
                level_desc = translate_prime_text(
                    prime_info.get("level_description", "N/A")
                )
                benefits = prime_info.get("level_benefits", [])
                benefits_en = [translate_prime_text(b) for b in benefits]
                benefits_text = (
                    "\n".join([f"  ✦ {b}" for b in benefits_en])
                    if benefits_en else "  • None"
                )

                badge = "👑" if prime_level >= 8 else ("💎" if prime_level >= 5 else "⭐")

                final_text = (
                    "╔══════════════════════════════╗\n"
                    "      👑 *PRIME CHECK RESULT*\n"
                    "╚══════════════════════════════╝\n\n"
                    "👤 *Player Info*\n"
                    f"├ 🆔 UID    : `{uid}`\n"
                    f"├ 👤 Name   : `{nickname}`\n"
                    f"└ 🌐 Region : `{region}`\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "👑 *PRIME STATUS*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{badge} *Level*    : `{prime_label}` (Lv. `{prime_level}`)\n"
                    f"💎 *Diamonds* : `{diamonds_req}`\n\n"
                    "🎁 *Benefits*\n"
                    f"{benefits_text}\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "📖 *Description*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"_{level_desc}_\n\n"
                    f"👨‍💻 {DEV_HANDLE}  |  💬 {SUPPORT_HANDLE}\n\n"
                    "_Powered by RG Visit Bot ⚡_"
                )

                if len(final_text) > 4000:
                    final_text = final_text[:4000] + "..."

                await status_msg.edit_text(
                    final_text,
                    parse_mode="Markdown",
                    reply_markup=prime_again_keyboard()
                )

    except asyncio.TimeoutError:
        try:
            await status_msg.edit_text(
                "⏱️ *Timeout*\nPlease try again.",
                parse_mode="Markdown",
                reply_markup=prime_again_keyboard()
            )
        except Exception:
            pass
    except Exception as e:
        print(f"[PRIME EXCEPTION] {repr(e)}")
        try:
            await status_msg.edit_text(
                f"❌ *Error*\n`{str(e)[:100]}`",
                parse_mode="Markdown",
                reply_markup=prime_again_keyboard()
            )
        except Exception:
            pass

    context.user_data.clear()


# ==================================================
# SENSITIVITY
# ==================================================

async def run_sensi_generator(update, context):

    device = context.user_data.get("sensi_device", "")

    status_msg = await update.message.reply_text(
        "╔══════════════════════════════╗\n"
        "   🎯 *GENERATING SENSITIVITY...*\n"
        "╚══════════════════════════════╝\n\n"
        f"📱 Device : `{device}`\n\n"
        "⏳ Please wait...",
        parse_mode="Markdown"
    )

    try:
        timeout = aiohttp.ClientTimeout(total=25)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.freefiremania.com.br/paginas/gerar-sensibilidade.php",
            "Origin": "https://www.freefiremania.com.br",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                SENSI_API_URL,
                json={"device": device, "dpiMode": "sem"},
                headers=headers
            ) as response:
                raw_text = await response.text()
                print(f"\n[SENSI] HTTP {response.status}\n{raw_text}")

                if response.status != 200:
                    await status_msg.edit_text(
                        f"❌ *Sensi Failed*\nHTTP: `{response.status}`",
                        parse_mode="Markdown",
                        reply_markup=sensi_again_keyboard()
                    )
                    context.user_data.clear()
                    return

                try:
                    data = json.loads(raw_text)
                except Exception:
                    data = {"raw": raw_text}

                dev = data.get("device", device)
                dpi = data.get("dpi", "N/A")
                is_fallback = data.get("isFallback", False)
                matched = data.get("matchedDevice", None)

                geral = data.get("geral", 0)
                red_dot = data.get("redDot", 0)
                scope2x = data.get("scope2x", 0)
                scope4x = data.get("scope4x", 0)
                sniper = data.get("sniper", 0)
                free_look = data.get("freeLook", 0)

                match_badge = "⚠️ *Approximate*" if is_fallback else "✅ *Exact match*"
                matched_line = f"🔍 Matched : `{matched}`\n" if matched else ""

                final_text = (
                    "╔══════════════════════════════╗\n"
                    "    🎯 *SENSITIVITY GENERATED*\n"
                    "╚══════════════════════════════╝\n\n"
                    "📱 *Device Info*\n"
                    f"├ 📱 Device  : `{dev}`\n"
                    f"├ 📐 DPI     : `{dpi}`\n"
                    f"{matched_line}"
                    f"└ 🎯 Match   : {match_badge}\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "⚙️ *SENSITIVITY SETTINGS*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🎯 *General*   : `{geral}`\n"
                    f"🔴 *Red Dot*   : `{red_dot}`\n"
                    f"🔭 *2x Scope*  : `{scope2x}`\n"
                    f"🔭 *4x Scope*  : `{scope4x}`\n"
                    f"🎯 *Sniper*    : `{sniper}`\n"
                    f"👁️ *Free Look* : `{free_look}`\n\n"
                    f"👨‍💻 {DEV_HANDLE}  |  💬 {SUPPORT_HANDLE}\n\n"
                    "_Powered by RG Visit Bot ⚡_"
                )

                if len(final_text) > 4000:
                    final_text = final_text[:4000] + "..."

                await status_msg.edit_text(
                    final_text,
                    parse_mode="Markdown",
                    reply_markup=sensi_again_keyboard()
                )

    except asyncio.TimeoutError:
        try:
            await status_msg.edit_text(
                "⏱️ *Timeout*\nPlease try again.",
                parse_mode="Markdown",
                reply_markup=sensi_again_keyboard()
            )
        except Exception:
            pass
    except Exception as e:
        print(f"[SENSI EXCEPTION] {repr(e)}")
        try:
            await status_msg.edit_text(
                f"❌ *Error*\n`{str(e)[:100]}`",
                parse_mode="Markdown",
                reply_markup=sensi_again_keyboard()
            )
        except Exception:
            pass

    context.user_data.clear()


# ==================================================
# VISIT PROCESS
# ==================================================

async def run_visit_process_from_callback(query, context):
    uid = context.user_data.get("uid", "")
    server = context.user_data.get("server", "")
    key = context.user_data.get("key", "")
    total_requests = context.user_data.get("requests", 1)
    is_trial = context.user_data.get("is_trial", False)

    context.user_data["cancelled"] = False

    message = await query.message.reply_text(
        "🚀 *Starting...*", parse_mode="Markdown"
    )
    await _run_loop(message, context, uid, server, key, total_requests, is_trial)


async def run_visit_process(update, context):
    uid = context.user_data["uid"]
    server = context.user_data["server"]
    key = context.user_data["key"]
    total_requests = context.user_data["requests"]
    is_trial = context.user_data.get("is_trial", False)

    context.user_data["cancelled"] = False

    message = await update.message.reply_text(
        "🚀 *Starting...*", parse_mode="Markdown"
    )
    await _run_loop(message, context, uid, server, key, total_requests, is_trial)


async def _run_loop(message, context, uid, server, key, total_requests, is_trial):

    total_visits = 0
    successful = 0
    failed = 0
    last_player_name = "---"
    last_visit_count = 0

    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i in range(1, total_requests + 1):

            if context.user_data.get("cancelled"):
                try:
                    await message.edit_text(
                        "🛑 *CANCELLED*\n\n"
                        f"✅ `{successful}` | ❌ `{failed}` | 🔥 `{total_visits:,}`",
                        parse_mode="Markdown",
                        reply_markup=again_keyboard()
                    )
                except Exception:
                    pass
                context.user_data.clear()
                return

            try:
                async with session.get(
                    API_URL,
                    params={"uid": uid, "server_name": server, "key": key}
                ) as response:
                    raw_text = await response.text()
                    print(f"\n[VISIT {i}/{total_requests}] HTTP {response.status}\n{raw_text}")

                    if response.status != 200:
                        failed += 1
                    else:
                        try:
                            data = json.loads(raw_text)
                        except Exception:
                            data = {"raw": raw_text}
                        visit_count = int(data.get("VisitCount", 0) or 0)
                        total_visits += visit_count
                        successful += 1
                        last_player_name = data.get("PlayerName", "Unknown")
                        last_visit_count = visit_count
            except Exception as e:
                failed += 1
                print(f"[EXC] {repr(e)}")

            percent = int((i / total_requests) * 100)
            filled = int(percent / 10)
            bar = "█" * filled + "░" * (10 - filled)

            try:
                await message.edit_text(
                    "╔══════════════════════════════╗\n"
                    "      ⚡ *RG VISIT RUNNING*\n"
                    "╚══════════════════════════════╝\n\n"
                    f"🆔 UID    : `{uid}`\n"
                    f"👤 Player : `{last_player_name}`\n"
                    f"🌐 Server : `{server}`\n\n"
                    f"`{bar}` {percent}%\n\n"
                    f"📦 Requests : `{i}/{total_requests}`\n"
                    f"📊 Visits   : `{total_visits:,}`\n"
                    f"✅ Success  : `{successful}`\n"
                    f"❌ Failed   : `{failed}`",
                    parse_mode="Markdown",
                    reply_markup=cancel_keyboard()
                )
            except Exception:
                pass

            await asyncio.sleep(0.2)

    if is_trial:
        footer = (
            "🎁 *FREE TRIAL USED*\n"
            "✅ Next trial in: `24 hours`\n"
            f"🔑 Unlimited: {BUY_HANDLE}\n\n"
        )
    else:
        footer = (
            "🔑 *PREMIUM KEY USER*\n"
            f"💎 Thanks for supporting!\n\n"
        )

    try:
        await message.edit_text(
            "╔══════════════════════════════╗\n"
            "    🏁 *PROCESS COMPLETED*\n"
            "╚══════════════════════════════╝\n\n"
            "👤 *Player Info*\n"
            f"├ 🆔 UID    : `{uid}`\n"
            f"├ 👤 Name   : `{last_player_name}`\n"
            f"└ 🌐 Server : `{server}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📊 *SUMMARY*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📦 Total Requests : `{total_requests}`\n"
            f"✅ Successful     : `{successful}`\n"
            f"❌ Failed         : `{failed}`\n"
            f"📈 Last Visit     : `+{last_visit_count}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 *TOTAL VISITS : {total_visits:,}* 🔥\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ *Game ko restart karo* 🎮\n\n"
            f"{footer}"
            f"👨‍💻 {DEV_HANDLE}  |  💬 {SUPPORT_HANDLE}\n\n"
            "_Thanks for using RG Visit Bot ⚡_",
            parse_mode="Markdown",
            reply_markup=again_keyboard()
        )
    except Exception as e:
        print("Final edit error:", e)

    context.user_data.clear()


# ==================================================
# ERROR HANDLER
# ==================================================

async def error_handler(update, context):
    print("ERROR:", context.error)


# ==================================================
# MAINTENANCE MIDDLEWARE
# ==================================================

async def maintenance_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return

    if update.effective_user.id == ADMIN_ID:
        return

    if update.message and update.message.text and update.message.text.startswith("/start"):
        return

    if update.callback_query and update.callback_query.data == "back_home":
        return

    settings = load_admin_settings()
    if settings["maintenance"].get("bot", False):
        if update.callback_query:
            await update.callback_query.answer(
                "🔧 Bot under maintenance",
                show_alert=True
            )
        elif update.message:
            await update.message.reply_text(
                settings.get("maintenance_msg", "Under maintenance"),
                parse_mode="Markdown"
            )
        raise Exception("Bot in maintenance — blocked")


# ==================================================
# MAIN
# ==================================================

def main():

    print("====================================")
    print("       RG VISIT BOT v3")
    print("====================================")
    print("Bot starting...")

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.StatusUpdate.ALL,
            maintenance_middleware
        ),
        group=-1
    )
    application.add_handler(
        CallbackQueryHandler(maintenance_middleware),
        group=-1
    )

    application.add_handler(CommandHandler("admin", admin_cmd))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("visit", visit))
    application.add_handler(CommandHandler("prime", prime_cmd))
    application.add_handler(CommandHandler("sensi", sensi_cmd))
    application.add_handler(CommandHandler("cancel", cancel))

    application.add_handler(
        CallbackQueryHandler(admin_callback_router, pattern="^adm_")
    )

    application.add_handler(
        CallbackQueryHandler(user_callback_router)
    )

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )

    application.add_error_handler(error_handler)

    print("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
