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
    async def test_cmd(self, ctx: interactions.SlashContext):
        """Register as an extension command"""

        user_id = str(ctx.user.id)
        with open("data.json", "r") as f:
            info = json.load(f)
        if user_id not in info:
            info[user_id] = {"money": 0, "items": []}
            with open('data.json', 'w') as f:
                json.dump(info, f, indent=4)

        embed = interactions.Embed(
            str(ctx.user.display_name) + "'s Balance",
            description="Your Current Balance: " + str(info[user_id]['money']),
            color=interactions.Color.from_hex("#86cecb"),
        )
        await ctx.send(embed=embed)
        