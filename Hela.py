import os
import random
import time
import asyncio
# --- ASYNCIO LOOP FIX (Python ki bewakoofi ka ilaaj) ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
# --------------------------------------------------------

from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from groq import Groq

# Render/Environment Variables se keys uthana
BOT_TOKEN = os.environ.get("T")
GROQ_API_KEY = os.environ.get("G")
OWNER_ID = 8099984863
OWNER_USERNAME = "Carol_616"

API_ID = int(os.environ.get("A"))
API_HASH = os.environ.get("H")
app = Client("HelaBot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
groq_client = Groq(api_key=GROQ_API_KEY)

# Database (For Demo: In-memory dictionary)
economy = {} 
loans = {}
# --- ADMIN IDs & NEW DATABASE ---
ADMIN_IDS = [7574760011, 8099984863]
warns = {}
kills_db = {}

def add_kills_to_user(uid, amt):
    kills_db[uid] = kills_db.get(uid, 0) + amt

# --- TIME & PROTECTION DATABASE ---
protection_db = {}
cooldowns = {"daily": {}, "weekly": {}}
rewards = {"daily": 1200, "weekly": 5000}

# Secret Admin Protection Logic
def is_protected(uid):
    # Admins are ALWAYS protected secretly
    if uid in ADMIN_IDS:
        return True 
    # Normal users check
    if uid in protection_db:
        if time.time() < protection_db[uid]:
            return True
        else:
            del protection_db[uid] # Time over
    return False

# --- Helper Functions ---
def get_bal(uid): return economy.get(uid, 1000)
def set_bal(uid, amt): economy[uid] = get_bal(uid) + amt

# Global Rank Calculation
def get_rank(uid):
    sorted_eco = sorted(economy.items(), key=lambda x: x[1], reverse=True)
    for index, (user, bal) in enumerate(sorted_eco):
        if user == uid:
            return index + 1
    return "Unranked"

# --- PERFECT START COMMAND ---
@app.on_message(filters.command("start"))
async def start(client, message):
    
    # 1. Dhyan do: Agar koi Group ke "Help" button se aayega, SIRF TABHI ye line chalegi
    if len(message.command) > 1 and message.command[1] == "help":
        return await help_cmd(client, message) # Ye user ko direct help menu dega
        
    # 2. Agar user normally DM mein aaya hai aur Start dabaya hai, toh ye chalega:
    user_name = message.from_user.first_name
    text = (
        f"✨ Hieeeee {user_name}!\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💗 **Simple, smart & friendly chat bot**\n\n"
        "**What can I do?**\n"
        "• 💬 Fun & Easy Conversations\n"
        "• 🎮 Awesome Games & Economy\n"
        "• 🛡️ Group Management & Safety\n"
        "• ✨ A Safe & Smooth Experience\n\n"
        "✦ **Choose An Option Below :**"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me To Group", url=f"http://t.me/{client.me.username}?startgroup=true")],
        [InlineKeyboardButton("👤 Owner", url=f"https://t.me/Carol_616")] # Owner link fixed
    ])
    
    await message.reply_text(text, reply_markup=buttons)
    
# --- Updated Kill System ---
@app.on_message(filters.command("kill"))
async def kill_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply_text("⚔️ **Kise maut ke ghaat utarna hai? Pehle kisi ke message par reply toh karo!**")
    
    victim = message.reply_to_message.from_user
    killer = message.from_user

    # Khud ko maarne se rokne ke liye
    if victim.id == killer.id:
        return await message.reply_text("💀 **Khudkhushi paap hai! Hela ko ye pasand nahi. Kisi aur ko chuno!**")

    # Protection Check (Admins are secretly safe here too)
    if is_protected(victim.id):
        return await message.reply_text(
            f"🛡️ **S-H-A-K-T-I-H-E-E-N  P-R-A-H-A-A-R!**\n\n"
            f"**{victim.first_name}** Hela ki sharan mein hai (Protected). "
            f"Tumhara hathiyar iska baal bhi banka nahi kar sakta! ⚡"
        )

    # Baki ka logic (Paisa aur Kill count badhana)
    set_bal(killer.id, 500)
    add_kills_to_user(killer.id, 1) # Profile me kill count add karne ke liye
    
    total_kills = kills_db.get(killer.id, 0)

    await message.reply_text(
        f"💀 **H-E-L-A'S  W-R-A-T-H!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🩸 **{killer.first_name}** ki behremi se **{victim.first_name}** ka kaam tamam diya!\n"
        f"💰 Inam: **₹500** aapke khate mein jama ho gaye.\n"
        f"⚔️ **Total Kills:** {total_kills}\n"
        f"✨ Aae aise hi aghe badho "
    )

