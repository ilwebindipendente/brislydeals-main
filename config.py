import os
from dotenv import load_dotenv
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_MAIN = os.getenv("CHANNEL_MAIN", "@BrislyDeals")
CHANNEL_ALI  = os.getenv("CHANNEL_ALI", "@FengXpress")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Rome")

# Amazon
AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
AMAZON_PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG", "brislydeals-21")
AMAZON_HOST = os.getenv("AMAZON_HOST", "webservices.amazon.it")
AMAZON_REGION = os.getenv("AMAZON_REGION", "eu-west-1")

# Keepa
KEEPA_API_KEY = os.getenv("KEEPA_API_KEY")
USE_KEEPA = os.getenv("USE_KEEPA", "true").lower() == "true"
KEEPA_TTL_HOURS = int(os.getenv("KEEPA_TTL_HOURS", "12"))
KEEPA_DOMAIN = os.getenv("KEEPA_DOMAIN", "IT")

# Upstash
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_TOKEN")

# Regole
MIN_STARS = float(os.getenv("MIN_STARS", "4.0"))
MIN_DISCOUNT = int(os.getenv("MIN_DISCOUNT", "20"))
DEDUP_DAYS = int(os.getenv("DEDUP_DAYS", "4"))
POSTS_PER_SLOT = int(os.getenv("POSTS_PER_SLOT", "1"))

# Ricerca
KEYWORDS = [k.strip() for k in os.getenv("KEYWORDS","").split(";") if k.strip()]
MAX_ITEMS_PER_KEYWORD = int(os.getenv("MAX_ITEMS_PER_KEYWORD", "5"))

# Slot pubblicazione (lun-ven)
PUBLISH_HOURS = {9,11,13,15,17,19,21}

# AliExpress
USE_ALIEXPRESS = os.getenv("USE_ALIEXPRESS", "false").lower() == "true"

# Routing
AMZ_TO_MAIN = os.getenv("AMZ_TO_MAIN", "true").lower() == "true"
AMZ_TO_ALI  = os.getenv("AMZ_TO_ALI", "false").lower() == "true"
ALI_TO_MAIN = os.getenv("ALI_TO_MAIN", "true").lower() == "true"
ALI_TO_ALI  = os.getenv("ALI_TO_ALI", "true").lower() == "true"

