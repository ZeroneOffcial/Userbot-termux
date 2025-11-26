#!/usr/bin/env python3
import os
import sys
import re
import time
import json
import asyncio
import logging
import platform
import importlib.util
from telethon import TelegramClient, events, Button
logging.basicConfig(level=logging.INFO)

SETTINGS_FILE = "settings.py"
USER_SESSION = "user"
BOT_SESSION = "bot"

def mask_value(val: str, keep=4):
    if val is None:
        return ""
    s = str(val)
    if len(s) <= keep:
        return "*" * len(s)
    return s[:keep] + "*" * (len(s) - keep)

def input_api_id():
    while True:
        s = input("Enter API_ID: ").strip()
        if not s:
            print("❌ API_ID cannot be empty.")
            continue
        if not s.isdigit():
            print("❌ API_ID must be numeric.")
            continue
        if len(s) < 5:
            print("❌ API_ID must be at least 5 digits.")
            continue
        return int(s)

def input_api_hash():
    while True:
        s = input("Enter API_HASH: ").strip()
        if not s:
            print("❌ API_HASH cannot be empty.")
            continue
        if re.fullmatch(r"[0-9a-fA-F]{32}", s):
            return s
        if len(s) >= 16:
            confirm = input("⚠ API_HASH doesn't look standard (not 32 hex). Use anyway? (y/N): ").strip().lower()
            if confirm == "y":
                return s
        print("❌ API_HASH invalid. Usually 32 hex characters (0-9, a-f).")

def input_bot_token():
    while True:
        s = input("Enter BOT_TOKEN: ").strip()
        if not s:
            print("❌ BOT_TOKEN cannot be empty.")
            continue
        if re.fullmatch(r"\d{5,}:[A-Za-z0-9_-]{20,}", s):
            return s
        print("❌ BOT_TOKEN invalid. Format: <bot_id>:<bot_token>")
        retry = input("Try again? (Y to retry / other to continue): ").strip().lower()
        if retry != "y":
            pass

def input_owner_id():
    while True:
        s = input("Enter OWNER_ID (numeric): ").strip()
        if not s:
            print("❌ OWNER_ID cannot be empty.")
            continue
        if not s.isdigit():
            print("❌ OWNER_ID must be numeric.")
            continue
        return int(s)

def write_settings_py(cfg: dict):
    content = []
    content.append(f"API_ID = {int(cfg['API_ID'])}")
    content.append(f"API_HASH = \"{cfg['API_HASH']}\"")
    content.append(f"BOT_TOKEN = \"{cfg['BOT_TOKEN']}\"")
    content.append(f"OWNER_ID = {int(cfg['OWNER_ID'])}")
    with open(SETTINGS_FILE, "w") as f:
        f.write("\n".join(content))
    print("✅ settings.py saved.")

def load_settings_py():
    if not os.path.exists(SETTINGS_FILE):
        return None
    try:
        spec = importlib.util.spec_from_file_location("settings", SETTINGS_FILE)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        cfg = {
            "API_ID": getattr(settings, "API_ID", None),
            "API_HASH": getattr(settings, "API_HASH", None),
            "BOT_TOKEN": getattr(settings, "BOT_TOKEN", None),
            "OWNER_ID": getattr(settings, "OWNER_ID", None)
        }
        if None in cfg.values():
            print("⚠ settings.py missing required variables. Recreate it.")
            return None
        return cfg
    except Exception as e:
        print("⚠ Failed to load settings.py:", e)
        return None

def create_settings():
    print(">>> Enter Telegram configuration (validated).")
    cfg = {}
    cfg["API_ID"] = input_api_id()
    cfg["API_HASH"] = input_api_hash()
    cfg["BOT_TOKEN"] = input_bot_token()
    cfg["OWNER_ID"] = input_owner_id()
    write_settings_py(cfg)
    return cfg

def remove_session_files():
    removed = []
    patterns = [f"{USER_SESSION}.session", f"{USER_SESSION}.session-journal", f"{BOT_SESSION}.session", f"{BOT_SESSION}.session-journal"]
    for fn in os.listdir("."):
        for pat in patterns:
            if fn == pat or fn.startswith(pat):
                try:
                    os.remove(fn)
                    removed.append(fn)
                except Exception:
                    pass
    for fn in (f"{USER_SESSION}.session", f"{BOT_SESSION}.session"):
        if os.path.exists(fn):
            try:
                os.remove(fn)
                if fn not in removed:
                    removed.append(fn)
            except Exception:
                pass
    if removed:
        print("🗑️ Removed session files:", ", ".join(removed))
    else:
        print("⚠ No session files found to remove.")

def show_masked_config(cfg):
    print("\n=== CONFIG (MASKED) ===")
    print("API_ID   :", mask_value(str(cfg.get("API_ID")), keep=3))
    print("API_HASH :", mask_value(cfg.get("API_HASH"), keep=4))
    print("BOT_TOKEN:", mask_value(cfg.get("BOT_TOKEN"), keep=5))
    print("OWNER_ID :", cfg.get("OWNER_ID"))
    print("=======================\n")

def main_menu():
    while True:
        cfg = load_settings_py()
        if cfg:
            print("\n=== MAIN MENU ===")
            print("1. Edit settings")
            print("2. Run current settings")
            print("3. Remove sessions (user & bot)")
            print("4. Delete settings.py")
            print("0. Exit")
            choice = input("Choose (0/1/2/3/4): ").strip()
            if choice == "1":
                cfg = create_settings()
            elif choice == "2":
                show_masked_config(cfg)
                confirm = input("Proceed to start userbot & bot with this config? (y/N): ").strip().lower()
                if confirm == "y":
                    return cfg
                else:
                    print("Cancelled. Back to menu.")
            elif choice == "3":
                confirm = input("⚠ Confirm remove all session files (will logout user & bot)? (y/N): ").strip().lower()
                if confirm == "y":
                    remove_session_files()
                else:
                    print("Cancelled.")
            elif choice == "4":
                confirm = input("⚠ Confirm delete settings.py? (y/N): ").strip().lower()
                if confirm == "y":
                    try:
                        os.remove(SETTINGS_FILE)
                        print("✅ settings.py deleted.")
                    except Exception as e:
                        print("❌ Failed to delete settings.py:", e)
                else:
                    print("Cancelled.")
            elif choice == "0":
                print("Bye.")
                sys.exit(0)
            else:
                print("❌ Invalid choice, try again.")
        else:
            print("\nNo settings.py found, creating new:")
            cfg = create_settings()

cfg = main_menu()

API_ID = int(cfg["API_ID"])
API_HASH = cfg["API_HASH"]
BOT_TOKEN = cfg["BOT_TOKEN"]
OWNER_ID = int(cfg["OWNER_ID"])

user_client = TelegramClient(USER_SESSION, API_ID, API_HASH)
bot_client = TelegramClient(BOT_SESSION, API_ID, API_HASH)

BOT_USERNAME = None
MY_ID = None

async def send_owner_only(event):
    await event.reply("<blockquote>❌ <b>Access denied</b>\nOwner only feature.</blockquote>", parse_mode="html")

async def init_my_id(user_client):
    global MY_ID
    await user_client.start()
    me = await user_client.get_me()
    MY_ID = me.id
    print("✅ Logged in user ID:", MY_ID)

OWNER_FILE = "owner.json"

def load_owners():
    try:
        with open(OWNER_FILE, "r") as f:
            data = json.load(f)
            return set(map(str, data.get("owners", [])))
    except FileNotFoundError:
        return set()

def save_owners(owners):
    with open(OWNER_FILE, "w") as f:
        json.dump({"owners": list(owners)}, f, indent=4)

async def is_owner(event):
    user_id = str(event.sender_id)
    if user_id == str(OWNER_ID):
        return True
    if user_id in load_owners():
        return True
    return False

@user_client.on(events.NewMessage(pattern=r'^\.ping$'))
async def ping_handler(event):
    if not await is_owner(event):
        await event.reply("❌ You do not have access!")
        return
    await event.reply("🏓 Pong!")

@user_client.on(events.NewMessage(pattern=r'^\.addakses (\d+)$'))
async def add_akses(event):
    if str(event.sender_id) != str(OWNER_ID):
        await event.reply("❌ Only main owner can add access.")
        return
    new_id = event.pattern_match.group(1)
    owners = load_owners()
    if new_id in owners:
        await event.reply(f"⚠️ ID `{new_id}` already in access list.")
        return
    owners.add(new_id)
    save_owners(owners)
    await event.reply(f"✅ ID `{new_id}` added to access.")

@user_client.on(events.NewMessage(pattern=r'^\.delakses (\d+)$'))
async def del_akses(event):
    if str(event.sender_id) != str(OWNER_ID):
        await event.reply("❌ Only main owner can remove access.")
        return
    del_id = event.pattern_match.group(1)
    owners = load_owners()
    if del_id not in owners:
        await event.reply(f"⚠️ ID `{del_id}` not in access list.")
        return
    owners.remove(del_id)
    save_owners(owners)
    await event.reply(f"🗑️ ID `{del_id}` removed from access.")

@user_client.on(events.NewMessage(pattern=r'^\.listakses$'))
async def list_akses(event):
    if str(event.sender_id) != str(OWNER_ID):
        await event.reply("❌ Only main owner can view access list.")
        return
    owners = load_owners()
    text = f"👑 Main owner: `{OWNER_ID}`\n\n"
    text += "🛠️ Additional owners:\n"
    if owners:
        text += "\n".join(f"- `{oid}`" for oid in owners)
    else:
        text += "No additional owners."
    await event.reply(text)

original_excepthook = sys.excepthook
def safe_excepthook(exctype, value, tb):
    original_excepthook(exctype, value, tb)
sys.excepthook = safe_excepthook

START_TIME = time.time()

async def start_clients():
    global BOT_USERNAME
    os.system("clear")
    print("🔥 Starting USERBOT & BOT...")
    print("===================================")
    os_info = f"{platform.system()} {platform.release()} ({platform.architecture()[0]})"
    uptime_sec = int(time.time() - START_TIME)
    uptime = f"{uptime_sec // 3600}h {(uptime_sec % 3600)//60}m {uptime_sec % 60}s"
    try:
        import psutil
        ram = psutil.virtual_memory()
        ram_usage = f"{ram.percent}% ({ram.used//1024**2}MB / {ram.total//1024**2}MB)"
        cpu_usage = f"{psutil.cpu_percent(interval=1)}%"
    except Exception:
        ram_usage = "N/A"
        cpu_usage = "N/A"
    print("✅ OS:", os_info)
    print("✅ Uptime:", uptime)
    print("✅ RAM Usage:", ram_usage)
    print("✅ CPU Usage:", cpu_usage)
    print("===================================")
    try:
        await init_my_id(user_client)
        me = await user_client.get_me()
        print(f"✅ USER LOGIN: {me.first_name} (ID: {me.id})")
    except Exception as e:
        print("❌ Failed to login user_client:", e)
        raise
    try:
        await bot_client.start(bot_token=BOT_TOKEN)
        bot_info = await bot_client.get_me()
        BOT_USERNAME = bot_info.username
        print("✅ BOT ONLINE: @%s" % BOT_USERNAME)
    except Exception as e:
        print("❌ Failed to start bot_client:", e)
        raise
    print("✅ Userbot & Bot are running...")
    print("🔥 Type .allmenu in any chat to open menu.")
    try:
        await bot_client.send_message(int(OWNER_ID), f"♻ USERBOT ACTIVATED ✅\n\nOS: {os_info}\nUptime: {uptime}\nRAM: {ram_usage}\nCPU: {cpu_usage}", buttons=[[Button.inline("Open Menu", b"control")]])
    except Exception:
        pass
    await asyncio.gather(user_client.run_until_disconnected(), bot_client.run_until_disconnected())


# ================================
# Fungsi khusus akses
# ================================
async def khususakses(event):
    """
    Cek apakah user punya akses owner utama / tambahan
    """
    user_id = str(event.sender_id)
    if user_id == str(OWNER_ID) or user_id in load_owners():
        return True

    # Kalau tidak ada akses
    await event.reply(
        "<blockquote>❌ You need access owner</blockquote>",
        parse_mode="html"
    )
    return False
# ================================
# Fungsi khusus owner utama
# ================================
async def khususowner(event):
    """
    Cek apakah user adalah OWNER utama
    """
    user_id = str(event.sender_id)
    if user_id == str(OWNER_ID):
        return True

    # Kalau bukan owner utama
    await event.reply(
        "<blockquote>❌ Khusus owner only</blockquote>",
        parse_mode="html"
    )
    return False
@user_client.on(events.NewMessage(pattern=r'^\.allmenu$'))
async def allmenu_handler(event):
    if not await khususakses(event):
        return

    await event.reply(
        """<blockquote>
❒——————— PANEL MENU ————————❒
╰➤ .1gb nama,id
╰➤ .2gb nama,id
╰➤ .3gb nama,id
╰➤ .4gb nama,id
╰➤ .5gb nama,id
╰➤ .6gb nama,id
╰➤ .7gb nama,id
╰➤ .8gb nama,id
╰➤ .9gb nama,id
╰➤ .10gb nama,id
╰➤ .unli nama,ii
▢ .listserver ==> cek semua server yang tersedia
▢ .delserver id
▢ .listuser cek semua user yang tersedia
▢ .listadmin cek semua admin panel
▢ .cadmin nama,id
▢ .deladmin id
❒——————— GROUP MENU ————————❒
▢ .kick reply/id
▢ .promote reply/id
▢ .demote reply/id
▢ .pin reply
▢ .unpin reply
▢ .liston ==> cek semua yang online di group
▢ .mute reply
▢ .unmute reply
❒——————— OTHER MENU ————————❒
▢ .ai query
▢ .cekip domain
▢ .id
▢ .ipaddress IP
▢ .gimg generate IMG ( image )
▢ .rbg reply/caption ==> remove background 
▢ .cimg query
▢ .cgame query
❒——————— BOT MENU ————————❒
▢ .cfd all/group
▢ .afk reason
▢ .addbl
▢ .unbl
▢ .info
▢ .tt link tiktok
▢ .ttmp3 link tiktok
▢ .song query
▢ .block id ==> blokir telegram penggunaa
▢ .unblock id ==> buka blokiran penggunaa
❒——————— ENC PYTHON ————————❒
⪩ .encpy 50   •  Super ringan  
⪩ .encpy 100  •  Stabil (default)  
⪩ .encpy 125  •  Lebih aman  
⪩ .encpy 130  •  Project menengah  
⪩ .encpy 150  •  Balance performa  
⪩ .encpy 160  •  Tingkat lanjut  
⪩ .encpy 165  •  Hampir maksimal  
⪩ .encpy 170  •  Encode berat  
⪩ .encpy 185  •  High-level secure  

<b>⚠️ Tidak Disarankan </b>  
───────────────────────  
⪩ .encpy 190  •  Risiko error  
⪩ .encpy 200  •  Terlalu berat  
⪩ .encpy 225  •  Overkill  
⪩ .encpy 250  •  Sangat lambat  
⪩ .encpy 260  •  Tidak stabil  
⪩ .encpy 265  •  Extreme bbuk

<b>📖 Penjelasan Level ENC</b>  
───────────────────────  
• <b>50 – 130</b> → Ringan – cocok untuk script kecil/personal.  
• <b>150 – 170</b> → Medium-high – balance antara keamanan & performa.  
• <b>185+</b> → Sangat tinggi – aman, tapi makin berat dijalankan.  
• <b>190 – 265</b> → Eksperimental – rawan error, hanya untuk uji ekstrem.  
——————————————————————————————
</blockquote>""",
        parse_mode="html"
    )
    
@user_client.on(events.NewMessage(pattern=r"\.menu"))
async def allmenu_handler(event):
    if BOT_USERNAME is None:
        await event.respond("❌ Bot belum siap.")
        return
    try:
        results = await user_client.inline_query(BOT_USERNAME, "allmenu")
        if results:
            await results[0].click(event.chat_id)
        else:
            await event.respond("❌ Tidak ada hasil inline dari bot.")
    except Exception as e:
        await event.respond(f"❌ Error: {e}")
        
@user_client.on(events.NewMessage(pattern=r"\.control"))
async def control_handler(event):
    if BOT_USERNAME is None:
        await event.respond("❌ Bot belum siap.")
        return
    try:
        results = await user_client.inline_query(BOT_USERNAME, "control")
        if results:
            await results[0].click(event.chat_id)
        else:
            await event.respond("❌ Tidak ada hasil inline dari bot.")
    except Exception as e:
        await event.respond(f"❌ Error: {e}")
