"""
Shop System for Miku's Café Bot

This module implements the shop and inventory system, providing:
- Item shop with purchasable items
- Inventory management
- Staff item management tools
- Balance integration

The system includes features like:
- Permanent items with special effects
- Item purchase validation
- Inventory viewing and management
- Staff-only item management commands
- Balance tracking and updates

Constants:
    SHOP_ITEMS (Dict): Dictionary of available shop items with their properties:
        - name: Display name of the item
        - description: Item description and effects
        - price: Cost in currency
        - type: Item type (e.g., permanent)
"""

import os
import interactions
import json
from config import DEV_GUILD, STAFF_IDS
from src import logutil
from interactions import check
from typing import Dict, List, Optional, Union

logger = logutil.init_logger(os.path.basename(__file__))

# Define shop items
SHOP_ITEMS = {
    "lucky_charm": {
        "name": "Lucky Charm",
        "description": "Increases your luck in gambling games by 10%",
        "price": 15000,
        "type": "permanent"
    },
    "work_boost": {
        "name": "Work Boost",
        "description": "Doubles your /work earnings",
        "price": 10000,
        "type": "permanent"
    },
}

async def is_staff(ctx: interactions.SlashContext) -> bool:
    """
    Check if the user is a staff member.
    
    Args:
        ctx (SlashContext): The command context
        
    Returns:
        bool: True if the user is a staff member, False otherwise
    """
    return ctx.user.id in STAFF_IDS

