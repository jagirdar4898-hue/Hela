import os
import random
import time
import asyncio
from gtts import gTTS

# --- ASYNCIO LOOP FIX (Python ki bewakoofi ka ilaaj) ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
# --------------------------------------------------------

from pyrogram import Client, filters, enums, compose, StopPropagation
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from groq import Groq

# Environment variables
BOT_TOKEN = os.environ.get("T")
GROQ_API_KEY = os.environ.get("G")
OWNER_ID = 8099984863
OWNER_USERNAME = "Carol_616"

API_ID = int(os.environ.get("A"))
API_HASH = os.environ.get("H")
app = Client("HelaBot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
groq_client = Groq(api_key=GROQ_API_KEY)

# Databases
economy = {}
loans = {}
active_guess = {"name": None, "chat_id": None}
auto_guess_enabled = {}

# Admin IDs (Bot Owners)
ADMIN_IDS = [7574760011, 8099984863]
warns = {}
kills_db = {}

def add_kills_to_user(uid, amt):
    kills_db[uid] = kills_db.get(uid, 0) + amt

# Protection DB
protection_db = {}
cooldowns = {"daily": {}, "weekly": {}}
rewards = {"daily": 1200, "weekly": 5000}

def is_protected(uid):
    if uid in ADMIN_IDS:
        return True
    if uid in protection_db:
        if time.time() < protection_db[uid]:
            return True
        else:
            del protection_db[uid]
    return False

# Helper functions
def get_bal(uid): return economy.get(uid, 1000)
def set_bal(uid, amt): economy[uid] = get_bal(uid) + amt

def get_rank(uid):
    sorted_eco = sorted(economy.items(), key=lambda x: x[1], reverse=True)
    for index, (user, bal) in enumerate(sorted_eco):
        if user == uid:
            return index + 1
    return "Unranked"

# NEW: Check if user is admin in current group OR bot admin
async def is_group_or_bot_admin(client, message):
    user_id = message.from_user.id
    # Bot admins have full power
    if user_id in ADMIN_IDS:
        return True
    # In groups, check if user is admin/owner
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        try:
            member = await client.get_chat_member(message.chat.id, user_id)
            if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                return True
        except:
            pass
    return False

# Original admin check (bot owners only)
async def is_admin(message):
    return message.from_user.id in ADMIN_IDS

# --- START COMMAND ---
@app.on_message(filters.command("start"))
async def start(client, message):
    if len(message.command) > 1 and message.command[1] == "help":
        return await help_cmd(client, message)
    user_name = message.from_user.first_name
    text = (
        f"✨ Hieeeee {user_name}!\n"
        "──────────────────\n"
        "💗 **Simple, smart & friendly chat bot**\n\n"
        "**What can I do?**\n"
        "• 💬 Fun & Easy Conversations\n"
        "• 🎮 Awesome Games & Economy\n"
        "• 🛡️ Group Management & Safety\n"
        "• ✨ A Safe & Smooth Experience\n\n"
        "✯ **Choose An Option Below :**"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me To Group", url=f"http://t.me/{client.me.username}?startgroup=true")],
        [InlineKeyboardButton("👤 Owner", url=f"https://t.me/Carol_616")]
    ])
    await message.reply_text(text, reply_markup=buttons)

# --- KILL, ROB, GIVE, LOAN (unchanged, keep as is) ---
@app.on_message(filters.command("kill"))
async def kill_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ **Kise maut ke ghaat utarna hai? Pehle kisi ke message par reply toh karo!**")
    victim = message.reply_to_message.from_user
    killer = message.from_user
    if victim.id == killer.id:
        return await message.reply_text("💀 **Khudkhushi paap hai! Hela ko ye pasand nahi. Kisi aur ko chuno!**")
    if is_protected(victim.id):
        return await message.reply_text(
            f"🛡️ **S-H-A-K-T-I-H-E-E-N  P-R-A-H-A-A-R!**\n\n"
            f"**{victim.first_name}** Hela ki sharan mein hai (Protected). "
            f"Tumhara hathiyar iska baal bhi banka nahi kar sakta! ⚡"
        )
    set_bal(killer.id, 500)
    add_kills_to_user(killer.id, 1)
    total_kills = kills_db.get(killer.id, 0)
    await message.reply_text(
        f"💀 **H-E-L-A'S  W-R-A-T-H!**\n"
        f"──────────────────\n"
        f"🩸 **{killer.first_name}** ki behremi se **{victim.first_name}** ka kaam tamam diya!\n"
        f"💰 Inam: **₹500** aapke khate mein jama ho gaye.\n"
        f"⚔️ **Total Kills:** {total_kills}\n"
        f"✨ Aae aise hi aghe badho "
    )

@app.on_message(filters.command("rob"))
async def rob_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply_text("💰 **Lootne ke liye kisi ke message par reply karein!**")
    target = message.reply_to_message.from_user
    robber_id = message.from_user.id
    if is_protected(target.id):
        return await message.reply_text(
            f"🛡️ **C-H-O-R-I N-A-A-K-A-A-M!**\n\n"
            f"**{target.first_name}** par Hela ka kaala kavach hai! "
            f"Tumhari himmat kaise hui unke khazane ki taraf aankh uthane ki? ⚡"
        )
    if target.id == robber_id:
        return await message.reply_text("💀 **Apni hi jeb katoge kya? Murkh!**")
    target_bal = get_bal(target.id)
    if target_bal <= 0:
        return await message.reply_text(
            f"💀 **{target.first_name} ke paas ek futi kaudi nahi hai!**\n"
            f"Hela murdon aur bhikariyon ko nahi loot-ti. Jao kisi ameer ko dhoondo!"
        )
    loot = random.randint(0, 40000)
    if loot > target_bal:
        loot = target_bal
    set_bal(target.id, -loot)
    set_bal(robber_id, loot)
    extra_msg = "✨ Hela is chori par muskura rahi hai..."
    if get_bal(target.id) == 0:
        extra_msg = "💸 **Tumne ishe aakhiri chillar tak loot liya! Ab ye puri tarah kangal ho chuka hai!** 💀"
    await message.reply_text(
        f"🧤 **H-E-I-S-T S-U-C-C-E-S-S-F-U-L!**\n"
        f"──────────────────\n"
        f"👣 **{message.from_user.first_name}** ne badi behremi se **{target.first_name}** ki jeb se **₹{loot}** uda liye!\n\n"
        f"{extra_msg}"
    )

@app.on_message(filters.command("loan"))
async def loan_cmd(client, message):
    if len(message.command) < 2 or not message.reply_to_message:
        return await message.reply_text("Usage: Reply to user with `/loan [amount]`")
    amt = int(message.command[1])
    target = message.reply_to_message.from_user
    loans[target.id] = {"from": message.from_user.id, "amt": amt}
    await message.reply_text(f"💸 {message.from_user.first_name} ne aapko **₹{amt}** ka loan offer kiya hai.\nType `/accept` to take it.")

@app.on_message(filters.command("accept"))
async def accept_cmd(client, message):
    uid = message.from_user.id
    if uid in loans:
        data = loans.pop(uid)
        set_bal(data["from"], -data["amt"])
        set_bal(uid, data["amt"])
        await message.reply_text(f"✅ Transaction Done! ₹{data['amt']} aapke account mein aa gaye.")
    else:
        await message.reply_text("Aapke paas koi loan offer nahi hai.")

@app.on_message(filters.command(["give", "pay", "transfer"]))
async def give_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply_text("💸 **Kise daan dena hai? Pehle kisi ke message par reply karo!**")
    if len(message.command) < 2:
        return await message.reply_text("💰 **Kitni raqam deni hai? Likh kar batao!\nExample:** `/give 500`")
    try:
        amount = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ **Sirf numbers likho, Asgard mein alphabet wale sikke nahi chalte!**")
    if amount <= 0:
        return await message.reply_text("💀 **Hela ke saath mazaak? Zero ya negative raqam nahi bhej sakte!**")
    sender = message.from_user
    receiver = message.reply_to_message.from_user
    if sender.id == receiver.id:
        return await message.reply_text("💀 **Khud ki ek jeb se nikal kar dusri jeb mein daal rahe ho? Murkh Mortal!**")
    if receiver.id == client.me.id:
        return await message.reply_text("👑 **Hela ko tumhare chillar nahi chahiye. Kisi Insaan ko do!**")
    sender_bal = get_bal(sender.id)
    if sender_bal < amount:
        return await message.reply_text(f"💸 **Tumhari aukaat nahi hai itna daan dene ki! Tumhare paas sirf ₹{sender_bal} hain.**")
    set_bal(sender.id, -amount)
    set_bal(receiver.id, amount)
    await message.reply_text(
        f"🤝 **G-E-N-E-R-O-S-I-T-Y!**\n"
        f"──────────────────\n"
        f"✨ **{sender.first_name}** ne apni marzi se **{receiver.first_name}** ko **₹{amount}** daan mein diye hain!\n\n"
        f"💰 Dono ka khazana update ho gaya hai. Hela is bhaichare par muskura rahi hai! 🖤"
    )

