"""
Economy System for Miku's Café Bot

This module implements a complete economy system for Miku's Café, including:
- Balance checking and money transfers
- Work system with random jobs and earnings
- Gambling system (coinflip) with special items
- Leaderboard system
- Staff controls for balance modification

The system uses a JSON file for persistent storage and includes features like:
- Lucky charms that increase gambling odds
- Work boost items that double earnings
- Special user privileges
- Cooldowns on work commands

Constants:
    DATA_FILE (Path): Path to the JSON data file
    CURRENCY_EMOJI (str): Emoji used to represent currency
    EMBED_COLOR (Color): Default color for success embeds
    ERROR_COLOR (Color): Color used for error embeds
"""

import os
import json
import random
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from pathlib import Path

import interactions
from interactions import check, is_owner, cooldown, Buckets, SlashCommandChoice
from config import DEV_GUILD, STAFF_IDS
from src import logutil

logger = logutil.init_logger(os.path.basename(__file__))

# Constants
DATA_FILE = Path("data.json")
CURRENCY_EMOJI = "<:leek:1371580348881961041>"
EMBED_COLOR = interactions.Color.from_hex("#86cecb")
ERROR_COLOR = interactions.BrandColors.RED

@dataclass
class UserData:
    """
    Represents a user's economic data.
    
    Attributes:
        money (int): The user's current balance
        items (List[Dict[str, Any]]): List of items owned by the user
    """
    money: int
    items: List[Dict[str, Any]]

