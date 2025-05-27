"""
Blackjack System for Miku's Café Bot

This module implements a complete blackjack game system, including:
- Card deck management and shuffling
- Hand value calculation
- Game state management
- Interactive gameplay with buttons
- Automatic timeout handling
- Balance integration with economy system

The system includes features like:
- Standard blackjack rules
- Interactive hit/stand buttons
- Dealer AI (hits on 16, stands on 17)
- Game timeout after 5 minutes of inactivity
- Balance tracking and updates
- Detailed game state display

Constants:
    GAME_TIMEOUT (int): Time in seconds before a game times out (300 = 5 minutes)
"""

import interactions
from interactions import Button, ButtonStyle, ComponentContext
import random
from typing import List, Optional, Dict
import json
from config import DEV_GUILD
import asyncio
from datetime import datetime, timedelta

class Card:
    """
    Represents a playing card in the deck.
    
    Attributes:
        suit (str): The card's suit (Hearts, Diamonds, Clubs, Spades)
        value (str): The card's value (2-10, J, Q, K, A)
    """
    
    def __init__(self, suit: str, value: str):
        self.suit = suit
        self.value = value

    def __str__(self) -> str:
        """Returns string representation of the card."""
        return f"{self.value} of {self.suit}"

    def get_emoji(self) -> str:
        """Returns emoji representation of the card."""
        return self.__str__()

class Deck:
    """
    Represents a deck of playing cards.
    
    This class handles:
    - Deck initialization
    - Card shuffling
    - Card dealing
    """
    
    def __init__(self):
        """Initialize a new deck with 52 cards."""
        self.cards: List[Card] = []
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        for suit in suits:
            for value in values:
                self.cards.append(Card(suit, value))
        self.shuffle()

    def shuffle(self) -> None:
        """Shuffle the deck of cards."""
        random.shuffle(self.cards)

    def deal(self) -> Optional[Card]:
        """
        Deal a card from the deck.
        
        Returns:
            Optional[Card]: The dealt card, or None if deck is empty
        """
        if len(self.cards) > 0:
            return self.cards.pop()
        return None

class Hand:
    """
    Represents a player's or dealer's hand of cards.
    
    This class handles:
    - Adding cards to hand
    - Calculating hand value
    - Displaying hand contents
    """
    
    def __init__(self):
        """Initialize an empty hand."""
        self.cards: List[Card] = []

    def add_card(self, card: Card) -> None:
        """
        Add a card to the hand.
        
        Args:
            card (Card): The card to add
        """
        self.cards.append(card)

    def get_value(self) -> int:
        """
        Calculate the value of the hand.
        
        Returns:
            int: The total value of the hand
            Note: Aces are worth 11 if possible, otherwise 1
        """
        value = 0
        aces = 0

        for card in self.cards:
            if card.value in ['J', 'Q', 'K']:
                value += 10
            elif card.value == 'A':
                aces += 1
            else:
                value += int(card.value)

        for _ in range(aces):
            if value + 11 <= 21:
                value += 11
            else:
                value += 1

        return value

    def __str__(self) -> str:
        """Returns string representation of the hand."""
        return " | ".join(card.get_emoji() for card in self.cards)