# --- GROQ AI (unchanged) ---
@app.on_message(filters.text & ~filters.regex(r"^/"), group=4)
async def hela_chat(client, message):
    bot = await client.get_me()
    msg_text = message.text.lower()
    is_private = message.chat.type == enums.ChatType.PRIVATE
    is_reply = message.reply_to_message and message.reply_to_message.from_user.id == bot.id
    is_mentioned = "hela" in msg_text or (bot.username and f"@{bot.username.lower()}" in msg_text)
    if not is_private and not (is_reply or is_mentioned):
        return
    system_role = "You are Hela, the Goddess of Death from Marvel. You are regal, witty, and powerful. You speak with a bit of a superior attitude and uses Hinglish but remain helpful to your subjects. you replies in 2 to 3 lines only. if anyone ask you that who is your owner aur somethig related to this then reply captain ne batane se manha kiya hai . Use emojis like ⚔️, 💀, ✨."
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": message.text}
        ],
        model="llama-3.1-8b-instant",
    )
    response = chat_completion.choices[0].message.content
    await message.reply_text(response)

# --- ROLEPLAY MEDIA VAULT (unchanged) ---
rp_media = {"love": [], "kiss": [], "bite": [], "hug": [], "punch": [], "slap": [], "fight": []}

@app.on_message(filters.command("punch"))
async def punch_cmd(client, message):
    if await is_admin(message) and message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.animation):
        msg = message.reply_to_message
        rp_media["punch"].append({"type": "photo" if msg.photo else "animation", "id": msg.photo.file_id if msg.photo else msg.animation.file_id})
        return await message.reply_text("✨ **V-A-U-L-T  U-P-D-A-T-E-D!**\nYe kaufnaak Punch save ho gaya! 🥊")
    if not message.reply_to_message:
        return await message.reply_text("✨ **Kise maut ka swaad chakhana hai? Pehle reply toh karo!**")
    victim = message.reply_to_message.from_user.first_name
    sender = message.from_user.first_name
    punches = [
        f"⚡ **{sender}** ne apni puri taqat se **{victim}** ke jabde par 'Necro-Punch' mara! Haddiyan tootne ki awaaz aayi... 🦴",
        f"🥊 **{sender}** ka ek mukka aur **{victim}** seedha Asgard se dharti par ja gira!",
        f"💥 Ek jordar prahaar! **{sender}** ne **{victim}** ko hawa mein uchhaal diya!"
    ]
    text = random.choice(punches)
    if rp_media["punch"]:
        m = random.choice(rp_media["punch"])
        await (client.send_photo if m["type"] == "photo" else client.send_animation)(message.chat.id, m["id"], caption=text, reply_to_message_id=message.reply_to_message.id)
    else: await message.reply_text(text)

@app.on_message(filters.command("slap"))
async def slap_cmd(client, message):
    if await is_admin(message) and message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.animation):
        msg = message.reply_to_message
        rp_media["slap"].append({"type": "photo" if msg.photo else "animation", "id": msg.photo.file_id if msg.photo else msg.animation.file_id})
        return await message.reply_text("✨ **V-A-U-L-T  U-P-D-A-T-E-D!**\nYe zordaar Slap save ho gaya! 🖐️")
    if not message.reply_to_message:
        return await message.reply_text("✨ **Meri deni hui shaktiyon ka upyog sahi jagah karo! Reply to someone!**")
    victim = message.reply_to_message.from_user.first_name
    sender = message.from_user.first_name
    text = f"🖐️ **S-L-A-P!**\n\n**{sender}** ne **{victim}** ko itna zor se thappad mara ki 'Multiverse' ke saare sitare nazar aa gaye! 💫"
    if rp_media["slap"]:
        m = random.choice(rp_media["slap"])
        await (client.send_photo if m["type"] == "photo" else client.send_animation)(message.chat.id, m["id"], caption=text, reply_to_message_id=message.reply_to_message.id)
    else: await message.reply_text(text)

@app.on_message(filters.command("fight"))
async def fight_cmd(client, message):
    if await is_admin(message) and message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.animation):
        msg = message.reply_to_message
        rp_media["fight"].append({"type": "photo" if msg.photo else "animation", "id": msg.photo.file_id if msg.photo else msg.animation.file_id})
        return await message.reply_text("✨ **V-A-U-L-T  U-P-D-A-T-E-D!**\nYe epic Fight scene save ho gaya! ⚔️")
    if not message.reply_to_message:
        return await message.reply_text("⚔️ **Akele kisse ladoge? Kisi gunehgaar par reply karo!**")
    victim = message.reply_to_message.from_user.first_name
    sender = message.from_user.first_name
    winner = random.choice([sender, victim])
    loser = victim if winner == sender else sender
    text = (
        f"⚔️ **MAUT KA MAIDAN-E-JANG** ⚔️\n"
        f"──────────────────\n"
        f"🔥 **{sender}** aur **{victim}** ke beech ek pralaykaari yuddh shuru hua!\n"
        f"Talwarein takrayi, bijli kadki aur anth mein...\n\n"
        f"🏆 **{winner}** ne **{loser}** ko ghutno par la diya aur vijay prapt ki! 🔥"
    )
    if rp_media["fight"]:
        m = random.choice(rp_media["fight"])
        await (client.send_photo if m["type"] == "photo" else client.send_animation)(message.chat.id, m["id"], caption=text, reply_to_message_id=message.reply_to_message.id)
    else: await message.reply_text(text)

# --- DART (66% win chance) ---
@app.on_message(filters.command("dart"))
async def dart_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply_text("🎯 **Khela shuru karne ke liye raqam toh batao!**\nExample: `/dart 500`")
    try:
        bet_amount = int(message.command[1])
    except:
        return await message.reply_text("❌ **Sirf numbers likho, befuzool baatein nahi!**")
    user_id = message.from_user.id
    current_bal = get_bal(user_id)
    if bet_amount > current_bal:
        return await message.reply_text("💸 **Jeb mein chillar nahi aur khwaab Asgard ke? Pehle paise kamao!**")
    if bet_amount <= 0:
        return await message.reply_text("💀 **Hela ke saath mazaak? Sahi raqam dalo!**")
    status = await message.reply_text("🎯 **Hela apni talwar nishane par phek rahi hai...**")
    win_chance = random.randint(1, 100)
    # 66% win chance
    if win_chance <= 66:
        win_amt = bet_amount * 2
        set_bal(user_id, bet_amount)
        await status.edit_text(
            f"🎯 **BULLSEYE!**\n"
            f"──────────────────\n"
            f"👑 **{message.from_user.first_name}**, tumhara nishana achook hai!\n"
            f"💰 Aapne **₹{bet_amount}** dao par lagaye aur **₹{win_amt}** jeet liye!\n"
            f"✨ Hela tumse prasann hui!"
        )
    else:
        set_bal(user_id, -bet_amount)
        await status.edit_text(
            f"🎯 **MISSED!**\n"
            f"──────────────────\n"
            f"💀 **Afsos!** Nishana chook gaya aur tumhara naseeb bhi!\n"
            f"🔥 **₹{bet_amount}** mitti mein mil gaye. Agli baar dhyan se!"
        )

# --- MODERATION COMMANDS (now accessible to group admins + bot admins) ---
async def is_group_or_bot_admin(client, message):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        return True
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        try:
            member = await client.get_chat_member(message.chat.id, user_id)
            if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                return True
        except:
            pass
    return False

@app.on_message(filters.command("ban"))
async def ban_cmd(client, message):
    if not await is_group_or_bot_admin(client, message): return
    if not message.reply_to_message:
        return await message.reply_text("🔨 **Kise Asgard se nikalna hai? Reply karo!**")
    victim = message.reply_to_message.from_user
    try:
        await client.ban_chat_member(message.chat.id, victim.id)
        await message.reply_text(f"⚡ **B-A-N-N-E-D!**\n\n**{victim.first_name}** ko Hela ke darbaar se hamesha ke liye kaala paani bhej diya gaya! 💀")
    except Exception as e:
        await message.reply_text("❌ Mere paas admin rights nahi hain ya ye banda mujhse zyada powerful hai!")

