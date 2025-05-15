"""
This file provides a code for the /help module.
"""
import os
import interactions
from config import DEV_GUILD, STAFF_IDS
from src import logutil

logger = logutil.init_logger(os.path.basename(__file__))


class Help(interactions.Extension):
    @interactions.slash_command(
        "help", description="Shows list of commands", scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    async def help(self, ctx: interactions.SlashContext):
        """help embed"""
        embed = interactions.Embed(
            "Miku Café Bot Commands",
            description="This panel shows the basic overview of all commands that we have to offer. We hope you enjoy using our server's bot!  (**A LOT MORE IS STILL IN DEVELOPMENT**)",
            color=interactions.Color.from_hex("#86cecb"),
        )
        embed.add_field(name="Miscellaneous Commands", value=
                        """
                        </help:1372399261097918597> - Shows this help panel!
                        """, inline=False)
        embed.add_field(name="Economy Commands", value=
                        """
                        </balance:1371678604882087948> - Shows a user's current balance value.
                        </transfer:1371678604882087949> - Sends money to another user.
                        </work:1371957089437614081> - Work to get a bit of small cash.
                        </coinflip:1372000226117812267> - Gamble for a chance to double your money. 50/50 chance!!
                        </blackjack:1372413229757890671> - Play blackjack with the bot!
                        """, inline=False)
        embed.set_footer("This bot was made by ayumi~. Feel free to DM for any suggestions or bug reports <3")
        await ctx.send(embed=embed)

        if int(ctx.user.id) in STAFF_IDS:
            embed = interactions.Embed(
            "Admin Commands",
            description="This panel shows an overview of all the commands locked to Staff Members.",
            color=interactions.Color.from_hex("#86cecb"),
            )
            embed.add_field(name="Miscellaneous Commands", value=
                            """
                            </reload:1371946845391290368> - Reloads an extension that the bot has. Used in development.
                            </template:1371939869592522775> - Template extension that everything is based on. Used in development.
                            """, inline=False)
            embed.add_field(name="Economy Commands", value=
                            """
                            </modify:1371949806011813918> - Used to set a user's balance to any number. Can be used to reset to 0.
                            """, inline=False)
            await ctx.send(embed=embed, ephemeral=True)