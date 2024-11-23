from enum import Enum
from typing import Optional, Dict
import redis
import numpy as np
from datetime import datetime

class RedisKeyTypes(Enum):
    PDF_TEXT = "pdf:text"
    PDF_EMBEDDING = "pdf:emb"
    WEBPAGE_TEXT = "web:text"
    WEBPAGE_EMBEDDING = "web:emb"
    METADATA = "meta"

class RedisKeyManager:
    def __init__(self, redis_host: str, redis_port: int, redis_db: int):
        self.redis_text = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        self.redis_binary = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=False
        )