@app.on_message(filters.command("unban"))
async def unban_cmd(client, message):
    if not await is_group_or_bot_admin(client, message): return
    if not message.reply_to_message:
        return await message.reply_text("✨ **Kise azaad karna hai? Reply karo!**")
    victim = message.reply_to_message.from_user
    await client.unban_chat_member(message.chat.id, victim.id)
    await message.reply_text(f"✨ **R-E-B-I-R-T-H!**\n\n**{victim.first_name}** ke gunah maaf hue. Swarg mein wapas swagat hai! 🕊️")

@app.on_message(filters.command("kick"))
async def kick_cmd(client, message):
    if not await is_group_or_bot_admin(client, message): return
    if not message.reply_to_message:
        return await message.reply_text("👢 **Kise dhakke maar ke nikalna hai? Reply karo!**")
    victim = message.reply_to_message.from_user
    await client.ban_chat_member(message.chat.id, victim.id)
    await client.unban_chat_member(message.chat.id, victim.id)
    await message.reply_text(f"👢 **K-I-C-K-E-D!**\n\n**{victim.first_name}** ko Hela ne ek jordar laat maari aur wo group se bahar ja gira! 💥")

@app.on_message(filters.command("mute"))
async def mute_cmd(client, message):
    if not await is_group_or_bot_admin(client, message): return
    if not message.reply_to_message:
        return await message.reply_text("🤐 **Kisiki zubaan kaatni hai? Reply karo!**")
    victim = message.reply_to_message.from_user
    await client.restrict_chat_member(message.chat.id, victim.id, ChatPermissions(can_send_messages=False))
    await message.reply_text(f"🤐 **S-I-L-E-N-C-E!**\n\n**{victim.first_name}** ki awaaz chheen li gayi hai. Ab iski cheekh koi nahi sunega! 🤫")

@app.on_message(filters.command("unmute"))
async def unmute_cmd(client, message):
    if not await is_group_or_bot_admin(client, message): return
    if not message.reply_to_message:
        return await message.reply_text("🎙️ **Kise bolne ki azaadi deni hai? Reply karo!**")
    victim = message.reply_to_message.from_user
    await client.restrict_chat_member(
        message.chat.id, victim.id,
        ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
    )
    await message.reply_text(f"🎙️ **V-O-I-C-E R-E-S-T-O-R-E-D!**\n\n**{victim.first_name}**, Hela ne tumhari zubaan wapas kar di hai. Aukaat mein bolna! ✨")

@app.on_message(filters.command("warn"))
async def warn_cmd(client, message):
    if not await is_group_or_bot_admin(client, message): return
    if not message.reply_to_message:
        return await message.reply_text("⚠️ **Kise chetawani deni hai? Reply karo!**")
    victim = message.reply_to_message.from_user
    vid = victim.id
    warns[vid] = warns.get(vid, 0) + 1
    await message.reply_text(f"⚠️ **W-A-R-N-I-N-G!**\n\n**{victim.first_name}**, tumhari harkatein maut ko dawat de rahi hain!\n🔴 **Total Warns:** {warns[vid]}\nSudhar jao warna agla raasta seedha narak jata hai! 🔥")

# 🎲 DICE COMMAND (50% Win, 4x Payout)
pending_dice = {}

@app.on_message(filters.command("dice"))
async def dice_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply_text("🎲 **Daav toh lagao!** Likh kar batao: `/dice 100`")
    try:
        bet = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ **Mazaak mat karo, sahi number dalo!**")
    uid = message.from_user.id
    if get_bal(uid) < bet or bet <= 0:
        return await message.reply_text("💸 **Aukaat se bahar ka daav mat lagao! Pehle paise kamao.**")
    pending_dice[uid] = bet
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("1", callback_data="dice_1"), InlineKeyboardButton("2", callback_data="dice_2"), InlineKeyboardButton("3", callback_data="dice_3")],
        [InlineKeyboardButton("4", callback_data="dice_4"), InlineKeyboardButton("5", callback_data="dice_5"), InlineKeyboardButton("6", callback_data="dice_6")]
    ])
    await message.reply_text(f"🎲 **K-I-S-M-A-T  K-A  K-H-E-L!**\n\nTumhara Daav: **₹{bet}**\nBatao Asgard ka dice konsa number dikhayega?", reply_markup=buttons)

@app.on_callback_query(filters.regex(r"^dice_\d$"))
async def dice_callback(client, callback_query):
    uid = callback_query.from_user.id
    if uid not in pending_dice:
        return await callback_query.answer("❌ Tumhara koi daav nahi hai ya waqt nikal gaya!", show_alert=True)
    bet = pending_dice.pop(uid)
    chosen_num = int(callback_query.data.split("_")[1])
    is_win = random.choice([True, False])
    if is_win:
        rolled = chosen_num
        set_bal(uid, bet * 4)
        result_text = f"🎉 **J-A-C-K-P-O-T!**\nTumhari kismat chamak gayi! Tumne **₹{bet * 4}** jeet liye! ✨"
    else:
        rolled = random.choice([x for x in range(1, 7) if x != chosen_num])
        set_bal(uid, -bet)
        result_text = f"💀 **L-O-S-S!**\nTumne apna daav (**₹{bet}**) kho diya. Hela tumpar hass rahi hai!"
    text = (
        f"🎲 **H-E-L-A'S  D-I-C-E**\n"
        f"──────────────────\n"
        f"🎯 Tumne chuna: **{chosen_num}**\n"
        f"🎲 Dice par aaya: **{rolled}**\n\n"
        f"{result_text}"
    )
    await callback_query.message.edit_text(text)

@app.on_message(filters.command("all"))
async def mention_all_cmd(client, message):
    # Only works in groups
    if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("❌ Ye command sirf group mein kaam karti hai.")
    # Check if user is group admin or bot admin
    if not await is_group_or_bot_admin(client, message):
        return await message.reply_text("⛔ Sirf group admin ya bot owner sabko mention kar sakte hain.")
    # Get all non-bot members
    mentions = []
    async for member in client.get_chat_members(message.chat.id):
        if not member.user.is_bot:
            mentions.append(f"[{member.user.first_name}](tg://user?id={member.user.id})")
    if not mentions:
        return await message.reply_text("Is group mein koi mortal nahi hai!")
    # Split into chunks of ~50 mentions to avoid flood
    chunk_size = 50
    for i in range(0, len(mentions), chunk_size):
        chunk = mentions[i:i+chunk_size]
        await client.send_message(message.chat.id, " ".join(chunk), disable_web_page_preview=True)
        await asyncio.sleep(1)
    await message.reply_text(f"✅ **{len(mentions)}** mortals ko Hela ne bulaya!")

@app.on_message(filters.command("unwarn"))
async def unwarn_cmd(client, message):
    if not await is_group_or_bot_admin(client, message): return
    if not message.reply_to_message:
        return await message.reply_text("⚠️ **Kiski warning kam karni hai? Reply karo!**")
    victim = message.reply_to_message.from_user
    vid = victim.id
    if warns.get(vid, 0) > 0:
        warns[vid] -= 1
        await message.reply_text(f"✅ **Warn reduced!**\n\n**{victim.first_name}** ki ab {warns[vid]} warning bachi hai.")
    else:
        await message.reply_text(f"✅ **{victim.first_name}** pe koi warning nahi hai, wo already sudhar gaya!")

@app.on_message(filters.command("pin"))
async def pin_cmd(client, message):
    if not await is_group_or_bot_admin(client, message): return
    if not message.reply_to_message:
        return await message.reply_text("📌 **Hela ka kaunsa farmaan pin karna hai? Reply karo!**")
    await message.reply_to_message.pin()
    await message.reply_text("📌 **F-A-R-M-A-A-N!**\n\nHela ka aadesh aasman par likh diya gaya hai! Sab dhyaan dein! 📜")

@app.on_message(filters.command("say"))
async def say_cmd(client, message):
    if not await is_group_or_bot_admin(client, message): return
    if len(message.command) < 2:
        return await message.reply_text("🗣️ **Kya farmaan jaari karna hai? Likh kar batao!**")
    text_to_say = message.text.split(None, 1)[1]
    await message.delete()
    await client.send_message(message.chat.id, text_to_say)

