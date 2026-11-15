import asyncio, json, os, datetime, random, inspect

# جایگزین داخلی jdatetime؛ ربات برای اجرا به نصب jdatetime وابسته نیست.
def _jalali_to_gregorian(jy, jm, jd):
    jy = int(jy); jm = int(jm); jd = int(jd)
    jy2 = jy + 1595
    days = -355668 + (365 * jy2) + ((jy2 // 33) * 8) + (((jy2 % 33) + 3) // 4) + jd
    if jm < 7:
        days += (jm - 1) * 31
    else:
        days += ((jm - 1) * 30) + 6
    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1
    leap = (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)
    month_days = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 1
    while gm <= 12 and gd > month_days[gm - 1]:
        gd -= month_days[gm - 1]
        gm += 1
    return datetime.date(gy, gm, gd)

def _gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    jd = days + 1
    if jd <= 186:
        jm = (jd - 1) // 31 + 1
        jd = (jd - 1) % 31 + 1
    else:
        jm = (jd - 187) // 30 + 7
        jd = (jd - 187) % 30 + 1
    return jy, jm, jd

class _JalaliDate:
    def __init__(self, year, month, day):
        self.year, self.month, self.day = int(year), int(month), int(day)
    def togregorian(self):
        return _jalali_to_gregorian(self.year, self.month, self.day)

class _JalaliDateTime:
    @classmethod
    def fromgregorian(cls, datetime):
        obj = cls()
        obj._source = datetime
        obj.year, obj.month, obj.day = _gregorian_to_jalali(datetime.year, datetime.month, datetime.day)
        return obj
    @classmethod
    def now(cls):
        return cls.fromgregorian(datetime.datetime.now())
    def strftime(self, fmt):
        return fmt.replace('%Y', f'{self.year:04d}').replace('%m', f'{self.month:02d}').replace('%d', f'{self.day:02d}')

class _JDateTimeModule:
    datetime = _JalaliDateTime
    date = _JalaliDate

jdatetime = _JDateTimeModule()
from rubka import Robot
from rubka.context import Message
from rubka.keypad import ChatKeypadBuilder

MAIN_TOKEN = "CFIJDG0RDQNOQSQIZRNFZGGOQXWMUAIGFNPDPPEWMRCOORNRPGLXIUJNLGAQDREO"
MAKER_ADMIN_PASS = "/Abolfazl1389"
MAKER_ADMIN_ID = "u0CiSwU01183f8dc7bb5bcaa2d13d70d"
USERS_FILE = "maker_users.json"; BOTS_FILE = "maker_bots.json"
SETTINGS_FILE = "maker_settings.json"; BOTS_STATUS_FILE = "bots_status.json"
TICKETS_FILE = "maker_tickets.json"
ADS_FILE = "maker_ads.json"

def load_file(p, d):
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return d
def save_file(p, d):
    with open(p, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=2)

maker_users = load_file(USERS_FILE, {})
_maker_bots_raw = load_file(BOTS_FILE, {})
maker_settings = load_file(SETTINGS_FILE, {"start_ad": "", "blocked_users": []})
if not isinstance(maker_settings, dict): maker_settings = {"start_ad": "", "blocked_users": []}
maker_settings.setdefault("start_ad", ""); maker_settings.setdefault("blocked_users", [])
if not isinstance(maker_settings.get("blocked_users"), list): maker_settings["blocked_users"] = []
_bots_status_raw = load_file(BOTS_STATUS_FILE, {})
tickets = load_file(TICKETS_FILE, {})
ad_campaigns = load_file(ADS_FILE, {})

maker_bots = {}
for _uid, _data in _maker_bots_raw.items():
    if isinstance(_data, dict):
        _bid = f"b{_uid}_{int(datetime.datetime.now().timestamp())}"
        maker_bots[_uid] = [{"bot_id": _bid, "token": _data.get("token",""), "password": _data.get("password",""), "type": _data.get("type","anonymous"), "created_at": str(datetime.datetime.now())}]
    elif isinstance(_data, list):
        _clean = []
        for i, b in enumerate(_data):
            if not isinstance(b, dict): continue
            if "bot_id" not in b: b["bot_id"] = f"b{_uid}_{i}_{int(datetime.datetime.now().timestamp())}"
            b.setdefault("token",""); b.setdefault("password",""); b.setdefault("type","anonymous"); b.setdefault("created_at", str(datetime.datetime.now()))
            _clean.append(b)
        maker_bots[_uid] = _clean
    else:
        maker_bots[_uid] = []

bots_status = {}
for _key, _val in _bots_status_raw.items():
    if _key in maker_bots:
        for _b in maker_bots[_key]: bots_status[_b["bot_id"]] = _val
    else: bots_status[_key] = _val

save_file(BOTS_FILE, maker_bots); save_file(BOTS_STATUS_FILE, bots_status)

def save_maker(): save_file(USERS_FILE, maker_users); save_file(BOTS_FILE, maker_bots)
def save_settings(): save_file(SETTINGS_FILE, maker_settings)
def save_bots_status(): save_file(BOTS_STATUS_FILE, bots_status)
def save_tickets(): save_file(TICKETS_FILE, tickets)
def save_ads(): save_file(ADS_FILE, ad_campaigns)

VIP_COST = 0; VIP_DAYS = 30; VIP_BONUS_COINS = 50; AD_PRICE_TOMAN = 20000

def is_vip_active(uid):
    try:
        u = maker_users.get(str(uid), {})
        until = u.get("vip_until")
        if not until: return False
        return datetime.datetime.now() < datetime.datetime.fromisoformat(until)
    except: return False

def get_vip_days_left(uid):
    try:
        u = maker_users.get(str(uid), {})
        until = u.get("vip_until")
        if not until: return 0
        delta = datetime.datetime.fromisoformat(until) - datetime.datetime.now()
        return max(0, delta.days)
    except: return 0

def set_vip(uid, days=VIP_DAYS, bonus_coins=VIP_BONUS_COINS):
    uid = str(uid)
    if uid not in maker_users:
        maker_users[uid] = {"state": None, "temp": {}, "coins": 0}
    u = maker_users[uid]; now = datetime.datetime.now()
    if u.get("vip_until"):
        try:
            ce = datetime.datetime.fromisoformat(u["vip_until"])
            if ce > now: now = ce
        except: pass
    u["vip_until"] = (now + datetime.timedelta(days=days)).isoformat()
    u["coins"] = u.get("coins", 0) + int(bonus_coins or 0)
    u["vip_bonus_granted"] = True
    save_maker(); return u["vip_until"]

def user_bot_limit(uid): return 5 if is_vip_active(uid) else 1
def user_bot_count(uid): return len(maker_bots.get(str(uid), []))
def create_bot_id(uid): return f"b{uid}_{int(datetime.datetime.now().timestamp())}"

main_bot = Robot(MAIN_TOKEN)
maker_admins = [MAKER_ADMIN_ID]
child_tasks = {}
# نگاشت پیام‌های فورواردشده در چت پشتیبانی برای حفظ قابلیت Reply
support_reply_map = {}

# ================= منوها =================
def safe_user_name(value):
    """نام امن برای نمایش؛ هیچ coroutine/object داخلی نباید وارد رابط کاربر شود."""
    if value is None:
        return "کاربر"
    try:
        s = str(value).strip()
    except Exception:
        return "کاربر"
    if not s or s.startswith("<coroutine object") or "coroutine object" in s or s.startswith("<"):
        return "کاربر"
    return s[:80]

# پاک‌سازی نام‌های خراب ذخیره‌شده از نسخه‌های قبلی
_maker_names_changed = False
for _u in maker_users.values():
    if isinstance(_u, dict) and "name" in _u:
        _safe_name = safe_user_name(_u.get("name"))
        if _u.get("name") != _safe_name:
            _u["name"] = _safe_name
            _maker_names_changed = True
if _maker_names_changed:
    save_maker()

def maker_main_menu(uid=None):
    kb = ChatKeypadBuilder()
    kb.row(ChatKeypadBuilder().button("make", "➕ ساخت ربات جدید"))
    kb.row(ChatKeypadBuilder().button("mybots", "📋 ربات های من"), ChatKeypadBuilder().button("manage_bots", "🛠 مدیریت ربات‌ها"))
    kb.row(ChatKeypadBuilder().button("my_coins", "💰 سکه و شناسه"))
    kb.row(ChatKeypadBuilder().button("daily_maker", "🎁 سکه روزانه"), ChatKeypadBuilder().button("store", "🛍 فروشگاه"))
    kb.row(ChatKeypadBuilder().button("help", "📖 راهنما"), ChatKeypadBuilder().button("support_maker", "📞 پشتیبانی"))
    return kb.build()

def mybots_keypad_v2(uid):
    bots = maker_bots.get(str(uid), [])
    kb = ChatKeypadBuilder()
    for i, b in enumerate(bots, 1):
        bid = b.get("bot_id")
        active = bots_status.get(bid, {}).get("active", True)
        st = "🟢 روشن" if active else "🔴 خاموش"
        tn = {"anonymous":"چت","group_manager":"گروه","raw":"خام","shop":"فروشگاه"}.get(b.get("type"), "?")
        kb.row(ChatKeypadBuilder().button(f"info_{i}", f"📊 ربات {i} — {tn} — {st}"))
        toggle_text = f"🔴 خاموش کردن {i}" if active else f"🟢 روشن کردن {i}"
        kb.row(
            ChatKeypadBuilder().button(f"tog_{i}", toggle_text),
            ChatKeypadBuilder().button(f"del_{i}", f"🗑 حذف {i}"),
        )
    kb.row(ChatKeypadBuilder().button("back_mybots", "🔙 بازگشت"))
    return kb.build()

def bot_manager_menu(uid):
    kb = ChatKeypadBuilder()
    bots = maker_bots.get(str(uid), [])
    if not bots:
        kb.row(ChatKeypadBuilder().button("back_mybm", "🔙 بازگشت"))
        return kb.build()
    for i, b in enumerate(bots, 1):
        tn = {"raw":"ربات خام", "anonymous":"چت ناشناس", "group_manager":"مدیریت گروه", "shop":"فروشگاه"}.get(b.get("type"), "ربات")
        kb.row(ChatKeypadBuilder().button(f"bm_{i}", f"🤖 {i}. {tn}"))
    kb.row(ChatKeypadBuilder().button("back_mybm", "🔙 بازگشت"))
    return kb.build()

def bot_manage_actions(bot_type=None):
    kb = ChatKeypadBuilder()
    if bot_type == "group_manager":
        kb.row(ChatKeypadBuilder().button("gm_security", "🛡 امنیت گروه"), ChatKeypadBuilder().button("gm_settings", "⚙️ تنظیمات"))
        kb.row(ChatKeypadBuilder().button("gm_quick", "⚡ پاسخ سریع"), ChatKeypadBuilder().button("gm_words", "📝 کلمات ممنوع"))
        kb.row(ChatKeypadBuilder().button("gm_warnings", "⚠️ اخطار"), ChatKeypadBuilder().button("gm_coins", "💰 سکه و پاداش"))
        kb.row(ChatKeypadBuilder().button("gm_stats", "📊 آمار گروه"), ChatKeypadBuilder().button("gm_members", "👥 اعضا"))
        kb.row(ChatKeypadBuilder().button("gm_admins", "👑 ادمین‌ها"), ChatKeypadBuilder().button("gm_broadcast", "📢 پیام همگانی"))
        kb.row(ChatKeypadBuilder().button("bm_start", "📝 پیام استارت"), ChatKeypadBuilder().button("bm_command", "➕ افزودن دستور"))
        kb.row(ChatKeypadBuilder().button("bm_restart", "🔄 راه‌اندازی مجدد"), ChatKeypadBuilder().button("bm_back", "🔙 انتخاب ربات"))
    else:
        kb.row(ChatKeypadBuilder().button("bm_start", "📝 پیام استارت"), ChatKeypadBuilder().button("bm_keyboard", "⌨️ مدیریت کیبورد"))
        kb.row(ChatKeypadBuilder().button("bm_command", "➕ افزودن دستور"), ChatKeypadBuilder().button("bm_stats", "📊 آمار"))
        kb.row(ChatKeypadBuilder().button("bm_broadcast", "📢 پیام همگانی"))
        kb.row(ChatKeypadBuilder().button("bm_restart", "🔄 راه‌اندازی مجدد"))
        kb.row(ChatKeypadBuilder().button("bm_back", "🔙 انتخاب ربات"))
    return kb.build()

def _group_default_cfg(paths):
    raw=_manager_load(paths.get("gset",""), {})
    if not isinstance(raw,dict): raw={}
    base={"anti_link":True,"anti_id":False,"anti_badword":False,"anti_spam":False,"lock_group":False,"auto_kick":False,"delete_service":True,"welcome_msg":True,"goodbye_msg":True,"spam_limit":5,"warn_limit":3,"welcome_text":"به گروه خوش آمدی ✨","goodbye_text":"خداحافظ 👋","start_text":"سلام 👋\n\nبه ربات مدیریت گروه خوش آمدید.","quick_replies":{}}
    d=raw.get("__default__",{})
    if isinstance(d,dict): base.update(d)
    return raw,base

def _save_group_default(paths, cfg):
    raw,_=_group_default_cfg(paths); raw["__default__"]=cfg; return _manager_save(paths.get("gset",""), raw)

def group_words_kp():
    kb = ChatKeypadBuilder()
    kb.row(ChatKeypadBuilder().button("gm_w_list", "📋 لیست کلمات"), ChatKeypadBuilder().button("gm_w_add", "➕ افزودن کلمه"))
    kb.row(ChatKeypadBuilder().button("gm_w_remove", "➖ حذف کلمه"), ChatKeypadBuilder().button("gm_back", "🔙 بازگشت"))
    return kb.build()

def group_manage_kp(kind="main", gid=None):
    kb = ChatKeypadBuilder()
    if kind == "security":
        labels = [("anti_link","🔗 ضد لینک"),("anti_id","🆔 ضد آیدی"),("anti_badword","🚫 ضد کلمات"),("anti_spam","🛡 ضد اسپم"),("lock_group","🔒 قفل گروه"),("auto_kick","👢 کیک خودکار"),("delete_service","🧹 حذف سرویس")]
        for key,label in labels: kb.row(ChatKeypadBuilder().button("gm_toggle_"+key,label))
        kb.row(ChatKeypadBuilder().button("gm_back","🔙 بازگشت")); return kb.build()
    if kind == "settings":
        kb.row(ChatKeypadBuilder().button("gm_toggle_welcome","👋 خوش‌آمد روشن/خاموش"), ChatKeypadBuilder().button("gm_toggle_goodbye","👋 خداحافظ روشن/خاموش"))
        kb.row(ChatKeypadBuilder().button("gm_edit_welcome","✏️ متن خوش‌آمد"), ChatKeypadBuilder().button("gm_edit_goodbye","✏️ متن خداحافظی"))
        kb.row(ChatKeypadBuilder().button("gm_spam_limit","🛡 حد اسپم"), ChatKeypadBuilder().button("gm_warn_limit","⚠️ حد اخطار"))
        kb.row(ChatKeypadBuilder().button("gm_back","🔙 بازگشت")); return kb.build()
    if kind == "quick":
        kb.row(ChatKeypadBuilder().button("gm_q_add","➕ افزودن پاسخ"), ChatKeypadBuilder().button("gm_q_list","📋 لیست پاسخ‌ها"))
        kb.row(ChatKeypadBuilder().button("gm_q_remove","➖ حذف پاسخ"), ChatKeypadBuilder().button("gm_back","🔙 بازگشت")); return kb.build()
    if kind == "warnings":
        kb.row(ChatKeypadBuilder().button("gm_warn_limit","⚠️ حد اخطار"), ChatKeypadBuilder().button("gm_auto_kick","👢 کیک خودکار"))
        kb.row(ChatKeypadBuilder().button("gm_back","🔙 بازگشت")); return kb.build()
    if kind == "coins":
        kb.row(ChatKeypadBuilder().button("gm_coin_daily","🎁 سکه روزانه"), ChatKeypadBuilder().button("gm_coin_reward","💬 پاداش پیام"))
        kb.row(ChatKeypadBuilder().button("gm_back","🔙 بازگشت")); return kb.build()
    return bot_manage_actions("group_manager")

def bot_keyboard_menu():
    kb = ChatKeypadBuilder()
    kb.row(ChatKeypadBuilder().button("bm_add_button", "➕ افزودن دکمه"), ChatKeypadBuilder().button("bm_remove_button", "➖ حذف دکمه"))
    kb.row(ChatKeypadBuilder().button("bm_list_buttons", "📋 لیست دکمه‌ها"))
    kb.row(ChatKeypadBuilder().button("bm_keyboard_back", "🔙 بازگشت"))
    return kb.build()

def _manager_paths(bot):
    owner = str(bot.get("owner_id", ""))
    # در maker_bots، مالک به صورت کلید دیکشنری نگهداری می‌شود؛ این مقدار فقط برای مسیرهاست.
    typ = bot.get("type")
    if typ == "raw":
        dd = f"rawbot_{owner}"; return {
            "config": f"{dd}/config.json", "buttons": f"{dd}/buttons.json",
            "users": f"{dd}/users.json", "stats": f"{dd}/stats.json"
        }
    if typ == "shop":
        dd = f"shopbot_{owner}"; return {"config": f"{dd}/config.json", "users": f"{dd}/users.json", "orders": f"{dd}/orders.json"}
    if typ == "group_manager":
        dd = f"groupbot_{owner}"; return {"users": f"{dd}/users.json", "stats": f"{dd}/stats.json", "gset": f"{dd}/gset.json", "bads": f"{dd}/bads.json"}
    return {"users": f"users_{owner}.json"}

def _manager_load(path, default):
    try:
        if not os.path.exists(path): return default
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return default

def _manager_save(path, data):
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path); return True
    except: return False

def _manager_users(path):
    d = _manager_load(path, [])
    if isinstance(d, list): return [str(x) for x in d]
    if isinstance(d, dict): return [str(x) for x in d.keys()]
    return []

def _manager_type_name(t):
    return {"raw":"ربات خام", "anonymous":"چت ناشناس", "group_manager":"مدیریت گروه", "shop":"فروشگاه"}.get(t, "ربات")

def maker_admin_menu():
    kb = ChatKeypadBuilder()
    kb.row(ChatKeypadBuilder().button("stats", "📊 آمار ربات ساز"), ChatKeypadBuilder().button("maker_users_stats", "🏆 آمار کاربران"))
    kb.row(ChatKeypadBuilder().button("add_maker_coins", "💰 افزودن سکه"), ChatKeypadBuilder().button("remove_maker_coins", "🗑 حذف سکه"))
    kb.row(ChatKeypadBuilder().button("maker_broadcast", "📢 پیام همگانی"))
    kb.row(ChatKeypadBuilder().button("vip_users_list", "👑 لیست VIP ها"), ChatKeypadBuilder().button("give_vip", "🎁 اهدای VIP"))
    kb.row(ChatKeypadBuilder().button("remove_vip", "🗑 حذف VIP"), ChatKeypadBuilder().button("block_user", "🚫 مسدود کردن"))
    kb.row(ChatKeypadBuilder().button("unblock_user", "✅ رفع مسدودیت"), ChatKeypadBuilder().button("all_broadcast", "📢 همگانی همه"))
    kb.row(ChatKeypadBuilder().button("set_ad", "📢 ثبت تبلیغ"), ChatKeypadBuilder().button("del_ad", "🗑 حذف تبلیغ"))
    kb.row(ChatKeypadBuilder().button("broadcast_to_bots", "📨 ارسال تبلیغ به ربات‌ها"))
    kb.row(ChatKeypadBuilder().button("tickets_panel", "🎫 تیکت‌های پشتیبانی"))
    kb.row(ChatKeypadBuilder().button("stop_all_children", "🛑 خاموش فرزندها"), ChatKeypadBuilder().button("start_all_children", "▶️ روشن فرزندها"))
    kb.row(ChatKeypadBuilder().button("back", "🔙 بازگشت"))
    return kb.build()

def maker_creation_menu():
    kb = ChatKeypadBuilder()
    kb.row(ChatKeypadBuilder().button("build_raw_bot", "🛠 ربات خام — رایگان"))
    kb.row(ChatKeypadBuilder().button("build_chat_bot", "🤖 چت ناشناس — 1 سکه"))
    kb.row(ChatKeypadBuilder().button("build_group_bot", "👥 مدیریت گروه — 5 سکه"))
    kb.row(ChatKeypadBuilder().button("back", "🔙 بازگشت"))
    return kb.build()

def vip_panel_keypad():
    kb = ChatKeypadBuilder()
    kb.row(ChatKeypadBuilder().button("vip_buy", f"👑 خرید VIP ({VIP_COST} سکه)"))
    kb.row(ChatKeypadBuilder().button("vip_renew", "🔄 تمدید VIP"))
    kb.row(ChatKeypadBuilder().button("vip_status", "📊 وضعیت VIP من"))
    kb.row(ChatKeypadBuilder().button("vip_info", "ℹ️ مزایای VIP"))
    kb.row(ChatKeypadBuilder().button("back", "🔙 بازگشت"))
    return kb.build()

def support_keypad():
    kb = ChatKeypadBuilder()
    kb.row(ChatKeypadBuilder().button("new_ticket", "🎫 ثبت تیکت جدید"))
    kb.row(ChatKeypadBuilder().button("my_tickets", "📋 تیکت‌های من"))
    kb.row(ChatKeypadBuilder().button("back", "🔙 بازگشت"))
    return kb.build()

def ticket_answer_kp():
    kb = ChatKeypadBuilder()
    kb.row(ChatKeypadBuilder().button("cancel_t", "❌ لغو"))
    return kb.build()

def tickets_admin_kp():
    kb = ChatKeypadBuilder()
    kb.row(ChatKeypadBuilder().button("t_list_new", "📥 تیکت‌های جدید"))
    kb.row(ChatKeypadBuilder().button("t_list_all", "📋 همه تیکت‌ها"))
    kb.row(ChatKeypadBuilder().button("t_reply", "📤 پاسخ به تیکت"))
    kb.row(ChatKeypadBuilder().button("t_chat", "💬 چت با کاربر"))
    kb.row(ChatKeypadBuilder().button("back", "🔙 بازگشت"))
    return kb.build()

def ticket_chat_kp():
    kb = ChatKeypadBuilder()
    kb.row(ChatKeypadBuilder().button("chat_edit", "✏️ ویرایش آخرین پیام"), ChatKeypadBuilder().button("chat_delete", "🗑 حذف آخرین پیام"))
    kb.row(ChatKeypadBuilder().button("chat_send", "📤 ارسال پیام"), ChatKeypadBuilder().button("chat_end", "🔚 پایان گفتگو"))
    kb.row(ChatKeypadBuilder().button("back", "🔙 بازگشت"))
    return kb.build()

def tickets_all_kp():
    kb = ChatKeypadBuilder()
    kb.row(ChatKeypadBuilder().button("t_delete_all", "🗑 حذف همه تیکت‌ها"))
    kb.row(ChatKeypadBuilder().button("t_reply", "📤 پاسخ به تیکت"), ChatKeypadBuilder().button("t_chat", "💬 چت با کاربر"))
    kb.row(ChatKeypadBuilder().button("back", "🔙 بازگشت"))
    return kb.build()

def maker_help_text():
    return (
        "**📖 راهنمای کامل ربات ساز کانتر مود**\n\n"
        "**1️⃣ ساخت ربات در BotFather**\n"
        "• وارد @BotFather روبیکا شوید و ربات جدید بسازید.\n"
        "• توکن ربات را دریافت و نزد خود نگه دارید.\n\n"
        "**2️⃣ ساخت در ربات ساز**\n"
        "• از «➕ ساخت ربات جدید» نوع ربات را انتخاب کنید.\n"
        "• توکن را ارسال کنید.\n"
        "• یک رمز مدیریت برای ربات تعیین کنید.\n"
        "• بعد از ساخت، ربات از «📋 ربات های من» و «🛠 مدیریت ربات‌ها» قابل مدیریت است.\n\n"
        "**3️⃣ مدیریت ربات خام**\n"
        "پیام استارت، کیبورد، دکمه‌ها، دستورات، آمار و پیام همگانی را می‌توانید از پنل تغییر دهید.\n\n"
        "**4️⃣ مدیریت گروه**\n"
        "برای ربات «👥 مدیریت گروه» پنل اختصاصی دارید: ضد لینک، ضد آیدی، ضد اسپم، ضد کلمات، قفل گروه، اخطار، کیک خودکار، خوش‌آمد، خداحافظی، پاسخ سریع، سکه، آمار، اعضا، ادمین‌ها و پیام همگانی.\n\n"
        "**5️⃣ فروشگاه و VIP**\n"
        "در «🛍 فروشگاه» خرید تبلیغ و VIP را ببینید و برای پرداخت به PV سازنده پیام دهید. VIP یک ماهه است، ۵۰ سکه و ظرفیت ساخت ۵ ربات دارد و تبلیغات برای ربات‌های شما ارسال نمی‌شود.\n\n"
        "**6️⃣ پشتیبانی**\n"
        "از «📞 پشتیبانی» → «🎫 ثبت تیکت جدید» استفاده کنید و پیام مشکل خود را مستقیم ارسال کنید.\n\n"
        "🌐 وبسایت: **[کانتر مود](https://B2n.ir/Counter2Mod_ir)**\n"
        "👤 سازنده و پشتیبانی: **[ابوالفضل کاظمی](https://rubika.ir/Abolfazl_Kazemi_SFG)**"
    )

# ================= توابع کنترل =================
async def stop_child_bot(bot_id):
    if bot_id in child_tasks and not child_tasks[bot_id].done():
        child_tasks[bot_id].cancel()
        try: await child_tasks[bot_id]
        except asyncio.CancelledError: pass
    if bot_id not in bots_status: bots_status[bot_id] = {}
    bots_status[bot_id]["active"] = False
    save_bots_status()

async def start_child_bot(bot_id, owner_id, token, password, bot_type):
    if bot_id in child_tasks and not child_tasks[bot_id].done():
        await stop_child_bot(bot_id)
    if bot_type == "anonymous": task = asyncio.create_task(run_child_anonymous(owner_id, token, password))
    elif bot_type == "raw": task = asyncio.create_task(run_child_raw_bot(owner_id, token, password))
    elif bot_type == "shop": task = asyncio.create_task(run_child_shop_bot(owner_id, token, password))
    else: task = asyncio.create_task(run_child_group_manager(owner_id, token, password))
    child_tasks[bot_id] = task
    if bot_id not in bots_status: bots_status[bot_id] = {}
    bots_status[bot_id]["active"] = True
    save_bots_status()
    return task

async def stop_all_child_bots():
    s = 0
    for bid in list(child_tasks.keys()):
        if not child_tasks[bid].done(): child_tasks[bid].cancel(); s += 1
    for uid, bots in maker_bots.items():
        for b in bots:
            bid = b.get("bot_id")
            if bid:
                if bid not in bots_status: bots_status[bid] = {}
                bots_status[bid]["active"] = False
    save_bots_status(); return s

async def start_all_child_bots():
    s = 0
    for uid, bots in maker_bots.items():
        for b in bots:
            bid = b.get("bot_id")
            if not bid: continue
            active = bots_status.get(bid, {}).get("active", True)
            if active or bid not in bots_status:
                try:
                    await start_child_bot(bid, uid, b["token"], b["password"], b["type"])
                    s += 1; await asyncio.sleep(0.5)
                except Exception as e: print(f"err start {bid}: {e}")
    return s

# ================= ربات چت ناشناس =================
async def run_child_anonymous(owner_id, token, admin_password):
    try:
        bot = Robot(token)
        u_file = f"users_{owner_id}.json"; g_file = f"gifts_{owner_id}.json"
        s_file = f"support_{owner_id}.json"; r_file = f"reports_{owner_id}.json"
        users = load_file(u_file, {}); gift_codes = load_file(g_file, {})
        support_messages = load_file(s_file, {}); reports = load_file(r_file, [])
        waiting_users = []; active_chats = {}; group_chat = []; admin_users = []
        bot_should_run = True
        def save_u(): save_file(u_file, users)
        def save_g(): save_file(g_file, gift_codes)
        def save_s(): save_file(s_file, support_messages)
        def save_r(): save_file(r_file, reports)
        def get_ad():
            if is_vip_active(owner_id): return ""
            return maker_settings.get("start_ad", "")
        gender_kp = ChatKeypadBuilder().row(ChatKeypadBuilder().button("m","👦 پسر"), ChatKeypadBuilder().button("f","👧 دختر")).build()
        filter_kp = ChatKeypadBuilder().row(ChatKeypadBuilder().button("fm","👦 پسرها"), ChatKeypadBuilder().button("ff","👧 دخترها")).row(ChatKeypadBuilder().button("fa","🌐 همه")).build()
        main_kp = ChatKeypadBuilder().row(ChatKeypadBuilder().button("chat","💬 چت ناشناس")).row(ChatKeypadBuilder().button("chat_f","🎯 چت با فیلتر")).row(ChatKeypadBuilder().button("group","👥 چت گروهی")).row(ChatKeypadBuilder().button("daily","🎁 سکه روزانه"), ChatKeypadBuilder().button("coins","💰 موجودی")).row(ChatKeypadBuilder().button("profile","👤 پروفایل"), ChatKeypadBuilder().button("help_c","📖 راهنما")).row(ChatKeypadBuilder().button("support","📞 پشتیبانی")).build()
        search_kp = ChatKeypadBuilder().row(ChatKeypadBuilder().button("cancel","❌ لغو جستجو")).build()
        chat_kp = ChatKeypadBuilder().row(ChatKeypadBuilder().button("stop","❌ پایان چت"), ChatKeypadBuilder().button("report","🚨 گزارش")).build()
        group_kp = ChatKeypadBuilder().row(ChatKeypadBuilder().button("leave","❌ خروج")).build()
        sup_kp = ChatKeypadBuilder().row(ChatKeypadBuilder().button("cancel_s","❌ لغو")).build()
        admin_kp = ChatKeypadBuilder().row(ChatKeypadBuilder().button("stats","📈 آمار"), ChatKeypadBuilder().button("broadcast","📢 همگانی")).row(ChatKeypadBuilder().button("addc","➕ سکه"), ChatKeypadBuilder().button("resc","🔄 صفر")).row(ChatKeypadBuilder().button("cgift","🎁 کد هدیه"), ChatKeypadBuilder().button("view_reports","🚨 گزارش")).row(ChatKeypadBuilder().button("stop_bot","🛑 خاموش"), ChatKeypadBuilder().button("spanel","📞 پشتیبانی")).build()
        sup_admin_kp = ChatKeypadBuilder().row(ChatKeypadBuilder().button("view","📨 پیام‌ها"), ChatKeypadBuilder().button("reply","📤 پاسخ")).row(ChatKeypadBuilder().button("bka","🔙")).build()
        @bot.on_message()
        async def child_handler(b, message: Message):
            nonlocal bot_should_run
            user_id = str(message.chat_id); text = (message.text or "").strip()
            if text in ("admin", "/admin"): await message.reply("🔐 رمز:"); return
            if text in ("/start", "سلام", "شروع"):
                ad = get_ad()
                if user_id not in users:
                    users[user_id] = {"coins":0, "step":"name", "filter":"all"}; save_u()
                    msg = "👋 خوش آمدید!\nنام خود را وارد کنید:"
                    if ad: msg = f"{ad}\n\n{msg}"
                    await message.reply(msg); return
                else:
                    users[user_id]["step"] = None; save_u()
                    msg = "**🔙 منوی اصلی**"
                    if ad: msg = f"{ad}\n\n{msg}"
                    await message.reply(msg, chat_keypad=main_kp); return
            if user_id not in users and text != admin_password:
                users[user_id] = {"coins":0, "step":"name", "filter":"all"}; save_u()
                await message.reply("👋 نام:"); return
            user = users.get(user_id, {})
            if text == admin_password:
                if user_id not in admin_users: admin_users.append(user_id)
                await message.reply("✅ پنل مدیریت", chat_keypad=admin_kp); return
            if user.get("step") == "name":
                user["name"] = text; user["step"] = "age"; save_u()
                await message.reply("📅 سن:"); return
            if user.get("step") == "age":
                if not text.isdigit(): await message.reply("⚠️ عدد:"); return
                user["age"] = text; user["step"] = "gender"; save_u()
                await message.reply("👫 جنسیت:", chat_keypad=gender_kp); return
            if user.get("step") == "gender":
                if text not in ["👦 پسر", "👧 دختر"]:
                    await message.reply("⚠️ دکمه:", chat_keypad=gender_kp); return
                user["gender"] = text; user["step"] = None
                user["coins"] = user.get("coins",0) + 5; save_u()
                await message.reply("✅ ثبت‌نام!\n🎁 5 سکه پاداش", chat_keypad=main_kp); return
            if text in ("📖 راهنما", "help_c"):
                await message.reply("📖 راهنما:\n\n💬 چت ناشناس (3 سکه)\n🎯 چت با فیلتر\n👥 چت گروهی (5 سکه)\n🎁 سکه روزانه\n💰 موجودی\n👤 پروفایل\n📞 پشتیبانی"); return
            if text in ("💰 موجودی", "📊 موجودی من"):
                await message.reply(f"💰 {user.get('coins',0)} سکه"); return
            if text == "👤 پروفایل":
                await message.reply(f"👤 {user.get('name')}\n📅 {user.get('age')}\n👫 {user.get('gender')}\n💰 {user.get('coins',0)}"); return
            if text == "🎁 سکه روزانه":
                today = str(datetime.date.today())
                if user.get("last_daily") == today: await message.reply("⚠️ امروز گرفتی."); return
                user["coins"] = user.get("coins",0) + 2; user["last_daily"] = today; save_u()
                await message.reply(f"✅ 2 سکه. موجودی: {user['coins']}"); return
            if text in ("🔙 بازگشت", "🔙"):
                user["step"] = None; save_u()
                await message.reply("🔙", chat_keypad=main_kp); return
            if text == "📞 پشتیبانی":
                user["step"] = "support"; save_u()
                await message.reply("📝 پیام:", chat_keypad=sup_kp); return
            if user.get("step") == "support":
                if text == "❌ لغو":
                    user["step"] = None; save_u()
                    await message.reply("✅", chat_keypad=main_kp); return
                mid = str(datetime.datetime.now().timestamp())
                support_messages[mid] = {"user_id":user_id, "name":user.get("name"), "msg":text, "status":"new"}
                save_s(); user["step"] = None; save_u()
                for aid in admin_users:
                    try: await bot.send_message(aid, f"📨 {user.get('name')}: {text}\n🆔 {mid}")
                    except: pass
                await message.reply("✅ ارسال شد.", chat_keypad=main_kp); return
            if text == "🎯 چت با فیلتر":
                user["step"] = "set_filter"; save_u()
                await message.reply("🎯:", chat_keypad=filter_kp); return
            if user.get("step") == "set_filter":
                if text == "👦 پسرها": user["filter"] = "male"
                elif text == "👧 دخترها": user["filter"] = "female"
                else: user["filter"] = "all"
                user["step"] = None; save_u()
                await message.reply("✅", chat_keypad=main_kp); return
            if text == "💬 چت ناشناس":
                if user.get("coins",0) < 3: await message.reply("❌ نیاز 3 سکه"); return
                partner = None
                for i, w in enumerate(waiting_users):
                    if w == user_id: continue
                    w_u = users.get(w, {})
                    uf = user.get("filter", "all"); wf = w_u.get("filter", "all")
                    if uf == "male" and w_u.get("gender") != "👦 پسر": continue
                    if uf == "female" and w_u.get("gender") != "👧 دختر": continue
                    if wf == "male" and user.get("gender") != "👦 پسر": continue
                    if wf == "female" and user.get("gender") != "👧 دختر": continue
                    partner = waiting_users.pop(i); break
                if partner:
                    active_chats[user_id] = partner; active_chats[partner] = user_id
                    user["coins"] -= 3; users[partner]["coins"] -= 3; save_u()
                    p1 = f"👤 {user.get('name')}\n📅 {user.get('age')}\n👫 {user.get('gender')}"
                    p2 = f"👤 {users[partner].get('name')}\n📅 {users[partner].get('age')}\n👫 {users[partner].get('gender')}"
                    await message.reply(f"✅ وصل شدی!\n\n{p2}", chat_keypad=chat_kp)
                    try: await bot.send_message(partner, f"✅ وصل شدی!\n\n{p1}", chat_keypad=chat_kp)
                    except: pass
                else:
                    if user_id not in waiting_users: waiting_users.append(user_id)
                    await message.reply("⏳ جستجو...", chat_keypad=search_kp)
                return
            if text == "🚨 گزارش" and user_id in active_chats:
                partner = active_chats[user_id]
                reports.append({"reporter":user_id, "reported":partner, "time":str(datetime.datetime.now())})
                save_r()
                for aid in admin_users:
                    try: await bot.send_message(aid, f"🚨 گزارش: {user.get('name')} → {users.get(partner,{}).get('name')}")
                    except: pass
                await message.reply("✅ ثبت شد."); return
            if text in ("❌ لغو", "❌ پایان چت"):
                if user_id in waiting_users:
                    waiting_users.remove(user_id); await message.reply("✅", chat_keypad=main_kp)
                elif user_id in active_chats:
                    p = active_chats.pop(user_id); active_chats.pop(p, None)
                    await message.reply("❌ قطع شد.", chat_keypad=main_kp)
                    try: await bot.send_message(p, "❌ طرف قطع کرد.", chat_keypad=main_kp)
                    except: pass
                return
            if user_id in active_chats:
                try: await bot.send_message(active_chats[user_id], text)
                except: pass
                return
            if text == "👥 چت گروهی":
                if user.get("coins",0) < 5: await message.reply("❌ نیاز 5 سکه"); return
                if user_id not in group_chat:
                    group_chat.append(user_id); user["coins"] -= 5; save_u()
                    await message.reply("✅ وارد گروه", chat_keypad=group_kp)
                    for uid in group_chat:
                        if uid != user_id:
                            try: await bot.send_message(uid, f"👤 {user.get('name')} وارد شد!")
                            except: pass
                return
            if text == "❌ خروج":
                if user_id in group_chat: group_chat.remove(user_id); await message.reply("✅", chat_keypad=main_kp)
                return
            if user_id in group_chat and text != "❌ خروج":
                for uid in group_chat:
                    if uid != user_id:
                        try: await bot.send_message(uid, f"👤 {user.get('name')}: {text}")
                        except: pass
                return
            if user_id in admin_users:
                if text == "📈 آمار":
                    await message.reply(f"👥 {len(users)} | 💰 {sum(u.get('coins',0) for u in users.values())} | 💬 {len(active_chats)//2}"); return
                if text == "📢 همگانی":
                    user["step"] = "broadcast"; save_u()
                    await message.reply("✍️ متن:"); return
                if user.get("step") == "broadcast":
                    for uid in users:
                        try: await bot.send_message(uid, f"📢 {text}")
                        except: pass
                    user["step"] = None; save_u()
                    await message.reply("✅"); return
                if text == "➕ سکه":
                    user["step"] = "addcoin_id"; save_u()
                    await message.reply("🆔:"); return
                if user.get("step") == "addcoin_id":
                    user["target"] = text; user["step"] = "addcoin_am"; save_u()
                    await message.reply("💰:"); return
                if user.get("step") == "addcoin_am":
                    t = user.get("target")
                    if t in users and text.isdigit():
                        users[t]["coins"] = users[t].get("coins",0) + int(text); save_u()
                        await message.reply(f"✅ {text} سکه")
                        try: await bot.send_message(t, f"**🎁 {text} سکه از مدیریت دریافت شد**")
                        except: pass
                    else: await message.reply("❌")
                    user["step"] = None; save_u(); return
                if text == "🔄 صفر":
                    user["step"] = "res_c"; save_u()
                    await message.reply("🆔:"); return
                if user.get("step") == "res_c":
                    if text in users: users[text]["coins"] = 0; save_u(); await message.reply("✅")
                    else: await message.reply("❌")
                    user["step"] = None; save_u(); return
                if text == "🎁 کد هدیه":
                    user["step"] = "g_am"; save_u()
                    await message.reply("💰:"); return
                if user.get("step") == "g_am":
                    user["g_am"] = int(text); user["step"] = "g_cap"; save_u()
                    await message.reply("🔢:"); return
                if user.get("step") == "g_cap":
                    user["g_cap"] = int(text); user["step"] = "g_code"; save_u()
                    await message.reply("🔑:"); return
                if user.get("step") == "g_code":
                    gift_codes[text] = {"amount":user["g_am"], "capacity":user["g_cap"]}; save_g()
                    user["step"] = None; save_u()
                    await message.reply(f"✅ `{text}`"); return
                if text == "🛑 خاموش":
                    user["step"] = "confirm_stop_bot"; save_u()
                    await message.reply("⚠️ «تایید خاموشی»:"); return
                if user.get("step") == "confirm_stop_bot" and text == "تایید خاموشی":
                    bot_should_run = False
                    await message.reply("🛑 خداحافظ!")
                    for oid, bots in maker_bots.items():
                        for bb in bots:
                            if bb.get("token") == token:
                                bid2 = bb.get("bot_id")
                                if bid2:
                                    if bid2 not in bots_status: bots_status[bid2] = {}
                                    bots_status[bid2]["active"] = False
                                    save_bots_status()
                    await bot.stop(); return
                if text == "📞 پشتیبانی":
                    await message.reply("📞", chat_keypad=sup_admin_kp); return
                if text == "📨 پیام‌ها":
                    r = ""
                    for k,v in support_messages.items():
                        if v.get("status") == "new": r += f"🆔 {k} | {v['name']} | {v['msg']}\n"
                    await message.reply(r if r else "📭"); return
                if text == "📤 پاسخ":
                    user["step"] = "rep_id"; save_u()
                    await message.reply("🆔:"); return
                if user.get("step") == "rep_id":
                    user["target"] = text; user["step"] = "rep_msg"; save_u()
                    await message.reply("✍️:"); return
                if user.get("step") == "rep_msg":
                    t = user.get("target"); tuid = t
                    if t in support_messages:
                        tuid = support_messages[t]["user_id"]; support_messages[t]["status"] = "replied"; save_s()
                    if tuid in users:
                        try: await bot.send_message(tuid, f"📞 پاسخ: {text}")
                        except: pass
                        await message.reply("✅")
                    else: await message.reply("❌")
                    user["step"] = None; save_u(); return
                if text == "🔙":
                    await message.reply("🔙", chat_keypad=admin_kp); return
        retry_delay = 3
        while bot_should_run:
            try:
                await asyncio.to_thread(bot.run)
                retry_delay = 3
            except asyncio.CancelledError:
                break
            except Exception as e:
                err = str(e)
                if "502" in err or "Bad Gateway" in err or "APIRequestError" in err:
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 60)
                else:
                    print(f"Anon err: {e}")
                    await asyncio.sleep(5)
    except Exception as e: print(f"Anon Bot Error {owner_id}: {e}")

