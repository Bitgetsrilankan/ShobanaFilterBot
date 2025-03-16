from info import DATABASE_URI, DATABASE_URI2

# Bot information
SESSION = 'Media_search'  # Session name for the bot
USER_SESSION = 'User_Bot'  # Session name for the user bot
API_ID = 12345  # Replace with your actual API ID
API_HASH = '0123456789abcdef0123456789abcdef'  # Replace with your actual API hash
BOT_TOKEN = '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'  # Replace with your actual bot token
USERBOT_STRING_SESSION = ''  # Fill this if you have a userbot session

# Bot settings
CACHE_TIME = 300  # Cache duration in seconds
USE_CAPTION_FILTER = False  # Enable or disable caption filter

# Admins, Channels & Users
ADMINS = [12345789, 98765432]  # List of admin user IDs (integers only)
CHANNELS = [-10012345678, -100987654321]  # List of channel IDs (integers only)
AUTH_USERS = []  # List of authorized users (empty by default)
AUTH_CHANNEL = None  # Authorized channel (None by default)

# MongoDB information for two databases
DATABASE_NAME = 'Telegram'  # Name of the first database
DATABASE_NAME2 = 'Telegram2'  # Name of the second database
COLLECTION_NAME = 'channel_files'  # Collection name for the first database
COLLECTION_NAME2 = 'channel_files2'  # Collection name for the second database

# Temporary dictionary to store both database URIs
tempDict = {
    'db1': DATABASE_URI,      # URI for the first database
    'db2': DATABASE_URI2      # URI for the second database
}