# --- ECONOMY GOD COMMANDS (bot admins only) ---
@app.on_message(filters.command("gift"))
async def gift_cmd(client, message):
    if not await is_admin(message): return
    if len(message.command) < 2 or not message.reply_to_message:
        return await message.reply_text("💰 **Format:** Kisike message par reply karke likho `/gift 10000`")
    try:
        amount = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Sirf numbers likho!")
    victim = message.reply_to_message.from_user
    set_bal(victim.id, amount)
    await message.reply_text(
        f"👑 **R-O-Y-A-L B-O-U-N-T-Y!**\n"
        f"──────────────────\n"
        f"✨ Hela ke Senapati ne khazane ka darwaza khol diya!\n"
        f"**{victim.first_name}** ko **₹{amount}** ka vardan prapt hua! Aish karo Mortal! 🎉"
    )

@app.on_message(filters.command("addkill"))
async def addkill_cmd(client, message):
    if not await is_admin(message): return
    if len(message.command) < 2 or not message.reply_to_message:
        return await message.reply_text("💀 **Format:** Kisike message par reply karke likho `/addkill 5`")
    try:
        amount = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Sirf numbers likho!")
    victim = message.reply_to_message.from_user
    add_kills_to_user(victim.id, amount)
    total_kills = kills_db.get(victim.id, 0)
    await message.reply_text(
        f"🩸 **B-L-O-O-D-L-U-S-T!**\n"
        f"──────────────────\n"
        f"💀 Hela ne **{victim.first_name}** ki talwar ko aur bhayanak bana diya hai!\n"
        f"⚔️ **+{amount}** Kills add kar diye gaye hain.\n"
        f"🩸 **Total Kills:** {total_kills}"
    )

# --- PROFILE / BALANCE ---
@app.on_message(filters.command(["bal", "profile"]))
async def profile_cmd(client, message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    uid = target.id
    bal = get_bal(uid)
    kills = kills_db.get(uid, 0)
    rank = get_rank(uid)
    if is_protected(uid):
        if uid in protection_db and time.time() < protection_db[uid]:
            rem = int(protection_db[uid] - time.time())
            prot_status = f"🛡️ Active ({rem // 3600}h {(rem % 3600) // 60}m left)"
        else:
            prot_status = "🛡️ Active (Hela's Dark Magic ✨)"
    else:
        prot_status = "❌ Inactive (Khatre mein hai! 💀)"
    text = (
        f"👑 **P-R-O-F-I-L-E : {target.first_name}** 👑\n"
        f"──────────────────\n"
        f"💰 **Khazana (Balance):** ₹{bal}\n"
        f"💀 **Maut ka Aankda (Kills):** {kills}\n"
        f"🌍 **Global Rank:** #{rank}\n"
        f"🛡️ **Protection:** {prot_status}\n"
        f"──────────────────"
    )
    await message.reply_text(text)

# --- PROTECTION BUY ---
@app.on_message(filters.command("protection"))
async def protection_cmd(client, message):
    uid = message.from_user.id
    if is_protected(uid):
        if uid in protection_db:
            rem = int(protection_db[uid] - time.time())
            return await message.reply_text(f"🛡️ **Shanti rakho!** Tumhari protection chalu hai. ({rem // 3600}h {(rem % 3600) // 60}m left) ✨")
        else:
            return await message.reply_text("🛡️ **Tum par Hela ki kripa hai!** Tumhara aura hamesha protected hai. ✨")
    if len(message.command) > 1 and message.command[1].lower() == "buy":
        if get_bal(uid) < 500:
            return await message.reply_text("💸 **Kangal kahin ke!** Protection ki keemat ₹500 hai. Pehle paise kamao! 💀")
        set_bal(uid, -500)
        protection_db[uid] = time.time() + (24 * 3600)
        return await message.reply_text("🛡️ **A-U-R-A A-C-T-I-V-A-T-E-D!**\n\n✨ Hela ne tumse ₹500 le liye hain! Agle 24 ghante tak koi tumhe maar ya loot nahi sakta! Aish karo! 👑")
    else:
        await message.reply_text("❌ **Tumhari jaan khatre mein hai!** Koi bhi tumhe loot ya maar sakta hai.\n\n🛡️ **24 Ghante ki Protection** ke liye ₹500 lagenge.\nType karo: `/protection buy`")

# --- DAILY & WEEKLY REWARDS ---
@app.on_message(filters.command("daily"))
async def daily_cmd(client, message):
    uid = message.from_user.id
    now = time.time()
    last_claimed = cooldowns["daily"].get(uid, 0)
    if now - last_claimed < 86400:
        rem = int(86400 - (now - last_claimed))
        return await message.reply_text(f"⏳ **Lalach buri bala hai!** Apna inaam kal lena. ({rem // 3600}h {(rem % 3600) // 60}m left) 💀")
    amt = rewards["daily"]
    cooldowns["daily"][uid] = now
    set_bal(uid, amt)
    await message.reply_text(f"🌞 **D-A-I-L-Y B-O-U-N-T-Y!**\n\n✨ Hela tumhari aagyapalita se khush hui. Tumhe **₹{amt}** mile hain! 👑")

@app.on_message(filters.command("weekly"))
async def weekly_cmd(client, message):
    uid = message.from_user.id
    now = time.time()
    last_claimed = cooldowns["weekly"].get(uid, 0)
    if now - last_claimed < 604800:
        rem = int(604800 - (now - last_claimed))
        d = rem // 86400
        h = (rem % 86400) // 3600
        return await message.reply_text(f"⏳ **Sabar karo Mortal!** Weekly khazana khulne mein waqt hai. ({d}d {h}h left) 💀")
    amt = rewards["weekly"]
    cooldowns["weekly"][uid] = now
    set_bal(uid, amt)
    await message.reply_text(f"🌟 **W-E-E-K-L-Y T-R-E-A-S-U-R-E!**\n\n✨ Asgard ka khazana khul gaya hai! Tumhe **₹{amt}** ka maalik bana diya gaya hai! 🎉")

# --- ADMIN: EDIT REWARDS (bot admins only) ---
@app.on_message(filters.command("editdaily"))
async def editdaily_cmd(client, message):
    if not await is_admin(message): return
    if len(message.command) < 2: return await message.reply_text("✍️ Nayi raqam batao! (e.g., `/editdaily 2000`)")
    try:
        rewards["daily"] = int(message.command[1])
        await message.reply_text(f"✅ **Farmaan Jaari!** Daily reward ab **₹{rewards['daily']}** hai.")
    except:
        pass

@app.on_message(filters.command("users"))
async def users_list_cmd(client, message):
    if not await is_admin(message): 
        return await message.reply_text("⛔ **Aukaat mein Mortal!** Ye khufiya list sirf Hela ke Senapati dekh sakte hain.")
    if not economy:
        return await message.reply_text("📜 **Asgard khali hai!** Abhi tak koi mortal bot se nahi juda.")
    status_msg = await message.reply_text("⌛ **Asgard ki filein kholi ja rahi hain...**")
    user_list = []
    for uid in economy.keys():
        try:
            user = await client.get_users(uid)
            name = user.first_name if user.first_name else "Unknown"
            user_list.append(f"👤 {name} (`{uid}`)")
        except Exception:
            user_list.append(f"👤 Mysterious Mortal (`{uid}`)")
    header = f"👑 **H-E-L-A'S  S-U-B-J-E-C-T-S** (Total: {len(user_list)})\n──────────────────\n"
    current_msg = header
    for entry in user_list:
        if len(current_msg) + len(entry) > 4000:
            await message.reply_text(current_msg)
            current_msg = "──────────────────\n" + entry + "\n"
        else:
            current_msg += entry + "\n"
    await message.reply_text(current_msg)
    await status_msg.delete()

@app.on_message(filters.command("editweekly"))
async def editweekly_cmd(client, message):
    if not await is_admin(message): return
    if len(message.command) < 2: return await message.reply_text("✍️ Nayi raqam batao! (e.g., `/editweekly 10000`)")
    try:
        rewards["weekly"] = int(message.command[1])
        await message.reply_text(f"✅ **Farmaan Jaari!** Weekly reward ab **₹{rewards['weekly']}** hai.")
    except:
        pass

# --- REVIVE COMMAND ---
@app.on_message(filters.command("revive"))
async def revive_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply_text("✨ **Kise maut ke muh se wapas lana hai? Reply karo!**")
    target = message.reply_to_message.from_user
    healer = message.from_user
    if target.id == healer.id:
        return await message.reply_text("💀 **Khud ko revive nahi kar sakte! Kis aur se madad mango.**")
    if get_bal(healer.id) < 700:
        return await message.reply_text("💸 **Kangal!** Revive karne ki keemat **₹700** hai. Pehle Asgard ka tax chukao!")
    set_bal(healer.id, -700)
    await message.reply_text(
        f"🌟 **R-E-V-I-V-A-L  M-A-G-I-C!**\n"
        f"──────────────────\n"
        f"✨ **{healer.first_name}** ne **₹700** ki aahuti dekar **{target.first_name}** ki aatma ko Valhalla se wapas bula liya hai!\n"
        f"🕊️ Naya jeevan mubarak ho Mortal!"
    )

# --- LEADERBOARDS ---
@app.on_message(filters.command(["toprich", "rich"]))
async def toprich_cmd(client, message):
    if not economy:
        return await message.reply_text("📜 **Sab ke sab bhikari hain! Asgard ka khazana khali hai.**")
    sorted_eco = sorted(economy.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "💰 **T-O-P  10  R-I-C-H-E-S-T** 💰\n──────────────────\n"
    for i, (uid, bal) in enumerate(sorted_eco):
        try:
            user = await client.get_users(uid)
            name = user.first_name
        except:
            name = f"Mysterious Mortal ({uid})"
        text += f"**{i+1}.** {name} — **₹{bal}**\n"
    text += "──────────────────\n✨ Hela inki daulat par nazar rakhe hue hai..."
    await message.reply_text(text)

@app.on_message(filters.command(["topkill", "killers"]))
async def topkill_cmd(client, message):
    if not kills_db:
        return await message.reply_text("📜 **Asgard mein abhi tak shanti hai! Kisi ne kisi ka khoon nahi bahaya.**")
    sorted_kills = sorted(kills_db.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "💀 **T-O-P  10  K-I-L-L-E-R-S** 💀\n──────────────────\n"
    for i, (uid, kills) in enumerate(sorted_kills):
        if kills > 0:
            try:
                user = await client.get_users(uid)
                name = user.first_name
            except:
                name = f"Shadow Assassin ({uid})"
            text += f"**{i+1}.** {name} — **{kills} Kills** ⚔️\n"
    text += "──────────────────\n✨ Hela inke khooni khel se bohot prasann hai..."
    await message.reply_text(text)

# --- ROLEPLAY COMMANDS (love, kiss, bite, hug) ---
@app.on_message(filters.command("love"))
async def love_cmd(client, message):
    if await is_admin(message) and message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.animation):
        msg = message.reply_to_message
        media_type = "photo" if msg.photo else "animation"
        file_id = msg.photo.file_id if msg.photo else msg.animation.file_id
        rp_media["love"].append({"type": media_type, "id": file_id})
        return await message.reply_text("✨ **V-A-U-L-T  U-P-D-A-T-E-D!**\nYe chitra `/love` ke khazane mein save ho gaya hai! 🖤")
    if not message.reply_to_message:
        return await message.reply_text("🖤 **Kisse prem jatana hai? Reply karo!**")
    sender = message.from_user.first_name
    target = message.reply_to_message.from_user.first_name
    love_percent = random.randint(10, 100)
    text = (
        f"🖤 **A-S-G-A-R-D-I-A-N  R-O-M-A-N-C-E** 🖤\n"
        f"──────────────────\n"
        f"✨ **{sender}** aur **{target}** ke beech ka rishta Hela khud dekh rahi hai...\n"
        f"💘 **Love Match:** {love_percent}%\n"
        f"{'🔥 Maut bhi inhe alag nahi kar sakti!' if love_percent > 80 else '💀 Isse behtar toh akele marna hai!'}"
    )
    if rp_media["love"]:
        media = random.choice(rp_media["love"])
        if media["type"] == "photo":
            await client.send_photo(message.chat.id, photo=media["id"], caption=text, reply_to_message_id=message.reply_to_message.id)
        else:
            await client.send_animation(message.chat.id, animation=media["id"], caption=text, reply_to_message_id=message.reply_to_message.id)
    else:
        await message.reply_text(text)

@app.on_message(filters.command("kiss"))
async def kiss_cmd(client, message):
    if await is_admin(message) and message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.animation):
        msg = message.reply_to_message
        rp_media["kiss"].append({"type": "photo" if msg.photo else "animation", "id": msg.photo.file_id if msg.photo else msg.animation.file_id})
        return await message.reply_text("✨ **V-A-U-L-T  U-P-D-A-T-E-D!**\nYe kaufnaak chumban save ho gaya! 💋")
    if not message.reply_to_message: return await message.reply_text("💋 **Hawa mein chumban mat udao, kisi par reply karo!**")
    sender, target = message.from_user.first_name, message.reply_to_message.from_user.first_name
    text = f"💋 **{sender}** ne **{target}** ko ek zordaar aur zehreela chumban diya! ✨"
    if rp_media["kiss"]:
        m = random.choice(rp_media["kiss"])
        await (client.send_photo if m["type"] == "photo" else client.send_animation)(message.chat.id, m["id"], caption=text, reply_to_message_id=message.reply_to_message.id)
    else: await message.reply_text(text)

@app.on_message(filters.command("bite"))
async def bite_cmd(client, message):
    if await is_admin(message) and message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.animation):
        msg = message.reply_to_message
        rp_media["bite"].append({"type": "photo" if msg.photo else "animation", "id": msg.photo.file_id if msg.photo else msg.animation.file_id})
        return await message.reply_text("✨ **V-A-U-L-T  U-P-D-A-T-E-D!**\nYe khoonkhaar Bite GIF save ho gaya! 🧛")
    if not message.reply_to_message: return await message.reply_text("🧛 **Kisika khoon peena hai? Reply karo!**")
    sender, target = message.from_user.first_name, message.reply_to_message.from_user.first_name
    text = f"🧛 **{sender}** ne apne nukeele daant **{target}** ki gardan mein gada diye! Khoon beh raha hai... 🩸"
    if rp_media["bite"]:
        m = random.choice(rp_media["bite"])
        await (client.send_photo if m["type"] == "photo" else client.send_animation)(message.chat.id, m["id"], caption=text, reply_to_message_id=message.reply_to_message.id)
    else: await message.reply_text(text)

