import os
import interactions
import json
from config import DEV_GUILD
from src import logutil

logger = logutil.init_logger(os.path.basename(__file__))

class Balance(interactions.Extension):
    @interactions.slash_command(
        "balance", 
        description="Check current balance", 
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    async def check_balance(self, ctx: interactions.SlashContext):
        """Check if user is in db, if not add them"""

        user_id = str(ctx.user.id)
        with open("data.json", "r") as f:
            info = json.load(f)
        if user_id not in info:
            info[user_id] = {"money": 0, "items": []}
            with open('data.json', 'w') as f:
                json.dump(info, f, indent=4)

        embed = interactions.Embed(
            str(ctx.user.display_name) + "'s Balance",
            description="Your Current Balance: $" + str(info[user_id]['money']),
            color=interactions.Color.from_hex("#86cecb"),
        )
        await ctx.send(embed=embed)

class Transfer(interactions.Extension):
    @interactions.slash_command(
        "transfer",
        description="Transfers money to another user",
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
                description="You cannot send more than you have! You have $" + info[author_id]['money']+ "." ,
                color=interactions.Color.from_hex("#86cecb"),
            )
            await ctx.send(embed=embed)
            await ctx.send("cannot transfer", ephemeral=True)
        else:
            info[author_id]['money'] -= money
            info[send_id]['money'] += money

            embed = interactions.Embed(
                "Transfer Summary",
                description="<@" + str(author_id) + "> sent " + str(money) + " to <@" + str(send_id) + ">" ,
                color=interactions.Color.from_hex("#86cecb"),
            )
            await ctx.send(embed=embed)

        with open('data.json', 'w') as f:
            json.dump(info, f, indent=4)