import asyncio
import json
import time
import os
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

MAX_REQUESTS = 100

# Free Trial Key (1 request per 24 hours per user)
TRIAL_KEY = "RG_iCjEouu1jxYLQTLbIfSuQ6Rf"
TRIAL_COOLDOWN = 24 * 60 * 60  # seconds
TRIAL_REQUESTS = 1

# Handles
DEV_HANDLE = "@rgdev404"
SUPPORT_HANDLE = "@rgdev404"
BUY_HANDLE = "@rgdev404"

# Trial data file
TRIAL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trial_usage.json")


# ==================================================
# HELPERS
# ==================================================

def is_admin(update: Update):
    return update.effective_user and update.effective_user.id == ADMIN_ID


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
                InlineKeyboardButton("🔑 Buy Key", url=f"https://t.me/{BUY_HANDLE.lstrip('@')}"),
                InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_HANDLE.lstrip('@')}")
            ]
        ]
    )


def back_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back", callback_data="back_home")]]
    )


# ==================================================
# START / WELCOME
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    user = update.effective_user
    name = user.first_name if user else "User"

    welcome_text = (
        "╔══════════════════════════════╗\n"
        "     ⚡  *R G   V I S I T   B O T*  ⚡\n"
        "╚══════════════════════════════╝\n\n"

        f"👋 *Welcome, {name}!*\n\n"

        "🔥 Free Fire Visit Booster\n"
        "⚡ Fast • Reliable • Powerful\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 *FREE TRIAL AVAILABLE*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "✅ *1 Free Request every 24 hours*\n"
        "🔑 *Buy premium key for unlimited*\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ *IMPORTANT NOTICE* ⚠️\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "🎮 Visits count hone ke liye tumhe\n"
        "*game ko restart* karna zaroori hai.\n\n"

        "➡️ Restart karne ke baad hi visits\n"
        "   profile pe show honge.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 *COMMANDS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "🚀 /visit   —  Start visit process\n"
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

        "📌 *STEPS*\n\n"

        "1️⃣ Tap *🚀 Start Visit*\n"
        "2️⃣ Enter your Free Fire UID\n"
        "3️⃣ Enter server (e.g. IND / BD / PK)\n"
        "4️⃣ Use *Free Trial* OR enter paid key\n"
        "5️⃣ Sit back — visits will be sent!\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 *FREE TRIAL*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "✅ 1 request per 24 hours\n"
        "✅ No key needed — just tap the button\n"
        "⏳ Wait 24h to use again\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔑 *PREMIUM KEY*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        f"📦 Up to `{MAX_REQUESTS}` requests per run\n"
        "⚡ No cooldown\n"
        "💎 Full access\n\n"

        f"👉 Buy from: {BUY_HANDLE}\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ *REMINDER*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "🎮 Game restart karo\n"
        "   visit show karne ke liye\n\n"

        f"💬 Support: {SUPPORT_HANDLE}"
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


# ==================================================
# CALLBACK: CANCEL
# ==================================================

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
# CALLBACK: BACK HOME
# ==================================================

async def back_home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    if not query:
        return

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


# ==================================================
# CALLBACK: HOW IT WORKS
# ==================================================

async def how_it_works_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    if not query:
        return

    await query.answer()

    help_text = (
        "╔══════════════════════════════╗\n"
        "        ℹ️ *HOW IT WORKS*\n"
        "╚══════════════════════════════╝\n\n"

        "📌 *STEPS*\n\n"
        "1️⃣ Tap *🚀 Start Visit*\n"
        "2️⃣ Enter Free Fire UID\n"
        "3️⃣ Enter server (IND/BD/PK)\n"
        "4️⃣ Use *Free Trial* or paid key\n"
        "5️⃣ Sit back — visits sent!\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 *FREE TRIAL*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ 1 request / 24 hours\n"
        "✅ No key needed\n"
        "⏳ Cooldown: 24 hours\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔑 *PREMIUM KEY*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 Up to `{MAX_REQUESTS}` requests\n"
        "⚡ No cooldown\n"
        "💎 Full access\n\n"
        f"👉 Buy: {BUY_HANDLE}\n\n"

        "⚠️ *Game restart karo visit show karne ke liye*"
    )

    try:
        await query.edit_message_text(
            help_text,
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
    except Exception:
        pass


# ==================================================
# CALLBACK: START VISIT
# ==================================================

async def start_visit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    if not query:
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


# ==================================================
# CALLBACK: USE TRIAL
# ==================================================

async def use_trial_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    if not query:
        return

    user_id = query.from_user.id

    # Check cooldown
    allowed, remaining = can_use_trial(user_id)

    if not allowed:
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

    # Mark as used
    mark_trial_used(user_id)

    # Send processing start message
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

    # Run process
    await run_visit_process_from_callback(query, context)


# ==================================================
# VISIT COMMAND
# ==================================================

async def visit(update: Update, context: ContextTypes.DEFAULT_TYPE):

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
# MESSAGE HANDLER
# ==================================================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    step = context.user_data.get("step")

    # ----------------------------------------------
    # UID
    # ----------------------------------------------
    if step == "uid":

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

    # ----------------------------------------------
    # SERVER → ask key/trial
    # ----------------------------------------------
    elif step == "server":

        context.user_data["server"] = text.upper()
        context.user_data["step"] = "key"

        user_id = update.effective_user.id
        allowed, remaining = can_use_trial(user_id)

        if allowed:
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

    # ----------------------------------------------
    # API KEY
    # ----------------------------------------------
    elif step == "key":

        context.user_data["key"] = text

        # Check if trial key typed manually
        if text.strip() == TRIAL_KEY:

            user_id = update.effective_user.id
            allowed, remaining = can_use_trial(user_id)

            if not allowed:
                hours, minutes = remaining
                await update.message.reply_text(
                    "╔══════════════════════════════╗\n"
                    "        ⏳ *TRIAL COOLDOWN*\n"
                    "╚══════════════════════════════╝\n\n"
                    f"You can use the free trial again in:\n\n"
                    f"🕐 `{hours}h {minutes}m`\n\n"
                    f"🔑 Buy premium key from {BUY_HANDLE}\n"
                    "   for unlimited access!",
                    parse_mode="Markdown",
                    reply_markup=again_keyboard()
                )
                context.user_data.clear()
                return

            # Trial allowed
            mark_trial_used(user_id)
            context.user_data["requests"] = TRIAL_REQUESTS
            context.user_data["is_trial"] = True

            await run_visit_process(update, context)
            return

        # Paid key flow — ask request count
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

    # ----------------------------------------------
    # REQUEST COUNT
    # ----------------------------------------------
    elif step == "requests":

        try:
            requests_count = int(text)
        except ValueError:
            await update.message.reply_text(
                "❌ *Invalid input!*\n\nEnter a valid number.",
                parse_mode="Markdown"
            )
            return

        if requests_count < 1:
            await update.message.reply_text(
                "❌ *Too small!*\n\nMinimum: `1`",
                parse_mode="Markdown"
            )
            return

        if requests_count > MAX_REQUESTS:
            await update.message.reply_text(
                f"❌ *Too large!*\n\nMaximum: `{MAX_REQUESTS}`",
                parse_mode="Markdown"
            )
            return

        context.user_data["requests"] = requests_count
        await run_visit_process(update, context)


# ==================================================
# PROCESS — from callback (trial button)
# ==================================================

async def run_visit_process_from_callback(query, context):

    uid = context.user_data.get("uid", "")
    server = context.user_data.get("server", "")
    key = context.user_data.get("key", "")
    total_requests = context.user_data.get("requests", 1)
    is_trial = context.user_data.get("is_trial", False)

    context.user_data["cancelled"] = False

    message = await query.message.reply_text(
        "╔══════════════════════════════╗\n"
        "     🚀 *PROCESS STARTED*\n"
        "╚══════════════════════════════╝\n\n"
        f"🆔 UID    : `{uid}`\n"
        f"🌐 Server : `{server}`\n"
        f"📦 Total  : `{total_requests}`\n\n"
        f"⏳ Progress: 0%",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )

    await _run_loop(message, context, uid, server, key, total_requests, is_trial)


# ==================================================
# PROCESS — from message
# ==================================================

async def run_visit_process(update, context):

    uid = context.user_data["uid"]
    server = context.user_data["server"]
    key = context.user_data["key"]
    total_requests = context.user_data["requests"]
    is_trial = context.user_data.get("is_trial", False)

    context.user_data["cancelled"] = False

    message = await update.message.reply_text(
        "╔══════════════════════════════╗\n"
        "     🚀 *PROCESS STARTED*\n"
        "╚══════════════════════════════╝\n\n"
        f"🆔 UID    : `{uid}`\n"
        f"🌐 Server : `{server}`\n"
        f"📦 Total  : `{total_requests}`\n\n"
        f"⏳ Progress: 0%",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )

    await _run_loop(message, context, uid, server, key, total_requests, is_trial)


# ==================================================
# MAIN LOOP
# ==================================================

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
                print(f"\n[CANCELLED] Stopped at {i}/{total_requests}")

                try:
                    await message.edit_text(
                        "╔══════════════════════════════╗\n"
                        "           🛑 *CANCELLED*\n"
                        "╚══════════════════════════════╝\n\n"
                        f"✅ Success     : `{successful}`\n"
                        f"❌ Failed      : `{failed}`\n"
                        f"🔥 Total Visits: `{total_visits:,}`",
                        parse_mode="Markdown",
                        reply_markup=again_keyboard()
                    )
                except Exception:
                    pass

                context.user_data.clear()
                return

            try:

                params = {
                    "uid": uid,
                    "server_name": server,
                    "key": key
                }

                async with session.get(API_URL, params=params) as response:

                    raw_text = await response.text()

                    print("\n" + "=" * 60)
                    print(f"[REQUEST {i}/{total_requests}] HTTP {response.status}")
                    print(f"RAW RESPONSE: {raw_text}")
                    print("=" * 60)

                    if response.status != 200:
                        failed += 1
                        print(f"[FAILED] HTTP {response.status}")
                    else:
                        try:
                            data = json.loads(raw_text)
                        except Exception:
                            data = {"raw": raw_text}

                        visit_count = int(data.get("VisitCount", 0) or 0)
                        total_visits += visit_count
                        successful += 1

                        player_name = data.get("PlayerName", "Unknown")
                        last_player_name = player_name
                        last_visit_count = visit_count

                        print(f"[PARSED] {player_name} | VisitCount: {visit_count} | Total: {total_visits}")

            except Exception as e:
                failed += 1
                print(f"\n[EXCEPTION] Request {i}: {repr(e)}")

            # Progress
            percent = int((i / total_requests) * 100)
            filled = int(percent / 10)
            progress_bar = "█" * filled + "░" * (10 - filled)

            try:
                await message.edit_text(
                    "╔══════════════════════════════╗\n"
                    "      ⚡ *RG VISIT RUNNING*\n"
                    "╚══════════════════════════════╝\n\n"
                    f"🆔 UID    : `{uid}`\n"
                    f"👤 Player : `{last_player_name}`\n"
                    f"🌐 Server : `{server}`\n\n"
                    f"⏳ *Progress*\n"
                    f"`{progress_bar}` {percent}%\n\n"
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

    # ==================================================
    # FINAL RESULT
    # ==================================================

    if is_trial:
        trial_footer = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎁 *FREE TRIAL USED*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Next trial in: `24 hours`\n"
            f"🔑 Get unlimited: {BUY_HANDLE}\n\n"
        )
    else:
        trial_footer = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔑 *PREMIUM KEY USER*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💎 Thanks for supporting!\n"
            f"👨‍💻 Dev: {DEV_HANDLE}\n\n"
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

            "⚠️ *REMINDER*\n"
            "🎮 Game ko *restart* karo,\n"
            "   phir visits show honge.\n\n"

            f"{trial_footer}"

            f"👨‍💻 Dev     : {DEV_HANDLE}\n"
            f"💬 Support : {SUPPORT_HANDLE}\n\n"

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
# MAIN
# ==================================================

def main():

    print("====================================")
    print("       RG VISIT BOT")
    print("====================================")
    print("Bot starting...")

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("visit", visit))
    application.add_handler(CommandHandler("cancel", cancel))

    application.add_handler(CallbackQueryHandler(cancel_callback, pattern="^cancel_process$"))
    application.add_handler(CallbackQueryHandler(start_visit_callback, pattern="^start_visit$"))
    application.add_handler(CallbackQueryHandler(use_trial_callback, pattern="^use_trial$"))
    application.add_handler(CallbackQueryHandler(back_home_callback, pattern="^back_home$"))
    application.add_handler(CallbackQueryHandler(how_it_works_callback, pattern="^how_it_works$"))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )

    application.add_error_handler(error_handler)

    print("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