class BlackjackExtension(interactions.Extension):
    """
    Handles blackjack game functionality.
    
    This extension provides:
    - Game initialization and management
    - Interactive gameplay
    - Balance integration
    - Timeout handling
    """
    
    active_games: Dict[str, Dict] = {}
    GAME_TIMEOUT = 300  # 5 minutes in seconds

    def create_buttons(self) -> List[Button]:
        """
        Create the game control buttons.
        
        Returns:
            List[Button]: List of hit and stand buttons
        """
        hit_button = Button(
            style=ButtonStyle.SUCCESS,
            label="Hit",
            custom_id="hit_button"
        )
        
        stand_button = Button(
            style=ButtonStyle.DANGER,
            label="Stand",
            custom_id="stand_button"
        )
        
        return [hit_button, stand_button]

    def create_game_embed(self, player_hand: Hand, dealer_hand: Hand, bet: int, show_dealer: bool = False) -> interactions.Embed:
        """
        Create the game state embed.
        
        Args:
            player_hand (Hand): Player's current hand
            dealer_hand (Hand): Dealer's current hand
            bet (int): Current bet amount
            show_dealer (bool): Whether to show dealer's full hand
            
        Returns:
            interactions.Embed: Formatted game state embed
        """
        if not show_dealer:
            dealer_cards = f"{dealer_hand.cards[0]} | **?**"
            dealer_value = "?"
        else:
            dealer_cards = " | ".join(str(card) for card in dealer_hand.cards)
            dealer_value = dealer_hand.get_value()

        player_cards = " | ".join(str(card) for card in player_hand.cards)

        embed = interactions.Embed(
            title="Blackjack Game",
            color=interactions.Color.from_hex("#86cecb")
        )
        
        embed.add_field(
            name="Dealer's Hand",
            value=f"{dealer_cards}\nValue: {dealer_value}",
            inline=False
        )
        
        embed.add_field(
            name="Your Hand",
            value=f"{player_cards}\nValue: {player_hand.get_value()}",
            inline=False
        )
        
        embed.add_field(
            name="Bet Amount",
            value=f"<:leek:1371580348881961041>{bet}",
            inline=False
        )

        return embed

    async def timeout_game(self, user_id: str) -> None:
        """
        Handle game timeout after inactivity.
        
        Args:
            user_id (str): ID of the user whose game timed out
            
        Note:
            Deducts bet amount and updates user's balance
        """
        await asyncio.sleep(self.GAME_TIMEOUT)
        if user_id in self.active_games:
            game = self.active_games[user_id]
            if game.get("message"):
                try:
                    # Deduct the bet amount
                    with open("data.json", "r") as f:
                        data = json.load(f)
                    
                    bet_amount = game["bet"]
                    data[user_id]["money"] = max(0, data[user_id]["money"] - bet_amount)
                    
                    with open("data.json", "w") as f:
                        json.dump(data, f, indent=4)

                    embed = interactions.Embed(
                        title="Game Timed Out",
                        description=f"This game has expired due to inactivity.\nYou lost your bet of <:leek:1371580348881961041>{bet_amount}",
                        color=interactions.BrandColors.RED
                    )
                    embed.add_field(
                        name="💰 Balance Update",
                        value=f"New Balance: <:leek:1371580348881961041>**{data[user_id]['money']}**",
                        inline=False
                    )
                    await game["message"].edit(embed=embed, components=[])
                except Exception as e:
                    print(f"Error in timeout_game: {e}")
            del self.active_games[user_id]

    @interactions.slash_command(
        name="blackjack",
        description="Play a game of Blackjack!",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @interactions.slash_option(
        name="bet",
        description='How much do you want to bet? ("all" is also valid)',
        opt_type=interactions.OptionType.STRING,
        required=True,
    )
    async def blackjack(self, ctx: interactions.SlashContext, bet: str) -> None:
        """
        Start a new game of blackjack.
        
        Args:
            ctx (SlashContext): Command context
            bet (str): Bet amount or "all"
            
        Note:
            - Validates user's balance
            - Initializes game state
            - Starts timeout timer
        """
        # Verify user has enough money
        with open("data.json", "r") as f:
            data = json.load(f)
        
        user_id = str(ctx.user.id)
        if user_id not in data:
            data[user_id] = {"money": 0, "items": []}
            with open("data.json", "w") as f:
                json.dump(data, f, indent=4)
        
        try:
            if bet.lower() == "all":
                bet_amount = data[user_id]["money"]
                if bet_amount == 0:
                    embed = interactions.Embed(
                        description="You bet nothing and won absolutely nothing!!!",
                        color=interactions.BrandColors.RED,
                    )
                    await ctx.send(embed=embed)
                    return
            else:
                bet_amount = int(bet)
                if bet_amount <= 0:
                    embed = interactions.Embed(
                        description='Please input a positive integer value to bet! (or "all")',
                        color=interactions.BrandColors.RED,
                    )
                    await ctx.send(embed=embed)
                    return
                if bet_amount > data[user_id]["money"]:
                    embed = interactions.Embed(
                        description="You can't bet more than you have...",
                        color=interactions.BrandColors.RED,
                    )
                    await ctx.send(embed=embed)
                    return
        except ValueError:
            embed = interactions.Embed(
                description='Please input a positive integer value to bet! (or "all")',
                color=interactions.BrandColors.RED,
            )
            await ctx.send(embed=embed)
            return
        
        # Initialize game
        deck = Deck()
        player_hand = Hand()
        dealer_hand = Hand()

        # Initial deal
        for _ in range(2):
            player_hand.add_card(deck.deal())
            dealer_hand.add_card(deck.deal())

        # Store game state
        self.active_games[user_id] = {
            "deck": deck,
            "player_hand": player_hand,
            "dealer_hand": dealer_hand,
            "bet": bet_amount,
            "message": None,
            "last_action": datetime.now()
        }

        # Send initial game state
        embed = self.create_game_embed(player_hand, dealer_hand, bet_amount)
        message = await ctx.send(embed=embed, components=self.create_buttons())
        self.active_games[user_id]["message"] = message

        # Start timeout task
        asyncio.create_task(self.timeout_game(user_id))

    @interactions.component_callback("hit_button")
    async def hit_callback(self, ctx: ComponentContext) -> None:
        """
        Handle hit button press.
        
        Args:
            ctx (ComponentContext): Button interaction context
            
        Note:
            - Adds card to player's hand
            - Checks for bust
            - Updates game display
        """
        try:
            # Immediately defer the interaction to prevent timeout
            await ctx.defer(edit_origin=True)
            
            user_id = str(ctx.user.id)
            
            # Check if this is the player's game
            if user_id not in self.active_games:
                await ctx.send("This is not your game!", ephemeral=True)
                return

            # Update last action time
            self.active_games[user_id]["last_action"] = datetime.now()

            game = self.active_games[user_id]
            player_hand = game["player_hand"]
            dealer_hand = game["dealer_hand"]
            deck = game["deck"]
            bet = game["bet"]

            # Deal a new card
            player_hand.add_card(deck.deal())
            
            # Check for bust
            if player_hand.get_value() > 21:
                await self.end_game(ctx, user_id, "BUST")
                return

            # Update the game display
            embed = self.create_game_embed(player_hand, dealer_hand, bet)
            await ctx.edit(embed=embed, components=self.create_buttons())
        except Exception as e:
            print(f"Error in hit_callback: {e}")
            try:
                await ctx.send("An error occurred. Please try again.", ephemeral=True)
            except:
                pass

    @interactions.component_callback("stand_button")
    async def stand_callback(self, ctx: ComponentContext) -> None:
        """
        Handle stand button press.
        
        Args:
            ctx (ComponentContext): Button interaction context
            
        Note:
            - Dealer draws cards until 17 or higher
            - Determines winner
            - Ends game
        """
        try:
            # Immediately defer the interaction to prevent timeout
            await ctx.defer(edit_origin=True)
            
            user_id = str(ctx.user.id)
            
            # Check if this is the player's game
            if user_id not in self.active_games:
                await ctx.send("This is not your game!", ephemeral=True)
                return

            # Update last action time
            self.active_games[user_id]["last_action"] = datetime.now()

            game = self.active_games[user_id]
            player_hand = game["player_hand"]
            dealer_hand = game["dealer_hand"]
            deck = game["deck"]

            # Dealer's turn
            while dealer_hand.get_value() < 17:
                dealer_hand.add_card(deck.deal())

            # Determine winner
            dealer_value = dealer_hand.get_value()
            player_value = player_hand.get_value()

            if dealer_value > 21:
                await self.end_game(ctx, user_id, "DEALER_BUST")
            elif dealer_value > player_value:
                await self.end_game(ctx, user_id, "DEALER_WIN")
            elif player_value > dealer_value:
                await self.end_game(ctx, user_id, "PLAYER_WIN")
            else:
                await self.end_game(ctx, user_id, "TIE")
        except Exception as e:
            print(f"Error in stand_callback: {e}")
            try:
                await ctx.send("An error occurred. Please try again.", ephemeral=True)
            except:
                pass

    async def end_game(self, ctx: ComponentContext, user_id: str, result: str) -> None:
        """
        End the game and process results.
        
        Args:
            ctx (ComponentContext): Interaction context
            user_id (str): ID of the player
            result (str): Game result (BUST, DEALER_BUST, DEALER_WIN, PLAYER_WIN, TIE)
            
        Note:
            - Updates player's balance
            - Shows final game state
            - Cleans up game data
        """
        game = self.active_games[user_id]
        player_hand = game["player_hand"]
        dealer_hand = game["dealer_hand"]
        bet = game["bet"]

        embed = self.create_game_embed(player_hand, dealer_hand, bet, show_dealer=True)
        
        with open("data.json", "r") as f:
            data = json.load(f)
        
        # Create result header with emojis and formatting
        if result == "BUST":
            header = "💥 **BUST!** 💥"
            description = f"Your hand went over 21!\nYou lost <:leek:1371580348881961041>{bet}"
            color = interactions.BrandColors.RED
            data[user_id]["money"] -= bet
        elif result == "DEALER_BUST":
            header = "🎉 **YOU WIN!** 🎉"
            description = f"Dealer went bust!\nYou won <:leek:1371580348881961041>{bet}"
            color = interactions.Color.from_hex("#86cecb")
            data[user_id]["money"] += bet
        elif result == "DEALER_WIN":
            header = "❌ **DEALER WINS** ❌"
            description = f"Dealer's {dealer_hand.get_value()} beats your {player_hand.get_value()}\nYou lost <:leek:1371580348881961041>{bet}"
            color = interactions.BrandColors.RED
            data[user_id]["money"] -= bet
        elif result == "PLAYER_WIN":
            header = "🎉 **YOU WIN!** 🎉"
            description = f"Your {player_hand.get_value()} beats dealer's {dealer_hand.get_value()}\nYou won <:leek:1371580348881961041>{bet}"
            color = interactions.Color.from_hex("#86cecb")
            data[user_id]["money"] += bet
        else:  # TIE
            header = "🤝 **PUSH - IT'S A TIE!** 🤝"
            description = f"Both you and the dealer have {player_hand.get_value()}\nYour bet has been returned"
            color = interactions.Color.from_hex("#86cecb")

        embed = interactions.Embed(
            title="Blackjack Result",
            description=f"{header}\n\n{description}",
            color=color
        )
        
        # Show final hands
        embed.add_field(
            name="📍 Final Hands",
            value=f"**Dealer:** {' | '.join(str(card) for card in dealer_hand.cards)} (Value: {dealer_hand.get_value()})\n"
                  f"**You:** {' | '.join(str(card) for card in player_hand.cards)} (Value: {player_hand.get_value()})",
            inline=False
        )

        # Show balance update
        embed.add_field(
            name="💰 Balance Update",
            value=f"New Balance: <:leek:1371580348881961041>**{data[user_id]['money']}**",
            inline=False
        )
        
        with open("data.json", "w") as f:
            json.dump(data, f, indent=4)
        
        await ctx.message.edit(embed=embed, components=[])
        del self.active_games[user_id]

def setup(bot):
    """Initialize the blackjack extension."""
    BlackjackExtension(bot) 