@app.on_message(filters.command("hug"))
async def hug_cmd(client, message):
    if await is_admin(message) and message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.animation):
        msg = message.reply_to_message
        rp_media["hug"].append({"type": "photo" if msg.photo else "animation", "id": msg.photo.file_id if msg.photo else msg.animation.file_id})
        return await message.reply_text("✨ **V-A-U-L-T  U-P-D-A-T-E-D!**\nYe Hug GIF Asgard ke vault mein chala gaya! 🫂")
    if not message.reply_to_message: return await message.reply_text("🫂 **Kise gale lagana hai? Reply karo!**")
    sender, target = message.from_user.first_name, message.reply_to_message.from_user.first_name
    text = f"🫂 **{sender}** ne **{target}** ko itne zor se gale lagaya ki haddiyan chatakne ki awaaz aayi! 🦴✨"
    if rp_media["hug"]:
        m = random.choice(rp_media["hug"])
        await (client.send_photo if m["type"] == "photo" else client.send_animation)(message.chat.id, m["id"], caption=text, reply_to_message_id=message.reply_to_message.id)
    else: await message.reply_text(text)

# --- NEW: COUPLE COMMAND (with GIF support) ---
pending_couple_media = {}  # {admin_id: file_id} for storing replied media

@app.on_message(filters.command("couple"))
async def couple_cmd(client, message):
    # If admin replied to a GIF/sticker/photo, store it for future couple commands
    if await is_admin(message) and message.reply_to_message:
        replied = message.reply_to_message
        if replied.animation or replied.sticker or replied.photo:
            media_type = "animation" if replied.animation else "sticker" if replied.sticker else "photo"
            file_id = replied.animation.file_id if replied.animation else replied.sticker.file_id if replied.sticker else replied.photo.file_id
            pending_couple_media[message.from_user.id] = {"type": media_type, "id": file_id}
            return await message.reply_text("✨ **Couple GIF saved!** Ab `/couple` command use karne par ye media dikhega.")
    
    # Only works in groups
    if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("❌ **Couple command sirf group mein kaam karti hai!**")
    
    # Get all members (excluding bot and maybe the command user)
    try:
        members = []
        async for member in client.get_chat_members(message.chat.id, limit=200):
            if not member.user.is_bot:
                members.append(member.user)
        if len(members) < 2:
            return await message.reply_text("❌ **Is realm mein do mortal bhi nahi hain!**")
        # Pick two random distinct users
        chosen = random.sample(members, 2)
        user1, user2 = chosen[0], chosen[1]
    except Exception as e:
        return await message.reply_text("❌ Members list nahi laa sakta, try again later.")
    
    couple_text = (
        f"💕 **C-O-U-P-L-E  O-F  T-H-E  D-A-Y** 💕\n"
        f"──────────────────\n"
        f"✨ {user1.mention}  🤍  {user2.mention}\n"
        f"Hela ne inki jodi ko Asgard mein approve kar diya hai! 💘"
    )
    
    # Check if admin has stored a custom media
    admin_id = message.from_user.id
    if admin_id in pending_couple_media:
        media = pending_couple_media[admin_id]
        if media["type"] == "photo":
            await client.send_photo(message.chat.id, photo=media["id"], caption=couple_text)
        elif media["type"] == "animation":
            await client.send_animation(message.chat.id, animation=media["id"], caption=couple_text)
        elif media["type"] == "sticker":
            await client.send_sticker(message.chat.id, sticker=media["id"])
            await client.send_message(message.chat.id, couple_text)
        # Optionally delete stored media after use
        # del pending_couple_media[admin_id]
    else:
        await message.reply_text(couple_text)