# --- Updated Rob System (ZERO BALANCE LIMIT) ---
@app.on_message(filters.command("rob"))
async def rob_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply_text("💰 **Lootne ke liye kisi ke message par reply karein!**")
    
    target = message.reply_to_message.from_user
    robber_id = message.from_user.id

    # Protection Check
    if is_protected(target.id):
        return await message.reply_text(
            f"🛡️ **C-H-O-R-I N-A-A-K-A-A-M!**\n\n"
            f"**{target.first_name}** par Hela ka kaala kavach hai! "
            f"Tumhari himmat kaise hui unke khazane ki taraf aankh uthane ki? ⚡"
        )
    
    # Khud ko lootne se rokne ke liye
    if target.id == robber_id:
        return await message.reply_text("💀 **Apni hi jeb katoge kya? Murkh!**")

    target_bal = get_bal(target.id)
    
    # Agar target pehle se hi 0 par hai
    if target_bal <= 0:
        return await message.reply_text(
            f"💀 **{target.first_name} ke paas ek futi kaudi nahi hai!**\n"
            f"Hela murdon aur bhikariyon ko nahi loot-ti. Jao kisi ameer ko dhoondo!"
        )

    # Calculate loot amount (min 0, max 40000)
    loot = random.randint(0, 40000)
    
    # Agar loot ka amount uske total balance se zyada hai, toh bas utna hi looto jitna uske paas hai (taki minus me na jaye)
    if loot > target_bal:
        loot = target_bal

    # Paison ka transaction
    set_bal(target.id, -loot)
    set_bal(robber_id, loot)
    
    # Beizzati wala message (Agar kangal kar diya ho)
    extra_msg = "✨ Hela is chori par muskura rahi hai..."
    if get_bal(target.id) == 0:
        extra_msg = "💸 **Tumne ishe aakhiri chillar tak loot liya! Ab ye puri tarah kangal ho chuka hai!** 💀"

    await message.reply_text(
        f"🧤 **H-E-I-S-T S-U-C-C-E-S-S-F-U-L!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👣 **{message.from_user.first_name}** ne badi behremi se **{target.first_name}** ki jeb se **₹{loot}** uda liye!\n\n"
        f"{extra_msg}"
    )

# --- Loan System ---
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

# --- Groq AI (Latest Llama-3.3-70b-versatile) ---
@app.on_message(filters.text & ~filters.regex(r"^/"), group=4)
async def hela_chat(client, message):
    
    # --- Hela kab bolegi? ---
    bot = await client.get_me()
    msg_text = message.text.lower()
    
    # Check: Kya ye Private DM hai ya Group?
    is_private = message.chat.type == enums.ChatType.PRIVATE
    
    # Check 1: Kya kisi ne bot ke message par reply kiya hai?
    is_reply = message.reply_to_message and message.reply_to_message.from_user.id == bot.id
    # Check 2: Kya message mein "hela" likha hai ya bot ka username mention kiya hai?
    is_mentioned = "hela" in msg_text or (bot.username and f"@{bot.username.lower()}" in msg_text)
    
    # NAYA LOGIC: Agar Group hai, toh bina mention/reply ke chup rahegi. 
    # Par agar DM (Private) hai, toh har baat ka jawab degi!
    if not is_private and not (is_reply or is_mentioned):
        return 
    # ------------------------

    # System prompt
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
    
# --- LEGENDARY FUN COMMANDS: PUNCH, SLAP, FIGHT ---

@app.on_message(filters.command("punch"))
async def punch_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply_text("✨ **Kise maut ka swaad chakhana hai? Pehle reply toh karo!**")
    
    victim = message.reply_to_message.from_user.first_name
    sender = message.from_user.first_name
    
    punches = [
        f"⚡ **{sender}** ne apni puri taqat se **{victim}** ke jabde par 'Necro-Punch' mara! Haddiyan tootne ki awaaz aayi... 🦴",
        f"🥊 **{sender}** ka ek mukka aur **{victim}** seedha Asgard se dharti par ja gira!",
        f"💥 Ek jordar prahaar! **{sender}** ne **{victim}** ko hawa mein uchhaal diya!"
    ]
    await message.reply_text(random.choice(punches))

@app.on_message(filters.command("slap"))
async def slap_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply_text("✨ **Meri deni hui shaktiyon ka upyog sahi jagah karo! Reply to someone!**")
    
    victim = message.reply_to_message.from_user.first_name
    sender = message.from_user.first_name
    
    await message.reply_text(
        f"🖐️ **S-L-A-P!**\n\n**{sender}** ne **{victim}** ko itna zor se thappad mara ki 'Multiverse' ke saare sitare nazar aa gaye! 💫"
    )