# ================= ربات خام =================
async def run_child_raw_bot(owner_id, token, admin_password):
    try:
        bot = Robot(token)
        dd = f"rawbot_{owner_id}"; os.makedirs(dd, exist_ok=True)
        CF = f"{dd}/config.json"; BF = f"{dd}/buttons.json"
        UF = f"{dd}/users.json"; SF = f"{dd}/stats.json"; LF = f"{dd}/learn.json"
        RF = f"{dd}/auto_replies.json"; CMF = f"{dd}/commands.json"; BANF = f"{dd}/banned.json"
        def sd(d, f):
            tmp = f + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fp: json.dump(d, fp, ensure_ascii=False, indent=2)
            os.replace(tmp, f)
        def lj(p, d):
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f: return json.load(f)
                except: pass
            return d
        config = lj(CF, None)
        if not isinstance(config, dict): config = {"welcome_text":"👋 خوش آمدید!", "admin_ids":[]}; sd(config, CF)
        config.setdefault("welcome_text", "👋"); config.setdefault("admin_ids", [])
        if not isinstance(config["admin_ids"], list): config["admin_ids"] = []
        buttons = lj(BF, []); all_users = lj(UF, [])
        if not isinstance(buttons, list): buttons = []
        if not isinstance(all_users, list): all_users = []
        stats = lj(SF, {"total_messages":0, "users":{}})
        if not isinstance(stats, dict): stats = {"total_messages":0, "users":{}}
        stats.setdefault("users", {}); stats.setdefault("total_messages", 0)
        learn_data = lj(LF, {})
        if not isinstance(learn_data, dict): learn_data = {}
        auto_replies = lj(RF, {})
        if not isinstance(auto_replies, dict): auto_replies = {}
        commands_data = lj(CMF, {})
        if not isinstance(commands_data, dict): commands_data = {}
        banned_users = lj(BANF, [])
        if not isinstance(banned_users, list): banned_users = []
        banned_users = [str(x) for x in banned_users]
        admin_ids = set(config.get("admin_ids", []))
        o_s = str(owner_id)
        if o_s and o_s not in admin_ids:
            admin_ids.add(o_s); config["admin_ids"] = list(admin_ids); sd(config, CF)
        user_states = {}
        def sc(): sd(config, CF)
        def sb(): sd(buttons, BF)
        def su(): sd(list(all_users), UF)
        def ss(): sd(stats, SF)
        def sl(): sd(learn_data, LF)
        def sr(): sd(auto_replies, RF)
        def scmd(): sd(commands_data, CMF)
        def sbans(): sd(banned_users, BANF)
        def get_ad():
            if is_vip_active(owner_id): return ""
            return maker_settings.get("start_ad", "")
        def pr(r):
            if isinstance(r, list): r = random.choice(r) if r else ""
            if not isinstance(r, str): r = str(r)
            now = datetime.datetime.now()
            try:
                jal = jdatetime.datetime.fromgregorian(datetime=now)
                ds = f"{jal.year}-{jal.month}-{jal.day}"
            except: ds = now.strftime("%Y-%m-%d")
            r = r.replace("{dice}", str(random.randint(1,6)))
            r = r.replace("{coin}", random.choice(["شیر 🦁","خط ✂️"]))
            r = r.replace("{time}", now.strftime("%H:%M:%S"))
            r = r.replace("{date}", ds)
            r = r.replace("{random100}", str(random.randint(1,100)))
            r = r.replace("{users}", str(len(all_users)))
            return r
        def bk(uid=None):
            kb = ChatKeypadBuilder(); rows = {}
            for b in buttons:
                if not isinstance(b, dict): continue
                r = b.get("row", 0); rows.setdefault(r, []).append(b)
            for r in sorted(rows.keys()):
                try:
                    bt = [ChatKeypadBuilder().button(str(bb["id"]), str(bb["text"])) for bb in rows[r] if "id" in bb and "text" in bb]
                    if bt: kb.row(*bt)
                except: pass
            if uid and uid in admin_ids:
                try: kb.row(ChatKeypadBuilder().button("open_admin", "🔐 پنل"))
                except: pass
            if not buttons and not (uid and uid in admin_ids):
                try: kb.row(ChatKeypadBuilder().button("_d", "🚀 شروع"))
                except: pass
            try: return kb.build()
            except: return None
        def a_kp():
            kb = ChatKeypadBuilder()
            kb.row(ChatKeypadBuilder().button("set_welcome", "📝 خوش‌آمد"))
            kb.row(ChatKeypadBuilder().button("add_btn", "➕ دکمه"), ChatKeypadBuilder().button("remove_btn", "➖ حذف"))
            kb.row(ChatKeypadBuilder().button("manage_rows", "🔀 چیدمان"))
            kb.row(ChatKeypadBuilder().button("preview", "👁 پیش‌نمایش"), ChatKeypadBuilder().button("stats_a", "📊 آمار"))
            kb.row(ChatKeypadBuilder().button("broadcast_a", "📢 همگانی"), ChatKeypadBuilder().button("users_a", "👥 کاربران"))
            kb.row(ChatKeypadBuilder().button("learn_a", "🧠 آموزش"), ChatKeypadBuilder().button("auto_a", "⚡ پاسخ خودکار"))
            kb.row(ChatKeypadBuilder().button("command_a", "➕ دستور"), ChatKeypadBuilder().button("edit_btn_a", "✏️ ویرایش دکمه"))
            kb.row(ChatKeypadBuilder().button("ban_a", "🚫 مسدود/رفع"), ChatKeypadBuilder().button("templates_a", "📋 قالب‌ها"))
            kb.row(ChatKeypadBuilder().button("stop_bot_a", "🛑 خاموش"))
            kb.row(ChatKeypadBuilder().button("back_main", "🔙"))
            return kb.build()
        t_kp = ChatKeypadBuilder().row(ChatKeypadBuilder().button("tpl_group","👥 گروه")).row(ChatKeypadBuilder().button("tpl_fun","🎮 سرگرمی")).row(ChatKeypadBuilder().button("tpl_store","🛍 فروشگاه")).row(ChatKeypadBuilder().button("tpl_support","📞 پشتیبانی")).row(ChatKeypadBuilder().button("tpl_edu","📚 آموزشی")).row(ChatKeypadBuilder().button("tpl_news","📰 خبری")).row(ChatKeypadBuilder().button("tpl_islamic","🕌 مذهبی")).row(ChatKeypadBuilder().button("tpl_clear","🗑 پاک")).row(ChatKeypadBuilder().button("back_admin","🔙")).build()
        async def sk(chat_id, text, keypad=None, reply_to=None):
            if reply_to is not None:
                try:
                    if keypad: await reply_to.reply(text, chat_keypad=keypad)
                    else: await reply_to.reply(text)
                    return True
                except: pass
            try:
                if keypad:
                    try: await bot.send_message(chat_id, text, chat_keypad=keypad); return True
                    except:
                        try: await bot.send_message(chat_id, text, keypad=keypad); return True
                        except: pass
                await bot.send_message(chat_id, text); return True
            except: return False
        def apl_grp():
            buttons.clear()
            buttons.extend([
                {"id":"g_rules","text":"📜 قوانین","row":0,"response":"📜 قوانین:\n1️⃣ احترام\n2️⃣ بدون تبلیغ"},
                {"id":"g_admin","text":"🛡 راهنما","row":0,"response":"🛡 راهنما"},
                {"id":"g_stats","text":"📊 آمار","row":1,"response":"👥 {users}\n🕒 {time}"},
                {"id":"g_dice","text":"🎲 تاس","row":2,"response":"🎲 {dice}"},
                {"id":"g_coin","text":"🪙 شیر/خط","row":2,"response":"🪙 {coin}"},
            ]); sb()
        def apl_fun():
            buttons.clear()
            buttons.extend([
                {"id":"f_joke","text":"😂 جوک","row":0,"response":["😂 چرا ریاضی؟","😂 برنامه‌نویس!","😂 ویندوز!"]},
                {"id":"f_fact","text":"💡 دانستنی","row":0,"response":["💡 قلب!","💡 عسل!"]},
                {"id":"f_dice","text":"🎲 تاس","row":1,"response":"🎲 {dice}"},
                {"id":"f_coin","text":"🪙 شیر/خط","row":1,"response":"🪙 {coin}"},
                {"id":"f_fal","text":"🔮 فال","row":2,"response":["🔮 روز خوبی!","🔮 خبر خوب!"]},
                {"id":"f_time","text":"⏰ ساعت","row":2,"response":"⏰ {time}"},
            ]); sb()
        def apl_store():
            buttons.clear()
            buttons.extend([
                {"id":"s_list","text":"🛍 محصولات","row":0,"response":"🛍 محصولات:\n1. A — 10000\n2. B — 20000"},
                {"id":"s_order","text":"📦 سفارش","row":0,"response":"📦 اطلاعات سفارش"},
                {"id":"s_price","text":"💰 قیمت","row":1,"response":"💰 لیست قیمت"},
                {"id":"s_contact","text":"📞 تماس","row":1,"response":"📞 راه‌های ارتباطی"},
            ]); sb()
        def apl_support():
            buttons.clear()
            buttons.extend([
                {"id":"sp_guide","text":"📚 راهنما","row":0,"response":"📚 راهنما"},
                {"id":"sp_contact","text":"📞 پشتیبانی","row":0,"response":"📞 پیام بده"},
                {"id":"sp_faq","text":"❓ سوالات","row":1,"response":"❓ سوالات متداول"},
                {"id":"sp_report","text":"🐛 گزارش","row":1,"response":"🐛 مشکل خود را بنویسید"},
            ]); sb()
        def apl_edu():
            buttons.clear()
            buttons.extend([
                {"id":"e_lessons","text":"📖 درس‌ها","row":0,"response":"📖 ریاضی، فیزیک"},
                {"id":"e_exam","text":"📝 آزمون","row":0,"response":"📝 آزمون"},
                {"id":"e_grade","text":"📊 نمرات","row":1,"response":"📊 نمرات"},
                {"id":"e_ask","text":"❓ سوال","row":1,"response":"❓ سوال خود را بنویسید"},
            ]); sb()
        def apl_news():
            buttons.clear()
            buttons.extend([
                {"id":"n_today","text":"📰 امروز","row":0,"response":"📰 اخبار"},
                {"id":"n_sports","text":"⚽ ورزشی","row":0,"response":"⚽ اخبار ورزشی"},
                {"id":"n_econ","text":"💹 اقتصادی","row":1,"response":"💹 اخبار اقتصادی"},
                {"id":"n_tech","text":"💻 فناوری","row":1,"response":"💻 اخبار فناوری"},
            ]); sb()
        def apl_islamic():
            buttons.clear()
            buttons.extend([
                {"id":"i_quran","text":"📖 قرآن","row":0,"response":"📖 آیه امروز"},
                {"id":"i_hadith","text":"📜 حدیث","row":0,"response":"📜 حدیث"},
                {"id":"i_prayer","text":"🕌 اوقات","row":1,"response":"🕌 اوقات شرعی"},
                {"id":"i_doa","text":"🤲 دعا","row":1,"response":"🤲 دعای روز"},
            ]); sb()
        bot_should_run = True
        @bot.on_message()
        async def raw_handler(b, message: Message):
            nonlocal bot_should_run
            try:
                uid = str(message.chat_id); text = (message.text or "").strip()
                if uid in banned_users and uid not in admin_ids:
                    return
                # دستورات سفارشی و پاسخ‌های خودکار قبل از منوی عمومی اجرا می‌شوند.
                if text in commands_data and uid not in admin_ids:
                    await sk(uid, pr(commands_data[text]), bk(uid), reply_to=message); return
                if text in auto_replies and uid not in admin_ids:
                    await sk(uid, pr(auto_replies[text]), bk(uid), reply_to=message); return
                try:
                    if uid not in all_users: all_users.append(uid); su()
                except: pass
                try:
                    stats.setdefault("users", {})
                    stats["users"].setdefault(uid, {"messages":0, "name":""})
                    stats["users"][uid]["messages"] = stats["users"][uid].get("messages",0) + 1
                    stats["total_messages"] = stats.get("total_messages",0) + 1
                    try:
                        n = getattr(message, "name", None)
                        if callable(n): n = n()
                        if inspect.isawaitable(n): n = await n
                        n = safe_user_name(n)
                        if n != "کاربر": stats["users"][uid]["name"] = n
                    except Exception: pass
                    ss()
                except: pass
                if text and text == admin_password:
                    admin_ids.add(uid); config["admin_ids"] = list(admin_ids); sc()
                    await sk(uid, "✅ پنل:", a_kp(), reply_to=message); return
                is_admin = uid in admin_ids
                state = user_states.get(uid, {}) if is_admin else {}
                current = state.get("state") if isinstance(state, dict) else None
                if text in ("/start","شروع","start") and not current:
                    welcome = config.get("welcome_text", "👋")
                    ad = get_ad()
                    if ad: welcome = f"{ad}\n\n{welcome}"
                    if not buttons:
                        if is_admin:
                            welcome += "\n\n💡 پنل رو تنظیم کن:"
                            await sk(uid, welcome, a_kp(), reply_to=message)
                        else: await sk(uid, welcome + "\n\n⚠️ منویی تنظیم نشده.", None, reply_to=message)
                    else: await sk(uid, welcome, bk(uid), reply_to=message)
                    return
                if text == "🔐 پنل" and is_admin:
                    await sk(uid, "🔐", a_kp(), reply_to=message); return
                if is_admin:
                    if current and text in ("🔙 بازگشت", "🔙", "back", "بازگشت"):
                        user_states[uid] = {}
                        await sk(uid, "✅ لغو شد.", a_kp(), reply_to=message)
                        return
                    if current == "ban_user":
                        target = text.strip()
                        if target in banned_users: banned_users.remove(target); sbans(); reply="**✅ رفع مسدودیت شد.**"
                        else: banned_users.append(target); sbans(); reply="**🚫 کاربر مسدود شد.**"
                        user_states[uid] = {}; await sk(uid, f"{reply}\n`{target}`", a_kp(), reply_to=message); return
                    if current == "add_auto":
                        if "=>" not in text: await sk(uid, "❌ فرمت: ورودی => پاسخ", None, reply_to=message); return
                        k,v=text.split("=>",1); auto_replies[k.strip()]=v.strip(); sr(); user_states[uid]={}; await sk(uid,"✅ پاسخ خودکار ذخیره شد.",a_kp(),reply_to=message); return
                    if current == "add_command":
                        if "=>" not in text: await sk(uid, "❌ فرمت: /command => پاسخ", None, reply_to=message); return
                        k,v=text.split("=>",1); k=k.strip();
                        if not k.startswith("/"): k="/"+k
                        commands_data[k]=v.strip(); scmd(); user_states[uid]={}; await sk(uid,"✅ دستور ذخیره شد.",a_kp(),reply_to=message); return
                    if current == "edit_button":
                        if "=>" not in text: await sk(uid, "❌ فرمت: متن قدیمی => متن جدید => پاسخ جدید", None, reply_to=message); return
                        parts=[x.strip() for x in text.split("=>")]
                        if len(parts) < 2: await sk(uid,"❌",None,reply_to=message); return
                        old,new=parts[0],parts[1]; resp=parts[2] if len(parts)>2 else None
                        found=False
                        for bb in buttons:
                            if isinstance(bb,dict) and bb.get("text")==old:
                                bb["text"]=new
                                if resp is not None: bb["response"]=resp
                                found=True; break
                        if found: sb(); user_states[uid]={}; await sk(uid,"✅ دکمه ویرایش شد.",a_kp(),reply_to=message)
                        else: await sk(uid,"❌ دکمه پیدا نشد.",a_kp(),reply_to=message)
                        return
                    if current == "set_welcome":
                        config["welcome_text"] = text; sc(); user_states[uid] = {}
                        await sk(uid, "✅", a_kp(), reply_to=message); return
                    if current == "add_btn_text":
                        state["new_text"] = text; state["state"] = "add_btn_resp"; user_states[uid] = state
                        await sk(uid, "📝 پاسخ ({dice} {coin} {time} {date} {random100} {users}):", None, reply_to=message); return
                    if current == "add_btn_resp":
                        state["new_resp"] = text; state["state"] = "add_btn_row"; user_states[uid] = state
                        await sk(uid, "🔢 ردیف:", None, reply_to=message); return
                    if current == "add_btn_row":
                        try: rn = int(text)
                        except: rn = 0
                        bid = f"btn_{int(datetime.datetime.now().timestamp())}_{len(buttons)}"
                        buttons.append({"id":bid, "text":state.get("new_text"), "response":state.get("new_resp"), "row":rn})
                        sb(); user_states[uid] = {}
                        await sk(uid, "✅", a_kp(), reply_to=message); return
                    if current == "remove_btn":
                        for btn in buttons:
                            if isinstance(btn, dict) and btn.get("text") == text: buttons.remove(btn); break
                        sb(); user_states[uid] = {}
                        await sk(uid, "✅", a_kp(), reply_to=message); return
                    if current == "set_row":
                        p = text.rsplit(" ", 1)
                        if len(p) == 2:
                            try:
                                rn = int(p[1])
                                for btn in buttons:
                                    if isinstance(btn, dict) and btn.get("text") == p[0]: btn["row"] = rn; break
                                sb()
                            except: pass
                        user_states[uid] = {}
                        await sk(uid, "✅", a_kp(), reply_to=message); return
                    if current == "broadcast":
                        c = 0
                        for u in list(all_users):
                            try: await bot.send_message(u, f"📢 {text}"); c += 1; await asyncio.sleep(0.1)
                            except: pass
                        user_states[uid] = {}
                        await sk(uid, f"✅ {c}", a_kp(), reply_to=message); return
                    if current == "learn":
                        if "=>" in text:
                            k, v = text.split("=>", 1)
                            learn_data[k.strip()] = v.strip(); sl()
                            await sk(uid, "✅", None, reply_to=message)
                        else: await sk(uid, "❌ ورودی => پاسخ", None, reply_to=message)
                        return
                    if current == "confirm_stop" and text == "تایید خاموشی":
                        bot_should_run = False
                        await sk(uid, "🛑", None, reply_to=message)
                        for oid, bots in maker_bots.items():
                            for bb in bots:
                                if bb.get("token") == token:
                                    bid2 = bb.get("bot_id")
                                    if bid2:
                                        if bid2 not in bots_status: bots_status[bid2] = {}
                                        bots_status[bid2]["active"] = False
                                        save_bots_status()
                        await bot.stop(); return
                    if text == "📝 خوش‌آمد":
                        user_states[uid] = {"state":"set_welcome"}; await sk(uid, "✍️:", None, reply_to=message); return
                    if text == "➕ دکمه":
                        user_states[uid] = {"state":"add_btn_text"}; await sk(uid, "📝 متن:", None, reply_to=message); return
                    if text == "➖ حذف":
                        if not buttons: await sk(uid, "⚠️", None, reply_to=message); return
                        user_states[uid] = {"state":"remove_btn"}
                        l = "\n".join([f"• {bb.get('text','')}" for bb in buttons if isinstance(bb, dict)])
                        await sk(uid, f"📋:\n{l}\n\nمتن:", None, reply_to=message); return
                    if text == "🔀 چیدمان":
                        user_states[uid] = {"state":"set_row"}
                        l = "\n".join([f"• {bb.get('text','')} → {bb.get('row',0)}" for bb in buttons if isinstance(bb, dict)])
                        await sk(uid, f"📋:\n{l}\n\n«نام ردیف»", None, reply_to=message); return
                    if text == "👁 پیش‌نمایش":
                        await sk(uid, f"👁 {config.get('welcome_text','')}", bk(uid), reply_to=message); return
                    if text == "📊 آمار":
                        t = ""
                        s_u = sorted(stats.get("users",{}).items(), key=lambda x: x[1].get("messages",0), reverse=True)[:5]
                        for i,(u,d) in enumerate(s_u,1): t += f"\n{i}. {d.get('name','?')} — {d.get('messages',0)}"
                        await sk(uid, f"📊 کاربران: {len(all_users)}\n💬: {stats.get('total_messages',0)}\n🔘: {len(buttons)}\n🧠: {len(learn_data)}\n🏆{t or ' -'}", None, reply_to=message); return
                    if text == "📢 همگانی":
                        user_states[uid] = {"state":"broadcast"}; await sk(uid, "✍️:", None, reply_to=message); return
                    if text == "👥 کاربران":
                        names=[]
                        for u0 in all_users[:100]:
                            nm=stats.get("users",{}).get(str(u0),{}).get("name", "کاربر")
                            mark="🚫" if str(u0) in banned_users else "🟢"
                            names.append(f"{mark} `{u0}` — {safe_user_name(nm)}")
                        await sk(uid, "👥 کاربران\n\n" + ("\n".join(names) or "خالی"), a_kp(), reply_to=message); return
                    if text == "🚫 مسدود/رفع":
                        user_states[uid] = {"state":"ban_user"}; await sk(uid, "🆔 آیدی کاربر را بفرستید. اگر مسدود است، رفع مسدود می‌شود.", None, reply_to=message); return
                    if text == "⚡ پاسخ خودکار":
                        user_states[uid] = {"state":"add_auto"}; await sk(uid, "📌 فرمت: ورودی => پاسخ", None, reply_to=message); return
                    if text == "➕ دستور":
                        user_states[uid] = {"state":"add_command"}; await sk(uid, "📌 فرمت: /command => پاسخ", None, reply_to=message); return
                    if text == "✏️ ویرایش دکمه":
                        user_states[uid] = {"state":"edit_button"}; await sk(uid, "📌 فرمت: متن قدیمی => متن جدید => پاسخ جدید", None, reply_to=message); return
                    if text == "🧠 آموزش":
                        user_states[uid] = {"state":"learn"}; await sk(uid, "📚 «ورودی => پاسخ»", None, reply_to=message); return
                    if text == "📋 قالب‌ها":
                        await sk(uid, "📋:", t_kp, reply_to=message); return
                    if text == "🛑 خاموش":
                        user_states[uid] = {"state":"confirm_stop"}; await sk(uid, "⚠️ «تایید خاموشی»", None, reply_to=message); return
                    if text in ("🔙", "🔙 بازگشت"):
                        user_states[uid] = {}
                        await sk(uid, config.get("welcome_text",""), bk(uid), reply_to=message); return
                    if text == "👥 گروه": apl_grp(); await sk(uid, "✅", a_kp(), reply_to=message); return
                    if text == "🎮 سرگرمی": apl_fun(); await sk(uid, "✅", a_kp(), reply_to=message); return
                    if text == "🛍 فروشگاه": apl_store(); await sk(uid, "✅", a_kp(), reply_to=message); return
                    if text == "📞 پشتیبانی": apl_support(); await sk(uid, "✅", a_kp(), reply_to=message); return
                    if text == "📚 آموزشی": apl_edu(); await sk(uid, "✅", a_kp(), reply_to=message); return
                    if text == "📰 خبری": apl_news(); await sk(uid, "✅", a_kp(), reply_to=message); return
                    if text == "🕌 مذهبی": apl_islamic(); await sk(uid, "✅", a_kp(), reply_to=message); return
                    if text == "🗑 پاک":
                        buttons.clear(); sb()
                        await sk(uid, "✅", a_kp(), reply_to=message); return
                if text in learn_data:
                    await sk(uid, pr(learn_data[text]), None, reply_to=message); return
                for btn in buttons:
                    if isinstance(btn, dict) and btn.get("text") == text:
                        await sk(uid, pr(btn.get("response","")), bk(uid), reply_to=message); return
                if text == "🚀 شروع":
                    await sk(uid, config.get("welcome_text",""), bk(uid), reply_to=message); return
                await sk(uid, "❓ /start", bk(uid), reply_to=message)
            except Exception as eh: print(f"raw err: {eh}")
        retry_delay = 3
        while bot_should_run:
            try:
                await asyncio.to_thread(bot.run)
                retry_delay = 3
            except asyncio.CancelledError:
                break
            except Exception as e:
                err = str(e)
                if "502" in err or "Bad Gateway" in err or "APIRequestError" in err:
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 60)
                else:
                    print(f"Raw err: {e}")
                    await asyncio.sleep(5)
    except Exception as e: print(f"Raw Bot Error {owner_id}: {e}")

