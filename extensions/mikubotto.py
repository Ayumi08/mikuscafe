import discord
from discord.ext import commands
from discord import app_commands
import json
from pathlib import Path
from datetime import datetime, timedelta

# ------------------ CONFIG ------------------

MIKU_CAFE_ID = 1293596673691353189
GUILD_ID = 880704957240709181

BOOST_ANNOUNCE_CHANNEL_ID = 1381015457502593138
NOTIFY_CHANNEL_ID = 1336898107362775050

MIKU_DOUBLE_BOOST_ROLE = 1367934913139048578
CROSS_SERVER_BOOST_ROLE = 1294238726926372884
GUILD_LINKED_ROLE = 1293596673750339593  # 👈 Role to give in Miku Cafe if user is in GUILD_ID

BOT_TOKEN =

BOOST_LOG_FILE = Path("boost_log.json")

# ------------------ DATA ------------------

def load_boost_log():
    if BOOST_LOG_FILE.exists():
        with BOOST_LOG_FILE.open("r") as f:
            return json.load(f)
    return {}

def save_boost_log(data):
    with BOOST_LOG_FILE.open("w") as f:
        json.dump(data, f, indent=2)

boost_log = load_boost_log()

# ------------------ DISCORD SETUP ------------------

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ------------------ LOGGING ------------------

async def announce(message: str):
    channel = bot.get_channel(NOTIFY_CHANNEL_ID)
    if channel:
        await channel.send(f"🔔 {message}")

# ------------------ ROLE ASSIGNMENT ------------------

async def process_boost_roles(user: discord.User):
    miku_guild = bot.get_guild(MIKU_CAFE_ID)
    other_guild = bot.get_guild(GUILD_ID)

    if not miku_guild:
        return

    member = miku_guild.get_member(user.id)
    other_member = other_guild.get_member(user.id) if other_guild else None

    if not member:
        return

    now = datetime.utcnow()
    user_id_str = str(user.id)

    # Get boost timestamps from log for this user
    boost_times = []
    if user_id_str in boost_log:
        try:
            boost_times = [datetime.fromisoformat(ts) for ts in boost_log[user_id_str]]
        except Exception:
            boost_times = []

    recent_boosts = [ts for ts in boost_times if now - ts <= timedelta(days=1)]

    double_boost_role = miku_guild.get_role(MIKU_DOUBLE_BOOST_ROLE)
    cross_boost_role = miku_guild.get_role(CROSS_SERVER_BOOST_ROLE)
    guild_linked_role = miku_guild.get_role(GUILD_LINKED_ROLE)

    # ---------- DOUBLE BOOST ROLE ----------
    if len(recent_boosts) >= 2:
        if double_boost_role and double_boost_role not in member.roles:
            try:
                await member.add_roles(double_boost_role)
                await announce(f"Gave **Double Booster** role to {member.mention}")
            except Exception as e:
                await announce(f"❌ Failed to assign Double Booster role to {member.mention}: {e}")
    else:
        if double_boost_role and double_boost_role in member.roles and not member.premium_since:
            try:
                await member.remove_roles(double_boost_role)
                await announce(f"Removed **Double Booster** role from {member.mention} (no longer boosting)")
            except Exception as e:
                await announce(f"❌ Failed to remove Double Booster role from {member.mention}: {e}")

    # ---------- CROSS BOOST ROLE ----------
    if member.premium_since and other_member and other_member.premium_since:
        if cross_boost_role and cross_boost_role not in member.roles:
            try:
                await member.add_roles(cross_boost_role)
                await announce(f"Gave **Cross Booster** role to {member.mention}")
            except Exception as e:
                await announce(f"❌ Failed to assign Cross Booster role to {member.mention}: {e}")
    else:
        if cross_boost_role and cross_boost_role in member.roles:
            try:
                await member.remove_roles(cross_boost_role)
                await announce(f"Removed **Cross Booster** role from {member.mention}")
            except Exception as e:
                await announce(f"❌ Failed to remove Cross Booster role from {member.mention}: {e}")

    # ---------- GUILD LINKED ROLE ----------
    if other_member:
        if guild_linked_role and guild_linked_role not in member.roles:
            try:
                await member.add_roles(guild_linked_role)
                await announce(f"Gave **Guild Linked** role to {member.mention}")
            except Exception as e:
                await announce(f"❌ Failed to assign Guild Linked role to {member.mention}: {e}")
    else:
        if guild_linked_role and guild_linked_role in member.roles:
            try:
                await member.remove_roles(guild_linked_role)
                await announce(f"Removed **Guild Linked** role from {member.mention} (left other guild)")
            except Exception as e:
                await announce(f"❌ Failed to remove Guild Linked role from {member.mention}: {e}")

# ------------------ COMMANDS ------------------

@tree.command(name="syncboosts", description="Check all members for active boost roles")
async def syncboosts(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    miku_guild = bot.get_guild(MIKU_CAFE_ID)
    if not miku_guild:
        await interaction.followup.send("❌ Could not fetch Miku Cafe guild.")
        return

    updated = 0
    async for member in miku_guild.fetch_members(limit=None):
        await process_boost_roles(member)
        updated += 1

    await interaction.followup.send(f"✅ Checked {updated} members for boost roles.")

# ------------------ EVENTS ------------------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        await tree.sync(guild=discord.Object(id=MIKU_CAFE_ID))
        print("✅ Slash commands synced.")
    except Exception as e:
        print(f"❌ Slash sync failed: {e}")

@bot.event
async def on_message(message: discord.Message):
    await bot.process_commands(message)

    if message.channel.id != BOOST_ANNOUNCE_CHANNEL_ID:
        return

    if "just boosted the server" in message.content.lower():
        if not message.mentions:
            await announce("⚠️ Boost message detected but no user mentioned.")
            return

        for user in message.mentions:
            now_iso = datetime.utcnow().isoformat()
            user_id_str = str(user.id)

            boost_log.setdefault(user_id_str, []).append(now_iso)
            save_boost_log(boost_log)

            await process_boost_roles(user)

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.premium_since != after.premium_since:
        await process_boost_roles(after)

@bot.event
async def on_member_join(member: discord.Member):
    if member.guild.id == MIKU_CAFE_ID:
        await process_boost_roles(member)

@bot.event
async def on_member_remove(member: discord.Member):
    if member.guild.id == GUILD_ID:
        miku_guild = bot.get_guild(MIKU_CAFE_ID)
        if miku_guild:
            miku_member = miku_guild.get_member(member.id)
            if miku_member:
                await process_boost_roles(miku_member)

# ------------------ RUN BOT ------------------

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