# --- NEW: BROADCAST WITH REPLY SUPPORT ---
@app.on_message(filters.command("broadcast"))
async def broadcast_cmd(client, message):
    if not await is_admin(message):
        return await message.reply_text("⛔ **Aukaat mein!** Ye shakti sirf Hela ke hath mein hai.")
    
    # Check if replying to a message (any media or text)
    if message.reply_to_message:
        replied = message.reply_to_message
        # Determine target: either "all" or a specific ID from command
        args = message.text.split()
        target = args[1] if len(args) > 1 else "all"
        
        # Prepare content
        content_type = None
        content_data = None
        caption = replied.caption if replied.caption else ""
        
        if replied.text:
            content_type = "text"
            content_data = replied.text
        elif replied.photo:
            content_type = "photo"
            content_data = replied.photo.file_id
            caption = replied.caption or ""
        elif replied.video:
            content_type = "video"
            content_data = replied.video.file_id
            caption = replied.caption or ""
        elif replied.animation:
            content_type = "animation"
            content_data = replied.animation.file_id
            caption = replied.caption or ""
        elif replied.sticker:
            content_type = "sticker"
            content_data = replied.sticker.file_id
        elif replied.document:
            content_type = "document"
            content_data = replied.document.file_id
            caption = replied.caption or ""
        else:
            return await message.reply_text("❌ Is message type ko broadcast nahi kar sakta.")
        
        # Send to target
        if target.lower() == "all":
            status = await message.reply_text("🚀 **Pralay Shuru!** Sabhi realms mein message bheja ja raha hai...")
            success = 0
            failed = 0
            all_targets = set(list(economy.keys()))
            for uid in all_targets:
                try:
                    if content_type == "text":
                        await client.send_message(uid, content_data)
                    elif content_type == "photo":
                        await client.send_photo(uid, photo=content_data, caption=caption)
                    elif content_type == "video":
                        await client.send_video(uid, video=content_data, caption=caption)
                    elif content_type == "animation":
                        await client.send_animation(uid, animation=content_data, caption=caption)
                    elif content_type == "sticker":
                        await client.send_sticker(uid, sticker=content_data)
                    elif content_type == "document":
                        await client.send_document(uid, document=content_data, caption=caption)
                    success += 1
                    await asyncio.sleep(0.1)
                except Exception:
                    failed += 1
            await status.edit_text(
                f"✅ **Broadcast Completed!**\n"
                f"──────────────────\n"
                f"✨ Sahi se pahucha: `{success}`\n"
                f"💀 Failed: `{failed}`"
            )
        else:
            try:
                target_id = int(target)
                if content_type == "text":
                    await client.send_message(target_id, content_data)
                elif content_type == "photo":
                    await client.send_photo(target_id, photo=content_data, caption=caption)
                elif content_type == "video":
                    await client.send_video(target_id, video=content_data, caption=caption)
                elif content_type == "animation":
                    await client.send_animation(target_id, animation=content_data, caption=caption)
                elif content_type == "sticker":
                    await client.send_sticker(target_id, sticker=content_data)
                elif content_type == "document":
                    await client.send_document(target_id, document=content_data, caption=caption)
                await message.reply_text(f"✅ **Sandesh pahuch gaya!** User `{target_id}` ko Hela ka khat mil gaya hai.")
            except ValueError:
                await message.reply_text("❌ **Invalid ID!** 'all' likho ya sahi User ID dalo.")
            except Exception as e:
                await message.reply_text(f"❌ **Error:** {e}")
    else:
        # Fallback to old text-based broadcast
        if len(message.command) < 3:
            return await message.reply_text(
                "📢 **Format Galat Hai!**\n\n"
                "• Sabko bhejne ke liye: `/broadcast all [message]`\n"
                "• Kisi ID ko bhejne ke liye: `/broadcast [user_id] [message]`\n"
                "• Ya kisi message par reply karke `/broadcast all` karein."
            )
        target = message.command[1]
        broadcast_msg = message.text.split(None, 2)[2]
        if target.lower() == "all":
            status = await message.reply_text("🚀 **Pralay Shuru!** Sabhi realms mein message bheja ja raha hai...")
            success = 0
            failed = 0
            all_targets = set(list(economy.keys()))
            for uid in all_targets:
                try:
                    await client.send_message(uid, f"📢 **H-E-L-A  F-A-R-M-A-A-N**\n──────────────────\n\n{broadcast_msg}")
                    success += 1
                    await asyncio.sleep(0.1)
                except Exception:
                    failed += 1
            await status.edit_text(
                f"✅ **Broadcast Completed!**\n"
                f"──────────────────\n"
                f"✨ Sahi se pahucha: `{success}`\n"
                f"💀 Failed: `{failed}`"
            )
        else:
            try:
                target_id = int(target)
                await client.send_message(target_id, f"📢 **H-E-L-A  S-P-E-C-I-A-L  M-S-G**\n──────────────────\n\n{broadcast_msg}")
                await message.reply_text(f"✅ **Sandesh pahuch gaya!** User `{target_id}` ko Hela ka khat mil gaya hai.")
            except ValueError:
                await message.reply_text("❌ **Invalid ID!** 'all' likho ya sahi User ID dalo.")
            except Exception as e:
                await message.reply_text(f"❌ **Error:** {e}")

# --- NEW: GROUP SELECTION FOR BROADCAST (Inline Keyboard) ---

# Group selection ke liye temporary storage
group_msg_storage = {}  # {user_id: {"content_type", "content_data", "caption"}}

