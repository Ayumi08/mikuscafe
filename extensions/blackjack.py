"""
This file provides all the code for blackjack. 
This was really large so I seperated from the main economy.py extension.
"""

import interactions
from interactions import Button, ButtonStyle, ComponentContext
import random
from typing import List
import json
from config import DEV_GUILD

class Card:
    def __init__(self, suit: str, value: str):
        self.suit = suit
        self.value = value

    def __str__(self) -> str:
        return f"{self.value} of {self.suit}"

    def get_emoji(self) -> str:
        return self.__str__()

class Deck:
    def __init__(self):
        self.cards: List[Card] = []
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        for suit in suits:
            for value in values:
                self.cards.append(Card(suit, value))
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self) -> Card:
        if len(self.cards) > 0:
            return self.cards.pop()
        return None

class Hand:
    def __init__(self):
        self.cards: List[Card] = []

    def add_card(self, card: Card):
        self.cards.append(card)

    def get_value(self) -> int:
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
        return " | ".join(card.get_emoji() for card in self.cards)

class BlackjackExtension(interactions.Extension):
    active_games = {}

    def create_buttons(self):
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

    def create_game_embed(self, player_hand: Hand, dealer_hand: Hand, bet: int, show_dealer=False):
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
    async def blackjack(self, ctx: interactions.SlashContext, bet: str):
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
                        description="You won 60 trillion leeks and saved the Miku Universe!",
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
            "message": None
        }

        # Send initial game state
        embed = self.create_game_embed(player_hand, dealer_hand, bet_amount)
        message = await ctx.send(embed=embed, components=self.create_buttons())
        self.active_games[user_id]["message"] = message

    @interactions.component_callback("hit_button")
    async def hit_callback(self, ctx: ComponentContext):
        user_id = str(ctx.user.id)
        
        # Check if this is the player's game
        if user_id not in self.active_games:
            await ctx.send("This is not your game!", ephemeral=True)
            return

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
        await ctx.message.edit(embed=embed, components=self.create_buttons())

    @interactions.component_callback("stand_button")
    async def stand_callback(self, ctx: ComponentContext):
        user_id = str(ctx.user.id)
        
        # Check if this is the player's game
        if user_id not in self.active_games:
            await ctx.send("This is not your game!", ephemeral=True)
            return

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

    async def end_game(self, ctx: ComponentContext, user_id: str, result: str):
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
    BlackjackExtension(bot) 