@app.on_message(filters.command("fight"))
async def fight_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply_text("⚔️ **Akele kisse ladoge? Kisi gunehgaar par reply karo!**")
    
    victim = message.reply_to_message.from_user.first_name
    sender = message.from_user.first_name
    
    # Randomly deciding winner
    winner = random.choice([sender, victim])
    loser = victim if winner == sender else sender
    
    fight_text = (
        f"⚔️ **MAUT KA MAIDAN-E-JANG** ⚔️\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 **{sender}** aur **{victim}** ke beech ek pralaykaari yuddh shuru hua!\n"
        f"Talwarein takrayi, bijli kadki aur anth mein...\n\n"
        f"🏆 **{winner}** ne **{loser}** ko ghutno par la diya aur vijay prapt ki! 🔥"
    )
    await message.reply_text(fight_text)

# --- LEGENDARY DART (70% WIN CHANCE & PRO STYLE) ---

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

    # Animation feel (optional delay)
    status = await message.reply_text("🎯 **Hela apni talwar nishane par phek rahi hai...**")
    
    # 70% Win Logic
    win_chance = random.randint(1, 100)
    
    if win_chance <= 70:
        win_amt = bet_amount * 2
        set_bal(user_id, bet_amount) # Adding the profit
        await status.edit_text(
            f"🎯 **BULLSEYE!**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 **{message.from_user.first_name}**, tumhara nishana achook hai!\n"
            f"💰 Aapne **₹{bet_amount}** dao par lagaye aur **₹{win_amt}** jeet liye!\n"
            f"✨ Hela tumse prasann hui!"
        )
    else:
        set_bal(user_id, -bet_amount) # Losing money
        await status.edit_text(
            f"🎯 **MISSED!**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💀 **Afsos!** Nishana chook gaya aur tumhara naseeb bhi!\n"
            f"🔥 **₹{bet_amount}** mitti mein mil gaye. Agli baar dhyan se!"
        )

