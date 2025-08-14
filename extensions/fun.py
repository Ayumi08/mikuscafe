"""
Fun Commands for Miku's Café Bot

This module implements fun and entertainment commands, including:
- Fake ban messages for jokes
- Other entertainment features
"""

import os
import asyncio
import interactions
from config import DEV_GUILD, STAFF_IDS
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

    @interactions.slash_command(
        name="annoyping",
        description="Ping a user every 5 minutes (batzy only)",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @interactions.slash_option(
        name="user",
        description="The user to ping",
        opt_type=interactions.OptionType.USER,
        required=True
    )
    @interactions.slash_option(
        name="duration",
        description="How many times to ping (1-10, default: 3)",
        opt_type=interactions.OptionType.INTEGER,
        required=False,
        min_value=1,
        max_value=20
    )
    async def annoy_ping(self, ctx: interactions.SlashContext, user: interactions.User, duration: int = 3):
        """Ping a user every 5 minutes for a specified duration."""
        
        # Check if user is authorized (Ayumi or Batzy)
        ayumi_id = 705137748884848691
        batzy_id = 332262693626970112
        
        if ctx.user.id not in [ayumi_id, batzy_id]:
            await ctx.send("❌ Only Batzy can use this command!", ephemeral=True)
            return
        
        if user.id == ctx.user.id:
            await ctx.send("❌ You can't ping yourself!", ephemeral=True)
            return
            
        if user.bot:
            await ctx.send("❌ You can't ping bots!", ephemeral=True)
            return
        
        await ctx.send(f"🔔 Starting to ping {user.mention} every 5 minutes for {duration} times!", ephemeral=True)
        
        for i in range(duration):
            await ctx.channel.send(f"🔔 **Ping #{i+1}** - {user.mention}")
            
            if i < duration - 1:  # Don't wait after the last ping
                await asyncio.sleep(300)  # 300 seconds = 5 minutes
        
        await ctx.followup.send(f"✅ Finished pinging {user.mention}!", ephemeral=True)

def setup(bot):
    """Initialize the fun extension."""
    FunExtension(bot)