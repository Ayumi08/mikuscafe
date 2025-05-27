"""
Help System for Miku's Café Bot

This module implements the help command system, providing:
- Command overview and categorization
- Staff-specific command documentation
- Interactive help embeds
- Command descriptions and usage

The system includes features like:
- Separate help panels for regular users and staff
- Command categorization (Miscellaneous, Economy & Games)
- Ephemeral staff command display
- Color-coded embeds
- Footer with bot creator information

Constants:
    DEV_GUILD (int): Development guild ID for command scoping
    STAFF_IDS (List[int]): List of staff member IDs for command access
"""

import os
import interactions
from config import DEV_GUILD, STAFF_IDS
from src import logutil

logger = logutil.init_logger(os.path.basename(__file__))


class Help(interactions.Extension):
    """
    Handles help command functionality.
    
    This extension provides:
    - Main help command for all users
    - Staff-specific command documentation
    - Command categorization and organization
    """
    
    @interactions.slash_command(
        "help", description="Shows list of commands", scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    async def help(self, ctx: interactions.SlashContext) -> None:
        """
        Display help information for available commands.
        
        This method:
        1. Shows main help panel with all user commands
        2. If user is staff, shows additional staff commands panel
        
        Args:
            ctx (SlashContext): Command context
            
        Note:
            - Staff commands are shown in an ephemeral message
            - Commands are categorized by functionality
            - Development status is noted in description
        """
        # Create main help embed
        embed = interactions.Embed(
            "Miku Café Bot Commands",
            description="This panel shows the basic overview of all commands that we have to offer. We hope you enjoy using our server's bot!  (**A LOT MORE IS STILL IN DEVELOPMENT**)",
            color=interactions.Color.from_hex("#86cecb"),
        )
        
        # Add command categories
        embed.add_field(name="Miscellaneous Commands", value=
                        """
                        /help - Shows this help panel!
                        """, inline=False)
        embed.add_field(name="Economy & Games Commands", value=
                        """
                        /balance - Shows a user's current balance value.
                        /transfer - Sends money to another user.
                        /work - Work to get a bit of small cash.
                        /leaderboard - Shows the richest users.
                        /coinflip - Gamble for a chance to double your money. 50/50 chance!
                        /blackjack - Play blackjack with the bot!
                        /shop - Pull up the shop!
                        /buy - Buy items from the shop!
                        /inventory - Check your inventory!
                        """, inline=False)
        
        # Add footer with creator information
        embed.set_footer("This bot was made by ayumi~. Feel free to DM for any suggestions or bug reports <3")
        
        # Send main help panel
        await ctx.send(embed=embed)

        # If user is staff, show additional staff commands
        if int(ctx.user.id) in STAFF_IDS:
            # Create staff help embed
            embed = interactions.Embed(
                "Admin Commands",
                description="This panel shows an overview of all the commands locked to Staff Members.",
                color=interactions.Color.from_hex("#86cecb"),
            )
            
            # Add staff command categories
            embed.add_field(name="Miscellaneous Commands", value=
                            """
                            /reload - Reloads an extension that the bot has. Used in development.
                            /template - Template extension that everything is based on. Used in development.
                            """, inline=False)
            embed.add_field(name="Economy Commands", value=
                            """
                            /modify - Used to set a user's balance to any number. Can be used to reset to 0.
                            /manage_items - Manage user items
                            """, inline=False)
            
            # Send staff commands as ephemeral message
            await ctx.send(embed=embed, ephemeral=True)