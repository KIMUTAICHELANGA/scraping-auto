import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
WEBSITE_URL = os.getenv('WEBSITE_URL', 'https://aphrc.org')
CHECK_INTERVAL_HOURS = int(os.getenv('CHECK_INTERVAL_HOURS', 24))
MODEL_NAME = os.getenv('MODEL_NAME', 'all-MiniLM-L6-v2')