class EconomyManager:
    """
    Manages economy-related data operations.
    
    This class handles all data persistence operations for the economy system,
    including loading, saving, and user data management.
    """
    
    @staticmethod
    def load_data() -> Dict[str, UserData]:
        """
        Load user data from JSON file.
        
        Returns:
            Dict[str, UserData]: Dictionary mapping user IDs to their data
            
        Note:
            Returns empty dict if file doesn't exist or is invalid
        """
        try:
            with open(DATA_FILE, "r") as f:
                raw_data = json.load(f)
            return {k: UserData(**v) for k, v in raw_data.items()}
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON data")
            return {}

    @staticmethod
    def save_data(data: Dict[str, UserData]) -> None:
        """
        Save user data to JSON file.
        
        Args:
            data (Dict[str, UserData]): Dictionary of user data to save
            
        Note:
            Logs error if save operation fails
        """
        try:
            with open(DATA_FILE, "w") as f:
                json.dump({k: v.__dict__ for k, v in data.items()}, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save data: {e}")

    @staticmethod
    def get_user_data(user_id: str, data: Dict[str, UserData]) -> UserData:
        """
        Get or create user data.
        
        Args:
            user_id (str): Discord user ID
            data (Dict[str, UserData]): Current data dictionary
            
        Returns:
            UserData: User's data object, created if doesn't exist
        """
        if user_id not in data:
            data[user_id] = UserData(money=0, items=[])
        return data[user_id]

async def is_staff(ctx: interactions.SlashContext) -> bool:
    """
    Check if the user is a staff member.
    
    Args:
        ctx (SlashContext): The command context
        
    Returns:
        bool: True if the user is a staff member, False otherwise
    """
    return ctx.user.id in STAFF_IDS

class Balance(interactions.Extension):
    """
    Handles balance checking functionality.
    
    This extension provides commands to check user balances,
    creating new user entries if they don't exist.
    """
    
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
    async def check_balance(self, ctx: interactions.SlashContext, user: Optional[interactions.User] = None) -> None:
        """
        Check a user's balance.
        
        Args:
            ctx (SlashContext): Command context
            user (Optional[User]): Target user, defaults to command sender
            
        Note:
            Creates new user entry if user doesn't exist
        """
        user_id = str(ctx.user.id if user is None else user.id)
        data = EconomyManager.load_data()
        user_data = EconomyManager.get_user_data(user_id, data)
        
        display_name = ctx.user.display_name if user is None else user.display_name
        embed = interactions.Embed(
            f"{display_name}'s Balance",
            description=f"Balance: {CURRENCY_EMOJI}**{user_data.money}**",
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)
        EconomyManager.save_data(data)

class Transfer(interactions.Extension):
    """
    Handles money transfer functionality.
    
    This extension provides commands to transfer money between users,
    with validation for negative amounts and insufficient funds.
    """
    
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
    async def transfer(self, ctx: interactions.SlashContext, money: int, user: interactions.User) -> None:
        """
        Transfer money between users.
        
        Args:
            ctx (SlashContext): Command context
            money (int): Amount to transfer
            user (User): Target user
            
        Note:
            Validates transfer amount and sender's balance
        """
        if money <= 0:
            await ctx.send(
                embed=interactions.Embed(
                    "Transfer Summary",
                    description="You cannot transfer a negative or zero amount!",
                    color=ERROR_COLOR
                ),
                ephemeral=True
            )
            return

        data = EconomyManager.load_data()
        sender_id = str(ctx.user.id)
        receiver_id = str(user.id)
        
        sender_data = EconomyManager.get_user_data(sender_id, data)
        receiver_data = EconomyManager.get_user_data(receiver_id, data)

        if sender_data.money < money:
            await ctx.send(
                embed=interactions.Embed(
                    "Transfer Summary",
                    description=f"You cannot send more than you have! You have {CURRENCY_EMOJI}**{sender_data.money}**",
                    color=ERROR_COLOR
                ),
                ephemeral=True
            )
            return

        sender_data.money -= money
        receiver_data.money += money

        embed = interactions.Embed(
            "Transfer Summary",
            description=f"<@{sender_id}> sent {CURRENCY_EMOJI}**{money}** to <@{receiver_id}>",
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)
        EconomyManager.save_data(data)

class Admin(interactions.Extension):
    """
    Handles staff administrative commands.
    
    This extension provides commands for staff members to modify user balances.
    Requires staff permissions (STAFF_IDS from config) to use.
    """
    
    @interactions.slash_command(
        "modify",
        description="Staff only - Modify user balances",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @check(is_staff)
    @interactions.slash_option(
        "user",
        "User to modify",
        opt_type=interactions.OptionType.USER,
        required=True
    )
    @interactions.slash_option(
        "money",
        "Amount to set",
        opt_type=interactions.OptionType.INTEGER,
        required=True,
    )
    async def modify(self, ctx: interactions.SlashContext, money: int, user: interactions.User) -> None:
        """
        Modify user balance (staff only).
        
        Args:
            ctx (SlashContext): Command context
            money (int): New balance amount
            user (User): Target user
            
        Note:
            Requires staff permissions (STAFF_IDS from config) to use.
            All staff members can modify any user's balance.
        """
        data = EconomyManager.load_data()
        user_data = EconomyManager.get_user_data(str(user.id), data)
        user_data.money = money

        embed = interactions.Embed(
            "Balance Modification Summary",
            description=f"<@{user.id}> now has {CURRENCY_EMOJI}**{money}**\n\nModified by: {ctx.user.display_name}",
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)
        EconomyManager.save_data(data)

class Work(interactions.Extension):
    """
    Handles work system functionality.
    
    This extension provides commands for users to earn money through work,
    with random jobs and earnings. Includes work boost item support.
    """
    
    WORK_MESSAGES = [
        "You worked as a janitor at Miku's Café",
        "You helped organize a virtual concert",
        "You sold some rare collectibles",
        "You wrote song lyrics for a new track",
        "You designed custom merchandise",
        "You performed at a street concert",
        "You taught an online dance class",
        "You worked as a sound technician",
        "You helped set up a music festival",
        "You created digital art commissions",
        "You worked as a waitress at Miku's Café",
        "You composed a new background music track",
        "You moderated a virtual fan meeting",
        "You designed a new menu for Miku's Café",
        "You performed as a backup dancer",
        "You worked as a dishwasher at Miku's Café",
        "You sold limited edition merchandise",
        "You helped with stage lighting setup",
        "You created fan art for the café walls",
        "You delivered food orders from Miku's Café",
        "You worked as a chef at Miku's Café",
        "You organized a karaoke night",
        "You photographed special café events",
        "You managed the café's social media",
        "You repaired musical equipment",
        "You hosted a gaming tournament",
        "You worked as a barista trainer",
        "You designed new café uniforms",
        "You performed at a birthday party",
        "You helped with inventory management",
        "You helped with inventory management",
        "You hosted a latte art competition at Miku's Café",
        "You translated lyrics for an international release",
        "You managed ticket sales for a virtual concert",
        "You built stage props for a live show",
        "You edited a behind-the-scenes video",
        "You created an animated intro for a livestream",
        "You taught a voice synthesis workshop",
        "You styled costumes for a performance",
        "You assisted in a vocaloid software demo",
        "You curated a themed playlist for the café",
        "You worked as a delivery drone operator",
        "You ran the soundcheck before a concert",
        "You helped organize a fan art contest",
        "You developed a café-themed mobile game",
        "You painted a mural on the café's exterior",
        "You crafted hand-made accessories for fans",
        "You operated a merch booth at a convention",
        "You designed limited-edition café mugs",
        "You wrote a blog post about café events",
        "You voiced a character for a promotional skit",
        "You decorated the café for a seasonal event",
        "You helped choreograph a new dance routine",
        "You streamed a live DJ set featuring Miku tracks",
        "You created a themed bento menu",
        "You managed backstage operations during a show"
    ]

    @interactions.slash_command(
        "work",
        description="Work to make money!",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @cooldown(Buckets.USER, 1, 5)
    async def work(self, ctx: interactions.SlashContext) -> None:
        """
        Work to earn money.
        
        Args:
            ctx (SlashContext): Command context
            
        Note:
            - Random earnings between 20-200
            - Doubled with work boost item
            - 5 second cooldown per user
        """
        data = EconomyManager.load_data()
        user_data = EconomyManager.get_user_data(str(ctx.user.id), data)

        has_work_boost = any(item.get("id") == "work_boost" for item in user_data.items)
        earned_money = random.randint(20, 200) * (2 if has_work_boost else 1)
        
        user_data.money += earned_money
        work_message = random.choice(self.WORK_MESSAGES)

        embed = interactions.Embed(
            "Work Summary",
            description=f"{work_message} and earned {CURRENCY_EMOJI}**{earned_money}**!" + 
                       ("\n\n⚡ **Work Boost Active!**" if has_work_boost else ""),
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)
        EconomyManager.save_data(data)

class Leaderboard(interactions.Extension):
    """
    Handles leaderboard functionality.
    
    This extension provides commands to display user wealth rankings,
    showing top 10 users and the command sender's position.
    """
    
    @interactions.slash_command(
        "leaderboard",
        description="Shows the richest users",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    async def leaderboard(self, ctx: interactions.SlashContext) -> None:
        """
        Display user wealth leaderboard.
        
        Args:
            ctx (SlashContext): Command context
            
        Note:
            Shows top 10 users and sender's position if not in top 10
        """
        data = EconomyManager.load_data()
        sorted_users = sorted(data.items(), key=lambda x: x[1].money, reverse=True)
        
        leaderboard_text = "\n".join(
            f"**{i}.** <@{user_id}> - {CURRENCY_EMOJI}**{user_data.money}**"
            for i, (user_id, user_data) in enumerate(sorted_users[:10], 1)
        )

        embed = interactions.Embed(
            title="🏆 Leaderboard - Top 10 Richest Users",
            description=leaderboard_text,
            color=EMBED_COLOR
        )

        # Find author's position if not in top 10
        author_position = next(
            (i for i, (user_id, _) in enumerate(sorted_users, 1) if user_id == str(ctx.user.id)),
            None
        )

        if author_position and author_position > 10:
            author_data = data[str(ctx.user.id)]
            embed.add_field(
                name="Your Position in the Server",
                value=f"#{author_position} - {ctx.user.display_name} - {CURRENCY_EMOJI}**{author_data.money}**",
                inline=False
            )

        await ctx.send(embed=embed)

class Coinflip(interactions.Extension):
    """
    Handles coinflip gambling functionality.
    
    This extension provides commands for users to gamble their money,
    with special items affecting win chances and a special case for one user.
    """
    
    WIN_CHANCES = {
        "lucky_charm": 0.52,  # 52% win chance with lucky charm
        "default": 0.42      # 42% win chance without lucky charm
    }

    @interactions.slash_command(
        "coinflip",
        description="A chance to double your money.",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @interactions.slash_option(
        "selection",
        description="Heads or Tails?",
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
    async def flip(self, ctx: interactions.SlashContext, selection: str, money: str) -> None:
        """
        Play coinflip game.
        
        Args:
            ctx (SlashContext): Command context
            selection (str): User's choice (heads/tails)
            money (str): Bet amount or "all"
            
        Note:
            - Special user (ID: 705137748884848691) always wins
            - Lucky charm increases win chance to 52%
            - Default win chance is 42%
        """
        data = EconomyManager.load_data()
        user_data = EconomyManager.get_user_data(str(ctx.user.id), data)

        # Special case for specific user
        if str(ctx.user.id) == "705137748884848691":
            result = True
        else:
            has_lucky_charm = any(item.get("id") == "lucky_charm" for item in user_data.items)
            win_chance = self.WIN_CHANCES["lucky_charm" if has_lucky_charm else "default"]
            result = random.random() < win_chance

        try:
            bet_amount = int(money)
            if bet_amount == 0:
                await self._send_error(ctx, "You bet nothing and won absolutely nothing!!!")
                return
            if bet_amount < 0:
                await self._send_error(ctx, 'Please input a positive integer value to bet! (or "all")')
                return
            if bet_amount > user_data.money:
                await self._send_error(ctx, "You can't bet more than you have...")
                return

            await self._process_bet(ctx, user_data, selection, bet_amount, result, has_lucky_charm)

        except ValueError:
            if money.lower() == "all":
                if user_data.money == 0:
                    await self._send_error(ctx, "You bet nothing and won absolutely nothing!!!")
                    return
                await self._process_bet(ctx, user_data, selection, user_data.money, result, has_lucky_charm)
            else:
                await self._send_error(ctx, 'Please input a positive integer value to bet! (or "all")')

        EconomyManager.save_data(data)

    async def _send_error(self, ctx: interactions.SlashContext, message: str) -> None:
        """
        Send error message to user.
        
        Args:
            ctx (SlashContext): Command context
            message (str): Error message to send
        """
        await ctx.send(
            embed=interactions.Embed(
                description=message,
                color=ERROR_COLOR
            )
        )

    async def _process_bet(
        self,
        ctx: interactions.SlashContext,
        user_data: UserData,
        selection: str,
        bet_amount: int,
        result: bool,
        has_lucky_charm: bool
    ) -> None:
        """
        Process bet result and update user balance.
        
        Args:
            ctx (SlashContext): Command context
            user_data (UserData): User's data
            selection (str): User's choice (heads/tails)
            bet_amount (int): Amount bet
            result (bool): Whether user won
            has_lucky_charm (bool): Whether user has lucky charm
        """
        if result:
            user_data.money += bet_amount
            await ctx.send(
                embed=interactions.Embed(
                    title="Coinflip Result",
                    description=f"🎉 **YOU WIN!** 🎉\n\n"
                               f"You bet {CURRENCY_EMOJI}**{bet_amount}** on {selection}.\n"
                               f"It was {selection}!\n\n"
                               f"💰 **Balance Update**\n"
                               f"New Balance: {CURRENCY_EMOJI}**{user_data.money}**" +
                               ("\n\n🍀 **Lucky Charm Active!**" if has_lucky_charm else ""),
                    color=EMBED_COLOR
                )
            )
        else:
            user_data.money -= bet_amount
            opposite = "tails" if selection == "heads" else "heads"
            await ctx.send(
                embed=interactions.Embed(
                    title="Coinflip Result",
                    description=f"❌ **YOU LOSE!** ❌\n\n"
                               f"You bet {CURRENCY_EMOJI}**{bet_amount}** on {selection}.\n"
                               f"It was {opposite}!\n\n"
                               f"💰 **Balance Update**\n"
                               f"New Balance: {CURRENCY_EMOJI}**{user_data.money}**" +
                               ("\n\n🍀 **Lucky Charm Active!**" if has_lucky_charm else ""),
                    color=ERROR_COLOR
                )
            )

