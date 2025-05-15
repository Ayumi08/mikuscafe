"""
This file provides all the code for everything to do with economy.
"""
import os
import interactions
import json
import random
from config import DEV_GUILD
from src import logutil
from interactions import check, is_owner
from interactions import cooldown, Buckets
from interactions import SlashCommandChoice

logger = logutil.init_logger(os.path.basename(__file__))

class Balance(interactions.Extension):
    @interactions.slash_command(
        "balance", 
        description="Check current balance", 
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @interactions.slash_option(
        "user",
        "User to check balance to. Defaults to sender.",
        opt_type=interactions.OptionType.USER,
        required=False
    )
    async def check_balance(self, ctx: interactions.SlashContext, user="None"):
        """Check if user is in db, if not add them"""

        if user == "None":
            author = True
            user_id = str(ctx.user.id)
        else:
            author = False
            user_id = str(user.id)
        with open("data.json", "r") as f:
            info = json.load(f)
        if user_id not in info:
            info[user_id] = {"money": 0, "items": []}
            with open('data.json', 'w') as f:
                json.dump(info, f, indent=4)

        if author == True:
            embed = interactions.Embed(
                str(ctx.user.display_name) + "'s Balance",
                description="Balance: <:leek:1371580348881961041>**" + str(info[user_id]['money']) + "**",
                color=interactions.Color.from_hex("#86cecb"),
            )
        if author == False:
            embed = interactions.Embed(
                str(user.display_name) + "'s Balance",
                description="Balance: <:leek:1371580348881961041>**" + str(info[user_id]['money']) + "**",
                color=interactions.Color.from_hex("#86cecb"),
            )
        await ctx.send(embed=embed)

class Transfer(interactions.Extension):
    @interactions.slash_command(
        "transfer",
        description="Transfers money to another user.",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @interactions.slash_option(
        "money",
        "Amount to transfer",
        opt_type=interactions.OptionType.INTEGER,
        required=True,
    )
    @interactions.slash_option(
        "user",
        "User to transfer to",
        opt_type=interactions.OptionType.USER,
        required=True
    )
    async def transfer(self, ctx: interactions.SlashContext, money, user):
        """Transfer specific amount of money from author to specified user"""

        # str of ids
        author_id = str(ctx.user.id)
        send_id = str(user.id)

        # check if in db
        with open("data.json", "r") as f:
            info = json.load(f)
        if author_id not in info:
            info[author_id] = {"money": 0, "items": []}
        if send_id not in info:
            info[send_id] = {"money": 0, "items": []}

        # check if has enough money to send
        if info[author_id]['money'] < money:
            embed = interactions.Embed(
                "Transfer Summary",
                description="You cannot send more than you have! You have <:leek:1371580348881961041>**" + str(info[author_id]['money']) + "**",
                color=interactions.Color.from_hex("#86cecb"),
            )
            await ctx.send(embed=embed, ephemeral=True)
        else:
            info[author_id]['money'] -= money
            info[send_id]['money'] += money

            embed = interactions.Embed(
                "Transfer Summary",
                description="<@" + str(author_id) + "> sent <:leek:1371580348881961041>**" + str(money) + "** to <@" + str(send_id) + ">" ,
                color=interactions.Color.from_hex("#86cecb"),
            )
            await ctx.send(embed=embed)

        with open('data.json', 'w') as f:
            json.dump(info, f, indent=4)

class Admin(interactions.Extension):
    @interactions.slash_command(
        "modify",
        description="admin only",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @check(is_owner()) # CUSTOM CHECK TO ADMINS WIP
    @interactions.slash_option(
        "user",
        "User to set",
        opt_type=interactions.OptionType.USER,
        required=True
    )
    @interactions.slash_option(
        "money",
        "Amount to set",
        opt_type=interactions.OptionType.INTEGER,
        required=True,
    )
    async def modify(self, ctx: interactions.SlashContext, money, user):
        
        with open("data.json", "r") as f:
            info = json.load(f)
        
        if str(user.id) not in info:
            info[str(user.id)] = {"money": money, "items": []}
        else:
            info[str(user.id)]['money'] = money # so not to reset preexisting items
        
        embed = interactions.Embed(
                "Balance Modification Summary",
                description="<@" + str(user.id) + "> now has <:leek:1371580348881961041>**" + str(money) + "**",
                color=interactions.Color.from_hex("#86cecb"),
            )
        await ctx.send(embed=embed)

        with open('data.json', 'w') as f:
            json.dump(info, f, indent=4)

class Work(interactions.Extension):
    # List of possible work messages
    WORK_MESSAGES = [
        "You worked as a janitor at Miku's Café",
        "You helped organize a virtual concert",
        "You sold some rare collectibles",
        "You wrote song lyrics for a new track",
        "You designed custom merchandise",
        "You performed at a street concert",
        "You taught an online dance class",
        "You worked as a sound technician",
        "You helped set up a music festival",
        "You created digital art commissions",
        "You worked as a waitress at Miku's Café",
        "You composed a new background music track",
        "You moderated a virtual fan meeting",
        "You designed a new menu for Miku's Café",
        "You performed as a backup dancer",
        "You worked as a dishwasher at Miku's Café",
        "You sold limited edition merchandise",
        "You helped with stage lighting setup",
        "You created fan art for the café walls",
        "You delivered food orders from Miku's Café",
        "You worked as a chef at Miku's Café",
        "You organized a karaoke night",
        "You photographed special café events",
        "You managed the café's social media",
        "You repaired musical equipment",
        "You hosted a gaming tournament",
        "You worked as a barista trainer",
        "You designed new café uniforms",
        "You performed at a birthday party",
        "You helped with inventory management"
    ]

    @interactions.slash_command(
        "work",
        description="Work to make money!",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @cooldown(Buckets.USER, 1, 5)
    async def work(self, ctx: interactions.SlashContext):
        with open("data.json", "r") as f:
            info = json.load(f)
        
        if str(ctx.user.id) not in info:
            info[str(ctx.user.id)] = {"money": 0, "items": []}

        earnedmoney = random.randint(20,200)
        work_message = random.choice(self.WORK_MESSAGES)
        
        info[str(ctx.user.id)]['money'] += earnedmoney

        embed = interactions.Embed(
                "Work Summary",
                description=f"{work_message} and earned <:leek:1371580348881961041>**{earnedmoney}**!",
                color=interactions.Color.from_hex("#86cecb"),
            )
        await ctx.send(embed=embed)

        with open('data.json', 'w') as f:
            json.dump(info, f, indent=4)

class Leaderboard(interactions.Extension):
    @interactions.slash_command(
        "leaderboard",
        description="Shows the richest users",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    async def leaderboard(self, ctx: interactions.SlashContext):
        with open("data.json", "r") as f:
            info = json.load(f)
        
        # Sort users by money
        sorted_users = sorted(info.items(), key=lambda x: x[1]['money'], reverse=True)
        
        # Create leaderboard text
        leaderboard_text = ""
        for index, (user_id, data) in enumerate(sorted_users[:10], 1):
            user = await ctx.client.fetch_user(user_id)
            leaderboard_text += f"**{index}.** <@{user.id}> - <:leek:1371580348881961041>**{data['money']}**\n"
        
        # Find author's position if not in top 10
        author_position = None
        author_money = None
        for index, (user_id, data) in enumerate(sorted_users, 1):
            if user_id == str(ctx.user.id):
                author_position = index
                author_money = data['money']
                break
        
        embed = interactions.Embed(
            title="🏆 Leaderboard - Top 10 Richest Users",
            description=leaderboard_text,
            color=interactions.Color.from_hex("#86cecb"),
        )
        
        # Add author's position if not in top 10
        if author_position and author_position > 10:
            embed.add_field(
                name="Your Position in the Server",
                value=f"#{author_position} - {ctx.user.display_name} - <:leek:1371580348881961041>**{author_money}**",
                inline=False
            )
        
        await ctx.send(embed=embed)

class Coinflip(interactions.Extension):
    @interactions.slash_command(
        "coinflip",
        description="A chance to double your money.",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @interactions.slash_option(
        "selection",
        description= "Heads or Tails?",
        opt_type=interactions.OptionType.STRING,
        required=True,
        choices=[
            SlashCommandChoice(name="Heads", value="heads"),
            SlashCommandChoice(name="Tails", value="tails")
        ]
    )
    @interactions.slash_option(
        "money",
        'How much do you want to bet? ("all" is also valid)',
        opt_type=interactions.OptionType.STRING,
        required=True,
    )
    async def flip(self, ctx: interactions.SlashContext, selection, money):
        with open("data.json", "r") as f:
            info = json.load(f)
        
        if str(ctx.user.id) not in info:
            info[str(ctx.user.id)] = {"money": 0, "items": []}
        
        try:
            if int(money) == 0:
                embed = interactions.Embed(
                    description="You bet nothing and won absolutely nothing!!!",
                    color=interactions.BrandColors.RED,
                )
                await ctx.send(embed=embed)
            elif int(money) > info[str(ctx.user.id)]['money']:
                embed = interactions.Embed(
                    description="You can't bet more than you have...",
                    color=interactions.BrandColors.RED,
                )
                await ctx.send(embed=embed)
            elif int(money) < 0:
                embed = interactions.Embed(
                    description='Please input a positive integer value to bet! (or "all")',
                    color=interactions.BrandColors.RED,
                )
                await ctx.send(embed=embed)
            else:
                if random.choice(["heads", "tails"]) == selection:
                    embed = interactions.Embed(
                        title="Coinflip Result",
                        description=f"🎉 **YOU WIN!** 🎉\n\nYou bet <:leek:1371580348881961041>**{money}** on {selection}.\nIt was {selection}!\n\n💰 **Balance Update**\nNew Balance: <:leek:1371580348881961041>**{info[str(ctx.user.id)]['money'] + int(money)}**",
                        color=interactions.Color.from_hex("#86cecb"),
                    )
                    await ctx.send(embed=embed)
                    info[str(ctx.user.id)]['money'] += int(money)
                else:                    
                    if selection == "heads":
                        embed = interactions.Embed(
                            title="Coinflip Result",
                            description=f"❌ **YOU LOSE!** ❌\n\nYou bet <:leek:1371580348881961041>**{money}** on {selection}.\nIt was tails!\n\n💰 **Balance Update**\nNew Balance: <:leek:1371580348881961041>**{info[str(ctx.user.id)]['money'] - int(money)}**",
                            color=interactions.BrandColors.RED,
                        )
                    if selection == "tails":
                        embed = interactions.Embed(
                            title="Coinflip Result",
                            description=f"❌ **YOU LOSE!** ❌\n\nYou bet <:leek:1371580348881961041>**{money}** on {selection}.\nIt was heads!\n\n💰 **Balance Update**\nNew Balance: <:leek:1371580348881961041>**{info[str(ctx.user.id)]['money'] - int(money)}**",
                            color=interactions.BrandColors.RED,
                        )
                    await ctx.send(embed=embed)
                    info[str(ctx.user.id)]['money'] -= int(money)
        except ValueError:
            if str(money).lower() == "all":
                if info[str(ctx.user.id)]['money'] == 0:
                    embed = interactions.Embed(
                        description="You bet nothing and won absolutely nothing!!!",
                        color=interactions.BrandColors.RED,
                    )
                    await ctx.send(embed=embed)
                else:
                    if random.choice(["heads", "tails"]) == selection:
                        embed = interactions.Embed(
                            title="Coinflip Result",
                            description=f"🎉 **YOU WIN!** 🎉\n\nYou bet <:leek:1371580348881961041>**{info[str(ctx.user.id)]['money']}** on {selection}.\nIt was {selection}!\n\n💰 **Balance Update**\nNew Balance: <:leek:1371580348881961041>**{info[str(ctx.user.id)]['money'] * 2}**",
                            color=interactions.Color.from_hex("#86cecb"),
                        )
                        await ctx.send(embed=embed)
                        
                        info[str(ctx.user.id)]['money'] *= 2
                    else:
                        if selection == "heads":
                            embed = interactions.Embed(
                                title="Coinflip Result",
                                description=f"❌ **YOU LOSE!** ❌\n\nYou bet <:leek:1371580348881961041>**{info[str(ctx.user.id)]['money']}** on {selection}.\nIt was tails!\n\n💰 **Balance Update**\nNew Balance: <:leek:1371580348881961041>**0**",
                                color=interactions.BrandColors.RED,
                            )
                        if selection == "tails":
                            embed = interactions.Embed(
                                title="Coinflip Result",
                                description=f"❌ **YOU LOSE!** ❌\n\nYou bet <:leek:1371580348881961041>**{info[str(ctx.user.id)]['money']}** on {selection}.\nIt was heads!\n\n💰 **Balance Update**\nNew Balance: <:leek:1371580348881961041>**0**",
                                color=interactions.BrandColors.RED,
                            )
                        await ctx.send(embed=embed)
                        info[str(ctx.user.id)]['money'] = 0
            else:
                embed = interactions.Embed(
                    description='Please input a positive integer value to bet! (or "all")',
                    color=interactions.BrandColors.RED,
                )
                await ctx.send(embed=embed)
        
        with open('data.json', 'w') as f:
            json.dump(info, f, indent=4)

class Slots(interactions.Extension):
    # Slot symbols and their multipliers
    SYMBOLS = {
        "🎵": 5,    # Music note - highest payout
        "🎤": 4,    # Microphone
        "💖": 3,    # Heart
        "🌟": 2,    # Star
        "🎪": 1     # Circus tent - lowest payout
    }
    
    SYMBOLS_LIST = list(SYMBOLS.keys())
    
    @interactions.slash_command(
        "slots",
        description="Try your luck at the slot machine!",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @interactions.slash_option(
        "bet",
        'How much do you want to bet? ("all" is also valid)',
        opt_type=interactions.OptionType.STRING,
        required=True,
    )
    async def slots(self, ctx: interactions.SlashContext, bet):
        with open("data.json", "r") as f:
            info = json.load(f)
        
        if str(ctx.user.id) not in info:
            info[str(ctx.user.id)] = {"money": 0, "items": []}
        
        try:
            bet_amount = 0
            if str(bet).lower() == "all":
                bet_amount = info[str(ctx.user.id)]['money']
            else:
                bet_amount = int(bet)

            if bet_amount <= 0:
                embed = interactions.Embed(
                    description="You need to bet something to play!",
                    color=interactions.BrandColors.RED,
                )
                await ctx.send(embed=embed)
                
            if bet_amount > info[str(ctx.user.id)]['money']:
                embed = interactions.Embed(
                    description="You can't bet more than you have...",
                    color=interactions.BrandColors.RED,
                )
                await ctx.send(embed=embed)

            # Generate slot results
            slots = [random.choice(self.SYMBOLS_LIST) for _ in range(3)]
            
            # Calculate winnings
            winnings = 0
            if slots[0] == slots[1] == slots[2]:  # All three match
                multiplier = self.SYMBOLS[slots[0]]
                winnings = bet_amount * multiplier
            elif slots[0] == slots[1] or slots[1] == slots[2]:  # Two adjacent match
                matching_symbol = slots[0] if slots[0] == slots[1] else slots[1]
                multiplier = self.SYMBOLS[matching_symbol] // 2  # Half multiplier for two matches
                winnings = bet_amount * multiplier
            
            # Update balance
            old_balance = info[str(ctx.user.id)]['money']
            info[str(ctx.user.id)]['money'] += (winnings - bet_amount)
            new_balance = info[str(ctx.user.id)]['money']
            
            # Create result message
            slot_display = f"[ {slots[0]} | {slots[1]} | {slots[2]} ]"
            
            if winnings > 0:
                embed = interactions.Embed(
                    title="🎰 Slots Result",
                    description=f"**{slot_display}**\n\n🎉 **YOU WIN!** 🎉\n\nBet: <:leek:1371580348881961041>**{bet_amount}**\nWinnings: <:leek:1371580348881961041>**{winnings}**\n\n💰 **Balance Update**\nNew Balance: <:leek:1371580348881961041>**{new_balance}**",
                    color=interactions.Color.from_hex("#86cecb"),
                )
            else:
                embed = interactions.Embed(
                    title="🎰 Slots Result",
                    description=f"**{slot_display}**\n\n❌ **YOU LOSE!** ❌\n\nBet: <:leek:1371580348881961041>**{bet_amount}**\n\n💰 **Balance Update**\nNew Balance: <:leek:1371580348881961041>**{new_balance}**",
                    color=interactions.BrandColors.RED,
                )
            
            await ctx.send(embed=embed)

        except ValueError:
            embed = interactions.Embed(
                description='Please input a positive integer value to bet! (or "all")',
                color=interactions.BrandColors.RED,
            )
            await ctx.send(embed=embed)
        
        with open('data.json', 'w') as f:
            json.dump(info, f, indent=4)