@user_client.on(events.NewMessage(pattern=r"\.info"))
async def id_handler(event):
    if BOT_USERNAME is None:
        await event.respond("❌ Bot belum siap.")
        return
    try:
        results = await user_client.inline_query(BOT_USERNAME, f"cekid")
        if results:
            await results[0].click(event.chat_id)
        else:
            await event.respond("❌ Tidak ada hasil inline dari bot.")
    except Exception as e:
        await event.respond(f"❌ Error: {e}")
from telethon import events, Button
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors.rpcerrorlist import MessageNotModifiedError
import asyncio
def safe_attr(obj, attr):
    value = getattr(obj, attr, None)
    if not value:
        return "none"
    return value
    
@bot_client.on(events.InlineQuery)
async def inline_cekid_handler(event):
    if event.text != "cekid":
        return
    text = "<b>CEK DETAIL AKUN DAN DETAIL ANDA</b>"
    buttons = [
        [Button.inline("ℹ️ Detail User", data="show_detail")]
    ]
    result = event.builder.article(
        title="Cek ID",
        description="Klik tombol untuk ambil detail akun Anda",
        text=text,
        buttons=buttons,
        parse_mode="html"
    )
    await event.answer([result], switch_pm=False)
@bot_client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()
    sender_id = event.sender_id  
    if data == "show_detail":
        try:
            full_user = await bot_client(GetFullUserRequest(sender_id))
            user_obj = full_user.user if hasattr(full_user, "user") else full_user.users[0]
            first_name = safe_attr(user_obj, "first_name")
            username = safe_attr(user_obj, "username")
            phone = safe_attr(user_obj, "phone")
            about = safe_attr(full_user, "about")
            text = (
                f"<b>📌 Detail User</b>\n"
                f"<blockquote>ID: {sender_id}</blockquote>\n"
                f"<blockquote>Nama: {first_name}</blockquote>\n"
                f"<blockquote>Username: @{username}</blockquote>\n"
                f"<blockquote>Phone: {phone}</blockquote>\n"
                f"<blockquote>About: {about}</blockquote>"
            )
            buttons = [
                [Button.inline("⬅️ Kembali", data="back_menu")]
            ]
            try:
                await event.edit(text, buttons=buttons, parse_mode="html")
            except MessageNotModifiedError:
                pass  
        except Exception as e:
            await event.respond(f"❌ Error saat ambil detail: {e}")
    elif data == "back_menu":
        text = "<b>CEK DETAIL AKUN DAN DETAIL ANDA</b>"
        buttons = [
            [Button.inline("ℹ️ Detail User", data="show_detail")]
        ]
        try:
            await event.edit(text, buttons=buttons, parse_mode="html")
        except MessageNotModifiedError:
            pass


from telethon import events, Button

@bot_client.on(events.InlineQuery)
async def inline_handler(event):
    # Tangani query "control" saja
    if event.text.lower() != "control":
        return

    keyboard = [
        [Button.inline("𝚂𝚃𝙰𝚃𝚄𝚂 𝚄𝚂𝙴𝚁𝙱𝙾𝚃", b"userbot_menu"),
         Button.inline("𝙷𝙴𝙻𝙿 𝙼𝙴𝙽𝚄", b"back_main")],

        [Button.inline("𝚁𝚄𝙽 𝚄𝚂𝙴𝚁𝙱𝙾𝚃", b"run_userbot"),
         Button.inline("𝚁𝙴𝚂𝚃𝙰𝚁𝚃 𝚄𝚂𝙴𝚁𝙱𝙾𝚃", b"restart_userbot")],

        [Button.inline("𝚁𝙴𝚂𝚃𝙰𝚁𝚃 𝙱𝙾𝚃", b"restartbot"),
         Button.inline("𝚂𝙴𝚂𝚂𝙸𝙾𝙽 𝙽𝙰𝙼𝙴", b"session")],

        [Button.inline("𝚂𝙷𝚄𝚃𝙳𝙾𝚆𝙽 𝚄𝚂𝙴𝚁𝙱𝙾𝚃", b"shutdown_userbot")]
    ]

    caption = """📌 <b>Halo! Selamat datang di Userbot V3.0.0</b>
<blockquote>
<u>⏤͟͟͞͞Menu & Panduan</u>
Gunakan tombol di bawah untuk menjelajahi semua fitur.  
Fitur terbagi menjadi dua bagian utama:
➥ <b>Bot API</b> – otomatisasi dan integrasi canggih  
➥ <b>Userbot</b> – kontrol personal & tambahan fitur  
<u>⏤͟͟͞͞Update di Versi 3.0.0</u>
• Tombol interaktif untuk navigasi lebih cepat  
• Fitur tambahan dengan API khusus  
• Semua fitur resmi dari <a href="https://t.me/ZeroneOfficial">Zerone Official</a>  
💡 Tip: Klik tombol untuk melihat fitur dan panduan penggunaannya.  
════════════════════  
🚀 Nikmati pengalaman baru dengan Userbot V3.0.0!</blockquote>"""

    # Kirim sebagai pesan biasa, tombol bisa ditekan langsung
    builder = event.builder
    result = builder.article(
        title="📌 Control Menu",
        text=caption,
        buttons=keyboard,
        parse_mode="html"
    )
    await event.answer([result], cache_time=0)
    
@bot_client.on(events.InlineQuery)
async def inline_handler(event):
    if event.text != "allmenu":
        return
    builder = event.builder
    try:
        sender = await event.get_sender()
        username = sender.username or sender.first_name or "teman"
    except:
        username = "teman"
    total_handlers = len(user_client._event_builders)
    keyboard = [
        [Button.inline("ᴄᴍᴅ ᴍᴇɴᴜ", data=b"menu_1"), Button.inline("ᴜʙᴏᴛ ᴍᴇɴᴜ", data=b"menu_2")],
        [Button.inline("ɢʀᴏᴜᴘ ᴍᴇɴᴜ", data=b"menu_3"), Button.inline("ᴏᴛʜᴇʀ ᴍᴇɴᴜ", data=b"menu_4")],
        [Button.inline("ᴘᴀɴᴇʟ ᴍᴇɴᴜ", data=b"menu_7"), Button.inline("ᴄᴏɴᴛʀᴏʟ ᴍᴇɴᴜ", data=b"control")],
        [Button.inline("ᴛᴜᴛᴏʀɪᴀʟ", data=b"menu_5"), Button.inline("ᴇɴᴄ ᴘʏᴛʜᴏɴ", data=b"menu_8")]
    ]
    result = builder.article(
        title="📌 All Menu",
        text=f"""<blockquote>
( ! ) Welcome to Userbot Version 3.0.0
➥ Total Fitur : {total_handlers}
➥ Prefixs    : Titik
➥ User       : {username}
══════════════════════════
Terima kasih telah menggunakan userbot ini, semoga puas dan tidak ada kendala
</blockquote>""",
        buttons=keyboard,
        parse_mode="html"
    )
    await event.answer([result], cache_time=0)
@bot_client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode("utf-8")
    if data.startswith("back_main"):
        try:
            sender = await event.get_sender()
            username = sender.username or sender.first_name or "teman"
        except:
            username = "teman"
        total_handlers = len(user_client._event_builders)
        keyboard = [
            [Button.inline("ᴄᴍᴅ ᴍᴇɴᴜ", data=b"menu_1"), Button.inline("ᴜʙᴏᴛ ᴍᴇɴᴜ", data=b"menu_2")],
            [Button.inline("ɢʀᴏᴜᴘ ᴍᴇɴᴜ", data=b"menu_3"), Button.inline("ᴏᴛʜᴇʀ ᴍᴇɴᴜ", data=b"menu_4")],
            [Button.inline("ᴘᴀɴᴇʟ ᴍᴇɴᴜ", data=b"menu_7"), Button.inline("ᴄᴏɴᴛʀᴏʟ ᴍᴇɴᴜ", data=b"control")],
            [Button.inline("ᴛᴜᴛᴏʀɪᴀʟ", data=b"menu_5"), Button.inline("ᴇɴᴄ ᴘʏᴛʜᴏɴ", data=b"menu_8")]
        ]
        await event.edit(f"""<blockquote>
( ! ) Welcome to Userbot Version 3.0.0
➥ Total Fitur : {total_handlers}
➥ Prefixs    : Titik
➥ User       : {username}
══════════════════════════
Terima kasih telah menggunakan userbot ini, semoga puas dan tidak ada kendala
</blockquote>""",
            buttons=keyboard, parse_mode="html"
        )
@bot_client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode("utf-8")
    if data == "menu_1":
        await event.edit(
            """<blockquote>
❒——————— SHARE MENU ————————❒
⪩ .menu
⪩ .allmenu
⪩ .panelmenu
⪩ .ubotmenu
⪩ .encmenu
⪩ .othermenu
⪩ .groupmenu
⪩ .control
⪩ .
( ! ) sumpah cok bingung mau nambahin apa dah limit otak gua 😭
——————————————————————————————
</blockquote>""",
            buttons=[[Button.inline("⬅ Kembali", data=b"back_main")]],
            parse_mode="html",
            link_preview=False
        )
    elif data == "menu_2":
        await event.edit(
            """
<blockquote>
<b>❒——————— BOT MENU ————————❒</b>
▢ .cfd all/group
▢ .afk reason
▢ .addbl
▢ .unbl
▢ .tt link tiktok
▢ .info
▢ .ttmp3 link tiktok
▢ .song query
▢ .block id ==> blokir telegram penggunaa
▢ .unblock id ==> buka blokiran penggunaa
——————————————————————————————
Notes : bot ini hanyalah bot biasa dan gunakan sewajarnya karena ini adalah telegram bukan Whatsapp yang bila kamu terkena blokir akan susah untuk di pulihkan, jika ingin tau lebih lanjut bisa hubungi <a href="https://t.me/ZeroneOfficial">Owner disini ✨</a>
</blockquote>""",
            buttons=[[Button.inline("⬅ Kembali", data=b"back_main")]],
            parse_mode="html",
            link_preview=False
        )
    elif data == "menu_3":
        await event.edit(
            """
<blockquote>
❒——————— GROUP MENU ————————❒
▢ .kick reply/id
▢ .promote reply/id
▢ .demote reply/id
▢ .pin reply
▢ .unpin reply
▢ .liston ==> cek semua yang online di group
▢ .mute reply
▢ .unmute reply
——————————————————————————————
Notes : bot ini hanyalah bot biasa dan gunakan sewajarnya karena ini adalah telegram bukan Whatsapp yang bila kamu terkena blokir akan susah untuk di pulihkan, jika ingin tau lebih lanjut bisa hubungi <a href="https://t.me/ZeroneOfficial">Owner disini ✨</a>
</blockquote>""",
            buttons=[
                [Button.inline("⬅ Kembali", data=b"back_main")]
            ],
            parse_mode="html",
            link_preview=False
        )
    elif data == "menu_4":
        await event.edit("""
<blockquote>
❒——————— OTHER MENU ————————❒
▢ .ai query
▢ .cekip domain
▢ .id
▢ .ipaddress IP
▢ .gimg generate IMG ( image )
▢ .rbg reply/caption ==> remove background 
▢ .cimg query
▢ .cgame query
——————————————————————————————
Notes : bot ini hanyalah bot biasa dan gunakan sewajarnya karena ini adalah telegram bukan Whatsapp yang bila kamu terkena blokir akan susah untuk di pulihkan, jika ingin tau lebih lanjut bisa hubungi <a href="https://t.me/ZeroneOfficial">Owner disini ✨</a>
</blockquote>
            """,
            buttons=[[Button.inline("⬅ Kembali", data=b"back_main")]],
            parse_mode="html",
            link_preview=False
        )
    elif data == "menu_5":
        await event.edit("""📌 <b>Halo ini adalah menu terbaru script Userbot V3.0.0</b>
<blockquote>
<b><u>PILIH SALAH SATU TOMBOL</u></b>
akan mendapatkan beberapa menu dan panduan menggunakan fitur ini & fitur ini di design menjadi 2 bagian 1 bot api 2 userbot, ini adalah bantuan dari penggunaan menu nya
<b><u>ADA UPDATE APA SAJA DI VERSI 3.0.0 INI?</u></b>
kamu mendapatkan fitur lebih yaitu biaa button dan dapat extra fitur yang dimana fitur ini menyediakan api tertentu dan pastinya sudah di sediakan oleh <a href="https://t.me/ZeroneOfficial">Zerone Official</a> pastinya jadi tunggu apalagi cobain fitur baru dari penyedia userbot ini
</blockquote>""",
            buttons=[[Button.inline("⬅ Kembali", data=b"back_main")]],
            parse_mode="html",
            link_preview=False
        )
    elif data == "menu_6":
        await event.edit(
            "<pre>OTW CUK SABAR AJA </pre>",
            buttons=[[Button.inline("⬅ Kembali", data=b"back_main")]],
            parse_mode="html",
            link_preview=False
        )
    elif data == "menu_7":
        await event.edit("""
<blockquote>
❒——————— PANEL MENU ————————❒
╰➤ .1gb nama,id
╰➤ .2gb nama,id
╰➤ .3gb nama,id
╰➤ .4gb nama,id
╰➤ .5gb nama,id
╰➤ .6gb nama,id
╰➤ .7gb nama,id
╰➤ .8gb nama,id
╰➤ .9gb nama,id
╰➤ .10gb nama,id
╰➤ .unli nama,id
——————————————————————————————
▢ .listserver ==> cek semua server yang tersedia
▢ .delserver id
▢ .listuser cek semua user yang tersedia
▢ .listadmin cek semua admin panel
▢ .cadmin nama,id
▢ .deladmin id
——————————————————————————————
</blockquote>
            """,
            buttons=[[Button.inline("⬅ Kembali", data=b"back_main")]],
            parse_mode="html",
            link_preview=False
        )
    elif data == "menu_8":
        await event.edit( """
<b>🔐 𝗘𝗻𝗰𝗼𝗱𝗲 𝗣𝘆𝘁𝗵𝗼𝗻 — 𝗟𝗲𝘃𝗲𝗹 𝗢𝗽𝘀𝗶𝗼𝗻𝗮𝗹</b>

<blockquote>
<b>✨ Rekomendasi (Best Choice)</b>  
───────────────────────  
⪩ .encpy 50   •  Super ringan  
⪩ .encpy 100  •  Stabil (default)  
⪩ .encpy 125  •  Lebih aman  
⪩ .encpy 130  •  Project menengah  
⪩ .encpy 150  •  Balance performa  
⪩ .encpy 160  •  Tingkat lanjut  
⪩ .encpy 165  •  Hampir maksimal  
⪩ .encpy 170  •  Encode berat  
⪩ .encpy 185  •  High-level secure  

<b>⚠️ Tidak Disarankan </b>  
───────────────────────  
⪩ .encpy 190  •  Risiko error  
⪩ .encpy 200  •  Terlalu berat  
⪩ .encpy 225  •  Overkill  
⪩ .encpy 250  •  Sangat lambat  
⪩ .encpy 260  •  Tidak stabil  
⪩ .encpy 265  •  Extreme bbuk

<b>📖 Penjelasan Level ENC</b>  
───────────────────────  
• <b>50 – 130</b> → Ringan – cocok untuk script kecil/personal.  
• <b>150 – 170</b> → Medium-high – balance antara keamanan & performa.  
• <b>185+</b> → Sangat tinggi – aman, tapi makin berat dijalankan.  
• <b>190 – 265</b> → Eksperimental – rawan error, hanya untuk uji ekstrem.  
</blockquote>
""",
            buttons=[[Button.inline("⬅ Kembali", data=b"back_main")]],
            parse_mode="html",
            link_preview=False
        )


@user_client.on(events.NewMessage(pattern=r'^\.panelmenu$'))
async def panelmenu_handler(event):
    if not await khususakses(event):
        return

    await event.reply(
        """<blockquote>
❒——————— PANEL MENU ————————❒
╰➤ .1gb nama,id
╰➤ .2gb nama,id
╰➤ .3gb nama,id
╰➤ .4gb nama,id
╰➤ .5gb nama,id
╰➤ .6gb nama,id
╰➤ .7gb nama,id
╰➤ .8gb nama,id
╰➤ .9gb nama,id
╰➤ .10gb nama,id
╰➤ .unli nama,id
——————————————————————————————
▢ .listserver ==> cek semua server yang tersedia
▢ .delserver id
▢ .listuser cek semua user yang tersedia
▢ .listadmin cek semua admin panel
▢ .cadmin nama,id
▢ .deladmin id
——————————————————————————————

</blockquote>""",
        parse_mode="html"
    )