# ================= ربات فروشگاه =================
async def run_child_shop_bot(owner_id, token, admin_password):
    try:
        bot = Robot(token)
        dd = f"shopbot_{owner_id}"; os.makedirs(dd, exist_ok=True)
        PF = f"{dd}/products.json"; CF = f"{dd}/carts.json"; OF = f"{dd}/orders.json"
        DF = f"{dd}/discounts.json"; SF = f"{dd}/settings.json"; CFG = f"{dd}/config.json"
        UF = f"{dd}/users.json"
        def sd(d, f):
            tmp = f + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fp: json.dump(d, fp, ensure_ascii=False, indent=2)
            os.replace(tmp, f)
        def rl(p):
            if not os.path.exists(p): return []
            try:
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f); return d if isinstance(d, list) else []
            except: return []
        def wl(p, d): sd(d, p)
        def rd(p):
            if not os.path.exists(p): return {}
            try:
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f); return d if isinstance(d, dict) else {}
            except: return {}
        def wd(p, d): sd(d, p)
        if not os.path.exists(CFG): wd(CFG, {"welcome_text":"🛍 خوش آمدید!", "admin_ids":[]})
        if not os.path.exists(SF): wd(SF, {"shop_name":"فروشگاه", "phone":"", "address":""})
        if not os.path.exists(PF): wl(PF, [])
        if not os.path.exists(CF): wd(CF, {})
        if not os.path.exists(OF): wl(OF, [])
        if not os.path.exists(DF): wd(DF, {})
        if not os.path.exists(UF): wl(UF, [])
        config = rd(CFG); config.setdefault("welcome_text", "🛍 خوش آمدید!")
        config.setdefault("admin_ids", [])
        if not isinstance(config["admin_ids"], list): config["admin_ids"] = []
        admin_ids = set(config.get("admin_ids", []))
        o_s = str(owner_id)
        if o_s and o_s not in admin_ids:
            admin_ids.add(o_s); config["admin_ids"] = list(admin_ids); wd(CFG, config)
        user_states = {}
        def get_ad():
            if is_vip_active(owner_id): return ""
            return maker_settings.get("start_ad", "")
        def sc(): wd(CFG, config)
        def user_main_kp():
            kb = ChatKeypadBuilder()
            kb.row(ChatKeypadBuilder().button("view_products", "🛍 مشاهده محصولات"))
            kb.row(ChatKeypadBuilder().button("view_cart", "🛒 سبد خرید"))
            kb.row(ChatKeypadBuilder().button("my_orders", "📦 سفارش‌های من"))
            kb.row(ChatKeypadBuilder().button("track_order", "🔍 پیگیری سفارش"))
            kb.row(ChatKeypadBuilder().button("contact_us", "📞 تماس با ما"))
            return kb.build()
        def admin_kp():
            kb = ChatKeypadBuilder()
            kb.row(ChatKeypadBuilder().button("a_products", "📦 مدیریت محصولات"))
            kb.row(ChatKeypadBuilder().button("a_orders", "📋 مدیریت سفارش‌ها"))
            kb.row(ChatKeypadBuilder().button("a_discounts", "🎟 کدهای تخفیف"))
            kb.row(ChatKeypadBuilder().button("a_settings", "⚙️ تنظیمات فروشگاه"))
            kb.row(ChatKeypadBuilder().button("a_stats", "📊 آمار فروش"))
            kb.row(ChatKeypadBuilder().button("a_broadcast", "📢 پیام همگانی"))
            kb.row(ChatKeypadBuilder().button("a_stop", "🛑 خاموش کردن"))
            return kb.build()
        def products_kp():
            kb = ChatKeypadBuilder()
            kb.row(ChatKeypadBuilder().button("p_add", "➕ افزودن"))
            kb.row(ChatKeypadBuilder().button("p_remove", "➖ حذف"))
            kb.row(ChatKeypadBuilder().button("p_list", "📋 لیست"))
            kb.row(ChatKeypadBuilder().button("a_back", "🔙"))
            return kb.build()
        def orders_kp():
            kb = ChatKeypadBuilder()
            kb.row(ChatKeypadBuilder().button("o_view", "📋 مشاهده"))
            kb.row(ChatKeypadBuilder().button("o_change", "✏️ تغییر وضعیت"))
            kb.row(ChatKeypadBuilder().button("a_back", "🔙"))
            return kb.build()
        def discounts_kp():
            kb = ChatKeypadBuilder()
            kb.row(ChatKeypadBuilder().button("d_add", "➕ افزودن"))
            kb.row(ChatKeypadBuilder().button("d_list", "📋 لیست"))
            kb.row(ChatKeypadBuilder().button("d_remove", "➖ حذف"))
            kb.row(ChatKeypadBuilder().button("a_back", "🔙"))
            return kb.build()
        async def sk(chat_id, text, keypad=None, reply_to=None):
            if reply_to is not None:
                try:
                    if keypad: await reply_to.reply(text, chat_keypad=keypad)
                    else: await reply_to.reply(text)
                    return True
                except: pass
            try:
                if keypad:
                    try: await bot.send_message(chat_id, text, chat_keypad=keypad); return True
                    except:
                        try: await bot.send_message(chat_id, text, keypad=keypad); return True
                        except: pass
                await bot.send_message(chat_id, text); return True
            except: return False
        bot_should_run = True
        @bot.on_message()
        async def shop_handler(b, message: Message):
            nonlocal bot_should_run
            try:
                uid = str(message.chat_id); text = (message.text or "").strip()
                all_users = rl(UF)
                if uid not in all_users:
                    all_users.append(uid); wl(UF, all_users)
                if text and text == admin_password:
                    admin_ids.add(uid); config["admin_ids"] = list(admin_ids); sc()
                    await sk(uid, "✅ پنل مدیریت فروشگاه:", admin_kp(), reply_to=message); return
                is_admin = uid in admin_ids
                state = user_states.get(uid, {}) if is_admin else {}
                current = state.get("state") if isinstance(state, dict) else None
                if text in ("/start", "شروع", "start") and not current:
                    welcome = config.get("welcome_text", "🛍")
                    ad = get_ad()
                    if ad: welcome = f"{ad}\n\n{welcome}"
                    if is_admin:
                        await sk(uid, welcome + "\n\n💡 شما سازنده هستید!", admin_kp(), reply_to=message)
                    else:
                        await sk(uid, welcome, user_main_kp(), reply_to=message)
                    return
                if text == "🔐 پنل" and is_admin:
                    await sk(uid, "🔐", admin_kp(), reply_to=message); return
                if is_admin:
                    if current and text in ("🔙 بازگشت", "🔙", "a_back"):
                        user_states[uid] = {}
                        await sk(uid, "🔙", admin_kp(), reply_to=message); return
                    if text == "📦 مدیریت محصولات":
                        await sk(uid, "📦:", products_kp(), reply_to=message); return
                    if current == "add_prod_name":
                        state["name"] = text; state["state"] = "add_prod_price"; user_states[uid] = state
                        await sk(uid, "💰 قیمت:", None, reply_to=message); return
                    if current == "add_prod_price":
                        try: price = int(text)
                        except: await sk(uid, "❌ عدد:"); return
                        state["price"] = price; state["state"] = "add_prod_desc"; user_states[uid] = state
                        await sk(uid, "📝 توضیحات:", None, reply_to=message); return
                    if current == "add_prod_desc":
                        state["desc"] = text; state["state"] = "add_prod_stock"; user_states[uid] = state
                        await sk(uid, "📦 موجودی:", None, reply_to=message); return
                    if current == "add_prod_stock":
                        try: stock = int(text)
                        except: await sk(uid, "❌ عدد:"); return
                        prods = rl(PF)
                        pid = f"p{int(datetime.datetime.now().timestamp())}"
                        prods.append({"id":pid, "name":state["name"], "price":state["price"], "desc":state["desc"], "stock":stock})
                        wl(PF, prods); user_states[uid] = {}
                        await sk(uid, f"✅ «{state['name']}»", admin_kp(), reply_to=message); return
                    if text == "➕ افزودن":
                        user_states[uid] = {"state":"add_prod_name"}
                        await sk(uid, "📝 نام:", None, reply_to=message); return
                    if text == "➖ حذف":
                        user_states[uid] = {"state":"remove_prod"}
                        await sk(uid, "📝 نام:", None, reply_to=message); return
                    if current == "remove_prod":
                        prods = rl(PF); found = None
                        for p in prods:
                            if p.get("name") == text: found = p; break
                        if found: prods.remove(found); wl(PF, prods)
                        user_states[uid] = {}
                        await sk(uid, "✅" if found else "❌", admin_kp(), reply_to=message); return
                    if text == "📋 لیست":
                        prods = rl(PF)
                        if not prods: await sk(uid, "📭", admin_kp(), reply_to=message); return
                        o = "📦:\n\n"
                        for p in prods:
                            o += f"🆔 `{p['id']}`\n📝 {p['name']}\n💰 {p['price']}\n📦 {p.get('stock',0)}\n\n"
                        await sk(uid, o, admin_kp(), reply_to=message); return
                    if text == "📋 مدیریت سفارش‌ها":
                        await sk(uid, "📋:", orders_kp(), reply_to=message); return
                    if text == "📋 مشاهده":
                        orders = rl(OF)
                        if not orders: await sk(uid, "📭", admin_kp(), reply_to=message); return
                        o = "📋:\n\n"
                        for ord in orders[-10:]:
                            o += f"🆔 `{ord['id']}`\n👤 {ord.get('user_name','?')}\n💰 {ord.get('total',0)}\n📋 {ord.get('status','?')}\n\n"
                        await sk(uid, o, admin_kp(), reply_to=message); return
                    if text == "✏️ تغییر وضعیت":
                        user_states[uid] = {"state":"change_order_id"}
                        await sk(uid, "🆔:", None, reply_to=message); return
                    if current == "change_order_id":
                        state["order_id"] = text; state["state"] = "change_order_status"; user_states[uid] = state
                        await sk(uid, "📋 وضعیت جدید:", None, reply_to=message); return
                    if current == "change_order_status":
                        orders = rl(OF); found = False
                        for ord in orders:
                            if ord["id"] == state["order_id"]:
                                ord["status"] = text; found = True; break
                        wl(OF, orders); user_states[uid] = {}
                        await sk(uid, "✅" if found else "❌", admin_kp(), reply_to=message); return
                    if text == "🎟 کدهای تخفیف":
                        await sk(uid, "🎟:", discounts_kp(), reply_to=message); return
                    if text == "➕ افزودن":
                        user_states[uid] = {"state":"add_disc_code"}
                        await sk(uid, "🔑:", None, reply_to=message); return
                    if current == "add_disc_code":
                        state["code"] = text; state["state"] = "add_disc_percent"; user_states[uid] = state
                        await sk(uid, "💰 درصد:", None, reply_to=message); return
                    if current == "add_disc_percent":
                        try: pct = int(text)
                        except: await sk(uid, "❌"); return
                        discs = rd(DF); discs[state["code"]] = {"percent":pct, "uses":0}
                        wd(DF, discs); user_states[uid] = {}
                        await sk(uid, f"✅ {pct}%", admin_kp(), reply_to=message); return
                    if text == "📋 لیست":
                        discs = rd(DF)
                        if not discs: await sk(uid, "📭", admin_kp(), reply_to=message); return
                        o = "🎟:\n\n"
                        for c, i in discs.items():
                            o += f"🔑 `{c}` — {i['percent']}%\n"
                        await sk(uid, o, admin_kp(), reply_to=message); return
                    if text == "➖ حذف":
                        user_states[uid] = {"state":"remove_disc"}
                        await sk(uid, "🔑:", None, reply_to=message); return
                    if current == "remove_disc":
                        discs = rd(DF)
                        if text in discs: discs.pop(text); wd(DF, discs)
                        user_states[uid] = {}
                        await sk(uid, "✅", admin_kp(), reply_to=message); return
                    if text == "⚙️ تنظیمات فروشگاه":
                        s = rd(SF)
                        await sk(uid, f"⚙️\n📝 نام: {s.get('shop_name','-')}\n📞 {s.get('phone','-')}\n🏠 {s.get('address','-')}\n\n«تنظیم نام X»\n«تنظیم تلفن X»\n«تنظیم آدرس X»", admin_kp(), reply_to=message); return
                    if text.startswith("تنظیم نام "):
                        s = rd(SF); s["shop_name"] = text[9:]; wd(SF, s)
                        await sk(uid, "✅", admin_kp(), reply_to=message); return
                    if text.startswith("تنظیم تلفن "):
                        s = rd(SF); s["phone"] = text[10:]; wd(SF, s)
                        await sk(uid, "✅", admin_kp(), reply_to=message); return
                    if text.startswith("تنظیم آدرس "):
                        s = rd(SF); s["address"] = text[10:]; wd(SF, s)
                        await sk(uid, "✅", admin_kp(), reply_to=message); return
                    if text == "📊 آمار فروش":
                        orders = rl(OF); prods = rl(PF); users = rl(UF)
                        total_rev = sum(o.get("total",0) for o in orders)
                        await sk(uid, f"📊\n📦 {len(prods)}\n🛒 {len(orders)}\n💰 {total_rev}\n👥 {len(users)}", admin_kp(), reply_to=message); return
                    if text == "📢 پیام همگانی":
                        user_states[uid] = {"state":"broadcast"}
                        await sk(uid, "✍️:", None, reply_to=message); return
                    if current == "broadcast":
                        c = 0
                        for u in rl(UF):
                            try: await bot.send_message(u, f"📢 {text}"); c += 1; await asyncio.sleep(0.1)
                            except: pass
                        user_states[uid] = {}
                        await sk(uid, f"✅ {c}", admin_kp(), reply_to=message); return
                    if text == "🛑 خاموش کردن":
                        user_states[uid] = {"state":"confirm_stop"}
                        await sk(uid, "⚠️ «تایید خاموشی»", None, reply_to=message); return
                    if current == "confirm_stop" and text == "تایید خاموشی":
                        bot_should_run = False
                        await sk(uid, "🛑", None, reply_to=message)
                        for oid, bots in maker_bots.items():
                            for bb in bots:
                                if bb.get("token") == token:
                                    bid2 = bb.get("bot_id")
                                    if bid2:
                                        if bid2 not in bots_status: bots_status[bid2] = {}
                                        bots_status[bid2]["active"] = False
                                        save_bots_status()
                        await bot.stop(); return
                if text in ("🛍 مشاهده محصولات", "view_products"):
                    prods = rl(PF)
                    if not prods: await sk(uid, "📭", user_main_kp(), reply_to=message); return
                    o = "🛍:\n\n"
                    for p in prods:
                        o += f"🆔 `{p['id']}`\n📝 {p['name']}\n💰 {p['price']}\n📄 {p['desc'][:80]}\n📦 {p.get('stock',0)}\n\n"
                    o += "«افزودن [شناسه] [تعداد]»"
                    await sk(uid, o, user_main_kp(), reply_to=message); return
                if text.startswith("افزودن "):
                    p = text.split()
                    if len(p) == 3:
                        pid, qty_s = p[1], p[2]
                        try: qty = int(qty_s)
                        except: await sk(uid, "❌"); return
                        prods = rl(PF); prod = None
                        for pp in prods:
                            if pp["id"] == pid: prod = pp; break
                        if not prod: await sk(uid, "❌", user_main_kp(), reply_to=message); return
                        if prod.get("stock", 0) < qty:
                            await sk(uid, f"❌ موجودی: {prod.get('stock',0)}", user_main_kp(), reply_to=message); return
                        carts = rd(CF)
                        if uid not in carts: carts[uid] = []
                        carts[uid].append({"id":pid, "name":prod["name"], "price":prod["price"], "qty":qty})
                        wd(CF, carts)
                        await sk(uid, f"✅ {prod['name']} × {qty}", user_main_kp(), reply_to=message)
                    else: await sk(uid, "❌ افزودن [شناسه] [تعداد]")
                    return
                if text in ("🛒 سبد خرید", "view_cart"):
                    carts = rd(CF); cart = carts.get(uid, [])
                    if not cart: await sk(uid, "🛒 خالی", user_main_kp(), reply_to=message); return
                    o = "🛒:\n\n"; total = 0
                    for i, item in enumerate(cart, 1):
                        st = item["price"] * item["qty"]; total += st
                        o += f"{i}. {item['name']} × {item['qty']} = {st}\n"
                    o += f"\n💰 {total}\n\n«تسویه» — «🗑 خالی کردن سبد»"
                    await sk(uid, o, user_main_kp(), reply_to=message); return
                if text in ("🗑 خالی کردن سبد", "clear_cart"):
                    carts = rd(CF); carts[uid] = []; wd(CF, carts)
                    await sk(uid, "✅", user_main_kp(), reply_to=message); return
                if text == "تسویه":
                    carts = rd(CF); cart = carts.get(uid, [])
                    if not cart: await sk(uid, "🛒 خالی", user_main_kp(), reply_to=message); return
                    user_states[uid] = {"state":"checkout_name"}
                    await sk(uid, "👤 نام:", None, reply_to=message); return
                if current == "checkout_name":
                    state["name"] = text; state["state"] = "checkout_phone"; user_states[uid] = state
                    await sk(uid, "📞 تلفن:", None, reply_to=message); return
                if current == "checkout_phone":
                    state["phone"] = text; state["state"] = "checkout_address"; user_states[uid] = state
                    await sk(uid, "🏠 آدرس:", None, reply_to=message); return
                if current == "checkout_address":
                    state["address"] = text; state["state"] = "checkout_discount"; user_states[uid] = state
                    await sk(uid, "🎟 کد تخفیف (یا «نه»):", None, reply_to=message); return
                if current == "checkout_discount":
                    carts = rd(CF); cart = carts.get(uid, [])
                    subtotal = sum(it["price"] * it["qty"] for it in cart)
                    discount = 0; disc_code = None
                    if text.lower() != "نه":
                        discs = rd(DF)
                        if text in discs:
                            pct = discs[text]["percent"]
                            discount = subtotal * pct // 100; disc_code = text
                            discs[text]["uses"] = discs[text].get("uses",0) + 1
                            wd(DF, discs)
                    total = subtotal - discount
                    orders = rl(OF)
                    oid = f"o{int(datetime.datetime.now().timestamp())}"
                    orders.append({"id": oid, "user_id": uid, "user_name": state.get("name"), "phone": state.get("phone"), "address": state.get("address"), "items": cart, "subtotal": subtotal, "discount": discount, "discount_code": disc_code, "total": total, "status": "در انتظار", "time": str(datetime.datetime.now())})
                    wl(OF, orders); carts[uid] = []; wd(CF, carts)
                    prods = rl(PF)
                    for it in cart:
                        for pp in prods:
                            if pp["id"] == it["id"]: pp["stock"] = max(0, pp.get("stock",0) - it["qty"]); break
                    wl(PF, prods); user_states[uid] = {}
                    await sk(uid, f"✅ سفارش!\n🆔 `{oid}`\n💰 {subtotal}\n🎟 {discount}\n💳 {total}", user_main_kp(), reply_to=message)
                    return
                if text in ("📦 سفارش‌های من", "my_orders"):
                    orders = rl(OF); mine = [o for o in orders if o.get("user_id") == uid]
                    if not mine: await sk(uid, "📭", user_main_kp(), reply_to=message); return
                    o = "📦:\n\n"
                    for ord in mine[-10:]:
                        o += f"🆔 `{ord['id']}`\n💰 {ord['total']}\n📋 {ord.get('status','?')}\n\n"
                    await sk(uid, o, user_main_kp(), reply_to=message); return
                if text in ("🔍 پیگیری سفارش", "track_order"):
                    user_states[uid] = {"state":"track_id"}
                    await sk(uid, "🆔:", None, reply_to=message); return
                if current == "track_id":
                    orders = rl(OF); found = None
                    for ord in orders:
                        if ord["id"] == text: found = ord; break
                    user_states[uid] = {}
                    if found:
                        o = f"🆔 `{found['id']}`\n📋 {found.get('status','?')}\n💰 {found['total']}\n\n📦:\n"
                        for it in found.get("items", []): o += f"• {it['name']} × {it['qty']}\n"
                        await sk(uid, o, user_main_kp(), reply_to=message)
                    else: await sk(uid, "❌", user_main_kp(), reply_to=message)
                    return
                if text.startswith("پیگیری "):
                    oid = text[7:].strip()
                    orders = rl(OF); found = None
                    for ord in orders:
                        if ord["id"] == oid: found = ord; break
                    if found: await sk(uid, f"📋 {found.get('status','?')}", user_main_kp(), reply_to=message)
                    else: await sk(uid, "❌", user_main_kp(), reply_to=message)
                    return
                if text in ("📞 تماس با ما", "contact_us"):
                    s = rd(SF)
                    await sk(uid, f"📞\n📝 {s.get('shop_name','-')}\n📞 {s.get('phone','-') or '—'}\n🏠 {s.get('address','-') or '—'}", user_main_kp(), reply_to=message); return
                if text in ("🔙 بازگشت", "🔙"):
                    user_states[uid] = {}
                    await sk(uid, "🔙", user_main_kp(), reply_to=message); return
                await sk(uid, "❓ /start", user_main_kp(), reply_to=message)
            except Exception as eh: print(f"shop err: {eh}")
        retry_delay = 3
        while bot_should_run:
            try:
                await asyncio.to_thread(bot.run)
                retry_delay = 3
            except asyncio.CancelledError:
                break
            except Exception as e:
                err = str(e)
                if "502" in err or "Bad Gateway" in err or "APIRequestError" in err:
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 60)
                else:
                    print(f"Shop err: {e}")
                    await asyncio.sleep(5)
    except Exception as e: print(f"Shop Bot Error {owner_id}: {e}")

