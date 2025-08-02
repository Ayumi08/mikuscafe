"""
Fun Commands for Miku's Café Bot

This module implements fun and entertainment commands, including:
- Fake ban messages for jokes
- Other entertainment features
"""

import os
import interactions
from config import DEV_GUILD
from src import logutil

logger = logutil.init_logger(os.path.basename(__file__))

class FunExtension(interactions.Extension):
    """
    Handles fun and entertainment commands.
    
    This extension provides:
    - Fake ban messages
    - Other fun interactive commands
    """
    
    @interactions.slash_command(
        name="fakeban",
        description="Send a fake ban message for fun",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @interactions.slash_option(
        name="user",
        description="The user to 'ban'",
        opt_type=interactions.OptionType.USER,
        required=True
    )
    @interactions.slash_option(
        name="reason",
        description="The fake reason for the ban",
        opt_type=interactions.OptionType.STRING,
        required=False
    )
    async def fake_ban(self, ctx: interactions.SlashContext, user: interactions.User, reason: str = "being too awesome"):
        """Send a fake ban message."""
        
        embed = interactions.Embed(
            title="🔨 User Banned",
            description=f"**{user.display_name}** has been banned from the server!",
            color=interactions.BrandColors.RED
        )
        
        embed.add_field(
            name="👤 User",
            value=f"{user.mention} ({user.username})",
            inline=True
        )
        
        embed.add_field(
            name="🛡️ Moderator",
            value=ctx.user.mention,
            inline=True
        )
        
        embed.add_field(
            name="📝 Reason",
            value=reason,
            inline=False
        )
        
        embed.set_footer(text="⚠️ This is a fake ban message for entertainment purposes only!")
        
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        await ctx.send(embed=embed)

def setup(bot):
    """Initialize the fun extension."""
    FunExtension(bot)