@user_client.on(events.NewMessage(pattern=r'^\.ubotmenu$'))
async def ubotmenu_handler(event):
    if not await khususakses(event):
        return

    await event.reply(
        """<blockquote>
<b>❒——————— UBOT MENU ————————❒</b>
▢ .cfd all/group
▢ .afk reason
▢ .tt link tiktok
▢ .ttmp3 link tiktok
▢ .song query
▢ .block id ==> blokir telegram penggunaa
▢ .unblock id ==> buka blokiran penggunaa
——————————————————————————————
</blockquote>""",
        parse_mode="html"
    )

@user_client.on(events.NewMessage(pattern=r'^\.encmenu$'))
async def encmenu_handler(event):
    if not await khususakses(event):
        return

    await event.reply(
        """<blockquote>
<b>✨ Rekomendasi (Best Choice)</b>  
───────────────────────  
⪩ .encpy 50   •  Super ringan  
⪩ .encpy 100  •  Stabil (default)  
⪩ .encpy 125  •  Lebih aman  
⪩ .encpy 130  •  Project menengah  
⪩ .encpy 150  •  Balance performa  
⪩ .encpy 160  •  Tingkat lanjut  
⪩ .encpy 165  •  Hampir maksimal  
⪩ .encpy 170  •  Encode berat  
⪩ .encpy 185  •  High-level secure  

<b>⚠️ Tidak Disarankan </b>  
───────────────────────  
⪩ .encpy 190  •  Risiko error  
⪩ .encpy 200  •  Terlalu berat  
⪩ .encpy 225  •  Overkill  
⪩ .encpy 250  •  Sangat lambat  
⪩ .encpy 260  •  Tidak stabil  
⪩ .encpy 265  •  Extreme bbuk

<b>📖 Penjelasan Level ENC</b>  
───────────────────────  
• <b>50 – 130</b> → Ringan – cocok untuk script kecil/personal.  
• <b>150 – 170</b> → Medium-high – balance antara keamanan & performa.  
• <b>185+</b> → Sangat tinggi – aman, tapi makin berat dijalankan.  
• <b>190 – 265</b> → Eksperimental – rawan error, hanya untuk uji ekstrem.  
</blockquote>""",
        parse_mode="html"
    )


@user_client.on(events.NewMessage(pattern=r'^\.groupmenu$'))
async def groupmenu_handler(event):
    if not await khususakses(event):
        return

    await event.reply(
        """<blockquote>
❒——————— GROUP MENU ————————❒
▢ .kick reply/id
▢ .promote reply/id
▢ .demote reply/id
▢ .pin reply
▢ .unpin reply
▢ .liston ==> cek semua yang online di group
▢ .mute reply
▢ .unmute reply
——————————————————————————————
</blockquote>""",
        parse_mode="html"
    )


@user_client.on(events.NewMessage(pattern=r'^\.othermenu$'))
async def othermenu_handler(event):
    if not await khususakses(event):
        return

    await event.reply(
        """<blockquote>
❒——————— OTHER MENU ————————❒
▢ .ai query
▢ .cekip domain
▢ .id
▢ .ipaddress IP
▢ .gimg generate IMG ( image )
▢ .rbg reply/caption ==> remove background 
▢ .cimg query
▢ .cgame query
——————————————————————————————
</blockquote>""",
        parse_mode="html"
    )