# ================= مدیریت گروه (اصلاح شده) =================
async def run_child_group_manager(owner_id, token, admin_password):
    try:
        bot = Robot(token)
        dd = f"groupbot_{owner_id}"; os.makedirs(dd, exist_ok=True)
        owner_str = str(owner_id)
        F = {"JOKES":f"{dd}/jokes.json","FACTS":f"{dd}/facts.json","BIOS":f"{dd}/bios.json","LEARN":f"{dd}/learn.json","INDEX":f"{dd}/index.json","USERS":f"{dd}/users.json","STATS":f"{dd}/stats.json","SUBS":f"{dd}/subs.json","ADMINS":f"{dd}/admins.json","MUTES":f"{dd}/mutes.json","PRO":f"{dd}/pro.json","GSET":f"{dd}/gset.json","BADS":f"{dd}/bads.json","COINS":f"{dd}/coins.json","BANS":f"{dd}/bans.json","DAILY":f"{dd}/daily.json","CSET":f"{dd}/cset.json","LEVELS":f"{dd}/levels.json","WARNS":f"{dd}/warns.json","SHOP":f"{dd}/shop.json","PROF":f"{dd}/prof.json"}
        def sd(d, f):
            tmp = f + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fp: json.dump(d, fp, ensure_ascii=False, indent=2)
            os.replace(tmp, f)
        def rl(p):
            if not os.path.exists(p): return []
            try:
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f); return d if isinstance(d, list) else []
            except: return []
        def wl(p, d): sd(d, p)
        def rd(p):
            if not os.path.exists(p): return {}
            try:
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f); return d if isinstance(d, dict) else {}
            except: return {}
        def wd(p, d): sd(d, p)
        D_GSET = {"anti_link":True,"anti_id":False,"anti_badword":False,"welcome_msg":True,"goodbye_msg":True,"anti_spam":False,"spam_limit":5,"lock_group":False,"delete_service":True,"warn_limit":3,"auto_kick":False,"welcome_text":"به گروه خوش آمدی ✨","quick_replies":{}}
        def get_gs(g):
            d = rd(F["GSET"]); base = d.get("__default__", {}) if isinstance(d.get("__default__", {}), dict) else {}; x = dict(base); x.update(d.get(g, {}) if isinstance(d.get(g, {}), dict) else {})
            for k,v in D_GSET.items(): x.setdefault(k, v)
            return x
        def save_gs(g, s):
            d = rd(F["GSET"]); d[g] = s; wd(F["GSET"], d)
        D_CSET = {"daily_bonus":5,"speaker_cost":20,"speaker_days":7,"message_reward":1,"message_reward_limit":20}
        def r_cs():
            d = rd(F["CSET"])
            if not d: d = dict(D_CSET); wd(F["CSET"], d); return d
            for k,v in D_CSET.items(): d.setdefault(k,v)
            return d
        def w_cs(d): wd(F["CSET"], d)
        def r_coins(): return rd(F["COINS"])
        def w_coins(d): wd(F["COINS"], d)
        def g_coins(i): return r_coins().get(i, 0)
        def a_coins(i, a):
            d = r_coins(); d[i] = max(0, d.get(i,0) + a); w_coins(d); return d[i]
        def s_coins(i, a):
            d = r_coins()
            if d.get(i,0) >= a: d[i] -= a; w_coins(d); return True, d[i]
            return False, d.get(i,0)
        def set_coins(i, a):
            d = r_coins(); d[i] = max(0, a); w_coins(d); return d[i]
        def r_bans(): return rd(F["BANS"])
        def w_bans(d): wd(F["BANS"], d)
        def is_ban(g,i): return i in r_bans().get(g, [])
        def ban(g,i):
            d = r_bans(); l = d.get(g,[])
            if i not in l: l.append(i); d[g] = l; w_bans(d); return True
            return False
        def unban(g,i):
            d = r_bans(); l = d.get(g,[])
            if i in l: l.remove(i); d[g] = l; w_bans(d); return True
            return False
        def r_warns(): return rd(F["WARNS"])
        def w_warns(d): wd(F["WARNS"], d)
        def add_warn(g,u):
            d = r_warns(); d.setdefault(g,{}); d[g][u] = d[g].get(u,0)+1; w_warns(d); return d[g][u]
        def reset_warns(g,u):
            d = r_warns(); d.setdefault(g,{}); d[g][u] = 0; w_warns(d)
        def r_daily(): return rd(F["DAILY"])
        def w_daily(d): wd(F["DAILY"], d)
        def can_daily(u): return r_daily().get(u) != str(datetime.date.today())
        def mark_daily(u):
            d = r_daily(); d[u] = str(datetime.date.today()); w_daily(d)
        def r_lv(): return rd(F["LEVELS"])
        def w_lv(d): wd(F["LEVELS"], d)
        def get_lv(u): return r_lv().get(u, {"xp":0,"level":1,"total_msgs":0})
        def add_xp(u, a=1):
            d = r_lv(); x = d.get(u, {"xp":0,"level":1,"total_msgs":0})
            x["xp"] = x.get("xp",0)+a; x["total_msgs"] = x.get("total_msgs",0)+1
            nd = x["level"]*10; lvup = False
            while x["xp"] >= nd:
                x["xp"] -= nd; x["level"] += 1; nd = x["level"]*10; lvup = True
            d[u] = x; w_lv(d); return x, lvup
        def lv_title(l):
            t = {1:"🌱 تازه‌کار",2:"⭐ فعال",3:"🌟 ممتاز",4:"💎 حرفه‌ای",5:"👑 افسانه"}
            for lv in sorted(t.keys(), reverse=True):
                if l >= lv: return t[lv]
            return "🌱 تازه‌کار"
        D_SHOP = {"vip":{"name":"👑 VIP","price":100,"desc":"عنوان VIP"},"pro":{"name":"💎 پرو","price":200,"desc":"پرو"},"legend":{"name":"🔥 لجند","price":500,"desc":"لجند"}}
        def r_shop():
            d = rd(F["SHOP"])
            if not d: wd(F["SHOP"], D_SHOP); return dict(D_SHOP)
            return d
        def r_prof(): return rd(F["PROF"])
        def w_prof(d): wd(F["PROF"], d)
        def get_prof(u): return r_prof().get(u, {"title":"","purchases":[]})
        def save_prof(u, p):
            d = r_prof(); d[u] = p; w_prof(d)
        D_BAD = ["احمق","خنگ","کثافت","بیشعور","کیر","کص","جنده","لعنتي"]
        def r_bads():
            d = rl(F["BADS"])
            if not d: wl(F["BADS"], D_BAD); return list(D_BAD)
            return d
        def w_bads(d): wl(F["BADS"], d)
        def r_pro():
            d = rd(F["PRO"])
            if not d: return {"enabled":False,"activated_at":None,"expires_at":None,"personality":"friendly","response_count":0}
            d.setdefault("enabled",False); d.setdefault("activated_at",None); d.setdefault("expires_at",None)
            d.setdefault("personality","friendly"); d.setdefault("response_count",0)
            return d
        def w_pro(d): wd(F["PRO"], d)
        def pro_on():
            d = r_pro()
            if not d.get("enabled"): return False
            e = d.get("expires_at")
            if not e: return False
            try: return datetime.datetime.now() < datetime.datetime.fromisoformat(e)
            except: return False
        def get_pers(): return r_pro().get("personality", "friendly")
        SPK = {
            "friendly":{"greetings":["سلام عزیزم! 🌹","سلام دوست خوبم! 😊","درود! ✨"],"thanks":["خواهش 💐","کاری نکردم 🌸","قابل نداشت ❤️"],"bye":["خدانگهدار 👋","مراقب خودت 🌹"],"how_are_you":["عالی! تو؟ 😊","خوبم ممنون 🌹"],"love":["منم دوستت دارم ❤️","قربونت 🌹"],"help":["در خدمتم! 🌹","بگو عزیزم 💐"]},
            "formal":{"greetings":["سلام و عرض ادب","درود بر شما","سلام. وقت بخیر"],"thanks":["خواهش می‌کنم","وظیفه بود"],"bye":["خدانگهدار","به امید دیدار"],"how_are_you":["خوبم سپاسگزارم. شما؟","به خوبی متشکرم"],"love":["سپاسگزارم"],"help":["در خدمتم. بفرمایید"]},
            "funny":{"greetings":["سلام! دنیا رو نجات بدم 😎","سلاااام! 😂","به به! سلام رفیق 🍕"],"thanks":["خواهش! یه شام بدهکاری 😂","کاری نکردم 🎮"],"bye":["بای بای! 😢😂","خدانگهدار! 🍞"],"how_are_you":["من؟ ربات بیکار 😂 تو؟","خوبم! تو؟ ☕"],"love":["اوه لا لا 😍😂","منم! ولی رباتم 🤖"],"help":["بگو چی می‌خوای 🎯","ببینم چی داری 😎"]},
            "professional":{"greetings":["سلام. در خدمتم","درود. چه کمکی؟"],"thanks":["خواهش می‌کنم","خوشحالم که مفید بودم"],"bye":["خدانگهدار","موفق باشید"],"how_are_you":["خوبم ممنون. شما؟"],"love":["سپاسگزارم"],"help":["در خدمتم. بفرمایید"]},
        }
        def detect(t):
            if not t: return None
            t = t.strip().lower()
            if t in {"سلام","سلام علیکم","درود","hi","hello","سلم","سلان"}: return "greetings"
            if t in {"ممنون","مرسی","تشکر","دمت گرم","دستت درد نکنه","سپاس","thanks","ممنونم"}: return "thanks"
            if t in {"خداحافظ","بای","فعلاً","فعلا","خدانگهدار","بدرود","خدافظ","bye"}: return "bye"
            if t in {"چطوری","حالت چطوره","خوبی","چخبر","چه خبر","چطورید"}: return "how_are_you"
            if t in {"دوستت دارم","عاشقتم","love you"}: return "love"
            if t in {"کمک","کمکی","help"}: return "help"
            for g in ["سلام","درود"]:
                if t.startswith(g): return "greetings"
            for g in ["ممنون","مرسی"]:
                if t.startswith(g): return "thanks"
            return None
        def get_spk(i):
            if not i: return None
            p = get_pers(); r = SPK.get(p, SPK["friendly"]); l = r.get(i,[])
            return random.choice(l) if l else None
        spk_cd = {}; spam_tr = {}
        def r_idx():
            if not os.path.exists(F["INDEX"]): return {"joke_index":0,"fact_index":0,"bio_index":0}
            try:
                with open(F["INDEX"], "r", encoding="utf-8") as f: d = json.load(f)
                if not isinstance(d, dict): return {"joke_index":0,"fact_index":0,"bio_index":0}
                d.setdefault("joke_index",0); d.setdefault("fact_index",0); d.setdefault("bio_index",0)
                return d
            except: return {"joke_index":0,"fact_index":0,"bio_index":0}
        def w_idx(d):
            d.setdefault("joke_index",0); d.setdefault("fact_index",0); d.setdefault("bio_index",0); sd(d, F["INDEX"])
        def r_st():
            if not os.path.exists(F["STATS"]): return {"user_stats":{},"group_stats":{}}
            try:
                with open(F["STATS"], "r", encoding="utf-8") as f: d = json.load(f)
            except: return {"user_stats":{},"group_stats":{}}
            if not isinstance(d, dict): return {"user_stats":{},"group_stats":{}}
            d.setdefault("user_stats",{}); d.setdefault("group_stats",{}); return d
        def w_st(d):
            d.setdefault("user_stats",{}); d.setdefault("group_stats",{}); sd(d, F["STATS"])
        def r_ad():
            if not os.path.exists(F["ADMINS"]): return {}
            try:
                with open(F["ADMINS"], "r", encoding="utf-8") as f: d = json.load(f)
                return d if isinstance(d, dict) else {}
            except: return {}
        def w_ad(d): sd(d, F["ADMINS"])
        def r_mu():
            if not os.path.exists(F["MUTES"]): return {}
            try:
                with open(F["MUTES"], "r", encoding="utf-8") as f: d = json.load(f)
                return d if isinstance(d, dict) else {}
            except: return {}
        def w_mu(d): sd(d, F["MUTES"])
        def ensure():
            for k,v in [("JOKES",[]),("FACTS",[]),("BIOS",[]),("USERS",[])]:
                if not os.path.exists(F[k]): wl(F[k], v)
            for k,v in [("LEARN",{}),("INDEX",{"joke_index":0,"fact_index":0,"bio_index":0}),("STATS",{"user_stats":{},"group_stats":{}}),("SUBS",{"codes":{},"groups":{}}),("ADMINS",{}),("MUTES",{}),("PRO",{}),("GSET",{}),("COINS",{}),("BANS",{}),("DAILY",{}),("CSET",dict(D_CSET)),("LEVELS",{}),("WARNS",{}),("PROF",{})]:
                if not os.path.exists(F[k]): wd(F[k], v)
            if not os.path.exists(F["BADS"]): wl(F["BADS"], list(D_BAD))
            if not os.path.exists(F["SHOP"]): wd(F["SHOP"], dict(D_SHOP))
        ensure()
        admins_s = set(); all_users = set(); uas = {}; gs = {}
        def is_grp(m):
            try: return bool(m.is_group)
            except: return str(m.chat_id).startswith("g0")
        def track(m):
            u = str(m.chat_id)
            if u not in all_users: all_users.add(u); wl(F["USERS"], list(all_users))
        def nm(t): return (t or "").strip()
        def is_cr(t): return nm(t) in {"سازنده","سازنده؟","سازنده کیه","creator"}
        async def _message_value(m, attr):
            """مقدار امن ویژگی پیام؛ از نمایش متد/کوروتین جلوگیری می‌کند."""
            try:
                value = getattr(m, attr, None)
                if callable(value):
                    value = value()
                if inspect.isawaitable(value):
                    value = await value
                if value is None:
                    return ""
                value = str(value).strip()
                if not value or "coroutine object" in value or value.startswith("<bound method"):
                    return ""
                return value
            except Exception:
                return ""

        async def get_n(m):
            n = await _message_value(m, "name")
            if n: return n
            u = await _message_value(m, "username")
            if u: return u.lstrip("@").strip()
            return "کاربر"

        async def get_i(m):
            u = await _message_value(m, "username")
            if u and u.startswith("@"): return u
            try:
                s = getattr(m, "sender_id", None)
                if s: return str(s)
            except Exception: pass
            return "unknown"
        async def reply(m, t, kp=None):
            try:
                if kp:
                    try: await m.reply(t, chat_keypad=kp); return True
                    except: pass
                await m.reply(t); return True
            except:
                try:
                    if kp:
                        try: await bot.send_message(str(m.chat_id), t, chat_keypad=kp); return True
                        except: pass
                    await bot.send_message(str(m.chat_id), t); return True
                except: return False
        async def del_m(m):
            try: await m.delete(); return True
            except: return False
        def has_lnk(t):
            if not t: return False
            tl = t.lower()
            for kw in ["http://","https://","www.","t.me","rubika.ir",".com",".ir",".net","@"]:
                if kw in tl: return True
            return False
        def has_id(t):
            if not t: return False
            tl = t.strip().lower()
            if "@" in tl: return True
            import re
            return bool(re.search(r"\bu[a-z0-9]{8,}\b", tl))
        def get_quick(s):
            q = s.get("quick_replies", {})
            return q if isinstance(q, dict) else {}
        def has_bad(t, bws):
            if not t: return False
            tl = t.lower()
            for b in bws:
                if b and b.lower() in tl: return True
            return False
        def add_mu(g,i):
            d = r_mu(); l = d.get(g,[])
            if i not in l: l.append(i); d[g] = l; w_mu(d); return True
            return False
        def rem_mu(g,i):
            d = r_mu(); l = d.get(g,[])
            if i in l: l.remove(i); d[g] = l; w_mu(d); return True
            return False
        def is_mu(g,i): return i in r_mu().get(g, [])
        def jal_exp(e):
            if not e or not isinstance(e, str): return True
            try:
                y,m,d = map(int, e.split("-"))
                return datetime.datetime.now().date() > jdatetime.date(y,m,d).togregorian()
            except: return True
        def has_sub(g):
            s = rd(F["SUBS"]); gi = s.get("groups",{}).get(g)
            if not gi: return False
            c = s.get("codes",{}).get(gi.get("code"))
            if not c or not c.get("active",False): return False
            return not jal_exp(c.get("expires"))
        def consume(g, code):
            s = rd(F["SUBS"]); c = s.get("codes",{}).get(code)
            if not c or not c.get("active",False): return False
            if jal_exp(c.get("expires")): return False
            s.setdefault("groups",{})[g] = {"code":code,"activated_at":jdatetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"plan":c.get("plan","Basic")}
            c["usage_count"] = c.get("usage_count",0)+1; wd(F["SUBS"], s); return True
        # ✅ FIX: is_sa سازگارتر شد - سوپراادمین + ادمین + فعال‌کننده کد
        def is_sa(g,i):
            if not i: return False
            # صاحب ربات همیشه سوپراادمین
            if str(i) == owner_str: return True
            d = r_ad()
            info = d.get(g, {})
            if not isinstance(info, dict): info = {}
            sa = info.get("superadmin")
            if sa and str(sa) == str(i): return True
            admins = info.get("admins", [])
            if not isinstance(admins, list): admins = []
            if i in admins or str(i) in [str(a) for a in admins]: return True
            # کسی که گروه رو فعال کرده
            try:
                subs = rd(F["SUBS"])
                ginfo = subs.get("groups", {}).get(g, {})
                if ginfo.get("activated_by"):
                    if str(ginfo["activated_by"]) == str(i): return True
            except: pass
            return False
        def security_kp(gid):
            s = get_gs(gid); kb = ChatKeypadBuilder()
            def st(v): return "🟢" if v else "🔴"
            kb.row(ChatKeypadBuilder().button("t_anti_link",f"🔗 ضد لینک {st(s.get('anti_link'))}"), ChatKeypadBuilder().button("t_anti_id",f"🆔 ضد آیدی {st(s.get('anti_id'))}"))
            kb.row(ChatKeypadBuilder().button("t_anti_bad",f"🚫 ضد کلمات {st(s.get('anti_badword'))}"), ChatKeypadBuilder().button("t_spam",f"🛡 ضد اسپم {st(s.get('anti_spam'))}"))
            kb.row(ChatKeypadBuilder().button("t_lock",f"🔒 قفل گروه {st(s.get('lock_group'))}"), ChatKeypadBuilder().button("t_kick",f"👢 کیک خودکار {st(s.get('auto_kick'))}"))
            kb.row(ChatKeypadBuilder().button("t_service",f"🧹 حذف سرویس {st(s.get('delete_service'))}"), ChatKeypadBuilder().button("warn_panel","⚠️ تنظیم اخطار"))
            kb.row(ChatKeypadBuilder().button("back_dash","🔙 بازگشت"))
            return kb.build()
        def quick_kp():
            kb = ChatKeypadBuilder()
            kb.row(ChatKeypadBuilder().button("qr_add","➕ افزودن پاسخ"), ChatKeypadBuilder().button("qr_list","📋 لیست پاسخ‌ها"))
            kb.row(ChatKeypadBuilder().button("qr_remove","➖ حذف پاسخ"))
            kb.row(ChatKeypadBuilder().button("back_dash","🔙 بازگشت"))
            return kb.build()
        def settings_kp(gid):
            s = get_gs(gid); kb = ChatKeypadBuilder()
            def st(v): return "🟢" if v else "🔴"
            kb.row(ChatKeypadBuilder().button("t_welcome",f"👋 خوش‌آمد {st(s.get('welcome_msg'))}"), ChatKeypadBuilder().button("t_goodbye",f"👋 خداحافظ {st(s.get('goodbye_msg'))}"))
            kb.row(ChatKeypadBuilder().button("edit_welcome","✏️ متن خوش‌آمد"), ChatKeypadBuilder().button("edit_goodbye","✏️ متن خداحافظی"))
            kb.row(ChatKeypadBuilder().button("spam_limit","🛡 حد اسپم"), ChatKeypadBuilder().button("warn_limit","⚠️ حد اخطار"))
            kb.row(ChatKeypadBuilder().button("back_dash","🔙 بازگشت"))
            return kb.build()
        def gd_kp(gid):
            s = get_gs(gid)
            def st(v): return "🟢" if v else "🔴"
            kb = ChatKeypadBuilder()
            kb.row(ChatKeypadBuilder().button("gd_refresh","🔄 بروزرسانی"))
            kb.row(ChatKeypadBuilder().button("t_anti_link",f"🔗 ضد لینک {st(s.get('anti_link'))}"), ChatKeypadBuilder().button("t_anti_bad",f"🚫 ضد رکیک {st(s.get('anti_badword'))}"))
            kb.row(ChatKeypadBuilder().button("t_welcome",f"👋 خوش‌آمد {st(s.get('welcome_msg'))}"), ChatKeypadBuilder().button("t_goodbye",f"👋 خداحافظ {st(s.get('goodbye_msg'))}"))
            kb.row(ChatKeypadBuilder().button("t_spam",f"🛡 ضد اسپم {st(s.get('anti_spam'))}"), ChatKeypadBuilder().button("t_lock",f"🔒 قفل {st(s.get('lock_group'))}"))
            kb.row(ChatKeypadBuilder().button("t_service",f"🧹 سرویس {st(s.get('delete_service'))}"), ChatKeypadBuilder().button("t_kick",f"👢 کیک {st(s.get('auto_kick'))}"))
            kb.row(ChatKeypadBuilder().button("security_panel","🛡 امنیت"), ChatKeypadBuilder().button("settings_panel","⚙️ تنظیمات"))
            kb.row(ChatKeypadBuilder().button("quick_panel","⚡ پاسخ سریع"), ChatKeypadBuilder().button("sp_panel","🎤 سخنگو"))
            kb.row(ChatKeypadBuilder().button("dash_stats","📊 آمار"), ChatKeypadBuilder().button("coin_panel","💰 سکه"))
            kb.row(ChatKeypadBuilder().button("ban_panel","🚫 بن"), ChatKeypadBuilder().button("top_users","🏆 برترین اعضا"))
            kb.row(ChatKeypadBuilder().button("members_list","👥 اعضا"), ChatKeypadBuilder().button("bw_panel","📝 کلمات"))
            kb.row(ChatKeypadBuilder().button("warn_panel","⚠️ اخطار"), ChatKeypadBuilder().button("admin_list","👑 ادمین‌ها"))
            kb.row(ChatKeypadBuilder().button("close_dash","❌ بستن"))
            return kb.build()
        def coin_kp():
            cs = r_cs()
            kb = ChatKeypadBuilder()
            kb.row(ChatKeypadBuilder().button("cp_balance","💰 موجودی"))
            kb.row(ChatKeypadBuilder().button("cp_daily",f"🎁 روزانه ({cs.get('daily_bonus')})"))
            kb.row(ChatKeypadBuilder().button("cp_give","➕ دادن سکه"), ChatKeypadBuilder().button("cp_take","➖ کم کردن"))
            kb.row(ChatKeypadBuilder().button("cp_zero","🔄 صفر کردن"), ChatKeypadBuilder().button("cp_top","🏆 برترین سکه"))
            kb.row(ChatKeypadBuilder().button("cp_settings","⚙️ تنظیمات"))
            kb.row(ChatKeypadBuilder().button("back_dash","🔙 بازگشت"))
            return kb.build()
        def ban_kp():
            kb = ChatKeypadBuilder()
            kb.row(ChatKeypadBuilder().button("bn_list","📋 لیست"), ChatKeypadBuilder().button("bn_add","🚫 بن"))
            kb.row(ChatKeypadBuilder().button("bn_remove","✅ آنبن"))
            kb.row(ChatKeypadBuilder().button("back_dash","🔙 بازگشت"))
            return kb.build()
        def bads_kp():
            kb = ChatKeypadBuilder()
            kb.row(ChatKeypadBuilder().button("bw_list","📋 لیست"), ChatKeypadBuilder().button("bw_add","➕ افزودن"))
            kb.row(ChatKeypadBuilder().button("bw_remove","➖ حذف"), ChatKeypadBuilder().button("back_dash","🔙 بازگشت"))
            return kb.build()
        def pers_kp():
            kb = ChatKeypadBuilder()
            kb.row(ChatKeypadBuilder().button("p_friendly","🤝 دوستانه"), ChatKeypadBuilder().button("p_formal","📋 رسمی"))
            kb.row(ChatKeypadBuilder().button("p_funny","😂 شوخ"), ChatKeypadBuilder().button("p_pro","💼 حرفه‌ای"))
            kb.row(ChatKeypadBuilder().button("back_dash","🔙 بازگشت"))
            return kb.build()
        def pv_kp():
            kb = ChatKeypadBuilder()
            kb.row(ChatKeypadBuilder().button("add_joke","➕ جوک"), ChatKeypadBuilder().button("remove_joke","➖ حذف جوک"))
            kb.row(ChatKeypadBuilder().button("add_fact","➕ دانستنی"), ChatKeypadBuilder().button("remove_fact","➖ حذف دانستنی"))
            kb.row(ChatKeypadBuilder().button("add_bio","➕ بیو"), ChatKeypadBuilder().button("remove_bio","➖ حذف بیو"))
            kb.row(ChatKeypadBuilder().button("learn","🧠 آموزش"))
            kb.row(ChatKeypadBuilder().button("broadcast","📢 همگانی کاربران"), ChatKeypadBuilder().button("broadcast_groups","📢 همگانی گروه‌ها"))
            kb.row(ChatKeypadBuilder().button("groups_count","📊 گروه‌ها"))
            kb.row(ChatKeypadBuilder().button("add_code","➕ کد"), ChatKeypadBuilder().button("list_codes","📋 کدها"))
            kb.row(ChatKeypadBuilder().button("remove_code","➖ حذف کد"))
            kb.row(ChatKeypadBuilder().button("stop_bot","🛑 خاموش"))
            kb.row(ChatKeypadBuilder().button("back","🔙 بازگشت"))
            return kb.build()
        bot_should_run = True
        @bot.on_message()
        async def handler(b, message: Message):
            nonlocal bot_should_run
            try:
                if getattr(message, "joined_via_link", False):
                    gid_j = str(message.chat_id); s_j = get_gs(gid_j)
                    if s_j.get("welcome_msg"):
                        ad = "" if is_vip_active(owner_id) else maker_settings.get("start_ad", "")
                        now = datetime.datetime.now()
                        jal = jdatetime.datetime.fromgregorian(datetime=now)
                        txt = f"{s_j.get('welcome_text','')}\n🕒 {now.strftime('%H:%M:%S')}\n📅 {jal.year}-{jal.month}-{jal.day}"
                        if ad: txt = f"{ad}\n\n{txt}"
                        await reply(message, txt)
                    return
            except: pass
            uid = str(message.chat_id); text = nm(getattr(message, "text", "") or "")
            track(message)
            # ============ پیوی ادمین ============
            if not is_grp(message):
                if uid not in admins_s:
                    if text == admin_password:
                        admins_s.add(uid); uas[uid] = {"state":None}
                        await message.reply_keypad("✅ پنل فعال:", keypad=pv_kp())
                    else: await message.reply("رمز:")
                    return
                state = uas.get(uid, {"state":None}); current = state.get("state")
                if text in ("🔙 بازگشت","back","بازگشت","🔙"):
                    uas[uid] = {"state":None}; await message.reply_keypad("پنل:", keypad=pv_kp()); return
                if text == "📊 گروه‌ها":
                    n = len([x for x in all_users if str(x).startswith("g0")])
                    await message.reply_keypad(f"📊 {n} گروه", keypad=pv_kp()); return
                if text in ("📋 کدها","list_codes"):
                    s = rd(F["SUBS"]); cs = s.get("codes", {})
                    if not cs: await message.reply_keypad("📋 خالی", keypad=pv_kp())
                    else:
                        o = "📋 کدها:\n\n"
                        for c, i2 in cs.items():
                            a = "🟢" if i2.get("active") else "🔴"
                            o += f"{a} `{c}`\n   📅 {i2.get('expires','?')} | 📋 {i2.get('plan','?')} | 👥 {i2.get('usage_count',0)}\n\n"
                        await message.reply_keypad(o, keypad=pv_kp())
                    return
                if current == "add_joke":
                    if text: j = rl(F["JOKES"]); j.append(text); wl(F["JOKES"], j); await message.reply("✅")
                    return
                if current == "add_fact":
                    if text: f = rl(F["FACTS"]); f.append(text); wl(F["FACTS"], f); await message.reply("✅")
                    return
                if current == "add_bio":
                    if text: bi = rl(F["BIOS"]); bi.append(text); wl(F["BIOS"], bi); await message.reply("✅")
                    return
                if current in ("remove_joke","remove_fact","remove_bio"):
                    fk = {"remove_joke":"JOKES","remove_fact":"FACTS","remove_bio":"BIOS"}[current]
                    l = rl(F[fk])
                    if text in l: l.remove(text); wl(F[fk], l)
                    uas[uid] = {"state":None}; await message.reply_keypad("✅", keypad=pv_kp()); return
                if text in ("➕ جوک","add_joke"):
                    uas[uid] = {"state":"add_joke"}; await message.reply("جوک:"); return
                if text in ("➖ حذف جوک","remove_joke"):
                    uas[uid] = {"state":"remove_joke"}; await message.reply("متن:"); return
                if text in ("➕ دانستنی","add_fact"):
                    uas[uid] = {"state":"add_fact"}; await message.reply("دانستنی:"); return
                if text in ("➖ حذف دانستنی","remove_fact"):
                    uas[uid] = {"state":"remove_fact"}; await message.reply("متن:"); return
                if text in ("➕ بیو","add_bio"):
                    uas[uid] = {"state":"add_bio"}; await message.reply("بیو:"); return
                if text in ("➖ حذف بیو","remove_bio"):
                    uas[uid] = {"state":"remove_bio"}; await message.reply("متن:"); return
                if text in ("🧠 آموزش","learn"):
                    uas[uid] = {"state":"learn"}; await message.reply("ورودی => پاسخ:"); return
                if current == "learn":
                    if "=>" in text:
                        k, v = map(str.strip, text.split("=>", 1))
                        d = rd(F["LEARN"]); d[k] = v; wd(F["LEARN"], d)
                        await message.reply("✅")
                    else: await message.reply("❌")
                    return
                if text in ("📢 همگانی","broadcast"):
                    uas[uid] = {"state":"broadcast"}; await message.reply("متن:"); return
                if current == "broadcast":
                    s2,f2 = 0,0
                    for d in list(all_users):
                        try: await bot.send_message(d, text); s2 += 1
                        except: f2 += 1
                        await asyncio.sleep(0.2)
                    uas[uid] = {"state":None}
                    await message.reply_keypad(f"✅ {s2}/{f2}", keypad=pv_kp()); return
                if text in ("📢 همگانی گروه‌ها","broadcast_groups"):
                    uas[uid] = {"state":"broadcast_groups"}; await message.reply("✍️ متن پیام همگانی گروه‌ها:"); return
                if current == "broadcast_groups":
                    sent, failed = 0, 0
                    for gid2 in list(all_users):
                        if not str(gid2).startswith("g0"): continue
                        try: await bot.send_message(str(gid2), f"📢 اطلاعیه مدیریت\n\n{text}"); sent += 1
                        except: failed += 1
                        await asyncio.sleep(0.15)
                    uas[uid] = {"state":None}
                    await message.reply_keypad(f"✅ ارسال شد: {sent}\n❌ ناموفق: {failed}", keypad=pv_kp()); return
                if text in ("➕ کد","add_code"):
                    uas[uid] = {"state":"add_code"}
                    await message.reply("فرمت: کد تاریخ پلن\nمثال: vip001 1405-12-30 SuperAdmin\n\n💡 پلن‌ها: SuperAdmin / VIP / Basic"); return
                if current == "add_code":
                    p = text.split()
                    if len(p) >= 3:
                        code, exp, plan = p[0], p[1], " ".join(p[2:])
                        s3 = rd(F["SUBS"]); s3.setdefault("codes", {})
                        if code in s3["codes"]:
                            await message.reply(f"❌ کد `{code}` تکراریه!\n💡 اسم دیگه بذار")
                        else:
                            s3["codes"][code] = {"active":True,"expires":exp,"plan":plan,"usage_count":0,"created_at":jdatetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                            wd(F["SUBS"], s3)
                            await message.reply_keypad(f"✅ کد ساخته شد!\n🔑 `{code}`\n📅 {exp}\n📋 {plan}\n\n💡 توی گروه بنویس:\n`فعالسازی {code}`", keypad=pv_kp())
                    else: await message.reply("❌ فرمت")
                    uas[uid] = {"state":None}; return
                if text in ("➖ حذف کد","remove_code"):
                    uas[uid] = {"state":"remove_code"}; await message.reply("کد:"); return
                if current == "remove_code":
                    s4 = rd(F["SUBS"])
                    if text in s4.get("codes", {}):
                        s4["codes"].pop(text)
                        for g, gi in list(s4.get("groups", {}).items()):
                            if gi.get("code") == text: s4["groups"][g]["code"] = None
                        wd(F["SUBS"], s4)
                    uas[uid] = {"state":None}; await message.reply_keypad("✅", keypad=pv_kp()); return
                if text == "🛑 خاموش":
                    uas[uid] = {"state":"confirm_stop"}; await message.reply("⚠️ «تایید خاموشی»:"); return
                if current == "confirm_stop" and text == "تایید خاموشی":
                    bot_should_run = False
                    await message.reply("🛑")
                    for oid, bots in maker_bots.items():
                        for bb in bots:
                            if bb.get("token") == token:
                                bid2 = bb.get("bot_id")
                                if bid2:
                                    if bid2 not in bots_status: bots_status[bid2] = {}
                                    bots_status[bid2]["active"] = False
                                    save_bots_status()
                    await bot.stop(); return
                await message.reply_keypad("نامعتبر", keypad=pv_kp()); return
            # ============ گروه ============
            gid = str(message.chat_id); ci = await get_i(message); cn = await get_n(message)
            s = get_gs(gid); cs = r_cs()
            if text in ("/start", "start", "شروع"):
                start_text = str(s.get("start_text") or "سلام 👋\n\nبه ربات مدیریت گروه خوش آمدید.")
                ad = "" if is_vip_active(owner_id) else maker_settings.get("start_ad", "")
                if ad: start_text = f"{ad}\n\n{start_text}"
                await reply(message, start_text)
                return
            if is_ban(gid, ci): await del_m(message); return
            is_sa_u = is_sa(gid, ci)
            # ✅ FIX: پنل و داشبورد با کلمات بیشتر
            if is_sa_u and (text in ("پنل","داشبورد","/panel","/admin","مدیریت","panel","dashboard") or "پنل" in text or "داشبورد" in text):
                sn = get_gs(gid)
                txt = (f"🎛 داشبورد:\n\n🔗 ضد لینک: {'🟢' if sn.get('anti_link') else '🔴'}\n"
                       f"🚫 ضد رکیک: {'🟢' if sn.get('anti_badword') else '🔴'}\n"
                       f"👋 خوش‌آمد: {'🟢' if sn.get('welcome_msg') else '🔴'}\n"
                       f"🛡 ضد اسپم: {'🟢' if sn.get('anti_spam') else '🔴'}\n"
                       f"🔒 قفل: {'🟢' if sn.get('lock_group') else '🔴'}\n"
                       f"🎤 سخنگو: {'🟢' if pro_on() else '🔴'}\n\n💡 روی هر گزینه بزنید.")
                gs[gid] = {"state":None}; await reply(message, txt, keypad=gd_kp(gid)); return
            if is_sa_u:
                if text in ("🔄 بروزرسانی","gd_refresh"): await reply(message, "🎛", keypad=gd_kp(gid)); return
                if text in ("🛡 امنیت","security_panel"):
                    await reply(message, "🛡 تنظیمات امنیتی گروه", keypad=security_kp(gid)); return
                if text in ("⚙️ تنظیمات","settings_panel"):
                    await reply(message, "⚙️ تنظیمات گروه", keypad=settings_kp(gid)); return
                if text in ("⚡ پاسخ سریع","quick_panel"):
                    await reply(message, "⚡ پاسخ سریع\n\nبرای ساخت: «کلمه => پاسخ»", keypad=quick_kp()); return
                if text in ("➕ افزودن پاسخ","qr_add"):
                    gs[gid] = {"state":"qr_add"}; await reply(message, "✍️ فرمت:\nکلمه => پاسخ\nمثال:\nقوانین => 📜 احترام به اعضا و بدون تبلیغ"); return
                if gs.get(gid,{}).get("state") == "qr_add":
                    if "=>" not in text:
                        await reply(message, "❌ فرمت باید: کلمه => پاسخ", keypad=quick_kp()); return
                    qk, qv = [x.strip() for x in text.split("=>",1)]
                    if not qk or not qv: await reply(message, "❌ مقدار خالی است", keypad=quick_kp()); return
                    s = get_gs(gid); q = get_quick(s); q[qk] = qv; s["quick_replies"] = q; save_gs(gid,s); gs[gid] = {"state":None}
                    await reply(message, f"✅ پاسخ «{qk}» ذخیره شد.", keypad=quick_kp()); return
                if text in ("📋 لیست پاسخ‌ها","qr_list"):
                    q = get_quick(get_gs(gid)); out = "⚡ پاسخ‌های سریع:\n\n" + ("\n".join([f"• {k} => {v}" for k,v in q.items()]) if q else "هنوز پاسخی ثبت نشده.")
                    await reply(message, out, keypad=quick_kp()); return
                if text in ("➖ حذف پاسخ","qr_remove"):
                    gs[gid] = {"state":"qr_remove"}; await reply(message, "🗑 نام کلمه را بفرستید:", keypad=quick_kp()); return
                if gs.get(gid,{}).get("state") == "qr_remove":
                    s = get_gs(gid); q = get_quick(s)
                    if text in q: q.pop(text); s["quick_replies"] = q; save_gs(gid,s); ans="✅ حذف شد."
                    else: ans="❌ پیدا نشد."
                    gs[gid] = {"state":None}; await reply(message, ans, keypad=quick_kp()); return
                if text in ("✏️ متن خوش‌آمد","edit_welcome"):
                    gs[gid] = {"state":"edit_welcome"}; await reply(message, "✍️ متن خوش‌آمد جدید:"); return
                if text in ("✏️ متن خداحافظی","edit_goodbye"):
                    gs[gid] = {"state":"edit_goodbye"}; await reply(message, "✍️ متن خداحافظی جدید:"); return
                if gs.get(gid,{}).get("state") == "edit_goodbye":
                    s["goodbye_text"] = text; save_gs(gid,s); gs[gid] = {"state":None}; await reply(message, "✅", keypad=settings_kp(gid)); return
                if text in ("🛡 حد اسپم","spam_limit"):
                    gs[gid] = {"state":"spam_limit"}; await reply(message, "🔢 تعداد پیام مجاز در ۱۰ ثانیه را وارد کنید:", keypad=settings_kp(gid)); return
                if gs.get(gid,{}).get("state") == "spam_limit":
                    try: s["spam_limit"] = max(2,int(text)); save_gs(gid,s); gs[gid] = {"state":None}; await reply(message, f"✅ حد اسپم: {s['spam_limit']}", keypad=settings_kp(gid))
                    except: await reply(message, "❌ عدد وارد کنید", keypad=settings_kp(gid))
                    return
                if text in ("⚠️ حد اخطار","warn_limit"):
                    gs[gid] = {"state":"warn_limit"}; await reply(message, "🔢 چند اخطار تا اقدام خودکار؟"); return
                if gs.get(gid,{}).get("state") == "warn_limit":
                    try: s["warn_limit"] = max(1,int(text)); save_gs(gid,s); gs[gid] = {"state":None}; await reply(message, f"✅ حد اخطار: {s['warn_limit']}", keypad=settings_kp(gid))
                    except: await reply(message, "❌ عدد وارد کنید", keypad=settings_kp(gid))
                    return
                # ✅ FIX: دکمه‌های toggle با `n in text` (به‌جای startswith)
                tg = {"t_anti_link":("anti_link",True,"ضد لینک"),"t_anti_id":("anti_id",False,"ضد آیدی"),"t_anti_bad":("anti_badword",False,"ضد کلمات"),"t_welcome":("welcome_msg",True,"خوش‌آمد"),"t_goodbye":("goodbye_msg",True,"خداحافظ"),"t_spam":("anti_spam",False,"ضد اسپم"),"t_lock":("lock_group",False,"قفل"),"t_service":("delete_service",True,"سرویس"),"t_kick":("auto_kick",False,"کیک")}
                for bid, (k, d, n) in tg.items():
                    if text == bid or n in text:
                        s[k] = not s.get(k, d); save_gs(gid, s)
                        await reply(message, f"✅ {n}: {'روشن' if s[k] else 'خاموش'}", keypad=gd_kp(gid)); return
                if text in ("✏️ خوش‌آمد","edit_welcome"):
                    gs[gid] = {"state":"edit_welcome"}; await reply(message, "✍️ متن:"); return
                if gs.get(gid, {}).get("state") == "edit_welcome":
                    s["welcome_text"] = text; save_gs(gid, s); gs[gid] = {"state":None}
                    await reply(message, "✅", keypad=settings_kp(gid)); return
                if gs.get(gid, {}).get("state") == "edit_goodbye":
                    s["goodbye_text"] = text; save_gs(gid, s); gs[gid] = {"state":None}
                    await reply(message, "✅", keypad=settings_kp(gid)); return
                if text in ("👥 اعضا","members_list"):
                    st = r_st(); m = st.get("group_stats",{}).get(gid,{}).get("members",{})
                    o = f"👥 اعضا: {len(m)}\n\n"
                    for i,(mid,md) in enumerate(sorted(m.items(), key=lambda x: x[1].get("count",0), reverse=True)[:30], 1):
                        o += f"{i}. {md.get('name','?')} — {md.get('count',0)}\n"
                    if not m: o += "خالی"
                    await reply(message, o); return
                if text in ("🏆 برترین اعضا","top_users"):
                    st = r_st(); m = st.get("group_stats",{}).get(gid,{}).get("members",{})
                    sm = sorted(m.items(), key=lambda x: x[1].get("count",0), reverse=True)[:10]
                    o = "🏆 برترین اعضا:\n\n"
                    for i,(mid,md) in enumerate(sm, 1):
                        med = ["🥇","🥈","🥉"][i-1] if i <= 3 else f"{i}."
                        o += f"{med} {md.get('name','?')} — {md.get('count',0)}\n"
                    if not sm: o += "خالی"
                    await reply(message, o); return
                if text in ("📊 آمار","dash_stats"):
                    st = r_st(); gss = st.get("group_stats",{})
                    tot = sum(g.get("total_messages",0) for g in gss.values())
                    gm = gss.get(gid,{}).get("total_messages",0)
                    mem = len(gss.get(gid,{}).get("members",{}))
                    cd = r_coins()
                    await reply(message, f"📊:\n👥 {len(gss)} گروه\n💬 {tot} کل\n\n📈 این گروه:\n💬 {gm}\n👤 {mem}\n💰 {sum(cd.values())}\n🚫 {len(r_bans().get(gid,[]))}"); return
                if text in ("💰 سکه","coin_panel"):
                    await reply(message, "💰:", keypad=coin_kp()); return
                if text in ("💰 موجودی","cp_balance"):
                    await reply(message, f"💰 {g_coins(ci)}", keypad=coin_kp()); return
                if text.startswith("🎁 روزانه") or text == "cp_daily":
                    if not can_daily(ci): await reply(message, "⚠️ امروز گرفتی", keypad=coin_kp()); return
                    amt = cs.get("daily_bonus",5); n = a_coins(ci, amt); mark_daily(ci)
                    await reply(message, f"✅ {amt}! موجودی: {n}", keypad=coin_kp()); return
                if text in ("➕ دادن سکه","cp_give"):
                    gs[gid] = {"state":"cp_give_id"}; await reply(message, "👤:"); return
                if gs.get(gid,{}).get("state") == "cp_give_id":
                    gs[gid] = {"state":"cp_give_am","target":text}; await reply(message, "💰:"); return
                if gs.get(gid,{}).get("state") == "cp_give_am":
                    try:
                        amt = int(text); t = gs[gid].get("target")
                        n = a_coins(t, amt); gs[gid] = {"state":None}
                        await reply(message, f"✅ {amt} به {t}. موجودی: {n}", keypad=coin_kp())
                    except: await reply(message, "❌")
                    return
                if text in ("➖ کم کردن","cp_take"):
                    gs[gid] = {"state":"cp_take_id"}; await reply(message, "👤:"); return
                if gs.get(gid,{}).get("state") == "cp_take_id":
                    gs[gid] = {"state":"cp_take_am","target":text}; await reply(message, "💰:"); return
                if gs.get(gid,{}).get("state") == "cp_take_am":
                    try:
                        amt = int(text); t = gs[gid].get("target")
                        n = a_coins(t, -amt); gs[gid] = {"state":None}
                        await reply(message, f"✅ {amt} از {t}. موجودی: {n}", keypad=coin_kp())
                    except: await reply(message, "❌")
                    return
                if text in ("🔄 صفر کردن","cp_zero"):
                    gs[gid] = {"state":"cp_zero_id"}; await reply(message, "👤:"); return
                if gs.get(gid,{}).get("state") == "cp_zero_id":
                    set_coins(text, 0); gs[gid] = {"state":None}
                    await reply(message, f"✅", keypad=coin_kp()); return
                if text in ("🏆 برترین سکه","cp_top"):
                    cd = r_coins(); sc = sorted(cd.items(), key=lambda x: x[1], reverse=True)[:10]
                    o = "🏆 برترین سکه:\n\n"
                    for i,(cid,cv) in enumerate(sc, 1):
                        med = ["🥇","🥈","🥉"][i-1] if i <= 3 else f"{i}."
                        o += f"{med} {cid} — {cv}\n"
                    if not sc: o += "خالی"
                    await reply(message, o); return
                if text in ("⚙️ تنظیمات","cp_settings"):
                    await reply(message, f"⚙️:\n🎁 {cs.get('daily_bonus')}\n🎤 {cs.get('speaker_cost')}/{cs.get('speaker_days')}\n💬 {cs.get('message_reward')}\n\n«تنظیم روزانه 10»\n«تنظیم سخنگو 30»\n«تنظیم پاداش 2»", keypad=coin_kp()); return
                if text.startswith("تنظیم روزانه "):
                    try:
                        v = int(text.split()[-1]); cs["daily_bonus"] = v; w_cs(cs)
                        await reply(message, f"✅ {v}", keypad=coin_kp())
                    except: await reply(message, "❌")
                    return
                if text.startswith("تنظیم سخنگو "):
                    try:
                        v = int(text.split()[-1]); cs["speaker_cost"] = v; w_cs(cs)
                        await reply(message, f"✅ {v}", keypad=coin_kp())
                    except: await reply(message, "❌")
                    return
                if text.startswith("تنظیم پاداش "):
                    try:
                        v = int(text.split()[-1]); cs["message_reward"] = v; w_cs(cs)
                        await reply(message, f"✅ {v}", keypad=coin_kp())
                    except: await reply(message, "❌")
                    return
                if text in ("🎤 سخنگو","sp_panel"):
                    if pro_on():
                        pr = r_pro()
                        try:
                            ed = datetime.datetime.fromisoformat(pr["expires_at"])
                            jl = jdatetime.datetime.fromgregorian(datetime=ed)
                            es = f"{jl.year}/{jl.month}/{jl.day}"
                        except: es = "?"
                        pn = {"friendly":"🤝","formal":"📋","funny":"😂","professional":"💼"}.get(pr.get("personality"), "?")
                        await reply(message, f"🎤 فعال\n🎭 {pn}\n📅 {es}\n💬 {pr.get('response_count',0)}\n\n«شخصیت دوستانه/رسمی/شوخ/حرفه‌ای»\n«خاموش سخنگو»", keypad=pers_kp())
                    else:
                        cost = cs.get("speaker_cost", 20)
                        await reply(message, f"🎤 غیرفعال\n💰 هزینه: {cost}\n\n«فعالسازی سخنگو»", keypad=pers_kp())
                    return
                if text == "فعالسازی سخنگو":
                    if pro_on(): await reply(message, "⚠️ فعاله"); return
                    cost = cs.get("speaker_cost", 20)
                    if g_coins(ci) < cost: await reply(message, f"❌ {g_coins(ci)}/{cost}"); return
                    ok, nb = s_coins(ci, cost)
                    if ok:
                        dy = cs.get("speaker_days", 7); nw = datetime.datetime.now(); ex = nw + datetime.timedelta(days=dy)
                        w_pro({"enabled":True,"activated_at":nw.isoformat(),"expires_at":ex.isoformat(),"personality":"friendly","response_count":0})
                        jl = jdatetime.datetime.fromgregorian(datetime=ex)
                        await reply(message, f"✅ تا {jl.year}/{jl.month}/{jl.day}\n💰 {nb}")
                    return
                if text.startswith("شخصیت "):
                    if not pro_on(): await reply(message, "❌"); return
                    p = text.replace("شخصیت","").strip()
                    m = {"دوستانه":"friendly","رسمی":"formal","شوخ":"funny","حرفه‌ای":"professional","حرفه ای":"professional"}
                    if p in m:
                        pr = r_pro(); pr["personality"] = m[p]; w_pro(pr)
                        await reply(message, f"✅ {p}", keypad=pers_kp())
                    else: await reply(message, "❌")
                    return
                if text == "خاموش سخنگو":
                    pr = r_pro(); pr["enabled"] = False; w_pro(pr)
                    await reply(message, "✅"); return
                if text in ("🤝 دوستانه","p_friendly"):
                    pr = r_pro(); pr["personality"] = "friendly"; w_pro(pr)
                    await reply(message, "✅", keypad=pers_kp()); return
                if text in ("📋 رسمی","p_formal"):
                    pr = r_pro(); pr["personality"] = "formal"; w_pro(pr)
                    await reply(message, "✅", keypad=pers_kp()); return
                if text in ("😂 شوخ","p_funny"):
                    pr = r_pro(); pr["personality"] = "funny"; w_pro(pr)
                    await reply(message, "✅", keypad=pers_kp()); return
                if text in ("💼 حرفه‌ای","p_pro"):
                    pr = r_pro(); pr["personality"] = "professional"; w_pro(pr)
                    await reply(message, "✅", keypad=pers_kp()); return
                if text in ("🚫 بن","ban_panel"):
                    await reply(message, "🚫:", keypad=ban_kp()); return
                if text in ("📋 لیست","bn_list"):
                    bs = r_bans().get(gid, [])
                    o = f"📋 ({len(bs)}):\n" + ("\n".join([f"• {b}" for b in bs]) if bs else "خالی")
                    await reply(message, o, keypad=ban_kp()); return
                if text in ("🚫 بن","bn_add"):
                    gs[gid] = {"state":"bn_add"}; await reply(message, "👤:"); return
                if gs.get(gid,{}).get("state") == "bn_add":
                    ban(gid, text.strip()); gs[gid] = {"state":None}
                    await reply(message, "🚫", keypad=ban_kp()); return
                if text in ("✅ آنبن","bn_remove"):
                    gs[gid] = {"state":"bn_remove"}; await reply(message, "👤:"); return
                if gs.get(gid,{}).get("state") == "bn_remove":
                    unban(gid, text.strip()); gs[gid] = {"state":None}
                    await reply(message, "✅", keypad=ban_kp()); return
                if text in ("📝 کلمات","bw_panel"):
                    await reply(message, f"📝 ({len(r_bads())})", keypad=bads_kp()); return
                if text in ("📋 لیست","bw_list"):
                    bs = r_bads()
                    await reply(message, "📋:\n" + "\n".join([f"• {b}" for b in bs]), keypad=bads_kp()); return
                if text in ("➕ افزودن","bw_add"):
                    gs[gid] = {"state":"bw_add"}; await reply(message, "کلمه:"); return
                if gs.get(gid,{}).get("state") == "bw_add":
                    bs = r_bads()
                    if text and text not in bs: bs.append(text); w_bads(bs)
                    gs[gid] = {"state":None}
                    await reply(message, "✅", keypad=bads_kp()); return
                if text in ("➖ حذف","bw_remove"):
                    gs[gid] = {"state":"bw_remove"}; await reply(message, "کلمه:"); return
                if gs.get(gid,{}).get("state") == "bw_remove":
                    bs = r_bads()
                    if text in bs: bs.remove(text); w_bads(bs)
                    gs[gid] = {"state":None}
                    await reply(message, "✅", keypad=bads_kp()); return
                if text in ("👑 ادمین‌ها","admin_list"):
                    d = r_ad(); info = d.get(gid, {"superadmin":None,"admins":[]})
                    sa = info.get("superadmin") or "—"
                    al = info.get("admins", [])
                    o = f"👑 {sa}\n\n👤:\n" + ("\n".join([f"• {a}" for a in al]) if al else "خالی")
                    await reply(message, o); return
                if text in ("⚠️ اخطار","warn_panel"):
                    await reply(message, "⚠️ «اخطار @user»\n«صفر اخطار @user»"); return
                if text in ("❌ بستن","close_dash"):
                    gs[gid] = {"state":None}; await reply(message, "❌"); return
                if text in ("🔙 بازگشت","back_dash"):
                    await reply(message, "🎛", keypad=gd_kp(gid)); return
                if text.startswith("بن "):
                    t = text[3:].strip()
                    if t: ban(gid, t); await reply(message, f"🚫 {t}")
                    return
                if text.startswith("آنبن "):
                    t = text[5:].strip()
                    if t: unban(gid, t); await reply(message, f"✅ {t}")
                    return
                if text.startswith("سکه "):
                    p = text.split()
                    if len(p) >= 3:
                        try:
                            amt = int(p[2]); n = a_coins(p[1], amt)
                            await reply(message, f"✅ {amt} به {p[1]}. موجودی: {n}")
                        except: await reply(message, "❌")
                    elif len(p) == 2 and p[1].isdigit():
                        amt = int(p[1]); n = a_coins(ci, amt)
                        await reply(message, f"✅ {amt} به خودت. موجودی: {n}")
                    else: await reply(message, "❌ فرمت: سکه @user 50")
                    return
                if text.startswith("اخطار "):
                    t = text[6:].strip()
                    if t:
                        c = add_warn(gid, t); lm = s.get("warn_limit", 3)
                        await reply(message, f"⚠️ {t} ({c}/{lm})")
                        if c >= lm and s.get("auto_kick"):
                            ban(gid, t); await reply(message, f"👢 {t} کیک شد")
                    return
                if text.startswith("صفر اخطار "):
                    t = text[10:].strip()
                    if t: reset_warns(gid, t); await reply(message, "✅")
                    return
                if text.startswith("میوت "):
                    p = text.split()
                    if len(p) == 2:
                        if add_mu(gid, p[1]): await reply(message, f"🔇 {p[1]}")
                        else: await reply(message, "⚠️")
                    return
                if text.startswith("آنمیوت "):
                    p = text.split()
                    if len(p) == 2:
                        if rem_mu(gid, p[1]): await reply(message, f"🔊 {p[1]}")
                        else: await reply(message, "⚠️")
                    return
            # ============ کاربران عادی ============
            if text in ("سکه من","موجودی","امتیاز من"):
                await reply(message, f"💰 {cn}: {g_coins(ci)}"); return
            if text in ("سکه روزانه","🎁 روزانه","جایزه روزانه"):
                if not can_daily(ci): await reply(message, f"⚠️ {cn}، امروز گرفتی 🌹"); return
                amt = cs.get("daily_bonus",5); n = a_coins(ci, amt); mark_daily(ci)
                await reply(message, f"🎁 {cn}، {amt} سکه! موجودی: {n}"); return
            if text in ("پروفایل","پروفایل من"):
                lv = get_lv(ci); pr = get_prof(ci); st = r_st()
                ms = st["user_stats"].get(ci, {"messages":0})
                ttl = pr.get("title") or lv_title(lv.get("level",1))
                await reply(message, f"👤 {cn}\n🎖 لِوِل {lv.get('level',1)} ({lv_title(lv.get('level',1))})\n⭐ {lv.get('xp',0)}/{lv.get('level',1)*10}\n💬 {ms.get('messages',0)}\n💰 {g_coins(ci)}\n🏷 {ttl}"); return
            if text in ("رتبه من",):
                cd = r_coins(); sc = sorted(cd.items(), key=lambda x: x[1], reverse=True)
                try:
                    r = list(dict(sc).keys()).index(ci) + 1
                    await reply(message, f"🏆 {r}\n💰 {cd.get(ci,0)}")
                except: await reply(message, f"💰 {g_coins(ci)}")
                return
            if text in ("رتبه","برترین ها","top"):
                cd = r_coins(); sc = sorted(cd.items(), key=lambda x: x[1], reverse=True)[:5]
                o = "🏆:\n\n"
                for i,(cid,cv) in enumerate(sc, 1):
                    med = ["🥇","🥈","🥉"][i-1] if i <= 3 else f"{i}."
                    o += f"{med} {cid} — {cv}\n"
                if not sc: o += "خالی"
                await reply(message, o); return
            if text in ("شاپ","فروشگاه"):
                sh = r_shop(); o = "🛍:\n\n"
                for k,it in sh.items(): o += f"{it['name']} — {it['price']} سکه\n   {it['desc']}\n\n"
                o += "«خرید [آیتم]»"
                await reply(message, o); return
            if text.startswith("خرید "):
                ik = text[5:].strip().lower(); sh = r_shop()
                if ik not in sh: await reply(message, "❌"); return
                it = sh[ik]; pr = it["price"]
                if g_coins(ci) < pr: await reply(message, f"❌ {pr}/{g_coins(ci)}"); return
                ok, nb = s_coins(ci, pr)
                if ok:
                    p = get_prof(ci); p["title"] = it["name"]; p.setdefault("purchases", []).append(ik); save_prof(ci, p)
                    await reply(message, f"✅ {it['name']}\n💰 {nb}")
                return
            if text in ("سطح","لِوِل","level"):
                lv = get_lv(ci)
                await reply(message, f"⭐ {cn}\n🎖 {lv.get('level',1)}\nXP: {lv.get('xp',0)}/{lv.get('level',1)*10}"); return
            if text in ("راهنما","help"):
                await reply(message, "📖:\n💰 سکه من\n🎁 سکه روزانه\n🏆 رتبه\n👤 پروفایل\n⭐ سطح\n🛍 شاپ\n😂 جوک\n💡 دانستنی\n🎲 تاس\n📊 آمار گروه"); return
            # ✅ FIX: فعال‌سازی با ZWNJ و بدون ZWNJ + اضافه کردن به ادمین
            if text.startswith("فعال‌سازی") or text.startswith("فعالسازی"):
                code = text.replace("فعال‌سازی", "").replace("فعالسازی", "").strip()
                if code:
                    if consume(gid, code):
                        s2 = rd(F["SUBS"]); ginfo = s2.get("groups", {}).get(gid, {})
                        plan = ginfo.get("plan", "Basic")
                        # ذخیره فعال‌کننده
                        ginfo["activated_by"] = ci
                        s2["groups"][gid] = ginfo; wd(F["SUBS"], s2)
                        # ذخیره به عنوان ادمین/سوپراادمین
                        d = r_ad(); info = d.get(gid, {"superadmin":None, "admins":[]})
                        if not isinstance(info, dict): info = {"superadmin":None, "admins":[]}
                        if plan == "SuperAdmin":
                            info["superadmin"] = ci
                            msg = "👑 سوپراادمین شدید!\n\nحالا بنویسید: «پنل»"
                        else:
                            al = info.get("admins", [])
                            if not isinstance(al, list): al = []
                            if ci not in al: al.append(ci)
                            info["admins"] = al
                            msg = "✅ ادمین شدید!\n\nحالا بنویسید: «پنل»"
                        d[gid] = info; w_ad(d)
                        await reply(message, f"✅ فعال شد.\n📋 پلن: {plan}\n\n{msg}")
                    else:
                        await reply(message, "❌ کد نامعتبر یا منقضی شده.")
                else:
                    await reply(message, "❌ فرمت: فعالسازی CODE123")
                return
            if text.strip() == "آمار گروه":
                st = r_st(); gd = st["group_stats"].get(gid, {"total_messages":0,"members":{}})
                m = gd.get("members",{}); sm = sorted(m.items(), key=lambda x: x[1].get("count",0), reverse=True)[:20]
                o = f"📊:\n💬 {gd.get('total_messages',0)}\n👤 {len(m)}\n\n"
                for i,(uid2,md) in enumerate(sm, 1): o += f"{i}. {md.get('name','?')}: {md.get('count',0)}\n"
                await reply(message, o); return
            # ============ بررسی‌های امنیتی ============
            if s.get("lock_group") and not is_sa_u: await del_m(message); return
            if is_mu(gid, ci): await del_m(message); return
            if s.get("anti_id") and not is_sa_u and has_id(text):
                await del_m(message); await reply(message, f"🚫 {cn} ارسال آیدی ممنوع است!"); return
            if s.get("anti_link") and not is_sa_u and has_lnk(text):
                await del_m(message); await reply(message, f"🚫 {cn} لینک ممنوع!"); return
            if s.get("anti_badword") and not is_sa_u:
                if has_bad(text, r_bads()):
                    await del_m(message); c = add_warn(gid, ci); lm = s.get("warn_limit", 3)
                    await reply(message, f"🚫 {cn} کلمات!\n⚠️ {c}/{lm}")
                    if c >= lm and s.get("auto_kick"):
                        ban(gid, ci); await reply(message, f"👢 {cn} کیک شد")
                    return
            if s.get("anti_spam") and not is_sa_u:
                nw = datetime.datetime.now().timestamp(); k = (gid, ci)
                ar = spam_tr.get(k, []); ar = [t2 for t2 in ar if nw - t2 < 10]; ar.append(nw); spam_tr[k] = ar
                if len(ar) > s.get("spam_limit", 5):
                    await del_m(message); await reply(message, f"⚠️ {cn} آرام!"); return
            if not has_sub(gid):
                await reply(message, "❌ اشتراک فعال نیست.\n«فعالسازی CODE»"); return
            # ============ سخنگو ============
            if pro_on() and text and len(text) < 100:
                intent = detect(text)
                if intent:
                    nw = datetime.datetime.now().timestamp(); k = (gid, ci); last = spk_cd.get(k, 0)
                    if nw - last > 45:
                        spk_cd[k] = nw; r2 = get_spk(intent)
                        if r2:
                            await reply(message, r2)
                            try:
                                pr = r_pro(); pr["response_count"] = pr.get("response_count",0)+1; w_pro(pr)
                            except: pass
            # ============ آمار + XP ============
            st = r_st()
            if ci not in st["user_stats"]: st["user_stats"][ci] = {"messages":0,"joke":0,"fact":0,"bio":0}
            st["user_stats"][ci]["messages"] += 1
            if gid not in st["group_stats"]: st["group_stats"][gid] = {"total_messages":0,"members":{}}
            st["group_stats"][gid]["total_messages"] += 1
            if ci not in st["group_stats"][gid]["members"]: st["group_stats"][gid]["members"][ci] = {"count":0,"name":cn}
            st["group_stats"][gid]["members"][ci]["count"] += 1
            st["group_stats"][gid]["members"][ci]["name"] = cn
            w_st(st)
            try:
                ul, lu = add_xp(ci, 1)
                if lu: await reply(message, f"🎉 {cn}!\n🎖 لِوِل {ul['level']}\n🏷 {lv_title(ul['level'])}")
            except: pass
            if cs.get("message_reward",0) > 0 and not is_sa_u:
                try:
                    us = st["user_stats"].get(ci, {})
                    if us.get("messages",0) <= cs.get("message_reward_limit",20): a_coins(ci, cs.get("message_reward",0))
                except: pass
            # ============ پاسخ‌های سریع ============
            qrs = get_quick(s)
            if text in qrs and not is_sa_u:
                await reply(message, qrs[text]); return
            # ============ سرگرمی ============
            ln = rd(F["LEARN"])
            if text in ln: await reply(message, ln[text]); return
            if is_cr(text): await reply(message, "🤖 سازنده: @Pv_REGNOR"); return
            if text == "ربات": await reply(message, "جانم؟ 🤍"); return
            if text.startswith("امارم") or text.startswith("آمارم"):
                us = st["user_stats"].get(ci, {}); lv = get_lv(ci)
                await reply(message, f"📊\n💬 {us.get('messages',0)}\n😂 {us.get('joke',0)}\n💡 {us.get('fact',0)}\n👤 {us.get('bio',0)}\n🎖 {lv.get('level',1)}"); return
            if text.startswith("جوک"):
                j = rl(F["JOKES"])
                if j:
                    idx = r_idx(); i2 = idx.get("joke_index",0)
                    await reply(message, f"😂 {j[i2 % len(j)]}")
                    idx["joke_index"] = (i2+1) % len(j); w_idx(idx)
                    st["user_stats"][ci]["joke"] = st["user_stats"][ci].get("joke",0)+1; w_st(st)
                else: await reply(message, "هنوز جوکی نیست.")
                return
            if text.startswith("دانستنی"):
                f = rl(F["FACTS"])
                if f:
                    idx = r_idx(); i2 = idx.get("fact_index",0)
                    await reply(message, f"💡 {f[i2 % len(f)]}")
                    idx["fact_index"] = (i2+1) % len(f); w_idx(idx)
                    st["user_stats"][ci]["fact"] = st["user_stats"][ci].get("fact",0)+1; w_st(st)
                else: await reply(message, "هنوز دانستنی نیست.")
                return
            if text.startswith("بیو"):
                bi = rl(F["BIOS"])
                if bi:
                    idx = r_idx(); i2 = idx.get("bio_index",0)
                    await reply(message, f"👤 {bi[i2 % len(bi)]}")
                    idx["bio_index"] = (i2+1) % len(bi); w_idx(idx)
                else: await reply(message, "هنوز بیویی نیست.")
                return
            if text.startswith("تاس"):
                await reply(message, f"🎲 {cn}: {'⚫' * random.randint(1,6)}"); return
        retry_delay = 3
        while bot_should_run:
            try:
                await asyncio.to_thread(bot.run)
                retry_delay = 3
            except asyncio.CancelledError:
                break
            except Exception as e:
                err = str(e)
                if "502" in err or "Bad Gateway" in err or "APIRequestError" in err:
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 60)
                else:
                    print(f"Grp err: {e}")
                    await asyncio.sleep(5)
    except Exception as e: print(f"Grp Bot Error {owner_id}: {e}")

