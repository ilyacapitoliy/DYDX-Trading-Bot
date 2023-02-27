from dydx3.constants import API_HOST_GOERLI, API_HOST_MAINNET
from decouple import config

# !!!!! SELECT MODE !!!!!
MODE = "DEVELOPMENT" 

# CLose all open positions and orders
ABORT_ALL_POSITIONS = True

# Find Cointegrated Pairs
FIND_COINTEGRATED = True

# !
MANAGE_EXITS = True

# Place Trades
PLACE_TRADES = True

# Resolution
RESOLUTION = "1HOUR"

# Stats Window
WINDOW = 21

# Threshholds - Opening
MAX_HALF_LIFE = 24
ZSCORE_THRESH = 1.5
USD_PER_TRADE = 250
USD_MIN_COLLATERAL = 5000

TOKEN_FACTOR_10 = ["ETC-USD","ALGO-USD","ICP-USD","BTC-USD","XLM-USD","DOGE-USD","CELO-USD","TRON-USD","1INCH-USD","ZRX-USD","SNX-USD","XTZ-USD","TH-USD","AAVE-USD","SUSHI-USD","ZEC-USD","XMR-USD","MKR-USD","LINK-USD","DOT-USD","EOS-USD"]

# Threshholds - Closing
CLOSE_AT_ZSCORE_CROSS = True

# Ethereum Address
ETHEREUM_ADDRESS = "0x8A328B34986de4AcF6E7080eDF08663a09600127"

# KEYS - Production
# Must to be on Mainnet on DYDX
STARK_PRIVATE_KEY_MAINNET = config("STARK_PRIVATE_KEY_MAINNET") 
DYDX_API_KEY_MAINNET = config("DYDX_API_KEY_MAINNET") 
DYDX_API_SECRET_MAINNET = config("DYDX_API_SECRET_MAINNET") 
DYDX_API_PASSPHRASE_MAINNET = config("DYDX_API_PASSPHRASE_MAINNET") 

# KEYS - Development
# Must to be on Testnet on DYDX
STARK_PRIVATE_KEY_TESTNET = config("STARK_PRIVATE_KEY_TESTNET")
DYDX_API_KEY_TESTNET = config("DYDX_API_KEY_TESTNET")
DYDX_API_SECRET_TESTNET = config("DYDX_API_SECRET_TESTNET")
DYDX_API_PASSPHRASE_TESTNET = config("DYDX_API_PASSPHRASE_TESTNET")

# KEYS - Export
STARK_PRIVATE_KEY = STARK_PRIVATE_KEY_MAINNET if MODE == "PRODUCTION" else STARK_PRIVATE_KEY_TESTNET
DYDX_API_KEY = DYDX_API_KEY_MAINNET if MODE == "PRODUCTION" else DYDX_API_KEY_TESTNET
DYDX_API_SECRET = DYDX_API_SECRET_MAINNET if MODE == "PRODUCTION" else DYDX_API_SECRET_TESTNET
DYDX_API_PASSPHRASE = DYDX_API_PASSPHRASE_MAINNET if MODE == "PRODUCTION" else DYDX_API_PASSPHRASE_TESTNET 

# HOST - Export
HOST = API_HOST_MAINNET if MODE == "PRODUCTION" else API_HOST_GOERLI

# HTTP PROVIDER
HTTP_PROVIDER_MAINNET = "https://eth-mainnet.g.alchemy.com/v2/7oho7OrWxpl9GnTTlQNZKdDfrJpWh54M"
HTTP_PROVIDER_TESTNET = "https://eth-goerli.g.alchemy.com/v2/Ym7tyIP5svz4Iiaz_A3GHpKxSqL0Iwo8"
HTTP_PROVIDER = HTTP_PROVIDER_MAINNET if MODE == "PRODUCTION" else HTTP_PROVIDER_TESTNET