# --- SECURITY CHECK HELPER ---
async def is_admin(message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply_text("⛔ **Aukaat mein raho Mortal!** Ye shaktiyan sirf Hela ke khaas Senapatiyon ke liye hain.")
        return False
    return True

# --- MODERATION COMMANDS ---

@app.on_message(filters.command("ban"))
async def ban_cmd(client, message):
    if not await is_admin(message): return
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
    if not await is_admin(message): return
    if not message.reply_to_message:
        return await message.reply_text("✨ **Kise azaad karna hai? Reply karo!**")
    
    victim = message.reply_to_message.from_user
    await client.unban_chat_member(message.chat.id, victim.id)
    await message.reply_text(f"✨ **R-E-B-I-R-T-H!**\n\n**{victim.first_name}** ke gunah maaf hue. Swarg mein wapas swagat hai! 🕊️")

@app.on_message(filters.command("kick"))
async def kick_cmd(client, message):
    if not await is_admin(message): return
    if not message.reply_to_message:
        return await message.reply_text("👢 **Kise dhakke maar ke nikalna hai? Reply karo!**")
    
    victim = message.reply_to_message.from_user
    await client.ban_chat_member(message.chat.id, victim.id)
    await client.unban_chat_member(message.chat.id, victim.id) # Unbanning immediately acts as a kick
    await message.reply_text(f"👢 **K-I-C-K-E-D!**\n\n**{victim.first_name}** ko Hela ne ek jordar laat maari aur wo group se bahar ja gira! 💥")

@app.on_message(filters.command("mute"))
async def mute_cmd(client, message):
    if not await is_admin(message): return
    if not message.reply_to_message:
        return await message.reply_text("🤐 **Kisiki zubaan kaatni hai? Reply karo!**")
    
    victim = message.reply_to_message.from_user
    await client.restrict_chat_member(message.chat.id, victim.id, ChatPermissions(can_send_messages=False))
    await message.reply_text(f"🤐 **S-I-L-E-N-C-E!**\n\n**{victim.first_name}** ki awaaz chheen li gayi hai. Ab iski cheekh koi nahi sunega! 🤫")

@app.on_message(filters.command("unmute"))
async def unmute_cmd(client, message):
    if not await is_admin(message): return
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
    if not await is_admin(message): return
    if not message.reply_to_message:
        return await message.reply_text("⚠️ **Kise chetawani deni hai? Reply karo!**")
    
    victim = message.reply_to_message.from_user
    vid = victim.id
    warns[vid] = warns.get(vid, 0) + 1
    
    await message.reply_text(f"⚠️ **W-A-R-N-I-N-G!**\n\n**{victim.first_name}**, tumhari harkatein maut ko dawat de rahi hain!\n🔴 **Total Warns:** {warns[vid]}\nSudhar jao warna agla raasta seedha narak jata hai! 🔥")

@app.on_message(filters.command("pin"))
async def pin_cmd(client, message):
    if not await is_admin(message): return
    if not message.reply_to_message:
        return await message.reply_text("📌 **Hela ka kaunsa farmaan pin karna hai? Reply karo!**")
    
    await message.reply_to_message.pin()
    await message.reply_text("📌 **F-A-R-M-A-A-N!**\n\nHela ka aadesh aasman par likh diya gaya hai! Sab dhyaan dein! 📜")

@app.on_message(filters.command("say"))
async def say_cmd(client, message):
    if not await is_admin(message): return
    if len(message.command) < 2:
        return await message.reply_text("🗣️ **Kya farmaan jaari karna hai? Likh kar batao!**")
    
    text_to_say = message.text.split(None, 1)[1]
    await message.delete() # Admin ka message delete karke bot khud bolega
    await client.send_message(message.chat.id, text_to_say)

# --- ECONOMY / GOD COMMANDS FOR ADMINS ---

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
    set_bal(victim.id, amount) # Humara pichla balance function call ho raha hai
    
    await message.reply_text(
        f"👑 **R-O-Y-A-L B-O-U-N-T-Y!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
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
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💀 Hela ne **{victim.first_name}** ki talwar ko aur bhayanak bana diya hai!\n"
        f"⚔️ **+{amount}** Kills add kar diye gaye hain. \n"
        f"🩸 **Total Kills:** {total_kills}"
    )

# --- BAL / PROFILE COMMAND ---
@app.on_message(filters.command(["bal", "profile"]))
async def profile_cmd(client, message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    uid = target.id
    
    bal = get_bal(uid)
    kills = kills_db.get(uid, 0)
    rank = get_rank(uid)
    
    # Protection Status Check
    if is_protected(uid):
        if uid in protection_db and time.time() < protection_db[uid]:
            rem = int(protection_db[uid] - time.time())
            prot_status = f"🛡️ Active ({rem // 3600}h {(rem % 3600) // 60}m left)"
        else:
            # Admins ki protection secret rakhne ke liye sirf "Active" dikhayega
            prot_status = "🛡️ Active (Hela's Dark Magic ✨)"
    else:
        prot_status = "❌ Inactive (Khatre mein hai! 💀)"

    text = (
        f"👑 **P-R-O-F-I-L-E : {target.first_name}** 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 **Khazana (Balance):** ₹{bal}\n"
        f"💀 **Maut ka Aankda (Kills):** {kills}\n"
        f"🌍 **Global Rank:** #{rank}\n"
        f"🛡️ **Protection:** {prot_status}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    await message.reply_text(text)

# --- PROTECTION BUY COMMAND ---
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
        protection_db[uid] = time.time() + (24 * 3600) # 24 Hours in seconds
        return await message.reply_text("🛡️ **A-U-R-A A-C-T-I-V-A-T-E-D!**\n\n✨ Hela ne tumse ₹500 le liye hain! Agle 24 ghante tak koi tumhe maar ya loot nahi sakta! Aish karo! 👑")
    else:
        await message.reply_text("❌ **Tumhari jaan khatre mein hai!** Koi bhi tumhe loot ya maar sakta hai.\n\n🛡️ **24 Ghante ki Protection** ke liye ₹500 lagenge.\nType karo: `/protection buy`")

# --- DAILY & WEEKLY REWARDS ---
@app.on_message(filters.command("daily"))
async def daily_cmd(client, message):
    uid = message.from_user.id
    now = time.time()
    last_claimed = cooldowns["daily"].get(uid, 0)
    
    if now - last_claimed < 86400: # 24 hrs cooldown
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
    
    if now - last_claimed < 604800: # 7 days cooldown
        rem = int(604800 - (now - last_claimed))
        d = rem // 86400
        h = (rem % 86400) // 3600
        return await message.reply_text(f"⏳ **Sabar karo Mortal!** Weekly khazana khulne mein waqt hai. ({d}d {h}h left) 💀")
    
    amt = rewards["weekly"]
    cooldowns["weekly"][uid] = now
    set_bal(uid, amt)
    await message.reply_text(f"🌟 **W-E-E-K-L-Y T-R-E-A-S-U-R-E!**\n\n✨ Asgard ka khazana khul gaya hai! Tumhe **₹{amt}** ka maalik bana diya gaya hai! 🎉")

# --- ADMIN: EDIT REWARDS ---
@app.on_message(filters.command("editdaily"))
async def editdaily_cmd(client, message):
    if not await is_admin(message): return
    if len(message.command) < 2: return await message.reply_text("✍️ Nayi raqam batao! (e.g., `/editdaily 2000`)")
    try:
        rewards["daily"] = int(message.command[1])
        await message.reply_text(f"✅ **Farmaan Jaari!** Daily reward ab **₹{rewards['daily']}** hai.")
    except:
        pass

@app.on_message(filters.command("editweekly"))
async def editweekly_cmd(client, message):
    if not await is_admin(message): return
    if len(message.command) < 2: return await message.reply_text("✍️ Nayi raqam batao! (e.g., `/editweekly 10000`)")
    try:
        rewards["weekly"] = int(message.command[1])
        await message.reply_text(f"✅ **Farmaan Jaari!** Weekly reward ab **₹{rewards['weekly']}** hai.")
    except:
        pass

# --- REVIVE COMMAND (700 Rs) ---
@app.on_message(filters.command("revive"))
async def revive_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply_text("✨ **Kise maut ke muh se wapas lana hai? Reply karo!**")
    
    target = message.reply_to_message.from_user
    healer = message.from_user
    
    # Khud ko revive karne se rokna (Optional, but logical)
    if target.id == healer.id:
        return await message.reply_text("💀 **Khud ko revive nahi kar sakte! Kis aur se madad mango.**")

    # 700 Rs balance check
    if get_bal(healer.id) < 700:
        return await message.reply_text("💸 **Kangal!** Revive karne ki keemat **₹700** hai. Pehle Asgard ka tax chukao!")
        
    set_bal(healer.id, -700) # Cutting fees
    
    await message.reply_text(
        f"🌟 **R-E-V-I-V-A-L  M-A-G-I-C!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ **{healer.first_name}** ne **₹700** ki aahuti dekar **{target.first_name}** ki aatma ko Valhalla se wapas bula liya hai!\n"
        f"🕊️ Naya jeevan mubarak ho Mortal!"
    )

# --- MARVEL GUESS GAME DATABASE & LOGIC ---
MARVEL_CHARS = {
    "iron man": "https://i.annihil.us/u/prod/marvel/i/mg/9/c0/527bb7b37ff55/standard_xlarge.jpg",
    "thor": "https://i.annihil.us/u/prod/marvel/i/mg/d/d0/5269657a74350/standard_xlarge.jpg",
    "spider man": "https://i.annihil.us/u/prod/marvel/i/mg/3/50/526548a343e4b/standard_xlarge.jpg",
    "captain america": "https://i.annihil.us/u/prod/marvel/i/mg/3/50/537ba56d31087/standard_xlarge.jpg",
    "hulk": "https://i.annihil.us/u/prod/marvel/i/mg/5/a0/538615ca33ab0/standard_xlarge.jpg",
    "black widow": "https://i.annihil.us/u/prod/marvel/i/mg/f/30/50fecad1f395b/standard_xlarge.jpg",
    "hela": "https://i.annihil.us/u/prod/marvel/i/mg/4/20/546a1617e91d5/standard_xlarge.jpg"
}

active_guess = {"chat_id": None, "name": None, "msg_id": None}
auto_guess_status = {}
pending_marvel = {} # {admin_id: file_id}

# Game Start Function
async def start_guess_game(client, chat_id):
    char_name, char_img = random.choice(list(MARVEL_CHARS.items()))
    
    try:
        msg = await client.send_photo(
            chat_id, 
            photo=char_img, 
            caption=(
                "🎮 **G-U-E-S-S  T-H-E  M-A-R-V-E-L  L-E-G-E-N-D!**\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "✨ Pehchano is dhurandhar ko aur sirf naam likh kar bhejo!\n"
                "💰 Sahi jawab dene wale ko milenge **₹600**!\n"
                "⏳ Tumhare paas sirf **10 Minute** hain."
            )
        )
        active_guess["chat_id"] = chat_id
        active_guess["name"] = char_name
        active_guess["msg_id"] = msg.id
        
        # 10 minute delete timer start karein
        asyncio.create_task(guess_timer(client, chat_id, msg.id))
    except Exception as e:
        print(f"Guess game error: {e}")

# Timer Function (10 minutes)
async def guess_timer(client, chat_id, msg_id):
    await asyncio.sleep(600) # 10 minutes = 600 seconds
    if active_guess["msg_id"] == msg_id: # Agar abhi bhi wahi game chal raha hai
        active_guess["name"] = None # Game over
        try:
            await client.delete_messages(chat_id, msg_id)
            await client.send_message(chat_id, "⏳ **Waqt khatam!** Kisi ne Marvel Hero ko nahi pehchana. Khel samapt! 💀")
        except:
            pass

# --- ADMIN COMMAND: START/STOP 25 MIN AUTO LOOP ---
async def auto_guess_loop(client, chat_id):
    while auto_guess_status.get(chat_id, False):
        await asyncio.sleep(1500) # Wait 25 minutes
        if auto_guess_status.get(chat_id, False):
            await start_guess_game(client, chat_id)

@app.on_message(filters.command("autoguess"))
async def toggle_autoguess(client, message):
    if not await is_admin(message): return
    chat_id = message.chat.id
    
    if auto_guess_status.get(chat_id, False):
        auto_guess_status[chat_id] = False
        await message.reply_text("🛑 **Auto-Guess Deactivated!** Ab har 25 minute mein game nahi aayega.")
    else:
        auto_guess_status[chat_id] = True
        await message.reply_text("✅ **Auto-Guess Activated!** Ab Asgardian jadu se har 25 minute mein ek naya photo aayega! ✨")
        asyncio.create_task(auto_guess_loop(client, chat_id))

# --- ADMIN COMMAND: MANUAL GUESS OR ADD NEW ---
@app.on_message(filters.command("guessmarvel"))
async def manual_guess_cmd(client, message):
    if not await is_admin(message): return
    
    # 1. Admin Replying to a Photo to ADD to Database
    if message.reply_to_message and message.reply_to_message.photo:
        file_id = message.reply_to_message.photo.file_id
        pending_marvel[message.from_user.id] = file_id
        return await message.reply_text("✨ **Hela ko naya chitra mil gaya!**\nAb Asgard ke is naye yoddha ka **Naam** likh kar bhejo:")
        
    # 2. Normal Game Trigger (Starts the game in group)
    await start_guess_game(client, message.chat.id)

# --- Marvel Name Listener (Game Checker) ---
@app.on_message(filters.text, group=1)
async def check_guess_answer(client, message):
    if active_guess["name"] and message.chat.id == active_guess["chat_id"]:
        if message.text.lower().strip() == active_guess["name"].lower():
            set_bal(message.from_user.id, 600) 
            ans_name = active_guess["name"].title()
            active_guess["name"] = None 
            await message.reply_text(f"🎉 **B-I-N-G-O!**\n✨ **{message.from_user.first_name}** ne pehchana: **{ans_name}**.\n💰 **₹600** jeete!")

# --- Marvel Admin Add Character Listener ---
@app.on_message(filters.text, group=3) # Group 3 ensures it doesn't crash Groq AI
async def catch_marvel_name_listener(client, message):
    uid = message.from_user.id
    if uid in pending_marvel:
        char_name = message.text.lower().strip()
        file_id = pending_marvel.pop(uid)
        
        # Save to Database
        MARVEL_CHARS[char_name] = file_id
        
        await message.reply_text(
            f"✅ **M-A-S-T-E-R-P-I-E-C-E  S-A-V-E-D!**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎮 **{char_name.title()}** ab Asgard ke Guess Game mein shamil ho gaya hai!\n"
            f"Agli baar jab game aayega, ye yoddha zaroor dikhega! ✨"
        )

# --- TOP RICH LEADERBOARD ---
@app.on_message(filters.command(["toprich", "rich"]))
async def toprich_cmd(client, message):
    if not economy:
        return await message.reply_text("📜 **Sab ke sab bhikari hain! Asgard ka khazana khali hai.**")
    
    # Sort users by balance (Top 10)
    sorted_eco = sorted(economy.items(), key=lambda x: x[1], reverse=True)[:10]
    
    text = "💰 **T-O-P  10  R-I-C-H-E-S-T** 💰\n━━━━━━━━━━━━━━━━━━━━\n"
    
    for i, (uid, bal) in enumerate(sorted_eco):
        try:
            user = await client.get_users(uid)
            name = user.first_name
        except:
            name = f"Mysterious Mortal ({uid})"
            
        text += f"**{i+1}.** {name} — **₹{bal}**\n"
        
    text += "━━━━━━━━━━━━━━━━━━━━\n✨ Hela inki daulat par nazar rakhe hue hai..."
    await message.reply_text(text)

# --- TOP KILL LEADERBOARD ---
@app.on_message(filters.command(["topkill", "killers"]))
async def topkill_cmd(client, message):
    if not kills_db:
        return await message.reply_text("📜 **Asgard mein abhi tak shanti hai! Kisi ne kisi ka khoon nahi bahaya.**")
    
    # Sort users by kills (Top 10)
    sorted_kills = sorted(kills_db.items(), key=lambda x: x[1], reverse=True)[:10]
    
    text = "💀 **T-O-P  10  K-I-L-L-E-R-S** 💀\n━━━━━━━━━━━━━━━━━━━━\n"
    
    for i, (uid, kills) in enumerate(sorted_kills):
        if kills > 0: # Sirf unhe dikhao jinhone at least 1 kill kiya ho
            try:
                user = await client.get_users(uid)
                name = user.first_name
            except:
                name = f"Shadow Assassin ({uid})"
                
            text += f"**{i+1}.** {name} — **{kills} Kills** ⚔️\n"
        
    text += "━━━━━━━━━━━━━━━━━━━━\n✨ Hela inke khooni khel se bohot prasann hai..."
    await message.reply_text(text)

# --- ROLEPLAY MEDIA VAULT ---
rp_media = {"love": [], "kiss": [], "bite": [], "hug": []}

@app.on_message(filters.command("love"))
async def love_cmd(client, message):
    # 1. Admin Adding Media to Vault
    if await is_admin(message) and message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.animation):
        msg = message.reply_to_message
        media_type = "photo" if msg.photo else "animation"
        file_id = msg.photo.file_id if msg.photo else msg.animation.file_id
        rp_media["love"].append({"type": media_type, "id": file_id})
        return await message.reply_text("✨ **V-A-U-L-T  U-P-D-A-T-E-D!**\nYe chitra `/love` ke khazane mein save ho gaya hai! 🖤")
    
    # 2. Normal Command Usage
    if not message.reply_to_message:
        return await message.reply_text("🖤 **Kisse prem jatana hai? Reply karo!**")
        
    sender = message.from_user.first_name
    target = message.reply_to_message.from_user.first_name
    love_percent = random.randint(10, 100)
    
    text = (
        f"🖤 **A-S-G-A-R-D-I-A-N  R-O-M-A-N-C-E** 🖤\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ **{sender}** aur **{target}** ke beech ka rishta Hela khud dekh rahi hai...\n"
        f"💘 **Love Match:** {love_percent}%\n"
        f"{'🔥 Maut bhi inhe alag nahi kar sakti!' if love_percent > 80 else '💀 Isse behtar toh akele marna hai!'}"
    )
    
    # Send Media if Vault is not empty
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

# --- NAYE VARIABLES DATABASE ---
pending_dice = {}  # {user_id: bet_amount}
group_claim_cooldown = {}  # {chat_id: timestamp}

# 🎲 1. DICE COMMAND (50% Win, 4x Payout)
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
    
    # Inline Buttons for 1 to 6
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
    
    # 50% Win Probability
    is_win = random.choice([True, False])
    
    if is_win:
        rolled = chosen_num
        set_bal(uid, bet * 4)  # 4x Payout
        result_text = f"🎉 **J-A-C-K-P-O-T!**\nTumhari kismat chamak gayi! Tumne **₹{bet * 4}** jeet liye! ✨"
    else:
        # Koi dusra random number aayega
        rolled = random.choice([x for x in range(1, 7) if x != chosen_num])
        set_bal(uid, -bet)  # Bet cut
        result_text = f"💀 **L-O-S-S!**\nTumne apna daav (**₹{bet}**) kho diya. Hela tumpar hass rahi hai!"

    text = (
        f"🎲 **H-E-L-A'S  D-I-C-E**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Tumne chuna: **{chosen_num}**\n"
        f"🎲 Dice par aaya: **{rolled}**\n\n"
        f"{result_text}"
    )
    await callback_query.message.edit_text(text)


# 👤 2. SHOW ID COMMAND
@app.on_message(filters.command("showid"))
async def showid_cmd(client, message):
    user = message.from_user
    chat = message.chat
    
    text = (
        f"👤 **M-O-R-T-A-L'S  I-D**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ **Naam:** {user.first_name}\n"
        f"🆔 **User ID:** `{user.id}`\n"
    )
    
    if chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        text += (
            f"\n🏰 **R-E-A-L-M  I-N-F-O**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛡️ **Group:** {chat.title}\n"
            f"🆔 **Chat ID:** `{chat.id}`"
        )
    await message.reply_text(text)


# 👑 3. ADMIN LIST COMMAND
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
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌟 **Maha-Samrat (Owner):**\n{owner_name}\n\n"
        f"🛡️ **Senapati (Admins):**\n"
    )
    for adm in admins:
        text += f"• {adm}\n"
        
    await message.reply_text(text)


# 💰 4. CLAIM COMMAND (Group Members * 50, 5 Days Reset)
@app.on_message(filters.command("claim"))
async def claim_cmd(client, message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return await message.reply_text("⛔ **Ye realm (group) ka khazana hai, akele nahi lutega! Kisi group mein ja kar maango.**")
    
    chat_id = message.chat.id
    now = time.time()
    last_claim = group_claim_cooldown.get(chat_id, 0)
    
    # 5 Days = 432,000 seconds
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
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ **{message.from_user.first_name}** ne group ka gupt khazana dhoond liya!\n"
        f"👥 Group Members: {members_count}\n"
        f"💰 Inaam: **₹{reward}** aapke khate mein jama hue!\n\n"
        f"⏳ Agla khazana 5 din baad khulega."
    )


# 📜 5. HELP COMMAND (Redirects to DM)
@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        bot_info = await client.get_me()
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("✨ Hela Se Akele Milo (DM)", url=f"https://t.me/{bot_info.username}?start=help")]])
        await message.reply_text("📜 **Mortal! Asgard ke raaz khule aam group mein nahi bataye jaate. Mujhe DM mein milo!**", reply_markup=btn)
    else:
        # Direct DM Help text
        help_text = (
            "📜 **H-E-L-A'S  G-R-I-M-O-I-R-E (User Commands)**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Mortal, ye raaz sirf tumhare liye hain. Dhyan se padho:\n\n"
            "🎮 **GAMES & ECONOMY:**\n"
            "• `/bal` or `/profile` - Apna khazana, aura aur rank dekho.\n"
            "• `/daily` - Hela ki taraf se rozana ka bhatta (₹1200).\n"
            "• `/weekly` - Hafte ka bada khazana (₹5000).\n"
            "• `/rob` (Reply) - Dusre ka paisa looto.\n"
            "• `/kill` (Reply) - Kisi ki hatya karo aur ₹500 kamao.\n"
            "• `/dice <amt>` - 50% chance, 4x paisa wapas!\n"
            "• `/dart <amt>` - 70% chance jeetne ka.\n"
            "• `/revive` (Reply) - ₹700 dekar murde mein jaan dalo.\n"
            "• `/claim` - Group ka khazana (Har 5 din baad).\n"
            "• `/protection buy` - ₹500 mein 24 ghante ke liye maut se bacho.\n\n"
            "🏆 **LEADERBOARDS:**\n"
            "• `/toprich` - Asgard ke top 10 ameer log.\n"
            "• `/topkill` - Asgard ke top 10 khooni darinde.\n\n"
            "🎭 **FUN & ROLEPLAY:**\n"
            "• `/punch`, `/slap`, `/fight` - Dushmano se nipatne ke liye.\n"
            "• `/love`, `/kiss`, `/bite`, `/hug` - Pyaar aur nafrat ka khel.\n"
            "• `/showid` - Apni aur group ki jankari nikalne ke liye.\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "✨ *ye hai sarri commands jyada help chaiye toh /start likho aur owner se contact karo*"
        )
        await message.reply_text(help_text)