@user_client.on(events.NewMessage(pattern=r'^\.1gb(?:\s+(.*))?$'))
async def gb1_handler(event):
    if not await khususakses(event):
        return
    args_text = event.pattern_match.group(1)
    if not args_text or "," not in args_text:
        return await event.reply(
            "Format salah!\nGunakan:\n`.1gb namapanel,idtele`\n"
            "Contoh:\n`.1gb user,123456789`",
            parse_mode="markdown"
        )
    username, target_id = [x.strip() for x in args_text.split(",", 1)]
    name = username + "1gb"
    email = f"{username}@zerone,userbot"
    password = f"{username}354"
    spc = (
        'if [[ -d .git ]] && [[ {{AUTO_UPDATE}} == "1" ]]; then git pull; fi; '
        'if [[ ! -z ${NODE_PACKAGES} ]]; then /usr/local/bin/npm install ${NODE_PACKAGES}; fi; '
        'if [[ ! -z ${UNNODE_PACKAGES} ]]; then /usr/local/bin/npm uninstall ${UNNODE_PACKAGES}; fi; '
        'if [ -f /home/container/package.json ]; then /usr/local/bin/npm install; fi; '
        '/usr/local/bin/${CMD_RUN}')
    try:
        user_resp = requests.post(
            f"{settings.DOMAIN}/api/application/users",
            json={
                "email": email,
                "username": username,
                "first_name": username,
                "last_name": username,
                "language": "en",
                "password": password
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        user_resp.raise_for_status()
        user = user_resp.json()["attributes"]
        server_resp = requests.post(
            f"{settings.DOMAIN}/api/application/servers",
            json={
                "name": name,
                "description": "",
                "user": user["id"],
                "egg": int(settings.EGGS),
                "docker_image": "ghcr.io/parkervcp/yolks:nodejs_18",
                "startup": spc,
                "environment": {
                    "INST": "npm",
                    "USER_UPLOAD": "0",
                    "AUTO_UPDATE": "0",
                    "CMD_RUN": "npm start",
                },
                "limits": {
                    "memory": 1024,
                    "swap": 0,
                    "disk": 1024,
                    "io": 500,
                    "cpu": 30,
                },
                "feature_limits": {
                    "databases": 5,
                    "backups": 5,
                    "allocations": 1,
                },
                "deploy": {
                    "locations": [int(settings.LOC)],
                    "dedicated_ip": False,
                    "port_range": [],
                }
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        server_resp.raise_for_status()
        server = server_resp.json()["attributes"]
        await event.reply(
            f"✅ PANEL BERHASIL DIBUAT\n\n"
            f"🆔 ID: {user['id']}\n"
            f"👤 Nama: {username}\n"
            f"📧 Email: {email}\n"
            f"💾 Memory: {server['limits']['memory']} MB\n"
            f"💽 Disk: {server['limits']['disk']} MB\n"
            f"⚙️ CPU: {server['limits']['cpu']}%"
        )
        if settings.PP:
            await client.send_file(
                int(target_id),
                settings.PP,
                caption=(
                    f"🖥️ PANEL DATA UNTUK {target_id}\n\n"
                    f"🌐 Login: {settings.DOMAIN}\n"
                    f"👤 Username: {user['username']}\n"
                    f"🔐 Password: {password}\n\n"
                    f"⚠️ Jangan DDoS server\n"
                    f"⚠️ Tutup domain saat screenshot\n\n"
                    f"✅ Panel berhasil dibuat!"
                )
            )
    except Exception as e:
        await event.reply(f"❌ Gagal membuat panel: `{e}`")



@user_client.on(events.NewMessage(pattern=r'^\.2gb(?:\s+(.*))?$'))
async def gb2_handler(event):
    if not await khususakses(event):
        return
    args_text = event.pattern_match.group(1)
    if not args_text or "," not in args_text:
        return await event.reply(
            "Format salah!\nGunakan:\n`.2gb namapanel,idtele`\n"
            "Contoh:\n`.2gb user,123456789`",
            parse_mode="markdown"
        )
    username, target_id = [x.strip() for x in args_text.split(",", 1)]
    name = username + "2gb"
    email = f"{username}@zeron,userbot"
    password = f"{username}354"
    spc = 'if [[ -d .git ]] && [[ {{AUTO_UPDATE}} == "1" ]]; then git pull; fi; if [[ ! -z ${NODE_PACKAGES} ]]; then /usr/local/bin/npm install ${NODE_PACKAGES}; fi; if [[ ! -z ${UNNODE_PACKAGES} ]]; then /usr/local/bin/npm uninstall ${UNNODE_PACKAGES}; fi; if [ -f /home/container/package.json ]; then /usr/local/bin/npm install; fi; /usr/local/bin/${CMD_RUN}'
    try:
        user_resp = requests.post(
            f"{settings.DOMAIN}/api/application/users",
            json={
                "email": email,
                "username": username,
                "first_name": username,
                "last_name": username,
                "language": "en",
                "password": password
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        user = user_resp.json()["attributes"]
        server_resp = requests.post(
            f"{settings.DOMAIN}/api/application/servers",
            json={
                "name": name,
                "description": "",
                "user": user["id"],
                "egg": int(settings.EGGS),
                "docker_image": "ghcr.io/parkervcp/yolks:nodejs_18",
                "startup": spc,
                "environment": {
                    "INST": "npm",
                    "USER_UPLOAD": "0",
                    "AUTO_UPDATE": "0",
                    "CMD_RUN": "npm start",
                },
                "limits": {
                    "memory": 2048,
                    "swap": 0,
                    "disk": 2048,
                    "io": 500,
                    "cpu": 30,
                },
                "feature_limits": {
                    "databases": 5,
                    "backups": 5,
                    "allocations": 1,
                },
                "deploy": {
                    "locations": [int(settings.LOC)],
                    "dedicated_ip": False,
                    "port_range": [],
                }
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        server = server_resp.json()["attributes"]
        await event.reply(
            f"✅ PANEL BERHASIL DIBUAT\n\n"
            f"🆔 ID: {user['id']}\n"
            f"👤 Nama: {username}\n"
            f"📧 Email: {email}\n"
            f"💾 Memory: {server['limits']['memory']} MB\n"
            f"💽 Disk: {server['limits']['disk']} MB\n"
            f"⚙️ CPU: {server['limits']['cpu']}%"
        )
        if settings.PP:
            await client.send_file(
                int(target_id),
                settings.PP,
                caption=(
                    f"🖥️ PANEL DATA UNTUK {target_id}\n\n"
                    f"🌐 Login: {settings.DOMAIN}\n"
                    f"👤 Username: {user['username']}\n"
                    f"🔐 Password: {password}\n\n"
                    f"⚠️ Jangan DDoS server\n"
                    f"⚠️ Tutup domain saat screenshot\n\n"
                    f"✅ Panel berhasil dibuat!"
                )
            )
    except Exception as e:
        await event.reply(f"❌ Gagal membuat panel: `{e}`")
@user_client.on(events.NewMessage(pattern=r'^\.3gb(?:\s+(.*))?$'))
async def gb3_handler(event):
    if not await khususakses(event):
        return
    args_text = event.pattern_match.group(1)
    if not args_text or "," not in args_text:
        return await event.reply(
            "Format salah!\nGunakan:\n`.3gb namapanel,idtele`\n"
            "Contoh:\n`.3gb user,123456789`",
            parse_mode="markdown"
        )
    username, target_id = [x.strip() for x in args_text.split(",", 1)]
    name = username + "3gb"
    email = f"{username}@zerone,userbot"
    password = f"{username}354"
    spc = 'if [[ -d .git ]] && [[ {{AUTO_UPDATE}} == "1" ]]; then git pull; fi; if [[ ! -z ${NODE_PACKAGES} ]]; then /usr/local/bin/npm install ${NODE_PACKAGES}; fi; if [[ ! -z ${UNNODE_PACKAGES} ]]; then /usr/local/bin/npm uninstall ${UNNODE_PACKAGES}; fi; if [ -f /home/container/package.json ]; then /usr/local/bin/npm install; fi; /usr/local/bin/${CMD_RUN}'
    try:
        user_resp = requests.post(
            f"{settings.DOMAIN}/api/application/users",
            json={
                "email": email,
                "username": username,
                "first_name": username,
                "last_name": username,
                "language": "en",
                "password": password
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        user = user_resp.json()["attributes"]
        server_resp = requests.post(
            f"{settings.DOMAIN}/api/application/servers",
            json={
                "name": name,
                "description": "",
                "user": user["id"],
                "egg": int(settings.EGGS),
                "docker_image": "ghcr.io/parkervcp/yolks:nodejs_18",
                "startup": spc,
                "environment": {
                    "INST": "npm",
                    "USER_UPLOAD": "0",
                    "AUTO_UPDATE": "0",
                    "CMD_RUN": "npm start",
                },
                "limits": {
                    "memory": 3072,
                    "swap": 0,
                    "disk": 3072,
                    "io": 500,
                    "cpu": 30,
                },
                "feature_limits": {
                    "databases": 5,
                    "backups": 5,
                    "allocations": 1,
                },
                "deploy": {
                    "locations": [int(settings.LOC)],
                    "dedicated_ip": False,
                    "port_range": [],
                }
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        server = server_resp.json()["attributes"]
        await event.reply(
            f"✅ PANEL BERHASIL DIBUAT\n\n"
            f"🆔 ID: {user['id']}\n"
            f"👤 Nama: {username}\n"
            f"📧 Email: {email}\n"
            f"💾 Memory: {server['limits']['memory']} MB\n"
            f"💽 Disk: {server['limits']['disk']} MB\n"
            f"⚙️ CPU: {server['limits']['cpu']}%"
        )
        if settings.PP:
            await client.send_file(
                int(target_id),
                settings.PP,
                caption=(
                    f"🖥️ PANEL DATA UNTUK {target_id}\n\n"
                    f"🌐 Login: {settings.DOMAIN}\n"
                    f"👤 Username: {user['username']}\n"
                    f"🔐 Password: {password}\n\n"
                    f"⚠️ Jangan DDoS server\n"
                    f"⚠️ Tutup domain saat screenshot\n\n"
                    f"✅ Panel berhasil dibuat!"
                )
            )
    except Exception as e:
        await event.reply(f"❌ Gagal membuat panel: `{e}`")
@user_client.on(events.NewMessage(pattern=r'^\.4gb(?:\s+(.*))?$'))
async def gb4_handler(event):
    if not await khususakses(event):
        return
    args_text = event.pattern_match.group(1)
    if not args_text or "," not in args_text:
        return await event.reply(
            "Format salah!\nGunakan:\n`.4gb namapanel,idtele`\n"
            "Contoh:\n`.4gb zeroneuser,123456789`",
            parse_mode="markdown"
        )
    username, target_id = [x.strip() for x in args_text.split(",", 1)]
    name = username + "4gb"
    email = f"{username}@zerone,userbot"
    password = f"{username}354"
    spc = 'if [[ -d .git ]] && [[ {{AUTO_UPDATE}} == "1" ]]; then git pull; fi; if [[ ! -z ${NODE_PACKAGES} ]]; then /usr/local/bin/npm install ${NODE_PACKAGES}; fi; if [[ ! -z ${UNNODE_PACKAGES} ]]; then /usr/local/bin/npm uninstall ${UNNODE_PACKAGES}; fi; if [ -f /home/container/package.json ]; then /usr/local/bin/npm install; fi; /usr/local/bin/${CMD_RUN}'
    try:
        user_resp = requests.post(
            f"{settings.DOMAIN}/api/application/users",
            json={
                "email": email,
                "username": username,
                "first_name": username,
                "last_name": username,
                "language": "en",
                "password": password
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        user = user_resp.json()["attributes"]
        server_resp = requests.post(
            f"{settings.DOMAIN}/api/application/servers",
            json={
                "name": name,
                "description": "",
                "user": user["id"],
                "egg": int(settings.EGGS),
                "docker_image": "ghcr.io/parkervcp/yolks:nodejs_18",
                "startup": spc,
                "environment": {
                    "INST": "npm",
                    "USER_UPLOAD": "0",
                    "AUTO_UPDATE": "0",
                    "CMD_RUN": "npm start",
                },
                "limits": {
                    "memory": 4096,
                    "swap": 0,
                    "disk": 4096,
                    "io": 500,
                    "cpu": 60,
                },
                "feature_limits": {
                    "databases": 5,
                    "backups": 5,
                    "allocations": 1,
                },
                "deploy": {
                    "locations": [int(settings.LOC)],
                    "dedicated_ip": False,
                    "port_range": [],
                }
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        server = server_resp.json()["attributes"]
        await event.reply(
            f"✅ PANEL BERHASIL DIBUAT\n\n"
            f"🆔 ID: {user['id']}\n"
            f"👤 Nama: {username}\n"
            f"📧 Email: {email}\n"
            f"💾 Memory: {server['limits']['memory']} MB\n"
            f"💽 Disk: {server['limits']['disk']} MB\n"
            f"⚙️ CPU: {server['limits']['cpu']}%"
        )
        if settings.PP:
            await client.send_file(
                int(target_id),
                settings.PP,
                caption=(
                    f"🖥️ PANEL DATA UNTUK {target_id}\n\n"
                    f"🌐 Login: {settings.DOMAIN}\n"
                    f"👤 Username: {user['username']}\n"
                    f"🔐 Password: {password}\n\n"
                    f"⚠️ Jangan DDoS server\n"
                    f"⚠️ Tutup domain saat screenshot\n\n"
                    f"✅ Panel berhasil dibuat!"
                )
            )
    except Exception as e:
        await event.reply(f"❌ Gagal membuat panel: `{e}`")
@user_client.on(events.NewMessage(pattern=r'^\.5gb(?:\s+(.*))?$'))
async def gb5_handler(event):
    if not await khususakses(event):
        return
    args_text = event.pattern_match.group(1)
    if not args_text or "," not in args_text:
        return await event.reply(
            "Format salah!\nGunakan:\n`.5gb namapanel,idtele`\n"
            "Contoh:\n`.5gb zeroneuser,123456789`",
            parse_mode="markdown"
        )
    username, target_id = [x.strip() for x in args_text.split(",", 1)]
    name = username + "5gb"
    email = f"{username}@zerone,userbot"
    password = f"{username}354"
    spc = 'if [[ -d .git ]] && [[ {{AUTO_UPDATE}} == "1" ]]; then git pull; fi; if [[ ! -z ${NODE_PACKAGES} ]]; then /usr/local/bin/npm install ${NODE_PACKAGES}; fi; if [[ ! -z ${UNNODE_PACKAGES} ]]; then /usr/local/bin/npm uninstall ${UNNODE_PACKAGES}; fi; if [ -f /home/container/package.json ]; then /usr/local/bin/npm install; fi; /usr/local/bin/${CMD_RUN}'
    try:
        user_resp = requests.post(
            f"{settings.DOMAIN}/api/application/users",
            json={
                "email": email,
                "username": username,
                "first_name": username,
                "last_name": username,
                "language": "en",
                "password": password
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        user = user_resp.json()["attributes"]
        server_resp = requests.post(
            f"{settings.DOMAIN}/api/application/servers",
            json={
                "name": name,
                "description": "",
                "user": user["id"],
                "egg": int(settings.EGGS),
                "docker_image": "ghcr.io/parkervcp/yolks:nodejs_18",
                "startup": spc,
                "environment": {
                    "INST": "npm",
                    "USER_UPLOAD": "0",
                    "AUTO_UPDATE": "0",
                    "CMD_RUN": "npm start",
                },
                "limits": {
                    "memory": 5120,
                    "swap": 0,
                    "disk": 5120,
                    "io": 500,
                    "cpu": 70,
                },
                "feature_limits": {
                    "databases": 5,
                    "backups": 5,
                    "allocations": 1,
                },
                "deploy": {
                    "locations": [int(settings.LOC)],
                    "dedicated_ip": False,
                    "port_range": [],
                }
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        server = server_resp.json()["attributes"]
        await event.reply(
            f"✅ PANEL BERHASIL DIBUAT\n\n"
            f"🆔 ID: {user['id']}\n"
            f"👤 Nama: {username}\n"
            f"📧 Email: {email}\n"
            f"💾 Memory: {server['limits']['memory']} MB\n"
            f"💽 Disk: {server['limits']['disk']} MB\n"
            f"⚙️ CPU: {server['limits']['cpu']}%"
        )
        if settings.PP:
            await client.send_file(
                int(target_id),
                settings.PP,
                caption=(
                    f"🖥️ PANEL DATA UNTUK {target_id}\n\n"
                    f"🌐 Login: {settings.DOMAIN}\n"
                    f"👤 Username: {user['username']}\n"
                    f"🔐 Password: {password}\n\n"
                    f"⚠️ Jangan DDoS server\n"
                    f"⚠️ Tutup domain saat screenshot\n\n"
                    f"✅ Panel berhasil dibuat!"
                )
            )
    except Exception as e:
        await event.reply(f"❌ Gagal membuat panel: `{e}`")
@user_client.on(events.NewMessage(pattern=r'^\.6gb(?:\s+(.*))?$'))
async def gb6_handler(event):
    if not await khususakses(event):
        return
    args_text = event.pattern_match.group(1)
    if not args_text or "," not in args_text:
        return await event.reply(
            "Format salah!\nGunakan:\n`.6gb namapanel,idtele`\n"
            "Contoh:\n`.6gb zeroneuser,123456789`",
            parse_mode="markdown"
        )
    username, target_id = [x.strip() for x in args_text.split(",", 1)]
    name = username + "6gb"
    email = f"{username}@zerone,userbot"
    password = f"{username}354"
    spc = 'if [[ -d .git ]] && [[ {{AUTO_UPDATE}} == "1" ]]; then git pull; fi; if [[ ! -z ${NODE_PACKAGES} ]]; then /usr/local/bin/npm install ${NODE_PACKAGES}; fi; if [[ ! -z ${UNNODE_PACKAGES} ]]; then /usr/local/bin/npm uninstall ${UNNODE_PACKAGES}; fi; if [ -f /home/container/package.json ]; then /usr/local/bin/npm install; fi; /usr/local/bin/${CMD_RUN}'
    try:
        user_resp = requests.post(
            f"{settings.DOMAIN}/api/application/users",
            json={
                "email": email,
                "username": username,
                "first_name": username,
                "last_name": username,
                "language": "en",
                "password": password
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        user = user_resp.json()["attributes"]
        server_resp = requests.post(
            f"{settings.DOMAIN}/api/application/servers",
            json={
                "name": name,
                "description": "",
                "user": user["id"],
                "egg": int(settings.EGGS),
                "docker_image": "ghcr.io/parkervcp/yolks:nodejs_18",
                "startup": spc,
                "environment": {
                    "INST": "npm",
                    "USER_UPLOAD": "0",
                    "AUTO_UPDATE": "0",
                    "CMD_RUN": "npm start",
                },
                "limits": {
                    "memory": 6144,
                    "swap": 0,
                    "disk": 6144,
                    "io": 500,
                    "cpu": 80,
                },
                "feature_limits": {
                    "databases": 5,
                    "backups": 5,
                    "allocations": 1,
                },
                "deploy": {
                    "locations": [int(settings.LOC)],
                    "dedicated_ip": False,
                    "port_range": [],
                }
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        server = server_resp.json()["attributes"]
        await event.reply(
            f"✅ PANEL BERHASIL DIBUAT\n\n"
            f"🆔 ID: {user['id']}\n"
            f"👤 Nama: {username}\n"
            f"📧 Email: {email}\n"
            f"💾 Memory: {server['limits']['memory']} MB\n"
            f"💽 Disk: {server['limits']['disk']} MB\n"
            f"⚙️ CPU: {server['limits']['cpu']}%"
        )
        if settings.PP:
            await client.send_file(
                int(target_id),
                settings.PP,
                caption=(
                    f"🖥️ PANEL DATA UNTUK {target_id}\n\n"
                    f"🌐 Login: {settings.DOMAIN}\n"
                    f"👤 Username: {user['username']}\n"
                    f"🔐 Password: {password}\n\n"
                    f"⚠️ Jangan DDoS server\n"
                    f"⚠️ Tutup domain saat screenshot\n\n"
                    f"✅ Panel berhasil dibuat!"
                )
            )
    except Exception as e:
        await event.reply(f"❌ Gagal membuat panel: `{e}`")
@user_client.on(events.NewMessage(pattern=r'^\.7gb(?:\s+(.*))?$'))
async def gb7_handler(event):
    if not await khususakses(event):
        return
    args_text = event.pattern_match.group(1)
    if not args_text or "," not in args_text:
        return await event.reply(
            "Format salah!\nGunakan:\n`.7gb namapanel,idtele`\n"
            "Contoh:\n`.7gb zeroneuser,123456789`",
            parse_mode="markdown"
        )
    username, target_id = [x.strip() for x in args_text.split(",", 1)]
    name = username + "7gb"
    email = f"{username}@zerone,userbot"
    password = f"{username}354"
    spc = 'if [[ -d .git ]] && [[ {{AUTO_UPDATE}} == "1" ]]; then git pull; fi; if [[ ! -z ${NODE_PACKAGES} ]]; then /usr/local/bin/npm install ${NODE_PACKAGES}; fi; if [[ ! -z ${UNNODE_PACKAGES} ]]; then /usr/local/bin/npm uninstall ${UNNODE_PACKAGES}; fi; if [ -f /home/container/package.json ]; then /usr/local/bin/npm install; fi; /usr/local/bin/${CMD_RUN}'
    try:
        user_resp = requests.post(
            f"{settings.DOMAIN}/api/application/users",
            json={
                "email": email,
                "username": username,
                "first_name": username,
                "last_name": username,
                "language": "en",
                "password": password
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        user = user_resp.json()["attributes"]
        server_resp = requests.post(
            f"{settings.DOMAIN}/api/application/servers",
            json={
                "name": name,
                "description": "",
                "user": user["id"],
                "egg": int(settings.EGGS),
                "docker_image": "ghcr.io/parkervcp/yolks:nodejs_18",
                "startup": spc,
                "environment": {
                    "INST": "npm",
                    "USER_UPLOAD": "0",
                    "AUTO_UPDATE": "0",
                    "CMD_RUN": "npm start",
                },
                "limits": {
                    "memory": 7168,
                    "swap": 0,
                    "disk": 7168,
                    "io": 500,
                    "cpu": 90,
                },
                "feature_limits": {
                    "databases": 5,
                    "backups": 5,
                    "allocations": 1,
                },
                "deploy": {
                    "locations": [int(settings.LOC)],
                    "dedicated_ip": False,
                    "port_range": [],
                }
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        server = server_resp.json()["attributes"]
        await event.reply(
            f"✅ PANEL BERHASIL DIBUAT\n\n"
            f"🆔 ID: {user['id']}\n"
            f"👤 Nama: {username}\n"
            f"📧 Email: {email}\n"
            f"💾 Memory: {server['limits']['memory']} MB\n"
            f"💽 Disk: {server['limits']['disk']} MB\n"
            f"⚙️ CPU: {server['limits']['cpu']}%"
        )
        if settings.PP:
            await client.send_file(
                int(target_id),
                settings.PP,
                caption=(
                    f"🖥️ PANEL DATA UNTUK {target_id}\n\n"
                    f"🌐 Login: {settings.DOMAIN}\n"
                    f"👤 Username: {user['username']}\n"
                    f"🔐 Password: {password}\n\n"
                    f"⚠️ Jangan DDoS server\n"
                    f"⚠️ Tutup domain saat screenshot\n\n"
                    f"✅ Panel berhasil dibuat!"
                )
            )
    except Exception as e:
        await event.reply(f"❌ Gagal membuat panel: `{e}`")
@user_client.on(events.NewMessage(pattern=r'^\.8gb(?:\s+(.*))?$'))
async def gb8_handler(event):
    if not await khususakses(event):
        return
    args_text = event.pattern_match.group(1)
    if not args_text or "," not in args_text:
        return await event.reply(
            "Format salah!\nGunakan:\n`.8gb namapanel,idtele`\n"
            "Contoh:\n`.8gb zeroneuser,123456789`",
            parse_mode="markdown"
        )
    username, target_id = [x.strip() for x in args_text.split(",", 1)]
    name = username + "8gb"
    email = f"{username}@zerone,userbot"
    password = f"{username}354"
    spc = 'if [[ -d .git ]] && [[ {{AUTO_UPDATE}} == "1" ]]; then git pull; fi; if [[ ! -z ${NODE_PACKAGES} ]]; then /usr/local/bin/npm install ${NODE_PACKAGES}; fi; if [[ ! -z ${UNNODE_PACKAGES} ]]; then /usr/local/bin/npm uninstall ${UNNODE_PACKAGES}; fi; if [ -f /home/container/package.json ]; then /usr/local/bin/npm install; fi; /usr/local/bin/${CMD_RUN}'
    try:
        user_resp = requests.post(
            f"{settings.DOMAIN}/api/application/users",
            json={
                "email": email,
                "username": username,
                "first_name": username,
                "last_name": username,
                "language": "en",
                "password": password
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        user = user_resp.json()["attributes"]
        server_resp = requests.post(
            f"{settings.DOMAIN}/api/application/servers",
            json={
                "name": name,
                "description": "",
                "user": user["id"],
                "egg": int(settings.EGGS),
                "docker_image": "ghcr.io/parkervcp/yolks:nodejs_18",
                "startup": spc,
                "environment": {
                    "INST": "npm",
                    "USER_UPLOAD": "0",
                    "AUTO_UPDATE": "0",
                    "CMD_RUN": "npm start",
                },
                "limits": {
                    "memory": 8192,
                    "swap": 0,
                    "disk": 8192,
                    "io": 500,
                    "cpu": 100,
                },
                "feature_limits": {
                    "databases": 5,
                    "backups": 5,
                    "allocations": 1,
                },
                "deploy": {
                    "locations": [int(settings.LOC)],
                    "dedicated_ip": False,
                    "port_range": [],
                }
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        server = server_resp.json()["attributes"]
        await event.reply(
            f"✅ PANEL BERHASIL DIBUAT\n\n"
            f"🆔 ID: {user['id']}\n"
            f"👤 Nama: {username}\n"
            f"📧 Email: {email}\n"
            f"💾 Memory: {server['limits']['memory']} MB\n"
            f"💽 Disk: {server['limits']['disk']} MB\n"
            f"⚙️ CPU: {server['limits']['cpu']}%"
        )
        if settings.PP:
            await user_client.send_file(
                int(target_id),
                settings.PP,
                caption=(
                    f"🖥️ PANEL DATA UNTUK {target_id}\n\n"
                    f"🌐 Login: {settings.DOMAIN}\n"
                    f"👤 Username: {user['username']}\n"
                    f"🔐 Password: {password}\n\n"
                    f"⚠️ Jangan DDoS server\n"
                    f"⚠️ Tutup domain saat screenshot\n\n"
                    f"✅ Panel berhasil dibuat!"
                )
            )
    except Exception as e:
        await event.reply(f"❌ Gagal membuat panel: `{e}`")
@user_client.on(events.NewMessage(pattern=r'^\.10gb(?:\s+(.*))?$'))
async def gb10_handler(event):
    if not await khususakses(event):
        return
    args_text = event.pattern_match.group(1)
    if not args_text or "," not in args_text:
        return await event.reply(
            "Format salah!\nGunakan:\n`.10gb namapanel,idtele`\n"
            "Contoh:\n`.10gb zeroneuser,123456789`",
            parse_mode="markdown"
        )
    username, target_id = [x.strip() for x in args_text.split(",", 1)]
    name = username + "10gb"
    email = f"{username}@zerone,userbot"
    password = f"{username}354"
    spc = 'if [[ -d .git ]] && [[ {{AUTO_UPDATE}} == "1" ]]; then git pull; fi; if [[ ! -z ${NODE_PACKAGES} ]]; then /usr/local/bin/npm install ${NODE_PACKAGES}; fi; if [[ ! -z ${UNNODE_PACKAGES} ]]; then /usr/local/bin/npm uninstall ${UNNODE_PACKAGES}; fi; if [ -f /home/container/package.json ]; then /usr/local/bin/npm install; fi; /usr/local/bin/${CMD_RUN}'
    try:
        user_resp = requests.post(
            f"{settings.DOMAIN}/api/application/users",
            json={
                "email": email,
                "username": username,
                "first_name": username,
                "last_name": username,
                "language": "en",
                "password": password
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        user = user_resp.json()["attributes"]
        server_resp = requests.post(
            f"{settings.DOMAIN}/api/application/servers",
            json={
                "name": name,
                "description": "",
                "user": user["id"],
                "egg": int(settings.EGGS),
                "docker_image": "ghcr.io/parkervcp/yolks:nodejs_18",
                "startup": spc,
                "environment": {
                    "INST": "npm",
                    "USER_UPLOAD": "0",
                    "AUTO_UPDATE": "0",
                    "CMD_RUN": "npm start",
                },
                "limits": {
                    "memory": 10240,
                    "swap": 0,
                    "disk": 10240,
                    "io": 500,
                    "cpu": 150,
                },
                "feature_limits": {
                    "databases": 5,
                    "backups": 5,
                    "allocations": 1,
                },
                "deploy": {
                    "locations": [int(settings.LOC)],
                    "dedicated_ip": False,
                    "port_range": [],
                }
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        server = server_resp.json()["attributes"]
        await event.reply(
            f"✅ PANEL BERHASIL DIBUAT\n\n"
            f"🆔 ID: {user['id']}\n"
            f"👤 Nama: {username}\n"
            f"📧 Email: {email}\n"
            f"💾 Memory: {server['limits']['memory']} MB\n"
            f"💽 Disk: {server['limits']['disk']} MB\n"
            f"⚙️ CPU: {server['limits']['cpu']}%"
        )
        if settings.PP:
            await user_client.send_file(
                int(target_id),
                settings.PP,
                caption=(
                    f"🖥️ PANEL DATA UNTUK {target_id}\n\n"
                    f"🌐 Login: {settings.DOMAIN}\n"
                    f"👤 Username: {user['username']}\n"
                    f"🔐 Password: {password}\n\n"
                    f"⚠️ Jangan DDoS server\n"
                    f"⚠️ Tutup domain saat screenshot\n\n"
                    f"✅ Panel berhasil dibuat!"
                )
            )
    except Exception as e:
        await event.reply(f"❌ Gagal membuat panel: `{e}`")
@user_client.on(events.NewMessage(pattern=r'^\.unli(?:\s+(.*))?$'))
async def gb_unli_handler(event):
    if not await khususakses(event):
        return
    args_text = event.pattern_match.group(1)
    if not args_text or "," not in args_text:
        return await event.reply(
            "Format salah!\nGunakan:\n`.unli namapanel,idtele`\n"
            "Contoh:\n`.unli zeroneuser,123456789`",
            parse_mode="markdown"
        )
    username, target_id = [x.strip() for x in args_text.split(",", 1)]
    name = username + "unli"
    email = f"{username}@zerone,userbot"
    password = f"{username}354"
    spc = 'if [[ -d .git ]] && [[ {{AUTO_UPDATE}} == "1" ]]; then git pull; fi; if [[ ! -z ${NODE_PACKAGES} ]]; then /usr/local/bin/npm install ${NODE_PACKAGES}; fi; if [[ ! -z ${UNNODE_PACKAGES} ]]; then /usr/local/bin/npm uninstall ${UNNODE_PACKAGES}; fi; if [ -f /home/container/package.json ]; then /usr/local/bin/npm install; fi; /usr/local/bin/${CMD_RUN}'
    try:
        user_resp = requests.post(
            f"{settings.DOMAIN}/api/application/users",
            json={
                "email": email,
                "username": username,
                "first_name": username,
                "last_name": username,
                "language": "en",
                "password": password
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        user = user_resp.json()["attributes"]
        server_resp = requests.post(
            f"{settings.DOMAIN}/api/application/servers",
            json={
                "name": name,
                "description": "",
                "user": user["id"],
                "egg": int(settings.EGGS),
                "docker_image": "ghcr.io/parkervcp/yolks:nodejs_18",
                "startup": spc,
                "environment": {
                    "INST": "npm",
                    "USER_UPLOAD": "0",
                    "AUTO_UPDATE": "0",
                    "CMD_RUN": "npm start",
                },
                "limits": {
                    "memory": 0,
                    "swap": 0,
                    "disk": 10240,
                    "io": 500,
                    "cpu": 200,
                },
                "feature_limits": {
                    "databases": 5,
                    "backups": 5,
                    "allocations": 1,
                },
                "deploy": {
                    "locations": [int(settings.LOC)],
                    "dedicated_ip": False,
                    "port_range": [],
                }
            },
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        server = server_resp.json()["attributes"]
        await event.reply(
            f"✅ PANEL UNLIMITED BERHASIL DIBUAT\n\n"
            f"🆔 ID: {user['id']}\n"
            f"👤 Nama: {username}\n"
            f"📧 Email: {email}\n"
            f"💾 Memory: ∞\n"
            f"💽 Disk: {server['limits']['disk']} MB\n"
            f"⚙️ CPU: {server['limits']['cpu']}%"
        )
        if settings.PP:
            await user_client.send_file(
                int(target_id),
                settings.PP,
                caption=(
                    f"🖥️ PANEL DATA UNTUK {target_id}\n\n"
                    f"🌐 Login: {settings.DOMAIN}\n"
                    f"👤 Username: {user['username']}\n"
                    f"🔐 Password: {password}\n\n"
                    f"⚠️ Jangan DDoS server\n"
                    f"⚠️ Tutup domain saat screenshot\n\n"
                    f"✅ Panel berhasil dibuat!"
                )
            )
    except Exception as e:
        await event.reply(f"❌ Gagal membuat panel: `{e}`")
@user_client.on(events.NewMessage(pattern=r'^\.cadmin(?:\s+(.*))?$'))
async def cadmin_handler(event):
    if not await khususakses(event):
        return
    args_text = event.pattern_match.group(1)
    if not args_text or "," not in args_text:
        return await event.reply(
            "Format salah!\nGunakan:\n`.cadmin nama,id`\nContoh:\n`.cadmin adminuser,123456789`",
            parse_mode="markdown"
        )
    username, target_id = [x.strip() for x in args_text.split(",", 1)]
    email = f"{username}@zerone,userbot"
    password = f"{username}Admin0"
    try:
        user_resp = requests.post(
            f"{settings.DOMAIN}/api/application/users",
            json={
                "email": email,
                "username": username,
                "first_name": username,
                "last_name": username,
                "language": "en",
                "password": password,
                "admin": True
            },
            headers={
                "Authorization": f"Bearer {settings.PLTC}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        user_resp.raise_for_status()
        user = user_resp.json()["attributes"]
        await event.reply(
            f"✅ ADMIN PANEL BERHASIL DIBUAT\n\n"
            f"🆔 ID: {user['id']}\n"
            f"👤 Nama: {username}\n"
            f"📧 Email: {email}\n"
            f"🔐 Password: {password}"
        )
        if settings.PP:
            await user_client.send_file(
                int(target_id),
                settings.PP,
                caption=(
                    f"🖥️ ADMIN DATA UNTUK {target_id}\n\n"
                    f"🌐 Login: {settings.DOMAIN}\n"
                    f"👤 Username: {user['username']}\n"
                    f"🔐 Password: {password}\n\n"
                    f"⚠️ Jangan DDoS panel\n"
                    f"✅ Admin berhasil dibuat!"
                )
            )
    except Exception as e:
        await event.reply(f"❌ Gagal membuat admin: `{e}`")
@user_client.on(events.NewMessage(pattern=r'^\.listserver$'))
async def list_all_servers(event):
    if not await khususakses(event):
        return
    try:
        resp = requests.get(
            f"{settings.DOMAIN}/api/application/servers",
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        resp.raise_for_status()
        servers = resp.json().get("data", [])
        if not servers:
            return await event.reply("⚠️ Tidak ada server tersedia.")
        msg = "<b>📋 Daftar Semua Server</b>\n\n"
        for s in servers:
            attr = s["attributes"]
            status_resp = requests.get(
                f"{settings.DOMAIN}/api/client/servers/{attr['identifier']}/resources",
                headers={
                    "Authorization": f"Bearer {settings.PLTC}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            status_data = status_resp.json()
            status = status_data.get("attributes", {}).get(
                "current_state", attr.get("status", "unknown")
            )
            msg += (
                f"🆔 ID: {attr['id']}\n"
                f"👤 Nama: {attr['name']}\n"
                f"⚙️ Status: {status}\n"
                f"💾 RAM: {attr['limits']['memory']} MB\n\n"
            )
        await event.reply(msg, parse_mode="html")
    except Exception as e:
        await event.reply(f"❌ Gagal mengambil server: {e}")
@user_client.on(events.NewMessage(pattern=r'^\.delserver\s+(\d+)$'))
async def delete_server(event):
    if not await khususakses(event):
        return
    server_id = event.pattern_match.group(1)
    try:
        resp = requests.delete(
            f"{settings.DOMAIN}/api/application/servers/{server_id}",
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        if resp.status_code == 204:
            await event.reply(f"✅ Server dengan ID {server_id} berhasil dihapus.")
        else:
            data = resp.json()
            await event.reply(f"❌ Gagal menghapus server:\n`{data}`")
    except Exception as e:
        await event.reply(f"❌ Error saat menghapus server: `{e}`")
@user_client.on(events.NewMessage(pattern=r'^\.listuser$'))
async def list_user(event):
    if not await khususakses(event):
        return
    try:
        resp = requests.get(
            f"{settings.DOMAIN}/api/application/users",
            headers={
                "Authorization": f"Bearer {settings.PLTC}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        users = resp.json().get("data", [])[:10]
        if not users:
            return await event.reply("⚠️ Tidak ada user ditemukan.")
        msg = "<b>📌 LIST USER:</b>\n"
        for u in users:
            attrs = u["attributes"]
            username = attrs['username'].replace("<", "&lt;").replace(">", "&gt;")
            msg += f"ID: {attrs['id']}\nNAMA: {username}\n─────────────\n"
        await event.reply(msg, parse_mode="html")
    except Exception as e:
        await event.reply(f"❌ Gagal mengambil user: `{e}`")
@user_client.on(events.NewMessage(pattern=r'^\.listadmin$'))
async def list_admin(event):
    if not await khususakses(event):
        return
    try:
        resp = requests.get(
            f"{settings.DOMAIN}/api/application/users",
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        users = resp.json().get("data", [])
        msg = "<b>📌 LIST ADMIN PANEL:</b>\n"
        for u in users:
            attr = u["attributes"]
            if attr.get("admin"):
                msg += f"🆔 {attr['id']} | 👤 {attr['username']} | 📧 {attr['email']}\n"
        if msg == "<b>📌 LIST ADMIN PANEL:</b>\n":
            msg += "⚠️ Tidak ada admin ditemukan."
        await event.reply(msg, parse_mode="html")
    except Exception as e:
        await event.reply(f"❌ Gagal mengambil admin: `{e}`")
@user_client.on(events.NewMessage(pattern=r'^\.deladmin\s+(\d+)$'))
async def delete_admin(event):
    if not await khususakses(event):
        return
    admin_id = int(event.pattern_match.group(1))
    try:
        resp = requests.delete(
            f"{settings.DOMAIN}/api/application/users/{admin_id}",
            headers={
                "Authorization": f"Bearer {settings.PLTA}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        if resp.status_code == 204:
            await event.reply(f"✅ Admin dengan ID {admin_id} berhasil dihapus.", parse_mode="html")
        else:
            await event.reply(f"❌ Gagal menghapus admin: {resp.text}", parse_mode="html")
    except Exception as e:
        await event.reply(f"❌ Error: `{e}`", parse_mode="html")
@user_client.on(events.NewMessage(pattern=r'^\.kick(?:\s+|$)(.*)'))
async def kick_handler(event):
    sender = await event.get_sender()
    if not await khususakses(event):
        return
    if not event.is_group:
        return await event.reply(
            "<blockquote>❌ <b>Perintah hanya bisa dipakai di grup.</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    perms = await user_client.get_permissions(event.chat_id, sender.id)
    if not perms.is_admin:
        return await event.reply(
            "<blockquote>❌ <b>Maaf, saya bukan admin di grup ini.</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    target = None
    if event.is_reply:
        reply = await event.get_reply_message()
        target = reply.sender_id
    else:
        args = event.pattern_match.group(1).strip()
        if args.isdigit():
            target = int(args)
    if not target:
        return await event.reply(
            "<blockquote>⚠️ <b>Format salah!</b>\n"
            "Gunakan:\n.kick (reply pesan user)</blockquote>",
            parse_mode="html",
            link_preview=False
        )
    try:
        await client.kick_participant(event.chat_id, target)
        await event.reply(
            "<blockquote>✅ <b>User berhasil di-kick.</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    except Exception as e:
        await event.reply(
            f"<blockquote>❌ <b>Gagal kick:</b> <code>{e}</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
@user_client.on(events.NewMessage(pattern=r'^\.promote$'))
async def promote_handler(event):
    sender = await event.get_sender()
    if not await khususakses(event):
        return
    if not event.is_group:
        return await event.reply(
            "<blockquote>❌ <b>Perintah hanya bisa digunakan di grup.</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    me = await user_client.get_me()
    my_perms = await user_client.get_permissions(event.chat_id, me.id)
    if not my_perms.is_admin:
        return await event.reply(
            "<blockquote>❌ <b>Maaf, saya bukan admin di grup ini.</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    if not event.is_reply:
        return await event.reply(
            "<blockquote>⚠️ <b>Format salah!</b>\n"
            "Gunakan:\n.promote (reply user)</blockquote>",
            parse_mode="html",
            link_preview=False
        )
    reply = await event.get_reply_message()
    try:
        await user_client.edit_admin(
            event.chat_id,
            reply.sender_id,
            add_admins=False,
            invite_users=True,
            change_info=False,
            ban_users=True,
            delete_messages=True,
            pin_messages=True,
            manage_call=True
        )
        await event.reply(
            f"<blockquote>✅ <b>Berhasil promote:</b> <code>{reply.sender_id}</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    except Exception as e:
        await event.reply(
            f"<blockquote>❌ <b>Gagal promote:</b> <code>{e}</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
@user_client.on(events.NewMessage(pattern=r'^\.demote$'))
async def demote_handler(event):
    sender = await event.get_sender()
    if not await khususakses(event):
        return
    if not event.is_group:
        return await event.reply(
            "<blockquote>❌ <b>Perintah hanya bisa digunakan di grup.</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    me = await user_client.get_me()
    my_perms = await user_client.get_permissions(event.chat_id, me.id)
    if not my_perms.is_admin:
        return await event.reply(
            "<blockquote>❌ <b>Maaf, saya bukan admin di grup ini.</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    if not event.is_reply:
        return await event.reply(
            "<blockquote>⚠️ <b>Format salah!</b>\n"
            "Gunakan:\n.demote (reply user)</blockquote>",
            parse_mode="html",
            link_preview=False
        )
    reply = await event.get_reply_message()
    try:
        await user_client.edit_admin(
            event.chat_id,
            reply.sender_id,
            is_admin=False
        )
        await event.reply(
            f"<blockquote>✅ <b>Berhasil demote:</b> <code>{reply.sender_id}</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    except Exception as e:
        await event.reply(
            f"<blockquote>❌ <b>Gagal demote:</b> <code>{e}</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
MUTE_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=True
)
@user_client.on(events.NewMessage(pattern=r'^\.mute$'))
async def mute_handler(event):
    sender = await event.get_sender()
    if not await khususakses(event):
        return
    if not event.is_group:
        return await event.reply(
            "<blockquote>❌ <b>Perintah hanya bisa digunakan di grup.</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    me = await user_client.get_me()
    perms = await user_client.get_permissions(event.chat_id, me.id)
    if not perms.is_admin:
        return await event.reply(
            "<blockquote>❌ <b>Maaf, saya bukan admin di grup ini.</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    if not event.is_reply:
        return await event.reply(
            "<blockquote>⚠️ <b>Format salah!</b>\nGunakan:\n.mute (reply user)</blockquote>",
            parse_mode="html",
            link_preview=False
        )
    reply = await event.get_reply_message()
    target = await reply.get_sender()
    try:
        await client(EditBannedRequest(
            event.chat_id,
            target.id,
            MUTE_RIGHTS
        ))
        mention = f"@{target.username}" if target.username else f"<code>{target.id}</code>"
        await event.reply(
            f"<blockquote>✅ <b>Berhasil mute {mention}</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    except Exception as e:
        await event.reply(
            f"<blockquote>❌ <b>Gagal mute:</b> <code>{e}</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
from telethon.tl.types import ChatBannedRights
from telethon.tl.functions.channels import EditBannedRequest
UNMUTE_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=False
)
@user_client.on(events.NewMessage(pattern=r'^\.unmute$'))
async def unmute_handler(event):
    sender = await event.get_sender()
    if not await khususakses(event):
        return
    if not event.is_group:
        return await event.reply(
            "<blockquote>❌ <b>Perintah hanya bisa digunakan di grup.</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    me = await user_client.get_me()
    perms = await user_client.get_permissions(event.chat_id, me.id)
    if not perms.is_admin:
        return await event.reply(
            "<blockquote>❌ <b>Maaf, saya bukan admin di grup ini.</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    if not event.is_reply:
        return await event.reply(
            "<blockquote>⚠️ <b>Format salah!</b>\nGunakan:\n.unmute (reply user)</blockquote>",
            parse_mode="html",
            link_preview=False
        )
    reply = await event.get_reply_message()
    target = await reply.get_sender()
    try:
        await client(EditBannedRequest(
            event.chat_id,
            target.id,
            UNMUTE_RIGHTS
        ))
        mention = f"@{target.username}" if target.username else f"<code>{target.id}</code>"
        await event.reply(
            f"<blockquote>✅ <b>Berhasil unmute {mention}</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    except Exception as e:
        await event.reply(
            f"<blockquote>❌ <b>Gagal unmute:</b> <code>{e}</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
import tempfile, os, aiohttp
from telethon import events
@user_client.on(events.NewMessage(pattern=r'^\.tt(?:\s+(https?://\S+))?$'))
async def tiktok_dl_handler(event):
    sender = await event.get_sender()
    if not await khususakses(event):
        return
    url = event.pattern_match.group(1)
    if not url:
        return await event.reply(
            "<blockquote>📌 Format:\n"
            "• <code>.tt https://www.tiktok.com/@user/video/123</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    await event.reply("<blockquote>⏳ Sedang mengambil video TikTok...</blockquote>", parse_mode="html")
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://www.tikwm.com',
        'Referer': 'https://www.tikwm.com/',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10)',
        'X-Requested-With': 'XMLHttpRequest'
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('https://www.tikwm.com/api/', headers=headers, params={'url': url, 'hd': 1}) as resp:
                res_json = await resp.json()
        data = res_json.get("data")
        if not data:
            return await event.reply("<blockquote>❌ Gagal: Tidak ada data TikTok</blockquote>", parse_mode="html")
        video_url = data.get("play") or data.get("hdplay")
        title = data.get("title", "Unknown")
        duration = str(data.get("duration", 0)) + " detik"
        author_name = data.get("author", {}).get("nickname", "Unknown")
        music_title = data.get("music_info", {}).get("title", "Unknown")
        music_author = data.get("music_info", {}).get("author", "Unknown")
        caption = (
            f"<blockquote>🎵 <b>{title}</b>\n"
            f"👤 Creator: {author_name}\n"
            f"⏱ Durasi: {duration}\n"
            f"🎶 Music: {music_title} - {music_author}</blockquote>"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as resp:
                video_data = await resp.read()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    tmp.write(video_data)
                    tmp_path = tmp.name
                await event.reply(message=caption, file=tmp_path, parse_mode="html")
                os.unlink(tmp_path)
    except Exception as e:
        await event.reply(f"<blockquote>❌ Gagal mengambil video TikTok:\n<code>{e}</code></blockquote>", parse_mode="html")
@user_client.on(events.NewMessage(pattern=r'^\.ttmp3(?:\s+(https?://\S+))?$'))
async def tiktok_mp3_handler(event):
    sender = await event.get_sender()
    if not await khususakses(event):
        return
    url = event.pattern_match.group(1)
    if not url:
        return await event.reply(
            "<blockquote>📌 Format:\n"
            "• <code>.ttmp3 https://www.tiktok.com/@user/video/123</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    await event.reply("<blockquote>⏳ Sedang mengambil audio TikTok...</blockquote>", parse_mode="html")
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://www.tikwm.com',
        'Referer': 'https://www.tikwm.com/',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10)',
        'X-Requested-With': 'XMLHttpRequest'
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('https://www.tikwm.com/api/', headers=headers, params={'url': url, 'hd': 1}) as resp:
                res_json = await resp.json()
        data = res_json.get("data")
        if not data:
            return await event.reply("<blockquote>❌ Gagal: Tidak ada data TikTok</blockquote>", parse_mode="html")
        audio_url = data.get("music_info", {}).get("play_url")
        music_title = data.get("music_info", {}).get("title", "Unknown")
        music_author = data.get("music_info", {}).get("author", "Unknown")
        if not audio_url:
            return await event.reply("<blockquote>❌ Gagal: Tidak ada audio tersedia</blockquote>", parse_mode="html")
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_url) as resp:
                audio_data = await resp.read()
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tmp_file.write(audio_data)
                tmp_file.close()
        caption = f"<blockquote>🎶 {music_title} - {music_author}</blockquote>"
        await event.reply(file=tmp_file.name, caption=caption, parse_mode="html", link_preview=False)
        os.remove(tmp_file.name)
    except Exception as e:
        await event.reply(f"<blockquote>❌ Gagal mengambil audio TikTok:\n<code>{e}</code></blockquote>", parse_mode="html")
        
        
import yt_dlp

@user_client.on(events.NewMessage(pattern=r'^\.song(?:\s+(.+))?$'))
async def song_handler(event):
    if not await khususakses(event):
        return
    query = event.pattern_match.group(1)
    if not query:
        return await event.reply(
            "<blockquote>📌 Format:\n"
            "• <code>.song judul lagu</code>\n"
            "• <code>.song https://youtube.com/watch?v=xxxx</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )

    await event.reply("<blockquote>🔍 Sedang mencari lagu...</blockquote>", parse_mode="html")

    if not query.startswith("http"):
        query = f"ytsearch:{query}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(tempfile.gettempdir(), '%(title)s.%(ext)s'),
        'quiet': True,
        'noplaylist': True,
        'concurrent_fragment_downloads': 4,
        'youtube_skip_dash_manifest': True
    }

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                info = info['entries'][0]

            filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            title = info.get('title', 'Unknown')
            uploader = info.get('uploader', 'Unknown')
            duration = info.get('duration', 0)
            album = info.get('album', 'N/A')
            track = info.get('track', 'N/A')

            caption = (
                f"<blockquote>🎵 <b>{title}</b>\n"
                f"🎤 Artis: {uploader}\n"
                f"📀 Album: {album}\n"
                f"🎶 Track: {track}\n"
                f"⏱ Durasi: {duration // 60} menit {duration % 60} detik</blockquote>"
            )

            await user_client.send_file(
                event.chat_id,
                file=filename,
                caption=caption,
                parse_mode="html"
            )

    except Exception as e:
        await event.reply(f"<blockquote>❌ Gagal mengambil lagu:\n<code>{e}</code></blockquote>", parse_mode="html")
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)
            
@user_client.on(events.NewMessage(pattern=r'^\.pin$'))
async def pin_handler(event):
    sender = await event.get_sender()
    if not await khususakses(event):
        return
    if event.is_group:
        perms = await user_client.get_permissions(event.chat_id, sender.id)
        if not perms.is_admin:
            return await event.reply(
                "<blockquote>❌ <b>Maaf, saya bukan admin di grup ini.</b></blockquote>",
                parse_mode="html",
            link_preview=False
            )
    if not event.is_reply:
        return await event.reply(
            "<blockquote>⚠️ <b>Format salah!</b>\n"
            "Gunakan:\n.pin (reply pesan)</blockquote>",
            parse_mode="html",
            link_preview=False
        )
    reply = await event.get_reply_message()
    try:
        await user_client.pin_message(event.chat_id, reply.id, notify=False)
        await event.reply(
            "<blockquote>✅ <b>Pesan berhasil di-pin.</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    except Exception as e:
        await event.reply(
            f"<blockquote>❌ <b>Gagal pin:</b> <code>{e}</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
@user_client.on(events.NewMessage(pattern=r'^\.unpin$'))
async def unpin_handler(event):
    sender = await event.get_sender()
    if not await khususakses(event):
        return
    if event.is_group:
        me = await user_client.get_me()
        perms = await user_client.get_permissions(event.chat_id, me.id)
        if not perms.is_admin:
            return await event.reply(
                "<blockquote>❌ <b>Maaf, saya bukan admin di grup ini.</b></blockquote>",
                parse_mode="html",
            link_preview=False
            )
    try:
        await user_client.unpin_message(event.chat_id)
        await event.reply(
            "<blockquote>✅ <b>Berhasil menghapus pin.</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    except Exception as e:
        await event.reply(
            f"<blockquote>❌ <b>Gagal unpin:</b> <code>{e}</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
from telethon import events
from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
@user_client.on(events.NewMessage(pattern=r'^\.block(?:\s+(\d+))?$'))
async def block_handler(event):
    sender = await event.get_sender()
    if not await khususowner(event):
        return
    user_id = event.pattern_match.group(1)
    reply_msg = await event.get_reply_message()
    msg = (
        "<blockquote>📌 Format Block:\n"
        "• Reply chat → <code>.block</code>\n"
        "• Atau pakai ID → <code>.block &lt;user_id&gt;</code></blockquote>"
    )
    if event.is_group:
        if reply_msg:
            user = await reply_msg.get_sender()
            msg += f"\n\n👤 Reply ke: <b>{user.first_name}</b> (ID: <code>{user.id}</code>)"
        else:
            msg += "\n\n❌ Tidak ada reply, hanya menampilkan format."
        return await event.reply(msg, parse_mode="html")
    try:
        if reply_msg:
            user = await reply_msg.get_sender()
            user_id = user.id
        if not user_id:
            return await event.reply(msg, parse_mode="html")
        await client(BlockRequest(int(user_id)))
        await event.reply(f"<blockquote>✅ User <code>{user_id}</code> berhasil diblokir</blockquote>", parse_mode="html")
    except Exception as e:
        await event.reply(f"<blockquote>❌ Gagal blokir:\n<code>{str(e)}</code></blockquote>", parse_mode="html")
@user_client.on(events.NewMessage(pattern=r'^\.unblock(?:\s+(\d+))?$'))
async def unblock_handler(event):
    sender = await event.get_sender()
    if not await khususowner(event):
        return
    user_id = event.pattern_match.group(1)
    reply_msg = await event.get_reply_message()
    msg = (
        "<blockquote>📌 Format Unblock:\n"
        "• Reply chat → <code>.unblock</code>\n"
        "• Atau pakai ID → <code>.unblock &lt;user_id&gt;</code></blockquote>"
    )
    if event.is_group:
        if reply_msg:
            user = await reply_msg.get_sender()
            msg += f"\n\n👤 Reply ke: <b>{user.first_name}</b> (ID: <code>{user.id}</code>)"
        else:
            msg += "\n\n❌ Tidak ada reply, hanya menampilkan format."
        return await event.reply(msg, parse_mode="html")
    try:
        if reply_msg:
            user = await reply_msg.get_sender()
            user_id = user.id
        if not user_id:
            return await event.reply(msg, parse_mode="html")
        await client(UnblockRequest(int(user_id)))
        await event.reply(f"<blockquote>✅ User <code>{user_id}</code> berhasil di-unblock</blockquote>", parse_mode="html")
    except Exception as e:
        await event.reply(f"<blockquote>❌ Gagal unblock:\n<code>{str(e)}</code></blockquote>", parse_mode="html")
import json
import os
from telethon import events

BLACKLIST_FILE = "data/blacklist.json"

# ---------------- Helper Blacklist ---------------- #
def load_blacklist():
    # buat file jika belum ada
    if not os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, "w") as f:
            json.dump({"groups": []}, f)
    # load data
    with open(BLACKLIST_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {"groups": []}
    # pastikan selalu ada key "groups"
    if "groups" not in data or not isinstance(data["groups"], list):
        data["groups"] = []
    return data

def save_blacklist(data):
    with open(BLACKLIST_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- Owner check ---------------- #
async def is_owner(event):
    sender = await event.get_sender()
    return sender.id == settings.OWNER_ID

# ---------------- Add blacklist otomatis ---------------- #
@user_client.on(events.NewMessage(pattern=r'^\.addbl$'))
async def add_bl(event):
    if not await is_owner(event):
        return
    chat_id = str(event.chat_id)
    bl = load_blacklist()
    if chat_id in bl["groups"]:
        return await event.reply(f"⚠️ Chat ini sudah di-blacklist")
    bl["groups"].append(chat_id)
    save_blacklist(bl)
    await event.reply(f"✅ Chat ini berhasil di-blacklist ({chat_id})")

# ---------------- Remove blacklist otomatis ---------------- #
@user_client.on(events.NewMessage(pattern=r'^\.unbl$'))
async def un_bl(event):
    if not await is_owner(event):
        return
    chat_id = str(event.chat_id)
    bl = load_blacklist()
    if chat_id not in bl["groups"]:
        return await event.reply(f"⚠️ Chat ini tidak ada di blacklist")
    bl["groups"].remove(chat_id)
    save_blacklist(bl)
    await event.reply(f"✅ Chat ini berhasil dihapus dari blacklist ({chat_id})")

# ---------------- List blacklist ---------------- #
@user_client.on(events.NewMessage(pattern=r'^\.blist$'))
async def list_bl(event):
    if not await is_owner(event):
        return
    bl = load_blacklist()
    if not bl["groups"]:
        return await event.reply("✅ Tidak ada chat di blacklist")
    text = "📛 Daftar chat/group blacklist:\n" + "\n".join(bl["groups"])
    await event.reply(text)

# ---------------- CFD dengan blacklist ---------------- #
@user_client.on(events.NewMessage(pattern=r'^\.cfd(?: (all|group))?$'))
async def cfd_handler(event):
    if not await is_owner(event):
        return

    if not event.is_reply:
        return await event.reply(
            "<blockquote>⚠️ <b>Format salah!</b>\n"
            "Gunakan:\n"
            ".cfd (reply pesan)\n"
            ".cfd all (reply pesan)\n"
            ".cfd group (reply pesan)</blockquote>",
            parse_mode="html",
            link_preview=False
        )

    reply_msg = await event.get_reply_message()
    mode = event.pattern_match.group(1)
    bl = load_blacklist()  # daftar semua chat/group blacklist

    try:
        # ---------------- Forward ke chat saat ini ---------------- #
        if mode is None:
            if str(event.chat_id) in bl["groups"]:
                return await event.reply("⚠️ Chat ini di-blacklist, forward dibatalkan.")
            await user_client.forward_messages(event.chat_id, reply_msg)
            return await event.reply(
                "<blockquote>✅ <b>Pesan berhasil diforward ke chat ini.</b></blockquote>",
                parse_mode="html",
                link_preview=False
            )

        # ---------------- Forward ke semua ---------------- #
        elif mode == "all":
            async for dialog in user_client.iter_dialogs():
                if str(dialog.id) in bl["groups"]:
                    continue  # skip semua blacklist (group + private)
                try:
                    await user_client.forward_messages(dialog.id, reply_msg)
                except Exception:
                    continue
            return await event.reply(
                "<blockquote>✅ <b>Done Broadcasting all (skip blacklist).</b></blockquote>",
                parse_mode="html",
                link_preview=False
            )

        # ---------------- Forward ke semua group ---------------- #
        elif mode == "group":
            async for dialog in user_client.iter_dialogs():
                if dialog.is_group:
                    if str(dialog.id) in bl["groups"]:
                        continue  # skip group blacklist
                    try:
                        await user_client.forward_messages(dialog.id, reply_msg)
                    except Exception:
                        continue
            return await event.reply(
                "<blockquote>✅ <b>Done broadcasting Groups (skip blacklist).</b></blockquote>",
                parse_mode="html",
                link_preview=False
            )

    except Exception as e:
        return await event.reply(
            f"<blockquote>❌ <b>Gagal forward:</b> <code>{e}</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
import time
from telethon import events
AFK = {
    "is_afk": False,
    "reason": "",
    "start_time": 0
}
@user_client.on(events.NewMessage(pattern=r'^\.afk(?: (.*))?$'))
async def set_afk(event):
    sender = await event.get_sender()
    if not await khususowner(event):
        return
    reason = event.pattern_match.group(1)
    if not reason:
        reason = "AFK tanpa alasan"
    AFK["is_afk"] = True
    AFK["reason"] = reason
    AFK["start_time"] = time.time()
    await event.reply(
        f"<blockquote>✅ <b>AFK diaktifkan</b>\n📌 Alasan: {reason}</blockquote>",
        parse_mode="html"
    )
@user_client.on(events.NewMessage(pattern=r'^\.unafk$'))
async def unset_afk(event):
    sender = await event.get_sender()
    if not await khususakses(event):
        return
    if not AFK["is_afk"]:
        return await event.reply(
            "<blockquote>⚠️ <b>Tidak sedang AFK.</b></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    afk_time = time.time() - AFK["start_time"]
    hours, remainder = divmod(int(afk_time), 3600)
    minutes, seconds = divmod(remainder, 60)
    duration = f"{hours} jam {minutes} menit {seconds} detik"
    AFK["is_afk"] = False
    AFK["reason"] = ""
    AFK["start_time"] = 0
    await event.reply(
        f"<blockquote>✅ <b>AFK dimatikan</b>\n⏱ Lama AFK: {duration}</blockquote>",
        parse_mode="html"
    )
@user_client.on(events.NewMessage)
async def afk_auto_reply(event):
    if not AFK["is_afk"]:
        return
    if event.sender_id == settings.OWNER_ID:
        return
    afk_time = time.time() - AFK["start_time"]
    hours, remainder = divmod(int(afk_time), 3600)
    minutes, seconds = divmod(remainder, 60)
    duration = f"{hours} jam {minutes} menit {seconds} detik"
    if event.is_private:
        try:
            await event.reply(
                f"<blockquote>🤖 <b>Owner sedang AFK</b>\n"
                f"⏱ Lama AFK: {duration}\n"
                f"📌 Alasan: {AFK['reason']}</blockquote>",
                parse_mode="html",
            link_preview=False
            )
        except Exception:
            pass
    elif event.is_group and event.message.mentioned:
        try:
            await event.reply(
                f"<blockquote>🤖 <b>Owner sedang AFK</b>\n"
                f"⏱ Lama AFK: {duration}\n"
                f"📌 Alasan: {AFK['reason']}</blockquote>",
                parse_mode="html",
            link_preview=False
            )
        except Exception:
            pass
import aiohttp
import asyncio
import html
import json
from telethon import events

# ====== Settings Dummy API ======
GEMINI_API_KEY = "AIzaSyAQsLEZlDzGPzuNeC24tTgVQVtY6BJsauo"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# ====== Fungsi chunk untuk teks panjang ======
def _chunk(text, size=3500):
    for i in range(0, len(text), size):
        yield text[i:i+size]

# ====== Handler AI ======
@user_client.on(events.NewMessage(pattern=r'^\.ai(?: (.+))?$'))
async def ai_handler(event):
    sender = await event.get_sender()
    # Hanya owner bisa pakai
    if sender.id != settings.OWNER_ID:
        return await event.reply(
            "<blockquote>❌ Hanya owner yang bisa pakai command ini</blockquote>", parse_mode="html"
        )

    arg = (event.pattern_match.group(1) or "").strip()
    prompt = arg

    # Jika reply ke pesan, gunakan pesan itu sebagai prompt
    if not prompt and event.is_reply:
        rm = await event.get_reply_message()
        if rm.text:
            prompt = rm.text.strip()
        elif rm.media:
            # Jika reply ke foto, jelaskan foto
            prompt = "Analisis gambar berikut ini dalam Bahasa Indonesia"

    if not prompt:
        return await event.reply(
            "<blockquote>❌ Format salah.\n"
            "Contoh:\n"
            "• <code>.ai apa itu blackhole?</code>\n"
            "• Balas pesan lalu ketik <code>.ai</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )

    wait = await event.reply("<blockquote>⏳ Tanya ke Gemini/AI...</blockquote>", parse_mode="html")

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GEMINI_API_URL,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            ) as resp:
                raw_resp = await resp.text()
                if resp.status != 200:
                    try:
                        err = json.loads(raw_resp)
                        msg = err.get("error", {}).get("message", raw_resp)
                    except Exception:
                        msg = raw_resp
                    return await wait.edit(
                        f"<blockquote>❌ API error ({resp.status}):\n<code>{html.escape(msg)[:1500]}</code></blockquote>",
                        parse_mode="html",
                        link_preview=False
                    )

                data = json.loads(raw_resp)

        # Ambil hasil jawaban AI
        answer = ""
        for cand in data.get("candidates", []):
            parts = cand.get("content", {}).get("parts", [])
            for p in parts:
                t = p.get("text")
                if t:
                    answer += t

        if not answer:
            answer = f"(Tidak ada teks balasan)\n\n{json.dumps(data)[:1500]}"

        safe = html.escape(answer)
        first = True
        for piece in _chunk(safe, 3500):
            if first:
                await wait.edit(f"<blockquote>{piece}</blockquote>", parse_mode="html")
                first = False
            else:
                await event.reply(f"<blockquote>{piece}</blockquote>", parse_mode="html")

    except asyncio.TimeoutError:
        await wait.edit("<blockquote>❌ Timeout menghubungi API.</blockquote>", parse_mode="html")
    except Exception as e:
        await wait.edit(
            f"<blockquote>❌ Gagal memproses:\n<code>{html.escape(str(e))}</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
import aiohttp, html, os, json, asyncio
from telethon import events
RAWG_API_KEY = "256aa55b64ae4ea9827186d19ee4e1e1"
PEXELS_API_KEY = "Ot3oAA0WzF98jpwLKY6ZhVTr8W78j19TaE4etLCsPo2JuXCEiYtC0jdI"
REMOVE_BG_KEY = "eVKd42BmH15xWztqmTAEd4uG"
REMOVE_BG_URL = "https://api.remove.bg/v1.0/removebg"
DEPAI_API_KEY = "17a5e750-48a9-4323-aed9-c8ece45676da"
DEPAI_URL = "https://api.depai.org/v1/images/search"
@user_client.on(events.NewMessage(pattern=r'^\.cimg(?: (.+))?$'))
async def cimg_handler(event):
    if not await khususakses(event):
        return
    query = (event.pattern_match.group(1) or "").strip()
    if not query and event.is_reply:
        reply = await event.get_reply_message()
        query = (reply.message or "").strip()
    if not query:
        return await event.reply(
            "<blockquote>❌ Format salah.\n"
            "Pakai:\n"
            "• <code>.cimg kucing</code>\n"
            "• Balas pesan lalu ketik <code>.cimg</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    wait = await event.reply("<blockquote>🖼️ Cari foto...</blockquote>", parse_mode="html")
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=30) as resp:
                data = await resp.json()
        photos = data.get("photos", [])
        if not photos:
            return await wait.edit(f"<blockquote>❌ Foto <b>{html.escape(query)}</b> tidak ditemukan.</blockquote>", parse_mode="html")
        p = photos[0]
        img = p["src"]["original"]
        photographer = p.get("photographer", "-")
        caption = f"<b>📸 Dari:</b> {html.escape(photographer)}\n<b>🔍 Query:</b> {html.escape(query)}"
        await user_client.send_file(event.chat_id, img, caption=f"<blockquote>{caption}</blockquote>", parse_mode="html")
        await wait.delete()
    except Exception as e:
        await wait.edit(f"<blockquote>❌ Error:\n<code>{html.escape(str(e))}</code></blockquote>", parse_mode="html")
        
@user_client.on(events.NewMessage(pattern=r'^\.cgame(?: (.+))?$'))
async def cgame_handler(event):
    if not await khususakses(event):
        return
    query = (event.pattern_match.group(1) or "").strip()
    if not query and event.is_reply:
        reply = await event.get_reply_message()
        query = (reply.message or "").strip()
    if not query:
        return await event.reply(
            "<blockquote>❌ Format salah.\n"
            "Pakai:\n"
            "• <code>.cgame gta 5</code>\n"
            "• Balas pesan lalu ketik <code>.cgame</code></blockquote>",
            parse_mode="html",
            link_preview=False
        )
    wait = await event.reply("<blockquote>🎮 Cari game...</blockquote>", parse_mode="html")
    url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={query}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as resp:
                data = await resp.json()
        results = data.get("results", [])
        if not results:
            return await wait.edit(f"<blockquote>❌ Game <b>{html.escape(query)}</b> tidak ditemukan.</blockquote>", parse_mode="html")
        g = results[0]
        name = g.get("name", "-")
        released = g.get("released", "-")
        rating = g.get("rating", "-")
        genres = ", ".join(x["name"] for x in g.get("genres", [])) or "-"
        img = g.get("background_image")
        caption = f"<b>{html.escape(name)}</b>\n📅 Rilis: {released}\n⭐ Rating: {rating}\n🎭 Genre: {html.escape(genres)}"
        if img:
            await user_client.send_file(event.chat_id, img, caption=f"<blockquote>{caption}</blockquote>", parse_mode="html")
            await wait.delete()
        else:
            await wait.edit(f"<blockquote>{caption}</blockquote>", parse_mode="html")
    except Exception as e:
        await wait.edit(f"<blockquote>❌ Error:\n<code>{html.escape(str(e))}</code></blockquote>", parse_mode="html")
@user_client.on(events.NewMessage(pattern=r'^\.rbg$'))
async def removebg_handler(event):
    if not await khususakses(event):
        return
    reply_msg = await event.get_reply_message()
    target_msg = reply_msg or event
    if not target_msg.photo:
        return await event.reply("<blockquote>❌ Harus reply ke foto atau kirim foto dengan caption <code>.rbg</code></blockquote>", parse_mode="html")
    wait = await event.reply("<blockquote>⏳ Menghapus background...</blockquote>", parse_mode="html")
    try:
        photo_path = await target_msg.download_media(file="./temp_rbg.png")
        async with aiohttp.ClientSession() as session:
            with open(photo_path, "rb") as f:
                form = aiohttp.FormData()
                form.add_field("image_file", f, filename="image.png")
                form.add_field("size", "auto")
                async with session.post(REMOVE_BG_URL, headers={"X-Api-Key": REMOVE_BG_KEY}, data=form) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        return await wait.edit(f"<blockquote>❌ API error ({resp.status}):\n<code>{err_text}</code></blockquote>", parse_mode="html")
                    out_path = "./no_bg.png"
                    with open(out_path, "wb") as out:
                        out.write(await resp.read())
        await user_client.send_file(event.chat_id, out_path, force_document=True, caption="✅ Background berhasil dihapus", reply_to=event.reply_to_msg_id)
        await wait.delete()
        os.remove(photo_path)
        os.remove(out_path)
    except Exception as e:
        await wait.edit(f"<blockquote>❌ Gagal:\n<code>{str(e)}</code></blockquote>", parse_mode="html")
        

import marshal, lzma, gzip, bz2, binascii, zlib, random, tempfile, os, shutil

def pyfuscate_encode(source: str) -> str:
    """Encode 1 lapis"""
    selected_mode = random.choice((lzma, gzip, bz2, binascii, zlib))
    marshal_encoded = marshal.dumps(compile(source, "Py-Fuscate", "exec"))
    if selected_mode is binascii:
        return "import marshal,lzma,gzip,bz2,binascii,zlib;exec(marshal.loads(binascii.a2b_base64({})))".format(
            binascii.b2a_base64(marshal_encoded)
        )
    return "import marshal,lzma,gzip,bz2,binascii,zlib;exec(marshal.loads({}.decompress({})))".format(
        selected_mode.__name__, selected_mode.compress(marshal_encoded)
    )


@user_client.on(events.NewMessage(pattern=r'^\.encpy(?: |$)(\d+)?'))
async def encpy_handler(event):
    if not await khususakses(event):
        return

    level = event.pattern_match.group(1)
    if not level:
        return await event.reply("⚠️ Contoh: `.encpy <Level>` (reply ke file python)")

    try:
        level = int(level)
    except:
        return await event.reply("⚠️ Level harus angka")

    # 🔥 Batasi level max = 265
    if level < 1 or level > 265:
        return await event.reply("⚠️ Level minimal dan maksimal 265")

    if not event.is_reply:
        return await event.reply("⚠️ Harus reply ke file `.py`")

    reply = await event.get_reply_message()
    if not reply.file or not reply.file.name.endswith(".py"):
        return await event.reply("⚠️ File harus `.py`")

    temp_dir = tempfile.mkdtemp()
    input_path = os.path.join(temp_dir, reply.file.name)
    await reply.download_media(file=input_path)

    output_path = input_path.replace(".py", f".enc{level}.py")

    try:
        with open(input_path) as f:
            source = f.read()

        encoded = source
        for i in range(level):
            encoded = pyfuscate_encode(encoded)

        with open(output_path, "w") as out:
            out.write(
                f'# Encoded by Userbot\n# Zerone Official Not Dev\ntry:\n\t{encoded}\nexcept KeyboardInterrupt:\n\texit()'
            )

        await event.reply(
            f"✅ File berhasil di-encode ({level} lapis)",
            file=output_path
        )

    except Exception as e:
        await event.reply(f"❌ Gagal encode: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@user_client.on(events.NewMessage(pattern=r'^\.id$'))
async def id_handler(event):
    sender = await event.get_sender()
    if not await khususakses(event):
        return
    msg_id = event.message.id
    chat_id = event.chat_id
    user_id = sender.id
    reply_text = f"💎 ᴍᴇꜱꜱᴀɢᴇ ɪᴅ: `{msg_id}`\n" \
                 f"👑 ʏᴏᴜʀ ɪᴅ: `{user_id}`\n" \
                 f"⏺ ᴄʜᴀᴛ ɪᴅ: `{chat_id}`"
    if event.is_reply:
        replied_msg = await event.get_reply_message()
        reply_text += f"\n✅ ʀᴇᴘʟɪᴇᴅ ᴍᴇꜱꜱᴀɢᴇ ɪᴅ: `{replied_msg.id}`\n" \
                      f"✅ ʀᴇᴘʟɪᴇᴅ ᴜꜱᴇʀ ɪᴅ: `{replied_msg.sender_id}`"
    await event.reply(f"<blockquote>`{reply_text}`</blockquote>", parse_mode="html")
@user_client.on(events.NewMessage(pattern=r'^\.cekip (.+)$'))
async def cekip_handler(event):
    sender = await event.get_sender()
    if not await khususakses(event):
        return
    input_url = event.pattern_match.group(1)
    if not input_url:
        return await event.reply("<blockquote>❌ Contoh: .cekip https://example.com</blockquote>", parse_mode="html")
    if not input_url.startswith(("http://", "https://")):
        input_url = "https://" + input_url
    try:
        start_time = asyncio.get_event_loop().time()
        async with aiohttp.ClientSession() as session:
            async with session.get(input_url, timeout=5) as resp:
                end_time = asyncio.get_event_loop().time()
                response_time = f"{int((end_time - start_time)*1000)} ms"
                final_url = str(resp.url)
                parsed = urlparse(final_url)
                hostname = parsed.hostname or "-"
                ip = socket.gethostbyname(hostname)
                status = f"{resp.status} {resp.reason}"
                ctype = resp.headers.get("Content-Type", "-")
                size = resp.headers.get("Content-Length")
                size = f"{int(size):,} bytes" if size else "-"
                server = resp.headers.get("Server", "-")
                powered = resp.headers.get("X-Powered-By", "-")
                cache = resp.headers.get("Cache-Control", "-")
                https = "✅ Yes" if final_url.startswith("https://") else "❌ No"
                reply = f"""
<blockquote><b>🔍 {hostname}</b></blockquote>
<pre>📡 IP       : {ip}</pre>
<pre>🔗 Redirect : {"-" if final_url==input_url else final_url}</pre>
<pre>📝 Status   : {status}</pre>
<pre>📄 Type     : {ctype}</pre>
<pre>📦 Size     : {size}</pre>
<pre>🚀 Server   : {server}</pre>
<pre>⚙️ Powered  : {powered}</pre>
<pre>⏱️ Speed    : {response_time}</pre>
<pre>🛡️ HTTPS    : {https}</pre>
<pre>🧠 Cache    : {cache}</pre>
<pre>🌐 URL      : {input_url}</pre>
""".strip()
                await event.reply(reply, parse_mode="html")
    except Exception as e:
        await event.reply(f"<pre>❌ Gagal cek URL:\n{e}</pre>", parse_mode="html")
import aiohttp
import socket
from telethon import events
@user_client.on(events.NewMessage(pattern=r'^\.ipaddress(?:\s+(.+))?$'))
async def ipaddress_handler(event):
    sender = await event.get_sender()
    if sender.id != settings.OWNER_ID:
        return await event.reply("<blockquote>❌ Hanya owner yang bisa pakai perintah ini.</blockquote>", parse_mode="html")
    ip = event.pattern_match.group(1)
    if not ip:
        return await event.reply("❌ Contoh penggunaan:\n<code>.ipaddress 8.8.8.8</code>", parse_mode="html")
    try:
        socket.inet_aton(ip)
    except socket.error:
        return await event.reply("❌ IP tidak valid!\nContoh: <code>.ipaddress 1.1.1.1</code>", parse_mode="html")
    await event.reply("<blockquote>⏳ Mengecek informasi IP...</blockquote>", parse_mode="html")
    await msg.delete() 
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://ip-api.com/json/{ip}?fields=66846719") as resp:
                data = await resp.json()
        if data.get("status") != "success":
            return await event.reply(f"<blockquote>❌ Gagal cek IP: {data.get('message','Unknown error')}</blockquote>", parse_mode="html")
        reply = f"""
<blockquote><b>📡 Informasi IP: {ip}</b></blockquote>
<pre>🌍 Negara    : {data.get('country','-')} ({data.get('countryCode','-')})</pre>
<pre>🏙️ Kota      : {data.get('city','-')}</pre>
<pre>🏞️ Region    : {data.get('regionName','-')}</pre>
<pre>📌 Koordinat : {data.get('lat','-')}, {data.get('lon','-')}</pre>
<pre>🏢 ISP       : {data.get('isp','-')}</pre>
<pre>🔗 Org       : {data.get('org','-')}</pre>
<pre>🛰️ ASN       : {data.get('as','-')}</pre>
<pre>🕹️ Timezone  : {data.get('timezone','-')}</pre>
<pre>🏡 Reverse   : {data.get('reverse','-')}</pre>
<pre>🌐 Proxy/VPN : {data.get('proxy','-')} | Hosting: {data.get('hosting','-')}</pre>
""".strip()
        await event.reply(reply, parse_mode="html")
    except Exception as e:
        await event.reply(f"<blockquote>❌ Error:\n<code>{str(e)}</code></blockquote>", parse_mode="html")
    
    
from datetime import datetime

@user_client.on(events.NewMessage(pattern=r'^\.done (.+)'))
async def done_handler(event):
    sender = await event.get_sender()
    
    # Hanya owner yang bisa pakai
    if not await khususakses(event):
        return  # langsung keluar kalau bukan owner

    # Ambil teks setelah .done
    text = event.pattern_match.group(1)
    
    # Split berdasarkan koma
    parts = text.split(",")
    if len(parts) < 2:
        return await event.reply("⚠️ Format salah! Gunakan: .done barang,harga[,pembayaran]")
    
    name_item = parts[0].strip()
    price = parts[1].strip()
    payment = parts[2].strip() if len(parts) > 2 else "Lainnya"
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    response = (
        f"<blockquote>「 𝗧𝗥𝗔𝗡𝗦𝗔𝗞𝗦𝗜 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 」\n</blockquote>"
        f"<blockquote>📦 <b>ʙᴀʀᴀɴɢ : {name_item}</b>\n"
        f"💸 <b>ɴᴏᴍɪɴᴀʟ : {price}</b>\n"
        f"🕰️ <b>ᴡᴀᴋᴛᴜ : {time}</b>\n"
        f"💳 <b>ᴘᴀʏᴍᴇɴᴛ : {payment}</b>\n</blockquote>"
        f"<blockquote>ᴛᴇʀɪᴍᴀᴋᴀsɪʜ ᴛᴇʟᴀʜ ᴏʀᴅᴇʀ</blockquote>"
    )
    
    # Kirim hasil
    await event.reply(response, parse_mode="html")


from telethon import events
from telethon.tl.types import UserStatusOnline, UserStatusRecently

@user_client.on(events.NewMessage(pattern=r'^\.liston$'))
async def liston_handler(event):
    if str(event.sender_id) != str(MY_ID):
        return await send_owner_only(event)
    if not event.is_group:
        return await event.reply("⚠️ Command ini hanya bisa di group!")
    try:
        online_users = []
        async for user in user_client.iter_participants(event.chat_id):
            if isinstance(user.status, (UserStatusOnline, UserStatusRecently)):
                name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                online_users.append(name or user.username or str(user.id))
        if not online_users:
            return await event.reply("📭 Tidak ada member yang online.")
        msg = "<b>🟢 Member Online:</b>\n\n"
        msg += "\n".join([f"• {name}" for name in online_users])
        msg += f"\n\n👥 Total online: {len(online_users)}"
        await event.reply(msg, parse_mode="html")
    except Exception as e:
        await event.reply(f"❌ Gagal mengambil data: `{e}`")        
        

@bot_client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode("utf-8")
    if data == "control":
        keyboard = [
    [Button.inline("𝚂𝚃𝙰𝚃𝚄𝚂 𝚄𝚂𝙴𝚁𝙱𝙾𝚃", b"userbot_menu"), Button.inline("𝙷𝙴𝙻𝙿 𝙼𝙴𝙽𝚄", b"back_main")],
    [Button.inline("𝚁𝚄𝙽 𝚄𝚂𝙴𝚁𝙱𝙾𝚃", b"run_userbot"), Button.inline("𝚁𝙴𝚂𝚃𝙰𝚁𝚃 𝚄𝚂𝙴𝚁𝙱𝙾𝚃", b"restart_userbot")],
    [Button.inline("𝚁𝙴𝚂𝚃𝙰𝚁𝚃 𝙱𝙾𝚃", b"restartbot"), Button.inline("𝚂𝙴𝚂𝚂𝙸𝙾𝙽 𝙽𝙰𝙼𝙴", b"session")],
    [Button.inline("𝚂𝙷𝚄𝚃𝙳𝙾𝚆𝙽 𝚄𝚂𝙴𝚁𝙱𝙾𝚃", b"shutdown_userbot")]
]
        await event.edit(
            """📌 <b>Halo! Selamat datang di Userbot V3.0.0</b>
<blockquote>
<u>⏤͟͟͞͞Menu & Panduan</u>
Gunakan tombol di bawah untuk menjelajahi semua fitur.  
Fitur terbagi menjadi dua bagian utama:
➥ <b>Bot API</b> – otomatisasi dan integrasi canggih  
➥ <b>Userbot</b> – kontrol personal & tambahan fitur  
<u>⏤͟͟͞͞Update di Versi 3.0.0</u>
• Tombol interaktif untuk navigasi lebih cepat  
• Fitur tambahan dengan API khusus  
• Semua fitur resmi dari <a href="https://t.me/ZeroneOfficial">Zerone Official</a>  
💡 Tip: Klik tombol untuk melihat fitur dan panduan penggunaannya.  
════════════════════  
🚀 Nikmati pengalaman baru dengan Userbot V3.0.0!</blockquote>""",
            buttons=keyboard,
            parse_mode="html",
            link_preview=False
        )
        
from telethon import events, Button
import asyncio
import settings
async def start_userbot():
    if not user_client.is_connected():
        await user_client.connect()
from telethon.tl.types import DocumentAttributeFilename
@bot_client.on(events.NewMessage(pattern=r"\/start"))
async def help_handler(event):
    keyboard = [
    [Button.inline("𝚂𝚃𝙰𝚃𝚄𝚂 𝚄𝚂𝙴𝚁𝙱𝙾𝚃", b"userbot_menu"), Button.inline("𝙷𝙴𝙻𝙿 𝙼𝙴𝙽𝚄", b"back_main")],
    [Button.inline("𝚁𝚄𝙽 𝚄𝚂𝙴𝚁𝙱𝙾𝚃", b"run_userbot"), Button.inline("𝚁𝙴𝚂𝚃𝙰𝚁𝚃 𝚄𝚂𝙴𝚁𝙱𝙾𝚃", b"restart_userbot")],
    [Button.inline("𝚁𝙴𝚂𝚃𝙰𝚁𝚃 𝙱𝙾𝚃", b"restartbot"), Button.inline("𝚂𝙴𝚂𝚂𝙸𝙾𝙽 𝙽𝙰𝙼𝙴", b"session")],
    [Button.inline("𝚂𝙷𝚄𝚃𝙳𝙾𝚆𝙽 𝚄𝚂𝙴𝚁𝙱𝙾𝚃", b"shutdown_userbot")]
]
    caption = """📌 <b>Halo! Selamat datang di Userbot V3.0.0</b>
<blockquote>
<u>⏤͟͟͞͞Menu & Panduan</u>
Gunakan tombol di bawah untuk menjelajahi semua fitur.  
Fitur terbagi menjadi dua bagian utama:
➥ <b>Bot API</b> – otomatisasi dan integrasi canggih  
➥ <b>Userbot</b> – kontrol personal & tambahan fitur  
<u>⏤͟͟͞͞Update di Versi 3.0.0</u>
• Tombol interaktif untuk navigasi lebih cepat  
• Fitur tambahan dengan API khusus  
• Semua fitur resmi dari <a href="https://t.me/ZeroneOfficial">Zerone Official</a>  
💡 Tip: Klik tombol untuk melihat fitur dan panduan penggunaannya.  
════════════════════  
🚀 Nikmati pengalaman baru dengan Userbot V3.0.0!</blockquote>"""
    await bot_client.send_file(
        event.chat_id,
        file="Media/control.jpg",
        caption=caption,
        buttons=keyboard,
        parse_mode="html",
        force_document=True,  
        attributes=[DocumentAttributeFilename(file_name="USERBOT VERSION 3.0.0")]
    )
from telethon import events, Button
import asyncio
CALLBACK_ACTIONS = {}
def register_callback(name):
    """Decorator untuk mendaftarkan handler callback."""
    def decorator(func):
        CALLBACK_ACTIONS[name] = func
        return func
    return decorator
@bot_client.on(events.CallbackQuery)
async def callback_handler(event):
    if event.sender_id != settings.OWNER_ID:
        await event.answer("Sok asik bet lu bukan siapa siapa.", alert=True)
        return
    data = event.data.decode("utf-8")
    handler = CALLBACK_ACTIONS.get(data)
    if handler:
        await handler(event)
        
@register_callback("userbot_menu")
async def show_userbot_menu(event):
    total_handlers = len(user_client._event_builders)
    status = "Running" if user_client.is_connected() else "Stopped"

    keyboard = [
        [Button.inline("⬅ Kembali", b"control")],
    ]

    await event.edit(
        f"<blockquote><b>Userbot Menu</b>\n➥ Total Fitur: {total_handlers}\n➥ Status: {status}</blockquote>",
        buttons=keyboard,
        parse_mode="html"
    )
    
@register_callback("restart_userbot")
async def restart_userbot(event):
    if user_client.is_connected():
        await event.edit(
            "<blockquote>⚠ <b>Userbot sudah berjalan!</b>\nTidak perlu restart.</blockquote>",
            buttons=[[Button.inline("⬅ Kembali", b"control")]],
            parse_mode="html"
        )
        return
    msg = await event.edit("<blockquote>♻️ Restarting userbot...</blockquote>", parse_mode="html")
    try:
        await user_client.disconnect()
        await asyncio.sleep(1)
    except:
        pass
    await start_userbot()
    asyncio.create_task(user_client.run_until_disconnected())
    await msg.edit(
        "<blockquote>✅ Userbot restarted!</blockquote>",
        buttons=[[Button.inline("⬅ Kembali", b"control")]],
        parse_mode="html"
    )
@register_callback("run_userbot")
async def run_userbot(event):
    if not user_client.is_connected():
        paused_handlers = list(user_client._event_builders)
        for h in paused_handlers:
            user_client.remove_event_handler(h)
        await start_clients()
        asyncio.create_task(user_client.run_until_disconnected())
        await asyncio.sleep(2)
        for h in paused_handlers:
            user_client.add_event_handler(h)
        await event.edit(
            "<blockquote>✅ Userbot sudah ON dan siap digunakan!</blockquote>",
            buttons=[[Button.inline("⬅ Kembali", b"control")]],
            parse_mode="html"
        )
    else:
        await event.edit(
            "<blockquote>⚠ Userbot sudah berjalan!</blockquote>",
            buttons=[[Button.inline("⬅ Kembali", b"control")]],
            parse_mode="html"
        )
from telethon import Button
@register_callback("shutdown_userbot")
async def shutdown_userbot(event):
    if user_client.is_connected():
        buttons = [
            [Button.inline("✅ YA", b"confirm_shutdown"), Button.inline("❌ TIDAK", b"cancel_shutdown")]
        ]
        await event.edit(
            "<blockquote><b>⚠ Yakin ingin mematikan Userbot?</b>\nSemua fitur akan berhenti.</blockquote>",
            buttons=buttons,
            parse_mode="html"
        )
    else:
        await event.edit(
            "<blockquote>⚠ Userbot sudah mati!</blockquote>",
            buttons=[[Button.inline("⬅ Kembali", b"control")]],
            parse_mode="html"
        )
@register_callback("confirm_shutdown")
async def confirm_shutdown(event):
    await user_client.disconnect()
    await event.edit(
        "<blockquote>🛑 <b>Userbot dimatikan!</b></blockquote>",
        buttons=[[Button.inline("⬅ Kembali", b"control")]],
        parse_mode="html"
    )
@register_callback("cancel_shutdown")
async def cancel_shutdown(event):
    await event.edit(
        "<blockquote>❌ <b>Shutdown dibatalkan.</b></blockquote>",
        buttons=[[Button.inline("⬅ Kembali", b"control")]],
        parse_mode="html"
    )
    
import os
import ast
import platform
from telethon import Button, events

PROJECT_DIR = "."  # folder project
MODULE_PAGE_SIZE = 20  # jumlah modul per halaman
module_cache = {}

def find_imports(path):
    """Scan semua .py di folder dan ambil modul import"""
    modules = set()
    for root, _, files in os.walk(path):
        for f in files:
            if f.endswith(".py"):
                try:
                    with open(os.path.join(root, f), encoding="utf-8") as source:
                        tree = ast.parse(source.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for n in node.names:
                                    modules.add(n.name.split('.')[0])
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    modules.add(node.module.split('.')[0])
                except Exception:
                    pass
    return sorted(modules)

def get_module_page(modules, page=0):
    start = page * MODULE_PAGE_SIZE
    end = start + MODULE_PAGE_SIZE
    return modules[start:end], len(modules)

# === SESSION HANDLER ===
@register_callback("session")
async def show_session(event, page: int = 0):
    me = await bot_client.get_me()
    os_info = f"{platform.system()} {platform.release()}"

    if "all_modules" not in module_cache:
        module_cache["all_modules"] = find_imports(PROJECT_DIR)

    modules_list = module_cache["all_modules"]
    page_items, total_len = get_module_page(modules_list, page)

    caption = (
        f"📌 Session Info\n\n"
        f"👤 Bot: @{getattr(me, 'username', 'N/A')}\n"
        f"💻 OS: {os_info}\n\n"
        f"📦 Modules (Page {page+1})\n"
        + "\n".join([f"• {m}" for m in page_items])
    )

    # tombol navigasi
    buttons = []
    nav = []
    if page > 0:
        nav.append(Button.inline("⬅ Prev", f"session_page:{page-1}"))
    if (page+1) * MODULE_PAGE_SIZE < total_len:
        nav.append(Button.inline("Next ➡", f"session_page:{page+1}"))
    if nav:
        buttons.append(nav)

    buttons.append([Button.inline("♻ Restart Bot", b"restartbot")])
    buttons.append([Button.inline("⬅ Kembali", b"control")])

    await event.edit(caption, buttons=buttons)

# === Pagination Handler ===
@bot_client.on(events.CallbackQuery(pattern=r"session_page:(\d+)"))
async def session_page_handler(event):
    page = int(event.pattern_match.group(1))
    await show_session(event, page)
    
# Callback restart bot dengan konfirmasi
@register_callback("restartbot")
async def restart_bot_prompt(event):
    buttons = [
        [Button.inline("✅ YA", b"confirm_restart"), Button.inline("❌ TIDAK", b"cancel_restart")]
    ]
    await event.edit(
        "<blockquote>⚠ <b>Yakin ingin me-restart bot sepenuhnya?</b>\nSemua handler dan session akan di-reload.</blockquote>",
        buttons=buttons,
        parse_mode="html"
    )

import asyncio
import os
import sys
from telethon import Button

# ================================
# Global untuk simpan ID pengirim restart
# ================================
RESTART_TRIGGER_ID = None

# ================================
# Callback restart
# ================================
@register_callback("confirm_restart")
async def confirm_restart(event):
    import os, sys

    # simpan ID pengirim untuk notifikasi nanti
    trigger_id = event.sender_id

    # Step 1: beri alert sementara
    msg = await event.edit("<blockquote>⚠ Bot akan direstart, mohon tunggu...</blockquote>", parse_mode="html")
    await asyncio.sleep(1)

    # Step 2: hapus pesan lama
    try:
        await msg.delete()
    except:
        pass

    # Step 3: kirim alert baru ke owner / yang men-trigger
    try:
        await bot_client.send_message(
            trigger_id,
            "♻ Bot Telah di restart cek di terminal / panel anda!"
        )
    except:
        pass

    # Step 4: restart Python sepenuhnya
    os.execv(sys.executable, [sys.executable] + sys.argv)

@register_callback("cancel_restart")
async def cancel_restart(event):
    await event.edit(
        "<blockquote>❌ Restart dibatalkan.</blockquote>",
        buttons=[[Button.inline("⬅ Kembali", b"control")]],
        parse_mode="html"
    )


async def main():
    await bot_client.start()
    await asyncio.gather(
        bot_client.run_until_disconnected()
    )
if __name__ == "__main__":
    asyncio.run(start_clients())