# ================= هندلر ربات ساز =================
@main_bot.on_message()
async def main_handler(bot, msg: Message):
    # chat_id برای ذخیره اطلاعات کاربر استفاده می‌شود؛ sender_id برای تشخیص مالک.
    # در Rubka، Message هر دو شناسه را در اختیار هندلر قرار می‌دهد.
    chat_id = str(getattr(msg, "chat_id", "") or "").strip()
    sender_id = str(getattr(msg, "sender_id", "") or "").strip()

    # اگر متن مستقیم موجود نبود، از raw_data هم به‌عنوان پشتیبان بخوان.
    raw_text = getattr(msg, "text", None)
    if not raw_text:
        raw = getattr(msg, "raw_data", None)
        if isinstance(raw, dict):
            raw_text = raw.get("text")
            if not raw_text and isinstance(raw.get("new_message"), dict):
                raw_text = raw["new_message"].get("text")
            if not raw_text and isinstance(raw.get("message"), dict):
                raw_text = raw["message"].get("text")

    # در بعضی نسخه‌های Rubka، فشردن ChatKeypad به‌جای msg.text،
    # شناسه دکمه را داخل aux_data.button_id می‌فرستد.
    # بنابراین هم متن و هم button_id را می‌خوانیم تا هیچ دکمه‌ای از کار نیفتد.
    button_id = ""
    aux = getattr(msg, "aux_data", None)
    if aux is not None:
        if isinstance(aux, dict):
            button_id = str(aux.get("button_id") or aux.get("buttonId") or aux.get("id") or "").strip()
        else:
            button_id = str(
                getattr(aux, "button_id", None)
                or getattr(aux, "buttonId", None)
                or getattr(aux, "id", None)
                or ""
            ).strip()

    if not button_id:
        raw = getattr(msg, "raw_data", None)
        if isinstance(raw, dict):
            candidates = [
                raw.get("button_id"), raw.get("buttonId"),
                raw.get("aux_data", {}).get("button_id") if isinstance(raw.get("aux_data"), dict) else None,
                raw.get("aux_data", {}).get("buttonId") if isinstance(raw.get("aux_data"), dict) else None,
            ]
            for candidate in candidates:
                if candidate:
                    button_id = str(candidate).strip()
                    break

    text = str(raw_text or "").strip()

    # شناسه‌های دکمه‌های پنل مدیریت را به متن واقعی دکمه تبدیل می‌کنیم.
    # اگر Rubka متن دکمه را فرستاده باشد، این بخش هیچ تغییری ایجاد نمی‌کند.
    keypad_button_text = {
        "stats": "📊 آمار ربات ساز",
        "maker_users_stats": "🏆 آمار کاربران",
        "make": "➕ ساخت ربات جدید",
        "mybots": "📋 ربات های من",
        "my_coins": "💰 سکه و شناسه",
        "daily_maker": "🎁 سکه روزانه",
        "store": "🛍 فروشگاه",
        "help": "📖 راهنما",
        "support_maker": "📞 پشتیبانی",
        "add_maker_coins": "💰 افزودن سکه",
        "remove_maker_coins": "🗑 حذف سکه",
        "maker_broadcast": "📢 پیام همگانی",
        "vip_users_list": "👑 لیست VIP ها",
        "give_vip": "🎁 اهدای VIP",
        "set_ad": "📢 ثبت تبلیغ",
        "del_ad": "🗑 حذف تبلیغ",
        "broadcast_to_bots": "📨 ارسال تبلیغ به ربات‌ها",
        "remove_vip": "🗑 حذف VIP",
        "block_user": "🚫 مسدود کردن",
        "unblock_user": "✅ رفع مسدودیت",
        "all_broadcast": "📢 همگانی همه",
        "tickets_panel": "🎫 تیکت‌های پشتیبانی",
        "stop_all_children": "🛑 خاموش فرزندها",
        "start_all_children": "▶️ روشن فرزندها",
        "t_list_new": "📥 تیکت‌های جدید",
        "t_list_all": "📋 همه تیکت‌ها",
        "t_reply": "📤 پاسخ به تیکت",
        "t_chat": "💬 چت با کاربر",
        "chat_edit": "✏️ ویرایش آخرین پیام",
        "chat_delete": "🗑 حذف آخرین پیام",
        "chat_send": "📤 ارسال پیام",
        "chat_end": "🔚 پایان گفتگو",
        "t_delete_all": "🗑 حذف همه تیکت‌ها",
        "back": "🔙 بازگشت",
        "a_back": "🔙",
        "manage_bots": "🛠 مدیریت ربات‌ها",
        "back_mybm": "🔙 بازگشت",
        "bm_back": "🔙 انتخاب ربات",
        "bm_keyboard_back": "🔙 بازگشت",
        "bm_start": "📝 پیام استارت",
        "bm_keyboard": "⌨️ مدیریت کیبورد",
        "bm_command": "➕ افزودن دستور",
        "bm_stats": "📊 آمار",
        "bm_broadcast": "📢 پیام همگانی",
        "bm_restart": "🔄 راه‌اندازی مجدد",
        "bm_add_button": "➕ افزودن دکمه",
        "bm_remove_button": "➖ حذف دکمه",
        "bm_list_buttons": "📋 لیست دکمه‌ها",
    }
    if button_id in keypad_button_text:
        text = keypad_button_text[button_id]

    # نرمال‌سازی برای جلوگیری از مشکل فاصله/نیم‌فاصله/حروف بزرگ و کوچک.
    normalized_text = (
        text.replace("\u200c", "")
            .replace("\ufeff", "")
            .strip()
            .lower()
    )

    # کلید اطلاعات کاربر همان chat_id قبلی است تا اطلاعات ذخیره‌شده خراب نشود.
    uid = chat_id or sender_id
    if uid not in maker_users:
        maker_users[uid] = {"state":None,"temp":{},"coins":0,"vip_until":None,"last_daily":None}
        save_maker()
    user = maker_users[uid]
    user.setdefault("coins", 0); user.setdefault("vip_until", None); user.setdefault("last_daily", None)
    # نام کاربر از Message.name/username در این نسخه ذخیره نمی‌شود تا هیچ coroutine وارد داده‌های پایدار نشود.

    # ============================================================
    # پنل مدیریت مخفی
    # فقط صاحب تعیین‌شده می‌تواند با /Abolfazl1389 وارد شود.
    # ============================================================
    admin_identity_ok = (
        sender_id == MAKER_ADMIN_ID
        or chat_id == MAKER_ADMIN_ID
    )

    # در گفت‌وگوی پشتیبانی، پیام‌های کاربر به ادمین فعال همان گفت‌وگو منتقل می‌شوند.
    if not admin_identity_ok:
        for _admin_uid, _admin_data in maker_users.items():
            if not isinstance(_admin_data, dict):
                continue
            if _admin_data.get("state") == "t_chat" and str(_admin_data.get("temp", {}).get("chat_user", "")) == str(uid):
                try:
                    _mid = getattr(msg, "message_id", None) or getattr(msg, "id", None)
                    if raw_text:
                        _sent = await bot.send_message(str(_admin_uid), f"💬 `{uid}`:\n{raw_text}")
                        _admin_mid = _sent.get("message_id") if isinstance(_sent, dict) else getattr(_sent, "message_id", None)
                        if _admin_mid and _mid:
                            support_reply_map[(str(_admin_uid), str(_admin_mid))] = str(_mid)
                    elif _mid and hasattr(bot, "forward_message"):
                        try: _sent = await bot.forward_message(chat_id=chat_id, message_id=str(_mid), to_chat_id=str(_admin_uid))
                        except TypeError: _sent = await bot.forward_message(chat_id, str(_mid), str(_admin_uid))
                        _admin_mid = _sent.get("message_id") if isinstance(_sent, dict) else getattr(_sent, "message_id", None)
                        if _admin_mid:
                            support_reply_map[(str(_admin_uid), str(_admin_mid))] = str(_mid)
                    else:
                        await bot.send_message(str(_admin_uid), f"📎 پیام رسانه‌ای از `{uid}` دریافت شد.")
                except Exception as _e:
                    print(f"support chat forward error: {_e}")
                return

    # کاربر مسدودشده هیچ بخشی از ربات‌ساز را نمی‌تواند استفاده کند؛ مدیر اصلی مستثنی است.
    if not admin_identity_ok and str(uid) in set(str(x) for x in maker_settings.get("blocked_users", [])):
        await msg.reply("**🚫 شما مسدود هستید و به ربات دسترسی ندارید**")
        return

    if normalized_text == MAKER_ADMIN_PASS.lower():
        if admin_identity_ok:
            maker_admins[:] = [MAKER_ADMIN_ID]
            user["state"] = None
            user["temp"] = {}
            save_maker()
            await msg.reply(
                "✅ خوش آمدید.\n\n**پنل مدیریت مخفی**",
                chat_keypad=maker_admin_menu()
            )
        else:
            await msg.reply("**__شما این دسترسی را ندارید__**")
        return

    # لغو/بازگشت در مراحل توکن و رمز باید قبل از پردازش state انجام شود.
    if user.get("state") in ("token", "password") and normalized_text in (
        "🔙 بازگشت", "🔙", "back", "بازگشت", "❌ لغو", "cancel"
    ):
        user["state"] = None
        user["temp"] = {}
        save_maker()
        await msg.reply("**🔙 منوی اصلی**", chat_keypad=maker_main_menu(uid))
        return

    if text == "/start":
        user["state"] = None; save_maker()
        vs = "👑 VIP" if is_vip_active(uid) else ""
        await msg.reply(
            f"**به ربات ساز کانتر مود خوش اومدی.**{vs}\n\n"
            "```ساخت ربات پیشرفته بدون کد نویسی!```\n\n\n**وضعیت حساب شما:**\n\n"
            f"💰 {user.get('coins',0)} سکه\n📊 ربات‌ها: {user_bot_count(uid)}/{user_bot_limit(uid)}",
            chat_keypad=maker_main_menu(uid))
        return

    # ================= مدیریت ربات‌های ساخته‌شده =================
    if text == "🛠 مدیریت ربات‌ها":
        bots = maker_bots.get(uid, [])
        user["state"] = None; user["temp"] = {}; save_maker()
        if not bots:
            await msg.reply("**شما هنوز رباتی نساختی.**", chat_keypad=maker_main_menu(uid)); return
        await msg.reply("🛠 **مدیریت ربات‌های شما**\n\nرباتی را که می‌خواهید طراحی یا مدیریت کنید انتخاب کنید:", chat_keypad=bot_manager_menu(uid)); return

    if text.startswith("🤖 ") and user.get("state") == "bot_manager_select":
        pass

    # بازگشت از فهرست ربات‌ها به منوی اصلی
    if button_id == "back_mybm":
        user["state"] = None; user["temp"] = {}; save_maker()
        await msg.reply("**🔙 منوی اصلی**", chat_keypad=maker_main_menu(uid)); return

    # انتخاب ربات از روی شناسه دکمه bm_N
    if button_id.startswith("bm_") and button_id[3:].isdigit():
        idx = int(button_id[3:]) - 1
        bots = maker_bots.get(uid, [])
        if 0 <= idx < len(bots):
            user["temp"] = {"manage_index": idx}; user["state"] = "bot_manager"
            save_maker()
            b = bots[idx]
            await msg.reply(
                f"🤖 **مدیریت ربات {idx+1}**\n\nنوع: {_manager_type_name(b.get('type'))}\n🆔 `{b.get('bot_id','-')}`\n\nیک بخش را انتخاب کنید:",
                chat_keypad=bot_manage_actions(b.get("type")))
        else: await msg.reply("❌ ربات پیدا نشد.", chat_keypad=bot_manager_menu(uid))
        return

    if text in ("🔙 انتخاب ربات", "🔙 بازگشت") and user.get("state") == "bot_manager":
        user["state"] = None; user["temp"] = {}; save_maker()
        await msg.reply("🛠 انتخاب ربات:", chat_keypad=bot_manager_menu(uid)); return

    if user.get("state") in ("bot_manager", "bot_keyboard", "bot_start", "bot_command", "bot_add_button", "bot_remove_button", "bot_broadcast", "gm_panel", "gm_security", "gm_settings", "gm_quick", "gm_words", "gm_warnings", "gm_coins", "gm_wait", "gm_broadcast"):
        bots = maker_bots.get(uid, [])
        idx = user.get("temp", {}).get("manage_index", -1)
        if not isinstance(idx, int) or idx < 0 or idx >= len(bots):
            user["state"] = None; user["temp"] = {}; save_maker()
            await msg.reply("❌ ربات انتخاب‌شده دیگر وجود ندارد.", chat_keypad=bot_manager_menu(uid)); return
        b = bots[idx]; b["owner_id"] = uid
        paths = _manager_paths(b)
        typ = b.get("type")

        if user.get("state") == "bot_manager":
            if typ == "group_manager" and text in ("🛡 امنیت گروه", "⚙️ تنظیمات", "⚡ پاسخ سریع", "📝 کلمات ممنوع", "⚠️ اخطار", "💰 سکه و پاداش", "📊 آمار گروه", "👥 اعضا", "👑 ادمین‌ها", "📢 پیام همگانی"):
                if text == "🛡 امنیت گروه": user["state"]="gm_security"; save_maker(); await msg.reply("🛡 تنظیمات امنیتی گروه", chat_keypad=group_manage_kp("security")); return
                if text == "⚙️ تنظیمات": user["state"]="gm_settings"; save_maker(); await msg.reply("⚙️ تنظیمات گروه", chat_keypad=group_manage_kp("settings")); return
                if text == "⚡ پاسخ سریع": user["state"]="gm_quick"; save_maker(); await msg.reply("⚡ پاسخ سریع", chat_keypad=group_manage_kp("quick")); return
                if text == "📝 کلمات ممنوع":
                    user["state"]="gm_words"; save_maker()
                    bs=_manager_load(paths.get("bads",""), []); bs=bs if isinstance(bs,list) else []
                    await msg.reply("📝 مدیریت کلمات ممنوع\n\n" + ("\n".join(f"• {x}" for x in bs) if bs else "لیست خالی است."), chat_keypad=group_words_kp()); return
                if text == "⚠️ اخطار": user["state"]="gm_warnings"; save_maker(); await msg.reply("⚠️ تنظیم اخطار", chat_keypad=group_manage_kp("warnings")); return
                if text == "💰 سکه و پاداش": user["state"]="gm_coins"; save_maker(); await msg.reply("💰 تنظیمات سکه و پاداش", chat_keypad=group_manage_kp("coins")); return
                if text == "📊 آمار گروه":
                    st=_manager_load(paths.get("stats",""), {}); await msg.reply(f"📊 آمار گروه\n\n💬 پیام‌ها: {st.get('total_messages',0) if isinstance(st,dict) else 0}", chat_keypad=bot_manage_actions(typ)); return
                if text == "👥 اعضا":
                    users=_manager_users(paths.get("users","")); await msg.reply(f"👥 اعضای ثبت‌شده: {len(users)}\n\n" + "\n".join(f"{i+1}. `{u}`" for i,u in enumerate(users[:50])) if users else "👥 عضوی ثبت نشده.", chat_keypad=bot_manage_actions(typ)); return
                if text == "👑 ادمین‌ها":
                    gs=_manager_load(paths.get("gset",""), {}); await msg.reply("👑 تنظیمات ادمین گروه از داخل خود گروه انجام می‌شود.\n\nصاحب ربات همیشه دسترسی مدیریت دارد.", chat_keypad=bot_manage_actions(typ)); return
                if text == "📢 پیام همگانی": user["state"]="gm_broadcast"; save_maker(); await msg.reply("📢 متن پیام همگانی گروه را بفرستید.", chat_keypad=bot_manage_actions(typ)); return
            if typ == "group_manager" and user.get("state") == "gm_security":
                if text in ("🔙 بازگشت", "🔙"): user["state"]="bot_manager"; save_maker(); await msg.reply("🔙", chat_keypad=bot_manage_actions(typ)); return
                keymap={"gm_toggle_anti_link":"anti_link","gm_toggle_anti_id":"anti_id","gm_toggle_anti_badword":"anti_badword","gm_toggle_anti_spam":"anti_spam","gm_toggle_lock_group":"lock_group","gm_toggle_auto_kick":"auto_kick","gm_toggle_delete_service":"delete_service"}
                textmap={"🔗 ضد لینک":"anti_link","🆔 ضد آیدی":"anti_id","🚫 ضد کلمات":"anti_badword","🛡 ضد اسپم":"anti_spam","🔒 قفل گروه":"lock_group","👢 کیک خودکار":"auto_kick","🧹 حذف سرویس":"delete_service"}
                k=keymap.get(button_id) or textmap.get(text)
                if k:
                    raw,cfg=_group_default_cfg(paths); cfg[k]=not bool(cfg.get(k)); _save_group_default(paths,cfg); await msg.reply(f"{'🟢' if cfg[k] else '🔴'} تنظیم شد", chat_keypad=group_manage_kp("security")); return
            if typ == "group_manager" and user.get("state") == "gm_settings":
                if text in ("🔙 بازگشت", "🔙"): user["state"]="bot_manager"; save_maker(); await msg.reply("🔙", chat_keypad=bot_manage_actions(typ)); return
                raw,cfg=_group_default_cfg(paths)
                if button_id == "gm_toggle_welcome" or text == "👋 خوش‌آمد روشن/خاموش": cfg["welcome_msg"]=not bool(cfg.get("welcome_msg")); _save_group_default(paths,cfg); await msg.reply("🟢 خوش‌آمد روشن شد." if cfg["welcome_msg"] else "🔴 خوش‌آمد خاموش شد.", chat_keypad=group_manage_kp("settings")); return
                if button_id == "gm_toggle_goodbye" or text == "👋 خداحافظ روشن/خاموش": cfg["goodbye_msg"]=not bool(cfg.get("goodbye_msg")); _save_group_default(paths,cfg); await msg.reply("🟢 خداحافظ روشن شد." if cfg["goodbye_msg"] else "🔴 خداحافظ خاموش شد.", chat_keypad=group_manage_kp("settings")); return
                if button_id == "gm_edit_welcome" or text == "👋 متن خوش‌آمد": user["state"]="gm_wait"; user["temp"]["gm_field"]="welcome_text"; save_maker(); await msg.reply("✍️ متن خوش‌آمد را بفرستید:", chat_keypad=group_manage_kp("settings")); return
                if button_id == "gm_edit_goodbye" or text == "👋 متن خداحافظی": user["state"]="gm_wait"; user["temp"]["gm_field"]="goodbye_text"; save_maker(); await msg.reply("✍️ متن خداحافظی را بفرستید:", chat_keypad=group_manage_kp("settings")); return
                if button_id == "gm_spam_limit" or text == "🛡 حد اسپم": user["state"]="gm_wait"; user["temp"]["gm_field"]="spam_limit"; save_maker(); await msg.reply("🔢 حد اسپم را بفرستید:", chat_keypad=group_manage_kp("settings")); return
                if button_id == "gm_warn_limit" or text == "⚠️ حد اخطار": user["state"]="gm_wait"; user["temp"]["gm_field"]="warn_limit"; save_maker(); await msg.reply("🔢 حد اخطار را بفرستید:", chat_keypad=group_manage_kp("settings")); return
            if typ == "group_manager" and user.get("state") == "gm_wait":
                if text in ("🔙 بازگشت", "🔙"): user["state"]="gm_settings"; user["temp"].pop("gm_field",None); save_maker(); await msg.reply("🔙", chat_keypad=group_manage_kp("settings")); return
                raw,cfg=_group_default_cfg(paths); field=user["temp"].get("gm_field")
                if field == "quick_add":
                    if "=>" not in text: await msg.reply("❌ فرمت: کلمه => پاسخ", chat_keypad=group_manage_kp("quick")); return
                    k,v=[x.strip() for x in text.split("=>",1)]; cfg.setdefault("quick_replies",{})[k]=v; _save_group_default(paths,cfg); user["state"]="gm_quick"; user["temp"].pop("gm_field",None); save_maker(); await msg.reply("✅ پاسخ سریع ذخیره شد.", chat_keypad=group_manage_kp("quick")); return
                if field == "quick_remove":
                    q=cfg.get("quick_replies",{}) if isinstance(cfg,dict) else {}; q.pop(text,None); cfg["quick_replies"]=q; _save_group_default(paths,cfg); user["state"]="gm_quick"; user["temp"].pop("gm_field",None); save_maker(); await msg.reply("✅ انجام شد.", chat_keypad=group_manage_kp("quick")); return
                if field in ("bad_add","bad_remove"):
                    badpath=paths.get("bads", f"groupbot_{uid}/bads.json"); bs=_manager_load(badpath, []); bs=bs if isinstance(bs,list) else []
                    if field == "bad_add" and text: bs.append(text); bs=list(dict.fromkeys(bs))
                    elif field == "bad_remove": bs=[x for x in bs if x != text]
                    _manager_save(badpath,bs); user["state"]="gm_words"; user["temp"].pop("gm_field",None); save_maker(); await msg.reply("✅ ذخیره شد.", chat_keypad=group_words_kp()); return
                if field in ("spam_limit","warn_limit","daily_bonus","message_reward"):
                    try: cfg[field]=max(1,int(text))
                    except: await msg.reply("❌ عدد معتبر وارد کنید.", chat_keypad=group_manage_kp("settings")); return
                else: cfg[field]=text
                _save_group_default(paths,cfg); user["state"]="gm_settings"; user["temp"].pop("gm_field",None); save_maker(); await msg.reply("✅ ذخیره شد.", chat_keypad=group_manage_kp("settings")); return
            if typ == "group_manager" and user.get("state") == "gm_quick":
                if text in ("🔙 بازگشت", "🔙"): user["state"]="bot_manager"; save_maker(); await msg.reply("🔙", chat_keypad=bot_manage_actions(typ)); return
                if button_id == "gm_q_add" or text == "➕ افزودن پاسخ": user["state"]="gm_wait"; user["temp"]["gm_field"]="quick_add"; save_maker(); await msg.reply("✍️ فرمت: کلمه => پاسخ", chat_keypad=group_manage_kp("quick")); return
                if button_id == "gm_q_remove" or text == "➖ حذف پاسخ": user["state"]="gm_wait"; user["temp"]["gm_field"]="quick_remove"; save_maker(); await msg.reply("✍️ کلمه را بفرستید:", chat_keypad=group_manage_kp("quick")); return
                if button_id == "gm_q_list" or text == "📋 لیست پاسخ‌ها":
                    cfg=_manager_load(paths["gset"], {}); q=cfg.get("quick_replies",{}) if isinstance(cfg,dict) else {}
                    out="⚡ پاسخ‌ها:\n\n" + ("\n".join(f"• {k} => {v}" for k,v in q.items()) or "خالی")
                    await msg.reply(out, chat_keypad=group_manage_kp("quick")); return
            if typ == "group_manager" and user.get("state") == "gm_words":
                if text in ("🔙 بازگشت", "🔙") or button_id == "gm_back": user["state"]="bot_manager"; save_maker(); await msg.reply("🔙", chat_keypad=bot_manage_actions(typ)); return
                badpath=paths.get("bads", f"groupbot_{uid}/bads.json"); bs=_manager_load(badpath, []); bs=bs if isinstance(bs,list) else []
                if button_id == "gm_w_list" or text == "📋 لیست کلمات": await msg.reply("📝 کلمات ممنوع:\n\n" + ("\n".join(f"• {x}" for x in bs) if bs else "خالی"), chat_keypad=group_words_kp()); return
                if button_id == "gm_w_add" or text == "➕ افزودن کلمه": user["state"]="gm_wait"; user["temp"]["gm_field"]="bad_add"; save_maker(); await msg.reply("✍️ کلمه ممنوع را بفرستید:", chat_keypad=group_words_kp()); return
                if button_id == "gm_w_remove" or text == "➖ حذف کلمه": user["state"]="gm_wait"; user["temp"]["gm_field"]="bad_remove"; save_maker(); await msg.reply("✍️ کلمه برای حذف را بفرستید:", chat_keypad=group_words_kp()); return
            if typ == "group_manager" and user.get("state") == "gm_warnings":
                if text in ("🔙 بازگشت", "🔙"): user["state"]="bot_manager"; save_maker(); await msg.reply("🔙", chat_keypad=bot_manage_actions(typ)); return
                if button_id == "gm_warn_limit" or text == "⚠️ حد اخطار": user["state"]="gm_wait"; user["temp"]["gm_field"]="warn_limit"; save_maker(); await msg.reply("🔢 حد اخطار:", chat_keypad=group_manage_kp("warnings")); return
                if button_id == "gm_auto_kick" or text == "👢 کیک خودکار":
                    raw,cfg=_group_default_cfg(paths); cfg["auto_kick"]=not bool(cfg.get("auto_kick")); _save_group_default(paths,cfg); await msg.reply("✅ تنظیم شد.", chat_keypad=group_manage_kp("warnings")); return
            if typ == "group_manager" and user.get("state") == "gm_coins":
                if text in ("🔙 بازگشت", "🔙"): user["state"]="bot_manager"; save_maker(); await msg.reply("🔙", chat_keypad=bot_manage_actions(typ)); return
                if button_id in ("gm_coin_daily","gm_coin_reward") or text in ("🎁 سکه روزانه","💬 پاداش پیام"): user["state"]="gm_wait"; user["temp"]["gm_field"]="daily_bonus" if (button_id=="gm_coin_daily" or text=="🎁 سکه روزانه") else "message_reward"; save_maker(); await msg.reply("🔢 مقدار جدید را بفرستید:", chat_keypad=group_manage_kp("coins")); return
            if typ == "group_manager" and user.get("state") == "gm_broadcast":
                if text in ("🔙 بازگشت", "🔙"): user["state"]="bot_manager"; save_maker(); await msg.reply("🔙", chat_keypad=bot_manage_actions(typ)); return
                users=_manager_users(paths.get("users","")); cb=Robot(b["token"]); sent=0
                for target in users:
                    try: await cb.send_message(target,text); sent+=1; await asyncio.sleep(.03)
                    except: pass
                user["state"]="bot_manager"; save_maker(); await msg.reply(f"📢 ارسال شد: {sent}", chat_keypad=bot_manage_actions(typ)); return
            if text == "📝 پیام استارت":
                user["state"] = "bot_start"; save_maker()
                current = ""
                if typ in ("raw", "shop"): current = _manager_load(paths.get("config",""), {}).get("welcome_text", "")
                await msg.reply(f"📝 پیام استارت فعلی:\n\n{current or 'تنظیم نشده'}\n\n✍️ پیام جدید را بفرستید:", chat_keypad=bot_manage_actions(typ)); return
            if text == "⌨️ مدیریت کیبورد":
                if typ != "raw":
                    await msg.reply("ℹ️ مدیریت کامل کیبورد فعلاً برای «ربات خام» فعال است.", chat_keypad=bot_manage_actions(typ)); return
                user["state"] = "bot_keyboard"; save_maker()
                await msg.reply("⌨️ مدیریت کیبورد:", chat_keypad=bot_keyboard_menu()); return
            if text == "➕ افزودن دستور":
                if typ != "raw":
                    await msg.reply("ℹ️ افزودن دستور سفارشی فعلاً برای «ربات خام» فعال است.", chat_keypad=bot_manage_actions(typ)); return
                user["state"] = "bot_command"; save_maker()
                await msg.reply("➕ دستور را بفرستید؛ مثال:\n`/help | راهنمای ربات`\n\nفرمت: دستور | پاسخ", chat_keypad=bot_manage_actions(typ)); return
            if text == "📊 آمار":
                users = _manager_users(paths.get("users",""))
                total_msgs = 0
                st = _manager_load(paths.get("stats",""), {})
                if isinstance(st, dict): total_msgs = int(st.get("total_messages", 0) or 0)
                if typ == "shop":
                    orders = _manager_load(paths.get("orders",""), [])
                    await msg.reply(f"📊 آمار ربات {idx+1}\n\n👥 کاربران: {len(users)}\n📦 سفارش‌ها: {len(orders) if isinstance(orders,list) else 0}\n💬 پیام‌ها: {total_msgs}", chat_keypad=bot_manage_actions(typ))
                else:
                    await msg.reply(f"📊 آمار ربات {idx+1}\n\n👥 کاربران: {len(users)}\n💬 پیام‌ها: {total_msgs}\n🟢 وضعیت: {'فعال' if bots_status.get(b.get('bot_id'),{}).get('active',True) else 'خاموش'}", chat_keypad=bot_manage_actions(typ))
                return
            if text == "📢 پیام همگانی":
                user["state"] = "bot_broadcast"; save_maker()
                await msg.reply("📢 متن پیام همگانی را بفرستید.\n\nبرای لغو: 🔙", chat_keypad=bot_manage_actions(typ)); return
            if text == "🔄 راه‌اندازی مجدد":
                try:
                    bid=b.get("bot_id"); await start_child_bot(bid, uid, b["token"], b["password"], b["type"])
                    await msg.reply("✅ ربات با تنظیمات ذخیره‌شده دوباره راه‌اندازی شد.", chat_keypad=bot_manage_actions(typ))
                except Exception as e: await msg.reply(f"❌ خطا در راه‌اندازی: {e}", chat_keypad=bot_manage_actions(typ))
                return

        if text in ("🔙 بازگشت", "🔙") and user.get("state") == "bot_keyboard":
            user["state"] = "bot_manager"; save_maker(); await msg.reply("🛠 مدیریت ربات:", chat_keypad=bot_manage_actions(typ)); return
        if text == "➕ افزودن دکمه" and user.get("state") == "bot_keyboard":
            user["state"] = "bot_add_button"; save_maker(); await msg.reply("➕ عنوان دکمه و پاسخ را بفرستید:\n`عنوان | پاسخ`", chat_keypad=bot_keyboard_menu()); return
        if text == "➖ حذف دکمه" and user.get("state") == "bot_keyboard":
            user["state"] = "bot_remove_button"; save_maker(); await msg.reply("➖ عنوان دقیق دکمه‌ای که باید حذف شود را بفرستید:", chat_keypad=bot_keyboard_menu()); return
        if text == "📋 لیست دکمه‌ها" and user.get("state") == "bot_keyboard":
            buttons = _manager_load(paths.get("buttons",""), [])
            if not buttons: out="⌨️ هنوز دکمه‌ای ساخته نشده."
            else: out="⌨️ دکمه‌های فعلی:\n\n" + "\n".join(f"{i+1}. {x.get('text','')}" for i,x in enumerate(buttons) if isinstance(x,dict))
            await msg.reply(out, chat_keypad=bot_keyboard_menu()); return

        if user.get("state") == "bot_start":
            if text in ("🔙", "🔙 بازگشت", "cancel", "لغو"):
                user["state"]="bot_manager"; save_maker(); await msg.reply("🔙", chat_keypad=bot_manage_actions(typ)); return
            if typ == "group_manager":
                raw_cfg, cfg = _group_default_cfg(paths)
                cfg["start_text"] = text
                _save_group_default(paths, cfg)
                user["state"]="bot_manager"; save_maker()
                await msg.reply("✅ پیام استارت مدیریت گروه ذخیره شد. برای اعمال فوری، «راه‌اندازی مجدد» را بزنید.", chat_keypad=bot_manage_actions(typ)); return
            if typ not in ("raw", "shop"):
                await msg.reply("❌ برای این نوع ربات، پیام استارت از این پنل قابل ویرایش نیست.", chat_keypad=bot_manage_actions(typ)); user["state"]="bot_manager"; save_maker(); return
            cfg=_manager_load(paths["config"], {})
            if not isinstance(cfg,dict): cfg={}
            cfg["welcome_text"] = text; _manager_save(paths["config"],cfg)
            user["state"]="bot_manager"; save_maker()
            await msg.reply("✅ پیام استارت ذخیره شد. برای اعمال فوری، «راه‌اندازی مجدد» را بزنید.", chat_keypad=bot_manage_actions(typ)); return

        if user.get("state") == "bot_command":
            if text in ("🔙", "🔙 بازگشت", "cancel", "لغو"):
                user["state"]="bot_manager"; save_maker(); await msg.reply("🔙", chat_keypad=bot_manage_actions(typ)); return
            if "|" not in text: await msg.reply("❌ فرمت اشتباه است. مثال: `/help | راهنمای ربات`", chat_keypad=bot_manage_actions(typ)); return
            cmd, resp = [x.strip() for x in text.split("|",1)]
            if not cmd: await msg.reply("❌ دستور خالی است.", chat_keypad=bot_manage_actions(typ)); return
            buttons=_manager_load(paths.get("buttons",""), [])
            if not isinstance(buttons,list): buttons=[]
            buttons=[x for x in buttons if not (isinstance(x,dict) and x.get("text")==cmd)]
            buttons.append({"id":"cmd_"+str(abs(hash(cmd))),"text":cmd,"row":max([int(x.get("row",0)) for x in buttons if isinstance(x,dict)] or [0]),"response":resp})
            _manager_save(paths["buttons"],buttons)
            user["state"]="bot_manager"; save_maker()
            await msg.reply("✅ دستور اضافه شد. برای اعمال فوری «راه‌اندازی مجدد» را بزنید.", chat_keypad=bot_manage_actions(typ)); return

        if user.get("state") == "bot_add_button":
            if "|" not in text: await msg.reply("❌ فرمت: عنوان | پاسخ", chat_keypad=bot_keyboard_menu()); return
            title, resp = [x.strip() for x in text.split("|",1)]
            buttons=_manager_load(paths["buttons"], [])
            if not isinstance(buttons,list): buttons=[]
            rows=[int(x.get("row",0)) for x in buttons if isinstance(x,dict) and str(x.get("row",0)).isdigit()]
            buttons.append({"id":"btn_"+str(abs(hash(title+resp))),"text":title,"row":(max(rows)+1 if rows else 0),"response":resp})
            _manager_save(paths["buttons"],buttons)
            user["state"]="bot_keyboard"; save_maker(); await msg.reply("✅ دکمه اضافه شد. برای اعمال فوری «راه‌اندازی مجدد» را بزنید.", chat_keypad=bot_keyboard_menu()); return

        if user.get("state") == "bot_remove_button":
            buttons=_manager_load(paths["buttons"], [])
            before=len(buttons) if isinstance(buttons,list) else 0
            buttons=[x for x in buttons if not (isinstance(x,dict) and x.get("text")==text)] if isinstance(buttons,list) else []
            _manager_save(paths["buttons"],buttons)
            user["state"]="bot_keyboard"; save_maker()
            await msg.reply("✅ حذف شد." if len(buttons)<before else "❌ چنین دکمه‌ای پیدا نشد.", chat_keypad=bot_keyboard_menu()); return

        if user.get("state") == "bot_broadcast":
            if text in ("🔙", "🔙 بازگشت", "cancel", "لغو"):
                user["state"]="bot_manager"; save_maker(); await msg.reply("🔙", chat_keypad=bot_manage_actions(typ)); return
            users=_manager_users(paths.get("users",""))
            sent=0; failed=0
            try:
                cb=Robot(b["token"])
                for target in users:
                    try: await cb.send_message(str(target), text); sent += 1; await asyncio.sleep(0.05)
                    except: failed += 1
            except Exception as e:
                await msg.reply(f"❌ اتصال به ربات ناموفق بود: {e}", chat_keypad=bot_manage_actions(typ)); return
            user["state"]="bot_manager"; save_maker()
            await msg.reply(f"📢 همگانی تمام شد.\n\n✅ ارسال موفق: {sent}\n❌ ناموفق: {failed}\n👥 کل کاربران ثبت‌شده: {len(users)}", chat_keypad=bot_manage_actions(typ)); return

    if text == "📖 راهنما":
        await msg.reply(maker_help_text(), chat_keypad=maker_main_menu(uid)); return
    
    if text in ("💰 سکه و شناسه", "💰 سکه و کد پیگیری"):
        vipst = "🟢 فعال" if is_vip_active(uid) else "🔴 غیرفعال"
        exp = user.get("vip_until") or "ندارد"
        await msg.reply(
            f"**💰 سکه:** `{user.get('coins',0)}`\n\n"
            f"**🆔 شناسه پیگیری:**\n`{uid}`\n\n"
            f"**👑 وضعیت VIP:** `{vipst}`\n"
            f"**📅 اعتبار VIP:** `{exp}`\n"
            f"**🤖 ظرفیت ساخت:** `{user_bot_count(uid)}/{user_bot_limit(uid)}`"
        )
        return
    
    if text == "📞 پشتیبانی":
        user["state"] = None; save_maker()
        await msg.reply(
            "**📞 سیستم پشتیبانی**\n\n"
            "🎫 برای ثبت تیکت جدید، روی دکمه زیر بزنید.\n"
            "📋 برای دیدن تیکت‌های قبلی، «تیکت‌های من» را بزنید.",
            chat_keypad=support_keypad())
        return
    
    if text == "🎫 ثبت تیکت جدید":
        user["state"] = "ticket_message"; save_maker()
        await msg.reply("**📩 لطفاً پیام خود را برای پشتیبانی ارسال کنید.**", chat_keypad=ticket_answer_kp()); return
    if user.get("state") == "ticket_message":
        if text in ("❌ لغو","🔙 بازگشت"):
            user["state"] = None; save_maker()
            await msg.reply("✅ لغو شد.", chat_keypad=support_keypad()); return
        tid = f"T{int(datetime.datetime.now().timestamp()*1000)}"
        tickets[tid] = {"user_id": uid, "user_name": user.get("name", "کاربر"),
                        "subject": "پشتیبانی",
                        "messages": [{"from":"user","text":text,"time":str(datetime.datetime.now())}], "status": "open",
                        "created_at": str(datetime.datetime.now())}
        save_tickets()
        try: await bot.send_message(MAKER_ADMIN_ID, f"🎫 تیکت جدید `{tid}`\n👤 {user.get('name','کاربر')}\n🆔 `{uid}`\n\n💬 {text}")
        except: pass
        user["state"] = None; save_maker()
        await msg.reply(f"**✅ تیکت شما با موفقیت ثبت شد.**\n🆔 `{tid}`\n\n📨 پیام شما برای پشتیبانی ارسال شد و پس از بررسی پاسخ داده می‌شود.", chat_keypad=support_keypad()); return
        user["state"] = "ticket_msg"; user["temp"]["tid"] = tid; save_maker()
        await msg.reply(f"✅ تیکت `{tid}` ثبت شد.\n\n✍️ حالا متن کامل مشکل خود را بنویسید:", chat_keypad=ticket_answer_kp())
        return
    if user.get("state") == "ticket_msg":
        if text == "❌ لغو":
            user["state"] = None; user["temp"] = {}; save_maker()
            await msg.reply("✅ لغو شد.", chat_keypad=support_keypad()); return
        tid = user["temp"].get("tid")
        if tid and tid in tickets:
            tickets[tid]["messages"].append({"from": "user", "text": text, "time": str(datetime.datetime.now())})
            save_tickets()
            user["state"] = None; user["temp"] = {}; save_maker()
            await msg.reply(f"✅ پیام شما به تیکت `{tid}` ارسال شد.", chat_keypad=support_keypad())
            for aid in maker_admins:
                try:
                    await bot.send_message(aid, f"🎫 تیکت جدید!\n🆔 `{tid}`\n👤 {user.get('name','کاربر')}\n📝 {tickets[tid]['subject']}\n\n💬 {text}")
                except: pass
        return
    
    if text == "📋 تیکت‌های من":
        mine = [(k,v) for k,v in tickets.items() if v.get("user_id") == uid]
        if not mine:
            await msg.reply("📭 هیچ تیکتی ندارید.", chat_keypad=support_keypad()); return
        o = "**📋 تیکت‌های شما**:\n\n"
        for tid, t in mine[-10:]:
            st = "🟢 باز" if t.get("status") == "open" else "✅"
            o += f"🆔 `{tid}`\n📝 {t.get('subject','')}\n{st}\n\n"
        o += "💡 «تیکت T...» برای مشاهده"
        await msg.reply(o, chat_keypad=support_keypad()); return
    
    if text.startswith("تیکت T"):
        tid = text[5:].strip()
        if tid in tickets and tickets[tid].get("user_id") == uid:
            t = tickets[tid]
            o = f"🎫 تیکت `{tid}`\n📝 {t.get('subject','')}\n📌 وضعیت: {'باز' if t.get('status') == 'open' else 'پاسخ داده شد'}\n\n💬 گفتگو:\n\n"
            messages = t.get("messages", []) if isinstance(t.get("messages", []), list) else []
            for m in messages:
                who = "👤 شما" if m.get("from") == "user" else "🎧 پشتیبانی"
                o += f"{who}: {m.get('text','')}\n\n"
            await msg.reply(o, chat_keypad=support_keypad())
        else:
            await msg.reply("❌ یافت نشد.", chat_keypad=support_keypad())
        return
    
    if text in ("🔙 بازگشت", "back_mybots"):
        user["state"] = None; save_maker()
        await msg.reply("**🔙 منوی اصلی**", chat_keypad=maker_main_menu(uid)); return
    
    if text == "🎁 سکه روزانه":
        today = str(datetime.date.today())
        if user.get("last_daily") == today:
            await msg.reply("**شما هدیه امروز را قبلا دریافت کردید**"); return
        amt = 4 if is_vip_active(uid) else 2
        user["coins"] = user.get("coins", 0) + amt; user["last_daily"] = today; save_maker()
        await msg.reply(f"**🎁 {amt} سکه گرفتی!**\n💰 تعداد کل سکه های شما: {user['coins']}")
        return
    
    if text == "🛍 فروشگاه":
        user["state"] = None; save_maker()
        await msg.reply(
            "**🛍 فروشگاه کانتر مود**\n\n"
            f"**📢 تبلیغ: `{AD_PRICE_TOMAN:,}` تومان**\n"
            "پس از پرداخت، پیام تبلیغ شما به کاربران ربات‌های فعال ربات‌ساز ارسال می‌شود.\n"
            "هر بار پرداخت، تبلیغ فقط یک بار ارسال می‌شود.\n\n"
            "**👑 اشتراک یکماهه VIP**\n"
            "**قیمت اشتراک یکماهه:** `40,000` **تومان**\n"
            "⚡ سرعت و اولویت بهتر ربات‌ها\n"
            "🚫 تبلیغات برای ربات‌های شما ارسال نمی‌شود\n"
            "🤖 امکان ساخت حداکثر ۵ ربات\n"
            "💰 دریافت خودکار ۵۰ سکه\n\n"
            "**💳 برای خرید، روی آیدی زیر بزنید و در PV پیام دهید:**\n"
            "**[@Abolfazl_Kazemi_SFG](https://rubika.ir/Abolfazl_Kazemi_SFG)**",
            chat_keypad=maker_main_menu(uid))
        return
    if text == "👑 VIP":
        user["state"] = None; save_maker()
        active = is_vip_active(uid); dl = get_vip_days_left(uid) if active else 0
        st = f"🟢 فعال ({dl} روز)" if active else "🔴 غیرفعال"
        await msg.reply(
            f"👑 پنل VIP\n\nوضعیت: {st}\n💰 {user.get('coins',0)}\n\n"
            f"✨ مزایا:\n• 🚫 بدون تبلیغ\n• 📈 تا 5 ربات\n• 🎁 سکه دوبرابر\n• ⚡ پشتیبانی سریع\n\n"
            f"💰 {VIP_COST} سکه / {VIP_DAYS} روز",
            chat_keypad=vip_panel_keypad())
        return
    
    if text == "📊 وضعیت VIP من":
        if is_vip_active(uid):
            await msg.reply(f"👑 🟢 فعال\n📅 {get_vip_days_left(uid)} روز\n💰 {user.get('coins',0)}")
        else:
            await msg.reply(f"👑 🔴 غیرفعال\n💰 {user.get('coins',0)}")
        return
    
    if text == "ℹ️ مزایای VIP":
        await msg.reply(f"✨ VIP ({VIP_COST} سکه / {VIP_DAYS} روز):\n\n1️⃣ 🚫 بدون تبلیغ\n2️⃣ 📈 تا 5 ربات\n3️⃣ 🎁 سکه دوبرابر\n4️⃣ ⚡ پشتیبانی\n\n🔄 تمدیدپذیر"); return
    
    if text in ("👑 خرید VIP (100 سکه)","vip_buy"):
        await msg.reply("👑 خرید VIP\n\nبرای خرید یا فعال‌سازی VIP، به PV سازنده پیام دهید:\n[@Abolfazl_Kazemi_SFG](https://rubika.ir/Abolfazl_Kazemi_SFG)", chat_keypad=maker_main_menu(uid)); return
    
    if text in ("🔄 تمدید VIP","vip_renew"):
        await msg.reply("👑 تمدید VIP\n\nبرای تمدید به PV سازنده پیام دهید:\n[@Abolfazl_Kazemi_SFG](https://rubika.ir/Abolfazl_Kazemi_SFG)", chat_keypad=maker_main_menu(uid)); return
    
    if text in ("🛑 خاموش کردن همه","🛑 خاموش کردن تمام ربات ها"):
        bots = maker_bots.get(uid, [])
        if not bots:
            await msg.reply("❌ رباتی ندارید!"); return
        c = 0
        for b in bots:
            bid = b.get("bot_id")
            if bid and bid in child_tasks and not child_tasks[bid].done():
                child_tasks[bid].cancel(); c += 1
            if bid:
                if bid not in bots_status: bots_status[bid] = {}
                bots_status[bid]["active"] = False
        save_bots_status()
        await msg.reply(f"🛑 {c} ربات خاموش شد.")
        return
    
    if text in ("▶️ روشن کردن همه","▶️ روشن کردن تمام ربات ها"):
        bots = maker_bots.get(uid, [])
        if not bots:
            await msg.reply("❌ رباتی ندارید!"); return
        c = 0
        for b in bots:
            bid = b.get("bot_id")
            if bid and bid in child_tasks and not child_tasks[bid].done():
                child_tasks[bid].cancel(); await asyncio.sleep(0.3)
            try:
                await start_child_bot(bid, uid, b["token"], b["password"], b["type"])
                c += 1; await asyncio.sleep(0.5)
            except Exception as e: print(f"start err {bid}: {e}")
        await msg.reply(f"▶️ {c} ربات روشن شد.")
        return
    
    if admin_identity_ok and MAKER_ADMIN_ID in maker_admins:
        if text == "🏆 آمار کاربران":
            rows=[]
            for u2,data in maker_users.items():
                if not isinstance(data,dict): data={}
                rows.append((int(data.get("coins",0) or 0), str(u2), safe_user_name(data.get("name"))))
            rows.sort(key=lambda x:(x[0], x[1]), reverse=True)
            out="🏆 **لیدربورد کاربران — ۲۰ نفر اول**\n\n"
            for i,(coins,uid2,name) in enumerate(rows[:20],1):
                med=["🥇","🥈","🥉"][i-1] if i<=3 else f"{i}."
                out += f"{med} {safe_user_name(name)}\n🆔 `{uid2}`\n💰 {coins} سکه\n\n"
            await msg.reply(out or "📭 کاربری نیست.", chat_keypad=maker_admin_menu()); return
        if text == "📊 آمار ربات ساز":
            total_bots = sum(len(bots) for bots in maker_bots.values())
            active_bots = sum(1 for bots in maker_bots.values() for b in bots if bots_status.get(b.get("bot_id"), {}).get("active", True) and b.get("bot_id") in child_tasks and not child_tasks[b.get("bot_id")].done())
            inactive_bots = max(0, total_bots - active_bots)
            vip_count = sum(1 for u_id in maker_users if is_vip_active(u_id))
            blocked_count = len(set(str(x) for x in maker_settings.get("blocked_users", [])))
            total_coins = sum(int((d or {}).get("coins",0) or 0) for d in maker_users.values() if isinstance(d,dict))
            open_tickets = sum(1 for t in tickets.values() if t.get("status") == "open")
            answered_tickets = sum(1 for t in tickets.values() if t.get("status") == "answered")
            type_counts = {}
            for bl in maker_bots.values():
                for b in bl:
                    typ = _manager_type_name(b.get("type"))
                    type_counts[typ] = type_counts.get(typ,0)+1
            types_text = "\n".join(f"• {k}: {v}" for k,v in type_counts.items()) or "• بدون ربات"
            await msg.reply(
                "📊 **آمار دقیق ربات ساز**\n\n"
                f"👥 کاربران: {len(maker_users)}\n"
                f"🚫 مسدودها: {blocked_count}\n"
                f"👑 VIP فعال: {vip_count}\n"
                f"👤 بدون VIP: {max(0,len(maker_users)-vip_count)}\n"
                f"💰 مجموع سکه کاربران: {total_coins}\n"
                f"🤖 مجموع ربات‌ها: {total_bots}\n"
                f"🟢 ربات‌های فعال: {active_bots}\n"
                f"🔴 ربات‌های غیرفعال: {inactive_bots}\n"
                f"🎫 مجموع تیکت‌ها: {len(tickets)}\n"
                f"📥 تیکت‌های باز: {open_tickets}\n"
                f"✅ تیکت‌های پاسخ‌داده‌شده: {answered_tickets}\n\n"
                "📦 تفکیک ربات‌ها:\n" + types_text, chat_keypad=maker_admin_menu()); return
        if text in ("📢 ثبت تبلیغ","📢 تنظیم تبلیغ"):
            user["state"] = "wait_ad_text"; save_maker()
            await msg.reply("✍️ متن:"); return
        if text == "🗑 حذف تبلیغ":
            maker_settings["start_ad"] = ""
            save_settings()
            # حذف آگهی فعال از وضعیت حافظه نیز انجام می‌شود تا در اجرای بعدی ربات‌ها باقی نماند.
            for _cid, _campaign in list(ad_campaigns.items()):
                if isinstance(_campaign, dict) and _campaign.get("active") is True:
                    _campaign["active"] = False
            save_ads()
            user["state"] = None; user["temp"] = {}; save_maker()
            await msg.reply("✅ تبلیغ فعال با موفقیت حذف شد.\n📢 از این لحظه تبلیغ جدیدی به کاربران نمایش داده نمی‌شود.", chat_keypad=maker_admin_menu()); return
        if text == "🗑 حذف VIP":
            user["state"] = "remove_vip_id"; save_maker()
            await msg.reply("🆔 آیدی کاربری که باید VIP آن حذف شود را ارسال کنید:", chat_keypad=maker_admin_menu()); return
        if text == "🚫 مسدود کردن":
            user["state"] = "block_user_id"; save_maker()
            await msg.reply("🆔 آیدی کاربری که باید مسدود شود را ارسال کنید:", chat_keypad=maker_admin_menu()); return
        if text == "✅ رفع مسدودیت":
            user["state"] = "unblock_user_id"; save_maker()
            await msg.reply("🆔 آیدی کاربری که باید رفع مسدود شود را ارسال کنید:", chat_keypad=maker_admin_menu()); return
        if text == "📢 همگانی همه":
            user["state"] = "all_broadcast"; save_maker()
            await msg.reply("✍️ پیام را ارسال کنید. برای تمام مخاطبان ربات‌ساز و تمام مخاطبان ربات‌های ساخته‌شده ارسال می‌شود:", chat_keypad=maker_admin_menu()); return
        if text == "👑 لیست VIP ها":
            o = "👑 VIP های فعال:\n\n"; c = 0
            for u2 in maker_users:
                if is_vip_active(u2):
                    c += 1; dl = get_vip_days_left(u2)
                    o += f"• `{u2}` — {dl} روز\n"
            if c == 0: o += "کسی VIP نیست."
            else: o += f"\n📊 {c} VIP"
            await msg.reply(o); return
        if text == "🎁 اهدای VIP":
            user["state"] = "give_vip_id"; save_maker()
            await msg.reply("🆔:"); return
        if text == "📨 ارسال تبلیغ به ربات‌ها":
            user["state"] = "broadcast_to_bots"; save_maker()
            await msg.reply("✍️ متن:"); return
        if text == "🎫 تیکت‌های پشتیبانی":
            user["state"] = None; save_maker()
            await msg.reply("🎫 پنل تیکت‌ها:", chat_keypad=tickets_admin_kp()); return
        if text == "📥 تیکت‌های جدید":
            new_ts = [(k,v) for k,v in tickets.items() if v.get("status") == "open"]
            if not new_ts: await msg.reply("📭", chat_keypad=tickets_admin_kp()); return
            o = "📥 تیکت‌های باز:\n\n"
            for tid, t in new_ts[:20]:
                msgs = t.get("messages", []) if isinstance(t.get("messages", []), list) else []
                first_user = next((m for m in msgs if isinstance(m, dict) and m.get("from") == "user"), {})
                preview = str(first_user.get("text", "")).strip().replace("\n", " ")[:350] or "بدون متن"
                o += f"🆔 `{tid}`\n👤 {t.get('user_name','?')}\n💬 {preview}\n\n"
            await msg.reply(o, chat_keypad=tickets_admin_kp()); return
        if text == "📋 همه تیکت‌ها":
            if not tickets: await msg.reply("📭", chat_keypad=tickets_admin_kp()); return
            o = "📋:\n\n"
            for tid, t in list(tickets.items())[-20:]:
                st = "🟢" if t.get("status") == "open" else "✅"
                msgs = t.get("messages", []) if isinstance(t.get("messages", []), list) else []
                first_user = next((m for m in msgs if isinstance(m, dict) and m.get("from") == "user"), {})
                preview = str(first_user.get("text", "")).strip().replace("\n", " ")[:120] or "بدون متن"
                o += f"{st} `{tid}` — {t.get('user_name','?')}\n💬 {preview}\n\n"
            await msg.reply(o, chat_keypad=tickets_all_kp()); return
        if text == "🗑 حذف همه تیکت‌ها":
            user["state"] = "confirm_delete_tickets"; save_maker()
            await msg.reply("⚠️ **هشدار:** تمام تیکت‌ها برای همیشه حذف می‌شوند.\n\nبرای تأیید دقیقاً بنویسید: `تایید حذف همه تیکت‌ها`", chat_keypad=tickets_all_kp()); return
        if text == "💬 چت با کاربر":
            user["state"] = "t_chat_id"; user.setdefault("temp", {}).pop("chat_user", None); user["temp"].pop("last_chat_message_id", None); save_maker()
            await msg.reply("🆔 آیدی کاربر را بفرستید.\n\n💡 اگر از داخل تیکت وارد شده‌اید، همان آیدی درج‌شده در تیکت را کپی کنید.", chat_keypad=tickets_admin_kp()); return
        if text in ("پایان گفتگو", "🔚 پایان گفتگو", "chat_end") and user.get("state") in ("t_chat", "t_chat_edit", "t_chat_delete"):
            user["state"] = None; user["temp"] = {}; save_maker()
            await msg.reply("✅ گفتگو پایان یافت.", chat_keypad=tickets_admin_kp()); return
        if user.get("state") == "t_chat_id":
            target = text.strip()
            if target not in maker_users:
                await msg.reply("❌ این آیدی در کاربران ربات‌ساز پیدا نشد. دوباره آیدی صحیح را بفرستید:", chat_keypad=tickets_admin_kp()); return
            user["temp"]["chat_user"] = target; user["temp"].pop("last_chat_message_id", None); user["state"] = "t_chat"; save_maker()
            await msg.reply(f"💬 **گفتگو با `{target}` شروع شد.**\n\n📤 هر متن یا پیام را بفرستید تا برای کاربر ارسال شود.\n✏️ برای ویرایش آخرین پیام ارسالی، دکمه «ویرایش آخرین پیام» را بزنید.\n🗑 برای حذف آخرین پیام ارسالی، دکمه «حذف آخرین پیام» را بزنید.\n↩️ اگر روی پیام کاربر پاسخ بدهید، پاسخ شما به همان پیام مرتبط می‌شود.", chat_keypad=ticket_chat_kp()); return
        if user.get("state") == "t_chat_edit":
            target = str(user.get("temp", {}).get("chat_user", "")).strip()
            mid = str(user.get("temp", {}).get("last_chat_message_id", "")).strip()
            if not target or not mid:
                user["state"] = "t_chat"; save_maker()
                await msg.reply("❌ هنوز پیام ارسالی برای ویرایش وجود ندارد.", chat_keypad=ticket_chat_kp()); return
            if text in ("🔙 بازگشت", "🔚 پایان گفتگو", "chat_end"):
                user["state"] = "t_chat"; save_maker(); await msg.reply("لغو شد.", chat_keypad=ticket_chat_kp()); return
            try:
                await bot.edit_message_text(target, mid, text)
                user["state"] = "t_chat"; save_maker()
                await msg.reply("✅ آخرین پیام ویرایش شد.", chat_keypad=ticket_chat_kp())
            except Exception as e:
                user["state"] = "t_chat"; save_maker(); await msg.reply(f"❌ ویرایش انجام نشد: {e}", chat_keypad=ticket_chat_kp())
            return
        if user.get("state") == "t_chat_delete":
            target = str(user.get("temp", {}).get("chat_user", "")).strip()
            mid = str(user.get("temp", {}).get("last_chat_message_id", "")).strip()
            if not target or not mid:
                user["state"] = "t_chat"; save_maker()
                await msg.reply("❌ هنوز پیام ارسالی برای حذف وجود ندارد.", chat_keypad=ticket_chat_kp()); return
            try:
                await bot.delete_message(target, mid)
                user["temp"].pop("last_chat_message_id", None); user["state"] = "t_chat"; save_maker()
                await msg.reply("✅ آخرین پیام حذف شد.", chat_keypad=ticket_chat_kp())
            except Exception as e:
                user["state"] = "t_chat"; save_maker(); await msg.reply(f"❌ حذف انجام نشد: {e}", chat_keypad=ticket_chat_kp())
            return
        if user.get("state") == "t_chat":
            target = str(user.get("temp", {}).get("chat_user", "")).strip()
            if not target:
                user["state"] = None; user["temp"] = {}; save_maker(); return
            if text in ("📤 ارسال پیام", "chat_send"):
                await msg.reply("✍️ متن پیام را بفرستید:", chat_keypad=ticket_chat_kp()); return
            if text in ("✏️ ویرایش آخرین پیام", "chat_edit"):
                if not user.get("temp", {}).get("last_chat_message_id"):
                    await msg.reply("❌ هنوز پیامی از شما برای ویرایش ارسال نشده است.", chat_keypad=ticket_chat_kp()); return
                user["state"] = "t_chat_edit"; save_maker(); await msg.reply("✏️ متن جدید آخرین پیام را بفرستید:", chat_keypad=ticket_chat_kp()); return
            if text in ("🗑 حذف آخرین پیام", "chat_delete"):
                if not user.get("temp", {}).get("last_chat_message_id"):
                    await msg.reply("❌ هنوز پیامی از شما برای حذف ارسال نشده است.", chat_keypad=ticket_chat_kp()); return
                user["state"] = "t_chat_delete"; save_maker(); await msg.reply("🗑 برای تأیید حذف آخرین پیام، «بله» بفرستید یا «🔙 بازگشت» را بزنید.", chat_keypad=ticket_chat_kp()); return
            if text.strip() == "بله" and user.get("temp", {}).get("last_chat_message_id"):
                mid = str(user["temp"].get("last_chat_message_id"));
                try:
                    await bot.delete_message(target, mid); user["temp"].pop("last_chat_message_id", None); save_maker(); await msg.reply("✅ آخرین پیام حذف شد.", chat_keypad=ticket_chat_kp())
                except Exception as e: await msg.reply(f"❌ حذف انجام نشد: {e}", chat_keypad=ticket_chat_kp())
                return
            try:
                _admin_reply_id = getattr(msg, "reply_to_message_id", None)
                _target_reply_id = support_reply_map.get((str(chat_id), str(_admin_reply_id))) if _admin_reply_id else None
                if text:
                    _sent = await bot.send_message(target, text, reply_to_message_id=str(_target_reply_id) if _target_reply_id else None)
                    _sent_mid = _sent.get("message_id") if isinstance(_sent, dict) else getattr(_sent, "message_id", None)
                    if _sent_mid:
                        user["temp"]["last_chat_message_id"] = str(_sent_mid); save_maker()
                        if _admin_reply_id:
                            support_reply_map[(str(chat_id), str(_sent_mid))] = str(_admin_reply_id)
                else:
                    mid = getattr(msg, "message_id", None) or getattr(msg, "id", None)
                    if mid and hasattr(bot, "forward_message"):
                        try: _sent = await bot.forward_message(chat_id=chat_id, message_id=str(mid), to_chat_id=target)
                        except TypeError: _sent = await bot.forward_message(chat_id, str(mid), target)
                        _sent_mid = _sent.get("message_id") if isinstance(_sent, dict) else getattr(_sent, "message_id", None)
                        if _sent_mid: user["temp"]["last_chat_message_id"] = str(_sent_mid); save_maker()
                    else:
                        await bot.send_message(target, "📎 پیام رسانه‌ای دریافت شد.")
                await msg.reply("✅ ارسال شد.\n💡 برای ویرایش یا حذف همین پیام از دو دکمه بالای کیبورد استفاده کنید.", chat_keypad=ticket_chat_kp()); return
            except Exception as e:
                await msg.reply(f"❌ ارسال انجام نشد: {e}", chat_keypad=ticket_chat_kp()); return
        if text == "📤 پاسخ به تیکت":
            user["state"] = "t_reply_id"; user.setdefault("temp", {}).pop("tid", None); save_maker()
            await msg.reply("🆔 شماره تیکت را ارسال کنید:", chat_keypad=tickets_admin_kp()); return
        if user.get("state") == "t_reply_id":
            tid = text.strip()
            if tid not in tickets:
                await msg.reply("❌ این شماره تیکت پیدا نشد. دوباره شماره صحیح را بفرستید:", chat_keypad=tickets_admin_kp()); return
            user["temp"]["tid"] = tid; user["state"] = "t_reply_msg"; save_maker()
            t = tickets[tid]
            msgs = t.get("messages", []) if isinstance(t.get("messages", []), list) else []
            history = ""
            for m in msgs[-10:]:
                who = "👤 کاربر" if m.get("from") == "user" else "🎧 پشتیبانی"
                history += f"{who}: {m.get('text','')}\n\n"
            await msg.reply(f"🎫 تیکت `{tid}`\n👤 {t.get('user_name','کاربر')}\n\n💬 سابقه پیام‌ها:\n{history or 'بدون پیام'}\n✍️ حالا پاسخ خود را ارسال کنید:", chat_keypad=tickets_admin_kp()); return
        if user.get("state") == "t_reply_msg":
            tid = str(user.get("temp", {}).get("tid", "")).strip()
            if not tid or tid not in tickets:
                user["state"] = None; user["temp"] = {}; save_maker()
                await msg.reply("❌ تیکت پیدا نشد.", chat_keypad=tickets_admin_kp()); return
            reply_text = text.strip()
            if not reply_text or reply_text in ("📤 پاسخ به تیکت", "🔙 بازگشت", "🔙"):
                await msg.reply("❌ متن پاسخ خالی است. پاسخ خود را ارسال کنید:", chat_keypad=tickets_admin_kp()); return
            target_id = str(tickets[tid].get("user_id", "")).strip()
            try:
                await bot.send_message(target_id, f"🎫 پاسخ تیکت `{tid}`:\n\n{reply_text}")
            except Exception as e:
                await msg.reply(f"❌ ارسال پاسخ به کاربر انجام نشد.\n\n{e}", chat_keypad=tickets_admin_kp()); return
            tickets[tid].setdefault("messages", []).append({"from":"admin", "text":reply_text, "time":str(datetime.datetime.now())})
            tickets[tid]["status"] = "answered"
            tickets[tid]["answered_at"] = str(datetime.datetime.now())
            save_tickets()
            user["state"] = None; user["temp"] = {}; save_maker()
            await msg.reply(f"✅ پاسخ تیکت `{tid}` با موفقیت برای کاربر ارسال شد.", chat_keypad=tickets_admin_kp()); return
        if text == "🛑 خاموش فرزندها":
            await msg.reply("⏳..."); c = await stop_all_child_bots()
            await msg.reply(f"🛑 {c}"); return
        if text == "▶️ روشن فرزندها":
            await msg.reply("⏳..."); c = await start_all_child_bots()
            await msg.reply(f"▶️ {c}"); return
        if text == "💰 افزودن سکه":
            user["state"] = "add_maker_coin_id"; save_maker()
            await msg.reply("🆔 کاربر را بفرستید:"); return
        if text == "🗑 حذف سکه":
            user["state"] = "remove_maker_coin_id"; save_maker()
            await msg.reply("🆔 آیدی کاربر را بفرستید:"); return
        if text == "📢 پیام همگانی":
            user["state"] = "maker_broadcast"; save_maker()
            await msg.reply("✍️:"); return
    
    if user.get("state") == "wait_ad_text":
        maker_settings["start_ad"] = text; save_settings()
        campaign_id = f"AD{int(datetime.datetime.now().timestamp())}"
        ad_campaigns[campaign_id] = {"text":text,"created_at":str(datetime.datetime.now()),"delivered":[],"price":AD_PRICE_TOMAN,"paid":True,"active":True}
        sent_users=0; failed=0; skipped_vip=0; delivered=set()
        for target_uid in maker_users.keys():
            if is_vip_active(target_uid): skipped_vip += 1; continue
            try: await bot.send_message(str(target_uid), f"📢 تبلیغ\n\n{text}"); sent_users += 1; delivered.add(f"maker:{target_uid}")
            except: failed += 1
        for oid, blist in maker_bots.items():
            if is_vip_active(oid): skipped_vip += len(blist); continue
            for bb in blist:
                bid=bb.get("bot_id");
                if not bid or not bots_status.get(bid,{}).get("active",True): continue
                try:
                    if bb.get("type")=="anonymous": ufile=f"users_{oid}.json"
                    elif bb.get("type")=="raw": ufile=f"rawbot_{oid}/users.json"
                    elif bb.get("type")=="group_manager": ufile=f"groupbot_{oid}/users.json"
                    else: ufile=f"shopbot_{oid}/users.json"
                    recipients=load_file(ufile,[]); cb=Robot(bb["token"])
                    for target in recipients:
                        key=f"{bid}:{target}"
                        if key in delivered: continue
                        try: await cb.send_message(str(target), f"📢 تبلیغ\n\n{text}"); delivered.add(key); sent_users += 1; await asyncio.sleep(.03)
                        except: failed += 1
                except Exception as e: print(f"ad error: {e}")
        ad_campaigns[campaign_id]["delivered"] = list(delivered); save_ads()
        user["state"] = None; save_maker()
        await msg.reply(f"✅ تبلیغ ثبت و ارسال شد.\n🆔 {campaign_id}\n💰 مبلغ ثبت‌شده: {AD_PRICE_TOMAN:,} تومان\n📨 ارسال موفق: {sent_users}\n❌ ناموفق: {failed}\n👑 VIP مستثنی: {skipped_vip}", chat_keypad=maker_admin_menu()); return
    
    if user.get("state") == "confirm_delete_tickets":
        if text == "تایید حذف همه تیکت‌ها":
            count = len(tickets); tickets.clear(); save_tickets()
            user["state"] = None; user["temp"] = {}; save_maker()
            await msg.reply(f"✅ {count} تیکت حذف شد.", chat_keypad=tickets_admin_kp()); return
        user["state"] = None; user["temp"] = {}; save_maker()
        await msg.reply("❌ عملیات لغو شد.", chat_keypad=tickets_admin_kp()); return
    if user.get("state") == "remove_vip_id":
        tid = text.strip()
        if tid not in maker_users:
            user["state"] = None; save_maker(); await msg.reply("❌ کاربر پیدا نشد.", chat_keypad=maker_admin_menu()); return
        maker_users[tid]["vip_until"] = None; maker_users[tid]["vip_bonus_granted"] = False
        save_maker(); user["state"] = None; user["temp"] = {}; save_maker()
        try: await bot.send_message(tid, "⚠️ VIP حساب شما توسط مدیریت حذف شد.")
        except: pass
        await msg.reply(f"✅ VIP کاربر `{tid}` حذف شد.", chat_keypad=maker_admin_menu()); return
    if user.get("state") == "block_user_id":
        tid = text.strip()
        if tid == MAKER_ADMIN_ID:
            user["state"] = None; save_maker(); await msg.reply("❌ مدیر اصلی قابل مسدود کردن نیست.", chat_keypad=maker_admin_menu()); return
        blocked = set(str(x) for x in maker_settings.get("blocked_users", [])); blocked.add(tid)
        maker_settings["blocked_users"] = sorted(blocked); save_settings()
        user["state"] = None; user["temp"] = {}; save_maker()
        await msg.reply(f"🚫 کاربر `{tid}` مسدود شد.", chat_keypad=maker_admin_menu()); return
    if user.get("state") == "unblock_user_id":
        tid = text.strip(); blocked = set(str(x) for x in maker_settings.get("blocked_users", []))
        if tid in blocked: blocked.remove(tid); maker_settings["blocked_users"] = sorted(blocked); save_settings(); result="✅ رفع مسدودیت شد."
        else: result="ℹ️ این کاربر مسدود نبود."
        user["state"] = None; user["temp"] = {}; save_maker()
        await msg.reply(f"{result}\n`{tid}`", chat_keypad=maker_admin_menu()); return
    if user.get("state") == "all_broadcast":
        user["state"] = None; save_maker()
        total=0; failed=0; seen=set()
        for target_uid in maker_users.keys():
            target_uid=str(target_uid)
            if target_uid in seen or target_uid in set(str(x) for x in maker_settings.get("blocked_users", [])): continue
            try: await bot.send_message(target_uid, text); total+=1; seen.add(target_uid)
            except: failed+=1
        for oid, blist in maker_bots.items():
            for bb in blist:
                try:
                    if bb.get("type")=="anonymous": ufile=f"users_{oid}.json"
                    elif bb.get("type")=="raw": ufile=f"rawbot_{oid}/users.json"
                    elif bb.get("type")=="group_manager": ufile=f"groupbot_{oid}/users.json"
                    else: ufile=f"shopbot_{oid}/users.json"
                    recipients=load_file(ufile,[])
                    cb=Robot(bb["token"])
                    for target in recipients if isinstance(recipients,list) else []:
                        key=f"{bb.get('bot_id')}:{target}"
                        if key in seen: continue
                        try: await cb.send_message(str(target), text); total+=1; seen.add(key); await asyncio.sleep(.03)
                        except: failed+=1
                except: failed+=1
        await msg.reply(f"📢 ارسال همگانی تمام شد.\n✅ موفق: {total}\n❌ ناموفق: {failed}", chat_keypad=maker_admin_menu()); return
    if user.get("state") == "give_vip_id":
        tid = text
        if tid not in maker_users:
            await msg.reply("❌"); user["state"] = None; save_maker(); return
        user["temp"]["vip_target"] = tid
        user["state"] = "give_vip_days"; save_maker()
        await msg.reply("📅 چند روز؟"); return
    if user.get("state") == "give_vip_days":
        if not text.isdigit(): await msg.reply("❌ عدد:"); return
        days = int(text); tid = user["temp"].get("vip_target")
        if tid:
            until = set_vip(tid, days)
            try:
                exp = datetime.datetime.fromisoformat(until)
                jl = jdatetime.datetime.fromgregorian(datetime=exp)
                exp_str = f"{jl.year}/{jl.month}/{jl.day}"
            except: exp_str = until
            await msg.reply(f"✅ {days} روز VIP به {tid} ثبت شد + {VIP_BONUS_COINS} سکه + ظرفیت ۵ ربات + حذف تبلیغات")
            try: await bot.send_message(tid, f"🎁 {days} روز VIP از مدیریت!\n📅 {exp_str}")
            except: pass
        user["state"] = None; user["temp"] = {}; save_maker(); return
    
    if user.get("state") == "broadcast_to_bots":
        user["state"] = None; save_maker()
        total_bots = sum(len(bots) for bots in maker_bots.values())
        await msg.reply(f"⏳ به {total_bots} ربات...")
        total = 0; failed = 0; skipped_vip = 0
        for oid, bots in list(maker_bots.items()):
            if is_vip_active(oid):
                skipped_vip += len(bots)
                continue
            for b in bots:
                try:
                    temp_bot = Robot(b["token"])
                    if b["type"] == "anonymous": ufile = f"users_{oid}.json"
                    elif b["type"] == "raw": ufile = f"rawbot_{oid}/users.json"
                    elif b["type"] == "shop": ufile = f"shopbot_{oid}/users.json"
                    else: ufile = f"groupbot_{oid}/users.json"
                    users_list = load_file(ufile, [])
                    for u2 in users_list:
                        try:
                            await temp_bot.send_message(u2, f"📨 پیام مدیر:\n\n{text}")
                            total += 1; await asyncio.sleep(0.05)
                        except: failed += 1
                except: pass
        await msg.reply(f"✅ {total} / ❌ {failed}\n\n👑 VIP skip شده: {skipped_vip} ربات")
        return
    
    if user.get("state") == "add_maker_coin_id":
        if text not in maker_users:
            await msg.reply("❌"); user["state"] = None; save_maker(); return
        user["temp"]["target_id"] = text
        user["state"] = "add_maker_coin_amount"; save_maker()
        await msg.reply("💰:"); return
    if user.get("state") == "add_maker_coin_amount":
        if not text.isdigit(): await msg.reply("❌ عدد:"); return
        amt = int(text); tid = user["temp"].get("target_id")
        if tid and tid in maker_users:
            maker_users[tid]["coins"] = maker_users[tid].get("coins",0) + amt
            await msg.reply(f"✅ {amt}")
            try: await bot.send_message(tid, f"**🎁 {amt} سکه از مدیرت دریافت کردید**")
            except: pass
        user["state"] = None; user["temp"] = {}; save_maker(); return
    if user.get("state") == "remove_maker_coin_id":
        tid = text.strip()
        if tid not in maker_users:
            user["state"] = None; user["temp"] = {}; save_maker()
            await msg.reply("❌ کاربر پیدا نشد.", chat_keypad=maker_admin_menu()); return
        user["temp"]["target_id"] = tid
        user["state"] = "remove_maker_coin_amount"; save_maker()
        await msg.reply(f"💰 چند سکه از `{tid}` حذف شود؟"); return
    if user.get("state") == "remove_maker_coin_amount":
        if not text.isdigit():
            await msg.reply("❌ فقط عدد وارد کنید:"); return
        amt = max(0, int(text)); tid = user["temp"].get("target_id")
        if tid and tid in maker_users:
            old_coins = int(maker_users[tid].get("coins", 0) or 0)
            removed = min(old_coins, amt)
            maker_users[tid]["coins"] = old_coins - removed
            save_maker()
            await msg.reply(f"✅ {removed} سکه از `{tid}` حذف شد.\n💰 موجودی جدید: {maker_users[tid]['coins']}", chat_keypad=maker_admin_menu())
            try: await bot.send_message(tid, f"⚠️ {removed} سکه از حساب شما توسط مدیریت کسر شد.\n💰 موجودی: {maker_users[tid]['coins']}")
            except: pass
        user["state"] = None; user["temp"] = {}; save_maker(); return

    if user.get("state") == "maker_broadcast":
        user["state"] = None; save_maker()
        await msg.reply("⏳...")
        c = 0
        for uid2 in maker_users.keys():
            try: await bot.send_message(uid2, text); c += 1; await asyncio.sleep(0.1)
            except: pass
        await msg.reply(f"✅ {c}"); return
    
    if text == "📋 ربات های من":
        bots = maker_bots.get(uid, [])
        if not bots:
            await msg.reply("**شما هنوز رباتی نساختی.**"); return
        o = f"📋 ربات‌های شما ({len(bots)}/{user_bot_limit(uid)}):\n\n"
        for i, b in enumerate(bots, 1):
            tn = {"anonymous":"چت ناشناس","group_manager":"مدیریت گروه","raw":"ربات خام","shop":"فروشگاه"}.get(b["type"], "?")
            st = "🟢 فعال" if bots_status.get(b["bot_id"], {}).get("active", True) else "🔴 غیرفعال"
            o += f"{i}. {tn} — {st}\n   🔐 {b['password']}\n\n"
        o += "__**💡 از دکمه‌های زیر برای مدیریت استفاده کنید:**__"
        user["state"] = None; save_maker()
        await msg.reply(o, chat_keypad=mybots_keypad_v2(uid))
        return
    
    if text.startswith("🔴 خاموش کردن ") or text.startswith("🟢 روشن کردن "):
        try:
            idx = int(text.split()[-1]) - 1
            bots = maker_bots.get(uid, [])
            if 0 <= idx < len(bots):
                b = bots[idx]; bid = b["bot_id"]
                active = bots_status.get(bid, {}).get("active", True)
                if active:
                    if bid in child_tasks and not child_tasks[bid].done():
                        child_tasks[bid].cancel(); await asyncio.sleep(0.3)
                    bots_status[bid] = {"active": False}; save_bots_status()
                    await msg.reply(f"🔴 ربات {idx+1} خاموش شد.", chat_keypad=mybots_keypad_v2(uid))
                else:
                    try:
                        await start_child_bot(bid, uid, b["token"], b["password"], b["type"])
                        await msg.reply(f"🟢 ربات {idx+1} روشن شد.", chat_keypad=mybots_keypad_v2(uid))
                    except Exception as e:
                        print(f"start err: {e}")
                        await msg.reply(f"❌ خطا در روشن کردن: {e}", chat_keypad=mybots_keypad_v2(uid))
            else:
                await msg.reply("❌ ربات یافت نشد.", chat_keypad=mybots_keypad_v2(uid))
        except Exception as e:
            print(f"toggle err: {e}")
            await msg.reply("❌ خطا.", chat_keypad=mybots_keypad_v2(uid))
        return
    
    if text.startswith("🗑 حذف "):
        try:
            idx = int(text.split()[-1]) - 1
            bots = maker_bots.get(uid, [])
            if 0 <= idx < len(bots):
                b = bots[idx]; bid = b["bot_id"]
                if bid in child_tasks and not child_tasks[bid].done():
                    child_tasks[bid].cancel(); await asyncio.sleep(0.3)
                maker_bots[uid].pop(idx)
                if bid in bots_status: bots_status.pop(bid, None)
                if bid in child_tasks: child_tasks.pop(bid, None)
                save_maker(); save_bots_status()
                remaining = len(maker_bots.get(uid, []))
                if remaining > 0:
                    await msg.reply(f"🗑 ربات {idx+1} حذف شد.\n📊 باقیمانده: {remaining}", chat_keypad=mybots_keypad_v2(uid))
                else:
                    await msg.reply(f"🗑 ربات {idx+1} حذف شد.\n📊 رباتی ندارید.", chat_keypad=maker_main_menu(uid))
            else:
                await msg.reply("❌ ربات یافت نشد.", chat_keypad=mybots_keypad_v2(uid))
        except Exception as e:
            print(f"delete err: {e}")
            await msg.reply("❌ خطا.", chat_keypad=mybots_keypad_v2(uid))
        return
    
    if text.startswith("📊 ربات ") and "—" in text:
        try:
            idx = int(text.split()[2]) - 1
            bots = maker_bots.get(uid, [])
            if 0 <= idx < len(bots):
                b = bots[idx]
                tn = {"anonymous":"چت ناشناس","group_manager":"مدیریت گروه","raw":"ربات خام","shop":"فروشگاه"}.get(b["type"], "?")
                st = "🟢 فعال" if bots_status.get(b["bot_id"], {}).get("active", True) else "🔴 غیرفعال"
                await msg.reply(
                    f"📊 اطلاعات ربات {idx+1}:\n\n"
                    f"🎯 نوع: {tn}\n{st}\n\n"
                    f"🆔 `{b['bot_id']}`\n🔑 `{b['token']}`\n🔐 رمز: {b['password']}\n📅 ساخت: {b.get('created_at','?')}",
                    chat_keypad=mybots_keypad_v2(uid))
        except Exception as e:
            print(f"info err: {e}")
        return
    
    if text == "➕ ساخت ربات جدید":
        limit_info = f"👑 VIP فعال — تا {user_bot_limit(uid)} ربات" if is_vip_active(uid) else "💡 با VIP می‌تونید 5 ربات بسازید"
        await msg.reply(f"**🎯 انتخاب نوع ربات:**\n\n**📊 ظرفیت:** `{user_bot_count(uid)}/{user_bot_limit(uid)}`\n{limit_info}", chat_keypad=maker_creation_menu()); return
    
    if text == "🛠 ربات خام — رایگان":
        if user_bot_count(uid) >= user_bot_limit(uid):
            await msg.reply(f"❌ ظرفیت پر! {user_bot_count(uid)}/{user_bot_limit(uid)}\n\n💡 VIP (100 سکه) = تا 5 ربات."); return
        user["state"] = "token"; user["temp"] = {"type": "raw"}; save_maker()
        await msg.reply(f"🔑 توکن ربات را بفرستید:\n\n📊 ظرفیت: {user_bot_count(uid)}/{user_bot_limit(uid)}"); return
    if text == "🤖 چت ناشناس — 1 سکه":
        if user_bot_count(uid) >= user_bot_limit(uid):
            await msg.reply(f"❌ ظرفیت پر! {user_bot_count(uid)}/{user_bot_limit(uid)}"); return
        if user.get("coins",0) >= 1:
            user["coins"] -= 1; user["state"] = "token"; user["temp"] = {"type": "anonymous"}; save_maker()
            await msg.reply(f"**✅ 1 سکه کسر شد.**\n🔑 توکن:\n\n📊 ظرفیت: {user_bot_count(uid)}/{user_bot_limit(uid)}")
        else: await msg.reply("❌ سکه کم.")
        return
    if text == "👥 مدیریت گروه — 5 سکه":
        if user_bot_count(uid) >= user_bot_limit(uid):
            await msg.reply(f"❌ ظرفیت پر! {user_bot_count(uid)}/{user_bot_limit(uid)}"); return
        if user.get("coins",0) >= 5:
            user["coins"] -= 5; user["state"] = "token"; user["temp"] = {"type": "group_manager"}; save_maker()
            await msg.reply(f"**✅ 5 سکه کسر شد.**\n🔑 توکن:\n\n📊 ظرفیت: {user_bot_count(uid)}/{user_bot_limit(uid)}")
        else: await msg.reply("❌ سکه کم.")
        return
    if user.get("state") == "token":
        if len(text) < 30: await msg.reply("❌ توکن نامعتبر:"); return
        user["temp"]["token"] = text; user["state"] = "password"; save_maker()
        await msg.reply("🔐 رمز مدیریت ربات فرزند:"); return
    
    if user.get("state") == "password":
        token = user["temp"]["token"]; pwd = text; bt = user["temp"]["type"]
        bid = create_bot_id(uid)
        new_bot = {"bot_id": bid, "token": token, "password": pwd, "type": bt,
                   "created_at": str(datetime.datetime.now())}
        if uid not in maker_bots: maker_bots[uid] = []
        maker_bots[uid].append(new_bot)
        user["state"] = None; user["temp"] = {}; save_maker()
        await start_child_bot(bid, uid, token, pwd, bt)
        tn = {"anonymous":"چت ناشناس","group_manager":"مدیریت گروه","raw":"ربات خام","shop":"فروشگاه"}.get(bt, "?")
        await msg.reply(
            f"✅ ربات {tn} ساخته و روشن شد!\n\n"
            f"🆔 `{bid}`\n🔐 `{pwd}`\n\n"
            f"📊 ربات‌های شما: {user_bot_count(uid)}/{user_bot_limit(uid)}",
            chat_keypad=maker_main_menu(uid))
        return