# 📝 6. USER COMMANDS (Short list for Group)
@app.on_message(filters.command(["usercommands", "cmds"]))
async def usercmds_cmd(client, message):
    text = (
        "📜 **U-S-E-R  C-O-M-M-A-N-D-S**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Ye raaz har Mortal ke liye khule hain:\n"
        "`/profile`, `/daily`, `/weekly`, `/rob`, `/kill`\n"
        "`/dice`, `/dart`, `/protection`, `/revive`\n"
        "`/toprich`, `/topkill`, `/claim`\n"
        "`/punch`, `/slap`, `/fight`, `/hug`, `/love`\n"
        "`/showid`, `/adminlist`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Deep details ke liye `/help` type karo."
    )
    await message.reply_text(text)


# 🛡️ 7. ADMIN COMMANDS (Short list for Group)
@app.on_message(filters.command(["admincommands", "acmds"]))
async def admincmds_cmd(client, message):
    text = (
        "👑 **S-E-N-A-P-A-T-I  P-O-W-E-R-S**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Ye Hela ke khaas aadesh hain:\n"
        "`/ban`, `/unban`, `/kick`\n"
        "`/mute`, `/unmute`, `/warn`\n"
        "`/pin`, `/say`\n"
        "`/gift <amt>`, `/addkill <amt>`\n"
        "`/editdaily`, `/editweekly`\n"
        "`/guessmarvel` (Manual Hero Game)\n"
        "`/autoguess` (Start/Stop Auto Hero Game)\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ *Aam insaan inhe chhoone ki koshish na kare!*"
    )
    await message.reply_text(text)

# --- RENDER PORT FIX (Nakli Website) ---
import threading
from flask import Flask
import os # Ye ensure karega ki os module loaded hai

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "✨ Asgard is Safe! Hela is Alive and Ruling! 👑"

def run_web():
    web_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# Nakli website ko background mein chalu karo
threading.Thread(target=run_web).start()

# Asli bot ko start karo
app.run()
