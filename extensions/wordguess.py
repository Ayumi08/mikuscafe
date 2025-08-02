"""
Word Guess Scavenger Hunt System

This module implements a word guessing game system, including:
- Secret word configuration via environment variables
- 3-hour cooldown between guesses per user
- Modal-based guess submission
- Public announcements for correct guesses
- Admin controls for game management
"""

import os
import interactions
from interactions import Button, ButtonStyle, Modal, ModalContext, ComponentContext
import json
from datetime import datetime, timedelta
from config import DEV_GUILD, STAFF_IDS, EVENT_IDS
from src import logutil

logger = logutil.init_logger(os.path.basename(__file__))

class WordGuessExtension(interactions.Extension):
    """
    Handles word guessing game functionality.
    
    This extension provides:
    - Word guessing game with cooldowns
    - Modal-based guess submission
    - Admin controls for game management
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.game_active = True
        self.secret_word = os.getenv('SECRET_WORD', 'miku').lower()
        self.cooldown_minutes = 10
        
        # Load or initialize user cooldowns
        self.load_cooldowns()
    
    def load_cooldowns(self):
        """Load user cooldowns from JSON file."""
        try:
            with open('wordguess_data.json', 'r') as f:
                data = json.load(f)
                self.user_cooldowns = data.get('user_cooldowns', {})
        except (FileNotFoundError, json.JSONDecodeError):
            self.user_cooldowns = {}
    
    def save_cooldowns(self):
        """Save user cooldowns to JSON file."""
        data = {
            'user_cooldowns': self.user_cooldowns
        }
        with open('wordguess_data.json', 'w') as f:
            json.dump(data, f, indent=4)
    
    def is_user_on_cooldown(self, user_id: str) -> tuple[bool, datetime]:
        """Check if user is on cooldown and return cooldown status and next available time."""
        if user_id not in self.user_cooldowns:
            return False, datetime.now()
        
        last_guess = datetime.fromisoformat(self.user_cooldowns[user_id])
        next_guess = last_guess + timedelta(minutes=self.cooldown_minutes)
        
        if datetime.now() < next_guess:
            return True, next_guess
        return False, datetime.now()
    
    def create_guess_button(self) -> Button:
        """Create the guess submission button."""
        return Button(
            style=ButtonStyle.PRIMARY,
            label="Submit Guess",
            custom_id="guess_button"
        )
    
    def create_guess_embed(self) -> interactions.Embed:
        """Create the main guessing game embed."""
        embed = interactions.Embed(
            title="Guess the Word Scavenger Hunt",
            description="Think you know the word? Submit your guess below! You get one submission every 10 minutes.",
            color=interactions.Color.from_hex("#86cecb")
        )
        return embed
    
    def create_guess_modal(self) -> Modal:
        """Create the guess submission modal."""
        modal = Modal(
            interactions.ShortText(
                label="Think you know the word?",
                placeholder="Enter your guess here...",
                custom_id="guess_input",
                required=True,
                max_length=100
            ),
            title="Submit Your Guess",
            custom_id="guess_modal"
        )
        return modal
    
    @interactions.slash_command(
        name="wordguess",
        description="Start the word guessing scavenger hunt",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    async def start_wordguess(self, ctx: interactions.SlashContext):
        """Send the initial word guessing embed."""
        if not self.game_active:
            await ctx.send("The word guessing game is currently disabled.", ephemeral=True)
            return
        
        embed = self.create_guess_embed()
        button = self.create_guess_button()
        
        await ctx.send(embed=embed, components=[button])
    
    @interactions.component_callback("guess_button")
    async def guess_button_callback(self, ctx: ComponentContext):
        """Handle guess button press and show modal."""
        if not self.game_active:
            await ctx.send("The word guessing game is currently disabled.", ephemeral=True)
            return
        
        user_id = str(ctx.user.id)
        on_cooldown, next_time = self.is_user_on_cooldown(user_id)
        
        if on_cooldown:
            time_left = next_time - datetime.now()
            minutes = int(time_left.total_seconds() // 60)
            seconds = int(time_left.total_seconds() % 60)
            await ctx.send(
                f"You're on cooldown! Try again in {minutes}m {seconds}s.", 
                ephemeral=True
            )
            return
        
        modal = self.create_guess_modal()
        await ctx.send_modal(modal)
    
    @interactions.modal_callback("guess_modal")
    async def guess_modal_callback(self, ctx: ModalContext):
        """Handle guess submission from modal."""
        if not self.game_active:
            await ctx.send("The word guessing game is currently disabled.", ephemeral=True)
            return
        
        user_id = str(ctx.user.id)
        guess = ctx.responses["guess_input"].lower().strip()
        
        # Update cooldown regardless of guess result
        self.user_cooldowns[user_id] = datetime.now().isoformat()
        self.save_cooldowns()
        
        if guess == self.secret_word:
            # Correct guess - public announcement
            await ctx.send(
                f":partying_face: <@{user_id}> has guessed the word correctly!",
                ephemeral=False
            )
        else:
            # Incorrect guess - ephemeral message
            await ctx.send(
                "Incorrect, try again in 10 minutes!",
                ephemeral=True
            )
    
    @interactions.slash_command(
        name="wordguess_reset",
        description="Reset all user cooldowns (Staff only)",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    async def reset_cooldowns(self, ctx: interactions.SlashContext):
        """Reset all user cooldowns."""
        if ctx.user.id not in STAFF_IDS and ctx.user.id not in EVENT_IDS:
            await ctx.send("You don't have permission to use this command.", ephemeral=True)
            return
        
        self.user_cooldowns = {}
        self.save_cooldowns()
        
        embed = interactions.Embed(
            title="Cooldowns Reset",
            description="All user cooldowns have been reset. Everyone can guess again!",
            color=interactions.Color.from_hex("#86cecb")
        )
        await ctx.send(embed=embed, ephemeral=True)
    
    @interactions.slash_command(
        name="wordguess_toggle",
        description="Toggle the word guessing game on/off (Staff only)",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    async def toggle_game(self, ctx: interactions.SlashContext):
        """Toggle the word guessing game on/off."""
        if ctx.user.id not in STAFF_IDS and ctx.user.id not in EVENT_IDS:
            await ctx.send("You don't have permission to use this command.", ephemeral=True)
            return
        
        self.game_active = not self.game_active
        status = "enabled" if self.game_active else "disabled"
        
        embed = interactions.Embed(
            title="Game Status Updated",
            description=f"Word guessing game is now **{status}**.",
            color=interactions.Color.from_hex("#86cecb") if self.game_active else interactions.BrandColors.RED
        )
        await ctx.send(embed=embed, ephemeral=True)
    
    @interactions.slash_command(
        name="wordguess_setword",
        description="Change the secret word (Staff only)",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @interactions.slash_option(
        name="new_word",
        description="The new secret word",
        opt_type=interactions.OptionType.STRING,
        required=True,
        max_length=100
    )
    async def set_secret_word(self, ctx: interactions.SlashContext, new_word: str):
        """Change the secret word in .env file."""
        if ctx.user.id not in STAFF_IDS and ctx.user.id not in EVENT_IDS:
            await ctx.send("You don't have permission to use this command.", ephemeral=True)
            return
        
        new_word = new_word.lower().strip()
        
        # Read current .env file
        env_path = '.env'
        try:
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update SECRET_WORD line
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('SECRET_WORD='):
                    lines[i] = f'SECRET_WORD="{new_word}"\n'
                    updated = True
                    break
            
            # If SECRET_WORD doesn't exist, add it
            if not updated:
                lines.append(f'SECRET_WORD="{new_word}"\n')
            
            # Write back to .env file
            with open(env_path, 'w') as f:
                f.writelines(lines)
            
            # Update in memory
            self.secret_word = new_word
            
            embed = interactions.Embed(
                title="Secret Word Updated",
                description=f"The secret word has been changed to: **{new_word}**",
                color=interactions.Color.from_hex("#86cecb")
            )
            await ctx.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await ctx.send(f"Error updating .env file: {str(e)}", ephemeral=True)

def setup(bot):
    """Initialize the word guess extension."""
    WordGuessExtension(bot)