@app.on_message(filters.command("groups"))
async def groups_list_cmd(client, message):
    if not await is_admin(message):
        return await message.reply_text("⛔ **Aukaat mein!** Ye shakti sirf Hela ke hath mein hai.")
    
    # Agar kisi message par reply kiya hai toh store karo
    if message.reply_to_message:
        replied = message.reply_to_message
        content_type = None
        content_data = None
        caption = replied.caption if replied.caption else ""
        if replied.text:
            content_type = "text"
            content_data = replied.text
        elif replied.photo:
            content_type = "photo"
            content_data = replied.photo.file_id
            caption = replied.caption or ""
        elif replied.video:
            content_type = "video"
            content_data = replied.video.file_id
            caption = replied.caption or ""
        elif replied.animation:
            content_type = "animation"
            content_data = replied.animation.file_id
            caption = replied.caption or ""
        elif replied.sticker:
            content_type = "sticker"
            content_data = replied.sticker.file_id
        elif replied.document:
            content_type = "document"
            content_data = replied.document.file_id
            caption = replied.caption or ""
        else:
            return await message.reply_text("❌ Is type ka message forward nahi kar sakta.")
        group_msg_storage[message.from_user.id] = {
            "content_type": content_type,
            "content_data": content_data,
            "caption": caption
        }
    else:
        group_msg_storage[message.from_user.id] = None
    
    # Saare groups fetch karo jahaan bot hai
    groups = []
    async for dialog in client.get_dialogs():
        if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            groups.append(dialog.chat)
    if not groups:
        return await message.reply_text("❌ Bot kisi group mein nahi hai!")
    
    buttons = []
    for chat in groups[:50]:
        buttons.append([InlineKeyboardButton(chat.title, callback_data=f"sendgroup_{chat.id}")])
    buttons.append([InlineKeyboardButton("📢 Sabhi Groups mein bhejo", callback_data="sendgroup_all")])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="sendgroup_cancel")])
    
    await message.reply_text(
        "📢 **Group select karo:**\n(Jo message reply kiya tha, wahi bheja jayega)",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query(filters.regex(r"^sendgroup_"))
async def send_to_group_callback(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in group_msg_storage:
        await callback_query.answer("Session expired. /groups dobara use karo.", show_alert=True)
        return
    
    data = group_msg_storage[user_id]
    target = callback_query.data.split("_")[1]
    
    if target == "cancel":
        del group_msg_storage[user_id]
        await callback_query.message.edit_text("❌ Cancel kar diya.")
        await callback_query.answer()
        return
    
    # Saare groups list karo
    groups = []
    async for dialog in client.get_dialogs():
        if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            groups.append(dialog.chat)
    
    if not groups:
        await callback_query.answer("Koi group nahi mila!", show_alert=True)
        return
    
    if target == "all":
        await callback_query.answer("Sab groups mein bhej raha hoon...")
        success = 0
        failed = 0
        for chat in groups:
            try:
                if data and data["content_type"]:
                    ct = data["content_type"]
                    if ct == "text":
                        await client.send_message(chat.id, data["content_data"])
                    elif ct == "photo":
                        await client.send_photo(chat.id, photo=data["content_data"], caption=data["caption"])
                    elif ct == "video":
                        await client.send_video(chat.id, video=data["content_data"], caption=data["caption"])
                    elif ct == "animation":
                        await client.send_animation(chat.id, animation=data["content_data"], caption=data["caption"])
                    elif ct == "sticker":
                        await client.send_sticker(chat.id, sticker=data["content_data"])
                    elif ct == "document":
                        await client.send_document(chat.id, document=data["content_data"], caption=data["caption"])
                else:
                    await client.send_message(chat.id, "📢 Hela ka sandesh!")
                success += 1
            except Exception:
                failed += 1
            await asyncio.sleep(0.2)
        await callback_query.message.edit_text(f"✅ {success} groups mein bheja. Failed: {failed}")
        del group_msg_storage[user_id]
    else:
        # Single group
        try:
            chat_id = int(target)
            chat = await client.get_chat(chat_id)
            if data and data["content_type"]:
                ct = data["content_type"]
                if ct == "text":
                    await client.send_message(chat_id, data["content_data"])
                elif ct == "photo":
                    await client.send_photo(chat_id, photo=data["content_data"], caption=data["caption"])
                elif ct == "video":
                    await client.send_video(chat_id, video=data["content_data"], caption=data["caption"])
                elif ct == "animation":
                    await client.send_animation(chat_id, animation=data["content_data"], caption=data["caption"])
                elif ct == "sticker":
                    await client.send_sticker(chat_id, sticker=data["content_data"])
                elif ct == "document":
                    await client.send_document(chat_id, document=data["content_data"], caption=data["caption"])
            else:
                await client.send_message(chat_id, "📢 Hela ka sandesh!")
            await callback_query.message.edit_text(f"✅ {chat.title} mein message bhej diya.")
        except Exception as e:
            await callback_query.message.edit_text(f"❌ Error: {e}")
        del group_msg_storage[user_id]
    await callback_query.answer()

async def is_group_or_bot_admin(client, message):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        return True
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        try:
            member = await client.get_chat_member(message.chat.id, user_id)
            if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                return True
        except:
            pass
    return False

# --- OTHER COMMANDS (showid, adminlist, claim, help, usercommands, admincommands) ---
@app.on_message(filters.command("showid"))
async def showid_cmd(client, message):
    user = message.from_user
    chat = message.chat
    text = (
        f"👤 **M-O-R-T-A-L'S  I-D**\n"
        f"──────────────────\n"
        f"✨ **Naam:** {user.first_name}\n"
        f"🆔 **User ID:** `{user.id}`\n"
    )
    if chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        text += (
            f"\n🏰 **R-E-A-L-M  I-N-F-O**\n"
            f"──────────────────\n"
            f"🛡️ **Group:** {chat.title}\n"
            f"🆔 **Chat ID:** `{chat.id}`"
        )
    await message.reply_text(text)

@app.on_message(filters.command("adminlist"))
async def adminlist_cmd(client, message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return await message.reply_text("⛔ **Bewakoof! Ye DM hai, yahan ka raja sirf main aur mere Creator hain.**")
    owner_name = "Nahi Mila"
    admins = []
    async for member in client.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
        if member.status == enums.ChatMemberStatus.OWNER:
            owner_name = member.user.first_name
            if member.user.username: owner_name += f" (@{member.user.username})"
        else:
            admin_name = member.user.first_name
            if member.user.username: admin_name += f" (@{member.user.username})"
            admins.append(admin_name)
    text = (
        f"👑 **R-E-A-L-M  R-U-L-E-R-S** 👑\n"
        f"──────────────────\n"
        f"🌟 **Maha-Samrat (Owner):**\n{owner_name}\n\n"
        f"🛡️ **Senapati (Admins):**\n"
    )
    for adm in admins:
        text += f"• {adm}\n"
    await message.reply_text(text)

@app.on_message(filters.command("claim"))
async def claim_cmd(client, message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return await message.reply_text("⛔ **Ye realm (group) ka khazana hai, akele nahi lutega! Kisi group mein ja kar maango.**")
    chat_id = message.chat.id
    now = time.time()
    last_claim = group_claim_cooldown.get(chat_id, 0)
    if now - last_claim < 432000:
        rem = int(432000 - (now - last_claim))
        days = rem // 86400
        hrs = (rem % 86400) // 3600
        return await message.reply_text(f"⏳ **Lalach ki seema hoti hai!** Group ka khazana **{days} din aur {hrs} ghante** baad dubara khulega.")
    members_count = await client.get_chat_members_count(chat_id)
    reward = members_count * 50
    group_claim_cooldown[chat_id] = now
    set_bal(message.from_user.id, reward)
    await message.reply_text(
        f"🌟 **M-E-G-A  C-L-A-I-M!**\n"
        f"──────────────────\n"
        f"✨ **{message.from_user.first_name}** ne group ka gupt khazana dhoond liya!\n"
        f"👥 Group Members: {members_count}\n"
        f"💰 Inaam: **₹{reward}** aapke khate mein jama hue!\n\n"
        f"⏳ Agla khazana 5 din baad khulega."
    )

@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        bot_info = await client.get_me()
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("✨ Hela Se Akele Milo (DM)", url=f"https://t.me/{bot_info.username}?start=help")]])
        await message.reply_text("📜 **Mortal! Asgard ke raaz khule aam group mein nahi bataye jaate. Mujhe DM mein milo!**", reply_markup=btn)
    else:
        help_text = (
            "📜 **H-E-L-A'S  G-R-I-M-O-I-R-E (User Commands)**\n"
            "──────────────────\n"
            "Mortal, ye raaz sirf tumhare liye hain. Dhyan se padho:\n\n"
            "🎮 **GAMES & ECONOMY:**\n"
            "• `/bal` or `/profile` - Apna khazana, aura aur rank dekho.\n"
            "• `/daily` - Hela ki taraf se rozana ka bhatta (₹1200).\n"
            "• `/weekly` - Hafte ka bada khazana (₹5000).\n"
            "• `/rob` (Reply) - Dusre ka paisa looto.\n"
            "• `/kill` (Reply) - Kisi ki hatya karo aur ₹500 kamao.\n"
            "• `/dice <amt>` - 50% chance, 4x paisa wapas!\n"
            "• `/dart <amt>` - 66% chance jeetne ka.\n"
            "• `/revive` (Reply) - ₹700 dekar murde mein jaan dalo.\n"
            "• `/claim` - Group ka khazana (Har 5 din baad).\n"
            "• `/protection buy` - ₹500 mein 24 ghante ke liye maut se bacho.\n\n"
            "🏆 **LEADERBOARDS:**\n"
            "• `/toprich` - Asgard ke top 10 ameer log.\n"
            "• `/topkill` - Asgard ke top 10 khooni darinde.\n\n"
            "🎭 **FUN & ROLEPLAY:**\n"
            "• `/punch`, `/slap`, `/fight` - Dushmano se nipatne ke liye.\n"
            "• `/love`, `/kiss`, `/bite`, `/hug` - Pyaar aur nafrat ka khel.\n"
            "• `/couple` - Random do logo ko jodi banaye.\n"
            "• `/showid` - Apni aur group ki jankari nikalne ke liye.\n"
            "──────────────────\n"
            "✨ *ye hai sarri commands jyada help chaiye toh /start likho aur owner se contact karo*"
        )
        await message.reply_text(help_text)

@app.on_message(filters.command(["usercommands", "cmds"]))
async def usercmds_cmd(client, message):
    text = (
        "📜 **U-S-E-R  C-O-M-M-A-N-D-S**\n"
        "──────────────────\n"
        "Ye raaz har Mortal ke liye khule hain:\n"
        "`/profile`, `/daily`, `/weekly`, `/rob`, `/kill`\n"
        "`/dice`, `/dart`, `/protection`, `/revive`\n"
        "`/toprich`, `/topkill`, `/claim`\n"
        "`/punch`, `/slap`, `/fight`, `/hug`, `/love`, `/couple`\n"
        "`/showid`, `/adminlist`\n"
        "──────────────────\n"
        "Deep details ke liye `/help` type karo."
    )
    await message.reply_text(text)

@app.on_message(filters.command(["admincommands", "acmds"]))
async def admincmds_cmd(client, message):
    text = (
        "👑 **S-E-N-A-P-A-T-I  P-O-W-E-R-S**\n"
        "──────────────────\n"
        "Ye Hela ke khaas aadesh hain:\n"
        "`/ban`, `/unban`, `/kick`\n"
        "`/mute`, `/unmute`, `/warn`, `/unwarn`\n"
        "`/pin`, `/say`\n"
        "`/gift <amt>`, `/addkill <amt>`\n"
        "`/editdaily`, `/editweekly`\n"
        "`/guessmarvel` (Manual Hero Game)\n"
        "`/autoguess` (Start/Stop Auto Hero Game)\n"
        "`/groups` (Send message to selected groups)\n"
        "──────────────────\n"
        "⚠️ *Aam insaan inhe chhoone ki koshish na kare!*"
    )
    await message.reply_text(text)

# ==========================================
# --- MARVEL GUESS GAME (PRO LEVEL FIX) ---
# ==========================================

MARVEL_CHARS = {}
active_guess = {"chat_id": None, "name": None, "msg_id": None}
auto_guess_status = {}
adding_marvel_name = {}

@app.on_message(filters.command("marvel"))
async def add_marvel_cmd(client, message):
    if not await is_admin(message): return
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("❌ **Sirf photo par reply karke likho:** `/marvel`")
        raise StopPropagation
    file_id = message.reply_to_message.photo.file_id
    adding_marvel_name[message.from_user.id] = file_id
    await message.reply_text("✨ **Hela ko chitra mil gaya!**\nAb jaldi se Asgard ke is yoddha ka **Naam** likh kar bhejo (jaise: Iron Man):")
    raise StopPropagation

@app.on_message(filters.text, group=1)
async def master_text_listener(client, message):
    if not message.from_user: return
    uid = message.from_user.id
    chat_id = message.chat.id
    user_text = message.text.strip().lower()
    if uid in adding_marvel_name:
        file_id = adding_marvel_name.pop(uid)
        MARVEL_CHARS[user_text] = file_id
        await message.reply_text(
            f"✅ **S-A-V-E-D!**\n"
            f"──────────────────\n"
            f"🎮 **{user_text.title()}** ab Asgard ke Guess Game mein shamil ho gaya hai! ✨"
        )
        raise StopPropagation
    if active_guess.get("name") and chat_id == active_guess.get("chat_id"):
        correct_answer = active_guess["name"].lower()
        if user_text == correct_answer:
            set_bal(uid, 600)
            ans_name = active_guess["name"].title()
            active_guess["name"] = None
            active_guess["chat_id"] = None
            active_guess["msg_id"] = None
            await message.reply_text(
                f"🎉 **B-I-N-G-O!**\n"
                f"──────────────────\n"
                f"✨ **{message.from_user.first_name}** ki aankhein baaz ki tarah tez hain!\n"
                f"🦅 Sahi Jawab: **{ans_name}**\n"
                f"💰 Inaam: **₹600** aapke khate mein jama ho gaye!\n"
                f"⏳ Ab agle chitra ka intezaar karo."
            )
            raise StopPropagation

async def start_guess_game(client, chat_id):
    if not MARVEL_CHARS:
        try:
            await client.send_message(chat_id, "❌ **Khazana Khali Hai!**\nPehle Senapati (Admin) kisi photo par `/marvel` reply karke hero add karein.")
        except: pass
        return
    char_name, file_id = random.choice(list(MARVEL_CHARS.items()))
    try:
        msg = await client.send_photo(
            chat_id,
            photo=file_id,
            caption=(
                "🎮 **G-U-E-S-S  T-H-E  M-A-R-V-E-L  L-E-G-E-N-D!**\n"
                "──────────────────\n"
                "✨ Pehchano is dhurandhar ko aur sirf naam likh kar bhejo!\n"
                "💰 Sahi jawab dene wale ko milenge **₹600**!\n"
                "⏳ Tumhare paas sirf **10 Minute** hain."
            )
        )
        active_guess["chat_id"] = chat_id
        active_guess["name"] = char_name
        active_guess["msg_id"] = msg.id
        asyncio.create_task(guess_timer(client, chat_id, msg.id))
    except Exception as e:
        print(f"Guess game error: {e}")

async def guess_timer(client, chat_id, msg_id):
    await asyncio.sleep(600)
    if active_guess.get("msg_id") == msg_id and active_guess.get("name"):
        old_name = active_guess.get("name", "Unknown").title()
        active_guess["name"] = None
        active_guess["chat_id"] = None
        active_guess["msg_id"] = None
        try:
            await client.delete_messages(chat_id, msg_id)
            await client.send_message(chat_id, f"⏳ **Waqt khatam!** Kisi ne Asgard ke yoddha ko nahi pehchana.\n🦅 Wo **{old_name}** tha! Khel samapt! 💀")
        except: pass

# guessmarvel now available to ALL users (no admin check)
@app.on_message(filters.command("guessmarvel"))
async def guessmarvel_cmd(client, message):
    # All users can start the game in groups
    if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("❌ Ye command sirf group mein kaam karti hai.")
    await start_guess_game(client, message.chat.id)

# autoguess only in groups and only for group admins or bot admins
async def auto_guess_loop(client, chat_id):
    while auto_guess_status.get(chat_id, False):
        await asyncio.sleep(1500)
        if auto_guess_status.get(chat_id, False):
            await start_guess_game(client, chat_id)

@app.on_message(filters.command("autoguess"))
async def toggle_autoguess(client, message):
    # Only group admins or bot admins can toggle autoguess, and only in groups
    if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("❌ Autoguess sirf group mein activate kar sakte ho.")
    if not await is_group_or_bot_admin(client, message):
        return await message.reply_text("⛔ Sirf group admin ya bot owner autoguess toggle kar sakte hain.")
    chat_id = message.chat.id
    if auto_guess_status.get(chat_id, False):
        auto_guess_status[chat_id] = False
        await message.reply_text("🛑 **Auto-Guess Deactivated!** Ab har 25 minute mein game nahi aayega.")
    else:
        auto_guess_status[chat_id] = True
        await message.reply_text("✅ **Auto-Guess Activated!** Ab Asgardian jadu se har 25 minute mein ek naya photo aayega! ✨")
        asyncio.create_task(auto_guess_loop(client, chat_id))

# ==========================================
# --- VOICE COMMAND (unchanged) ---
@app.on_message(filters.command(["calvin", "speak", "voice"]))
async def voice_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply_text("🗣️ **Kya bolna hai? Likh kar batao!**\nExample: `/calvin Hela is the true queen of Asgard!`")
    text_to_speak = message.text.split(None, 1)[1]
    status_msg = await message.reply_text("✨ Hela apne shabdon ko aawaz de rahi hai...")
    try:
        tts = gTTS(text=text_to_speak, lang='hi', tld='co.in')
        audio_file = f"voice_{message.from_user.id}.ogg"
        tts.save(audio_file)
        await client.send_voice(
            chat_id=message.chat.id,
            voice=audio_file,
            caption=f"🗣️ **{message.from_user.first_name} ki Aawaz!**",
            reply_to_message_id=message.reply_to_message.id if message.reply_to_message else message.id
        )
        os.remove(audio_file)
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text("❌ **Gala kharab hai! Aawaz nahi nikal rahi.**")
        print(f"Voice Error: {e}")

# --- RENDER PORT FIX ---
import threading
from flask import Flask

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "✨ Asgard is Safe! Hela is Alive and Ruling! 👑"

def run_web():
    web_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

threading.Thread(target=run_web).start()

# Start bot
app.run()
