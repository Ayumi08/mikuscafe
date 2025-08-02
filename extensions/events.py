"""
Event System for Miku's Café Bot

This module implements event handlers for various Discord interactions, including:
- Message content triggers and responses
- Special reactions to user mentions
- Emoji moderation and auto-removal
- Custom reaction responses

The system includes features like:
- Case-insensitive message triggers
- Custom embed responses with GIFs
- Staff-specific reaction responses
- Banned emoji moderation
- Auto-deleting warning messages

Constants:
    BANNED_EMOJIS (List[str]): List of emojis that are banned from the server
"""

import os
import interactions
from src import logutil
from interactions import listen
from config import STAFF_IDS, EVENT_IDS

logger = logutil.init_logger(os.path.basename(__file__))

class MessageEvents(interactions.Extension):
    """
    Handles message-related events and reactions.
    
    This extension provides event handlers for:
    - Message content triggers
    - User mention reactions
    - Emoji moderation
    - Custom reaction responses
    """
    
    def __init__(self, client):
        super().__init__(client)
        self.reaction_ban_enabled = True
        logger.info(f"MessageEvents initialized with reaction_ban_enabled = {self.reaction_ban_enabled}")
    
    @listen()
    async def on_message_create(self, event: interactions.events.MessageCreate) -> None:
        """
        Handle message creation events.
        
        This method processes new messages and responds to specific triggers:
        - "miku miku" -> responds with "oo ee oo"
        - "1 2 3 ready?" -> responds with Miku beam GIF
        - Staff mentions -> adds custom reactions
        
        Args:
            event (MessageCreate): The message creation event
            
        Note:
            Case-insensitive matching is used for all triggers
        """
        # Check if the message content contains "miku miku" (case insensitive)
        if "miku miku" in event.message.content.lower():
            # Respond with "oo ee oo"
            await event.message.channel.send("oo ee oo")
        elif "1 2 3 ready?" in event.message.content.lower():
            embed = interactions.Embed( 
                title="Miku Miku BEEEEEAAAAAAMMMMM",
                color=interactions.Color.from_hex("#86cecb")
            )
            # Use local GIF file
            with open("assets/UbKYB1j90.gif", "rb") as f:
                file = interactions.File("assets/UbKYB1j90.gif")
                embed.set_image(url="attachment://UbKYB1j90.gif")
                await event.message.channel.send(embed=embed, file=file)
        # Reaction to mentions event
        elif event.message.mention_users and not event.message.message_reference:
            mentioned_users = [user async for user in event.message.mention_users]
            if any(mention.id == 705137748884848691 for mention in mentioned_users):
                await event.message.add_reaction("<:firefly:1372594981340053616>")
            elif any(mention.id == 332262693626970112 for mention in mentioned_users):
                await event.message.add_reaction("<:batman:1372598000492351529>")
            elif any(mention.id == 792064920413274142 for mention in mentioned_users):
                await event.message.add_reaction("<:fucku:1372598033132290129>")
            elif any(mention.id == 929368321365798932 for mention in mentioned_users):
                await event.message.add_reaction("<:lenshock:1372601063932428388>")

    @listen()
    async def on_message_reaction_add(self, event: interactions.events.MessageReactionAdd) -> None:
        """
        Handle message reaction events.
        
        This method processes new reactions and handles:
        - Banned emoji removal
        - Warning message sending
        - Reaction moderation
        
        Args:
            event (MessageReactionAdd): The reaction add event
            
        Note:
            - Warning messages auto-delete after 30 seconds
            - Failed moderation attempts are logged
        """
        # The pregnant man emoji name in Discord
        BANNED_EMOJIS = ["🫃", ]  # pregnant_man emoji
        
        # Check if the added reaction matches the banned emoji
        if str(event.emoji) in BANNED_EMOJIS:
            try:
                # Get the channel and message objects
                channel = await self.client.fetch_channel(event.message.channel.id)
                message = await channel.fetch_message(event.message.id)
                # Remove the reaction
                await message.remove_reaction(event.emoji, event.author)
                
                # Get the guild and reaction ban role
                guild = await self.client.fetch_guild(event.message.guild.id)
                reaction_ban_role = guild.get_role(1329546363662368859)
                
                # Add the reaction ban role to the user only if enabled
                if self.reaction_ban_enabled and reaction_ban_role:
                    member = await guild.fetch_member(event.author.id)
                    await member.add_role(reaction_ban_role)
                    
                    # Try to send warning as DM first, fallback to channel message with auto-deletion
                    warning = f"⚠️ You have been given the reaction ban role for using a banned emoji in this server."
                    try:
                        dm_channel = await event.author.create_dm()
                        await dm_channel.send(warning)
                    except:
                        # Fallback to channel message with auto-deletion if DM fails
                        warning_with_mention = f"⚠️ {event.author.mention}, you have been given the reaction ban role for using a banned emoji."
                        await channel.send(warning_with_mention, delete_after=30)
                    
                    logger.info(f"Added reaction ban role to user {event.author.id} for banned emoji reaction on message {event.message.id}")
                elif not self.reaction_ban_enabled:
                    # Send warning without adding role
                    warning = f"⚠️ You used a banned emoji. Please refrain from using banned emojis or you will be reaction banned."
                    try:
                        dm_channel = await event.author.create_dm()
                        await dm_channel.send(warning)
                    except:
                        # Fallback to channel message with auto-deletion if DM fails
                        warning_with_mention = f"⚠️ {event.author.mention}, you used a banned emoji. Please refrain from using banned emojis or you will be reaction banned."
                        await channel.send(warning_with_mention, delete_after=30)
                    
                    logger.info(f"Warned user {event.author.id} for banned emoji reaction on message {event.message.id} (role addition disabled)")
                elif not reaction_ban_role:
                    logger.error("Reaction ban role not found")
                
            except Exception as e:
                logger.error(f"Failed to process banned emoji reaction: {str(e)}")
    
    @interactions.slash_command(
        name="toggle_reaction_ban",
        description="Toggle reaction ban role assignment for banned emojis"
    )
    async def toggle_reaction_ban(self, ctx: interactions.SlashContext):
        """
        Toggle the reaction ban role assignment functionality.
        
        When enabled: Users get the reaction ban role when using banned emojis
        When disabled: Users only get warned but no role is assigned
        """
        if ctx.user.id not in STAFF_IDS and ctx.user.id not in EVENT_IDS:
            await ctx.send("You don't have permission to use this command.", ephemeral=True)
            return
        # Initialize the attribute if it doesn't exist
        if not hasattr(self, 'reaction_ban_enabled'):
            self.reaction_ban_enabled = True
            logger.warning("reaction_ban_enabled attribute was missing, initialized to True")
        
        self.reaction_ban_enabled = not self.reaction_ban_enabled
        status = "enabled" if self.reaction_ban_enabled else "disabled"
        
        await ctx.send(f"Reaction ban role assignment is now **{status}**")
        logger.info(f"Reaction ban role assignment toggled to {status} by {ctx.author.id}")
        