class Shop(interactions.Extension):
    """
    Handles shop and inventory functionality.
    
    This extension provides:
    - Shop display and item browsing
    - Item purchase system
    - Inventory management
    - Staff item management tools
    """
    
    @interactions.slash_command(
        "shop", 
        description="View the shop and buy items!", 
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    async def shop(self, ctx: interactions.SlashContext) -> None:
        """
        Display the shop interface with available items.
        
        Args:
            ctx (SlashContext): Command context
            
        Note:
            Shows item name, price, and description for each available item
        """
        embed = interactions.Embed(
            title="🏪 Miku's Shop",
            description="Welcome to the shop! Use `/buy` to purchase items.",
            color=interactions.Color.from_hex("#86cecb")
        )
        
        for item_id, item in SHOP_ITEMS.items():
            embed.add_field(
                name=f"{item['name']} - <:leek:1371580348881961041>{item['price']}",
                value=item['description'],
                inline=False
            )
        
        await ctx.send(embed=embed)

    @interactions.slash_command(
        "buy",
        description="Buy an item from the shop",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @interactions.slash_option(
        "item",
        "The item you want to buy",
        opt_type=interactions.OptionType.STRING,
        required=True,
        choices=[
            interactions.SlashCommandChoice(name=item["name"], value=item_id)
            for item_id, item in SHOP_ITEMS.items()
        ]
    )
    async def buy(self, ctx: interactions.SlashContext, item: str) -> None:
        """
        Handle item purchase requests.
        
        Args:
            ctx (SlashContext): Command context
            item (str): ID of the item to purchase
            
        Note:
            - Validates user's balance
            - Checks for duplicate items
            - Updates user's inventory and balance
            - Sends purchase confirmation
        """
        with open("data.json", "r") as f:
            info = json.load(f)
        
        user_id = str(ctx.user.id)
        
        # Initialize user if not in database
        if user_id not in info:
            info[user_id] = {"money": 0, "items": []}
        
        # Get item details
        item_data = SHOP_ITEMS[item]
        
        # Check if user already owns the item
        if "items" in info[user_id]:
            for owned_item in info[user_id]["items"]:
                if owned_item["id"] == item:
                    embed = interactions.Embed(
                        title="Purchase Failed",
                        description=f"You already own {item_data['name']}!",
                        color=interactions.BrandColors.RED
                    )
                    await ctx.send(embed=embed)
                    return
        
        # Check if user has enough money
        if info[user_id]["money"] < item_data["price"]:
            embed = interactions.Embed(
                title="Purchase Failed",
                description=f"You don't have enough money! You need <:leek:1371580348881961041>**{item_data['price']}** to buy {item_data['name']}.",
                color=interactions.BrandColors.RED
            )
            await ctx.send(embed=embed)
            return
        
        # Process purchase
        info[user_id]["money"] -= item_data["price"]
        
        # Add item to user's inventory
        if "items" not in info[user_id]:
            info[user_id]["items"] = []
        
        info[user_id]["items"].append({
            "id": item,
            "name": item_data["name"],
            "type": item_data["type"]
        })
        
        # Save changes
        with open("data.json", "w") as f:
            json.dump(info, f, indent=4)
        
        # Send confirmation
        embed = interactions.Embed(
            title="Purchase Successful!",
            description=f"You bought {item_data['name']} for <:leek:1371580348881961041>**{item_data['price']}**!",
            color=interactions.Color.from_hex("#86cecb")
        )
        await ctx.send(embed=embed)

    @interactions.slash_command(
        "inventory",
        description="View your inventory",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @interactions.slash_option(
        "user",
        "User to check inventory for. Defaults to sender.",
        opt_type=interactions.OptionType.USER,
        required=False
    )
    async def inventory(self, ctx: interactions.SlashContext, user: Optional[Union[str, interactions.User]] = "None") -> None:
        """
        Display a user's inventory.
        
        Args:
            ctx (SlashContext): Command context
            user (Optional[Union[str, interactions.User]]): Target user, defaults to command sender
            
        Note:
            - Shows all items in user's inventory
            - Displays empty inventory message if no items
            - Can view other users' inventories
        """
        with open("data.json", "r") as f:
            info = json.load(f)
        
        if user == "None":
            user_id = str(ctx.user.id)
            display_name = ctx.user.display_name
        else:
            user_id = str(user.id)
            display_name = user.display_name
        
        if user_id not in info or not info[user_id].get("items"):
            embed = interactions.Embed(
                title=f"{display_name}'s Inventory",
                description="Their inventory is empty!",
                color=interactions.Color.from_hex("#86cecb")
            )
        else:
            items_text = ""
            for item in info[user_id]["items"]:
                items_text += f"• {item['name']}\n"
            
            embed = interactions.Embed(
                title=f"{display_name}'s Inventory",
                description=items_text,
                color=interactions.Color.from_hex("#86cecb")
            )
        
        await ctx.send(embed=embed)

    @interactions.slash_command(
        "manage_items",
        description="Staff only - Manage user items",
        scopes=[DEV_GUILD] if DEV_GUILD else None
    )
    @check(is_staff)
    @interactions.slash_option(
        "action",
        "Add or remove an item",
        opt_type=interactions.OptionType.STRING,
        required=True,
        choices=[
            interactions.SlashCommandChoice(name="Add Item", value="add"),
            interactions.SlashCommandChoice(name="Remove Item", value="remove")
        ]
    )
    @interactions.slash_option(
        "user",
        "The user to manage items for",
        opt_type=interactions.OptionType.USER,
        required=True
    )
    @interactions.slash_option(
        "item",
        "The item to add or remove",
        opt_type=interactions.OptionType.STRING,
        required=True,
        choices=[
            interactions.SlashCommandChoice(name=item["name"], value=item_id)
            for item_id, item in SHOP_ITEMS.items()
        ]
    )
    async def manage_items(self, ctx: interactions.SlashContext, action: str, user: interactions.User, item: str) -> None:
        """
        Manage user items (Staff only).
        
        Args:
            ctx (SlashContext): Command context
            action (str): Action to perform (add/remove)
            user (interactions.User): Target user
            item (str): Item ID to manage
            
        Note:
            - Staff-only command
            - Can add or remove items from user inventories
            - Updates database with changes
            - Sends confirmation message with staff member's name
        """
        with open("data.json", "r") as f:
            info = json.load(f)
        
        user_id = str(user.id)
        
        # Initialize user if not in database
        if user_id not in info:
            info[user_id] = {"money": 0, "items": []}
        
        item_data = SHOP_ITEMS[item]
        
        if action == "add":
            # Add item to user's inventory
            if "items" not in info[user_id]:
                info[user_id]["items"] = []
            
            info[user_id]["items"].append({
                "id": item,
                "name": item_data["name"],
                "type": item_data["type"]
            })
            
            embed = interactions.Embed(
                title="Item Added",
                description=f"Added {item_data['name']} to <@{user_id}>'s inventory!\n\nModified by: {ctx.user.display_name}",
                color=interactions.Color.from_hex("#86cecb")
            )
        else:  # remove
            # Remove item from user's inventory
            if "items" in info[user_id]:
                info[user_id]["items"] = [i for i in info[user_id]["items"] if i["id"] != item]
            
            embed = interactions.Embed(
                title="Item Removed",
                description=f"Removed {item_data['name']} from <@{user_id}>'s inventory!\n\nModified by: {ctx.user.display_name}",
                color=interactions.Color.from_hex("#86cecb")
            )
        
        # Save changes
        with open("data.json", "w") as f:
            json.dump(info, f, indent=4)
        
        await ctx.send(embed=embed)