async def main():
    upd = False
    for uid, u in maker_users.items():
        if "vip_until" not in u:
            if u.get("vip"): u["vip_until"] = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
            else: u["vip_until"] = None
            u.pop("vip", None); upd = True
        if "last_daily" not in u: u["last_daily"] = None; upd = True
    if upd: save_maker()
    
    for uid, bots in maker_bots.items():
        for b in bots:
            bid = b.get("bot_id")
            if not bid: continue
            if bots_status.get(bid, {}).get("active", True):
                try:
                    await start_child_bot(bid, uid, b["token"], b["password"], b["type"])
                    await asyncio.sleep(0.2)
                except Exception as e: print(f"err start {bid}: {e}")
    
    print("ربات ساز در حال اجراست...")
    print(f"📊 کاربران: {len(maker_users)}")
    print(f"🤖 ربات‌ها: {sum(len(b) for b in maker_bots.values())}")
    retry_delay = 3
    while True:
        try:
            await asyncio.to_thread(main_bot.run)
            retry_delay = 3
        except asyncio.CancelledError:
            raise
        except Exception as e:
            err = str(e)
            if "502" in err or "Bad Gateway" in err or "APIRequestError" in err:
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)
            else:
                print(f"err: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    print("ربات ساز پیشرفته:")
    print("🛠 ربات خام | 🤖 چت ناشناس | 👥 مدیریت گروه | 🛍 فروشگاه")
    print("👑 VIP اشتراکی | 📞 پشتیبانی تیکتی | 🔐 پنل مدیریت")
    try: asyncio.run(main())
    except KeyboardInterrupt: print("\nمتوقف شد.")
    except Exception as e: print(f"خطا: {e}")
