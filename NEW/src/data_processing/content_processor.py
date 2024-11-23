from sentence_transformers import SentenceTransformer
import numpy as np
import redis
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)

class ContentProcessor:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0,
                 model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.redis = redis.Redis(
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
        self.logger = logging.getLogger(__name__)

    def chunk_text(self, text: str, max_length: int = 512) -> List[str]:
        """Split text into chunks suitable for embedding"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > max_length:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
                
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks

    def generate_embeddings(self, text: str) -> List[np.ndarray]:
        """Generate embeddings for text chunks"""
        chunks = self.chunk_text(text)
        return [self.model.encode(chunk) for chunk in chunks]

    def store_content(self, url: str, content: Dict, embeddings: List[np.ndarray]):
        """Store content and embeddings in Redis"""
        try:
            # Store text content
            content_key = f"content:{url}"
            self.redis.hset(content_key, mapping={
                'text': content['content'],
                'title': content['title'],
                'last_updated': content['last_updated']
            })
            
            # Store embeddings
            embedding_key = f"embedding:{url}"
            for i, emb in enumerate(embeddings):
                self.redis_binary.hset(embedding_key, f"chunk_{i}", emb.tobytes())
            
            # Update index
            self.redis.sadd("urls", url)
            self.redis.hset("url_updates", url, datetime.now().isoformat())
            
        except Exception as e:
            self.logger.error(f"Error storing content for {url}: {e}")
            raise

    def process_new_content(self, content_dict: Dict[str, Dict]):
        """Process and store new content"""
        for url, content in content_dict.items():
            try:
                self.logger.info(f"Processing content for {url}")
                embeddings = self.generate_embeddings(content['content'])
                self.store_content(url, content, embeddings)
                self.logger.info(f"Successfully processed {url}")
            except Exception as e:
                self.logger.error(f"Failed to process {url}: {e}")

    def cleanup_old_content(self, current_urls: List[str]):
        """Remove content for URLs that no longer exist"""
        stored_urls = self.redis.smembers("urls")
        for url in stored_urls:
            if url not in current_urls:
                self.logger.info(f"Removing old content for {url}")
                self.redis.delete(f"content:{url}")
                self.redis.delete(f"embedding:{url}")
                self.redis.srem("urls", url)
                self.redis.hdel("url_updates", url)