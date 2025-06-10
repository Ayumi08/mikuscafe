# Miku's Café Discord Bot

A feature-rich Discord bot built with discord.py-interactions that provides various entertainment and utility features for Miku's Café.

## Features

- **Economy System**: Manage virtual currency and transactions
- **Blackjack**: Play blackjack with virtual currency
- **Shop System**: Purchase items and manage inventory
- **Event System**: Setup autoresponding events
- **Help System**: Comprehensive command documentation

## Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Discord Server with appropriate permissions

## Installation
MEOWWWWWWWWWWWWWWWW
1. Clone the repository:
```bash
git clone https://github.com/yourusername/mikuscafe.git
cd mikuscafe
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Unix or MacOS
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your Discord bot token:
```
TOKEN=your_discord_bot_token_here
```

## Configuration

The bot's configuration can be modified in `config.py`:
- `DEBUG`: Enable/disable debug logging
- `DEV_GUILD`: Set the development guild ID for testing
- `STAFF_IDS`: List of staff member Discord IDs

## Project Structure

```
mikuscafe/
├── assets/           # Static assets and resources
├── extensions/       # Bot command modules
│   ├── blackjack.py  # Blackjack game implementation
│   ├── economy.py    # Economy system
│   ├── events.py     # Event management
│   ├── help.py       # Help command system
│   └── shops.py      # Shop system
├── src/             # Core functionality
├── config.py        # Configuration settings
├── main.py          # Bot entry point
└── requirements.txt # Project dependencies
```

## Running the Bot

1. Ensure your virtual environment is activated
2. Run the bot:
```bash
python main.py
```

## Development

### Adding New Commands

1. Create a new file in the `extensions` directory
2. Use the template from `extensions/template.py`
3. Implement your command logic
4. The bot will automatically load your new extension on startup

### Reloading Extensions

Use the `/reload` command (available only in the development guild) to reload all extensions without restarting the bot.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For support, join our Discord server: [.gg/mikuscafe](https://discord.gg/mikuscafe)
