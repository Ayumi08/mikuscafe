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
    @interactions.slash_command(
        "work",
        description="Work to make money!",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @cooldown(Buckets.USER, 1, 10)
    async def work(self, ctx: interactions.SlashContext):
        with open("data.json", "r") as f:
            info = json.load(f)
        
        if str(ctx.user.id) not in info:
            info[str(ctx.user.id)] = {"money": 0, "items": []}

        earnedmoney = random.randint(100,2000)
        
        info[str(ctx.user.id)]['money'] += earnedmoney

        embed = interactions.Embed(
                "Work Summary",
                description="You worked a shift and earned <:leek:1371580348881961041>**" + str(earnedmoney) + "**!",
                color=interactions.Color.from_hex("#86cecb"),
            )
        await ctx.send(embed=embed)

        with open('data.json', 'w') as f:
            json.dump(info, f, indent=4)

class Gamble(interactions.Extension):
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
                        "Coinflip",
                        description="You bet <:leek:1371580348881961041>**" + str(money) + "** on " + selection + ".\nIt was " + selection + ". **You Win!**",
                        color=interactions.Color.from_hex("#86cecb"),
                    )
                    await ctx.send(embed=embed)
                    info[str(ctx.user.id)]['money'] += int(money)
                else:                    
                    if selection == "heads":
                        embed = interactions.Embed(
                            "Coinflip",
                            description="You bet <:leek:1371580348881961041>**" + str(money) + "** on " + selection + ".\nIt was tails.",
                            color=interactions.BrandColors.RED,
                        )
                    if selection == "tails":
                        embed = interactions.Embed(
                            "Coinflip",
                            description="You bet <:leek:1371580348881961041>**" + str(money) + "** on " + selection + ".\nIt was heads.",
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
                            "Coinflip",
                            description="You bet <:leek:1371580348881961041>**" + str(info[str(ctx.user.id)]['money']) + "** on " + selection + ".\nIt was " + selection + ". **You Win!**",
                            color=interactions.Color.from_hex("#86cecb"),
                        )
                        await ctx.send(embed=embed)
                        
                        info[str(ctx.user.id)]['money'] *= 2
                    else:
                        if selection == "heads":
                            embed = interactions.Embed(
                                "Coinflip",
                                description="You bet <:leek:1371580348881961041>**" + str(info[str(ctx.user.id)]['money']) + "** on " + selection + ".\nIt was tails.",
                                color=interactions.BrandColors.RED,
                            )
                        if selection == "tails":
                            embed = interactions.Embed(
                                "Coinflip",
                                description="You bet <:leek:1371580348881961041>**" + str(info[str(ctx.user.id)]['money']) + "** on " + selection + ".\nIt was heads.",
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