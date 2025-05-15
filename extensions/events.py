"""
This file provides code for events like message intents.
"""

import os
import interactions
from src import logutil
from interactions import listen

logger = logutil.init_logger(os.path.basename(__file__))

class MessageEvents(interactions.Extension):
    @listen()
    async def on_message_create(self, event):
        # Check if the message content contains "miku miku" (case insensitive)
        if "miku miku" in event.message.content.lower():
            # Respond with "oo ee oo"
            await event.message.channel.send("oo ee oo")
        elif "1 2 3 ready?" in event.message.content.lower():
            embed = interactions.Embed( 
                title="Miku Miku BEEEEEAAAAAAMMMMM",
                color=interactions.Color.from_hex("#86cecb")
            )
            embed.set_image(url="https://images-ext-1.discordapp.net/external/_8uAGYmcG11pgX5gWLCwCnUnI6abZiOvw-oS5TfseAM/https/retrorender.online/UbKYB1j90.gif?width=400&height=157")
            await event.message.channel.send(embed=embed)
        # Reaction to mentions event
        elif event.message.mention_users and not event.message.message_reference:
            mentioned_users = [user async for user in event.message.mention_users]
            if any(mention.id == 705137748884848691 for mention in mentioned_users):
                await event.message.add_reaction("<:firefly:1372594981340053616>")
            elif any(mention.id == 332262693626970112 for mention in mentioned_users):
                await event.message.add_reaction("<:batman:1372598000492351529>")
            elif any(mention.id == 148697141076951041 for mention in mentioned_users):
                await event.message.add_reaction("<:retrorender:1372598417506828470>")
            elif any(mention.id == 792064920413274142 for mention in mentioned_users):
                await event.message.add_reaction("<:fucku:1372598033132290129>")
            elif any(mention.id == 929368321365798932 for mention in mentioned_users):
                await event.message.add_reaction("<:lenshock:1372601063932428388>")

    @listen()
    async def on_message_reaction_add(self, event):
        """Event handler for when a reaction is added to a message"""
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
                
                # Send warning message that auto-deletes after 30 seconds
                warning = f"⚠️ {event.author.mention}, the use of that emoji is banned in this server. Further usage will result in a reaction ban."
                await channel.send(warning, delete_after=30)
                
                logger.info(f"Removed banned emoji reaction from message {event.message.id}")
            except Exception as e:
                logger.error(f"Failed to remove reaction: {str(e)}")
        