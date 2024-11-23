from typing import Dict, List, Optional
import redis
import json
from datetime import datetime
import logging
from src.config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB

class DataVersionManager:
    def __init__(self, redis_host: str = REDIS_HOST, redis_port: int = REDIS_PORT, redis_db: int = REDIS_DB):
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        self.logger = logging.getLogger(__name__)
        
        # Keys for version tracking
        self.VERSION_KEY = "data_version:current"
        self.VERSION_HISTORY_KEY = "data_version:history"
        self.CONTENT_VERSION_KEY = "content:versions"
        
    def create_new_version(self) -> str:
        """Create a new data version and return its ID"""
        timestamp = datetime.now().isoformat()
        version_id = f"v_{timestamp}"
        
        # Store new version information
        version_info = {
            "version_id": version_id,
            "created_at": timestamp,
            "status": "creating"
        }
        
        # Add to version history
        self.redis.lpush(self.VERSION_HISTORY_KEY, json.dumps(version_info))
        
        return version_id
    
    def finalize_version(self, version_id: str, content_mapping: Dict[str, str]):
        """Finalize a version after all content is processed"""
        try:
            # Update version status
            self.redis.hset(
                f"version:{version_id}",
                mapping={
                    "status": "active",
                    "finalized_at": datetime.now().isoformat(),
                    "content_count": len(content_mapping)
                }
            )
            
            # Store content mappings for this version
            for content_id, content_hash in content_mapping.items():
                self.redis.hset(
                    f"version:{version_id}:content",
                    content_id,
                    content_hash
                )
            
            # Set as current version
            self.redis.set(self.VERSION_KEY, version_id)
            
            self.logger.info(f"Finalized version {version_id} with {len(content_mapping)} content items")
            
        except Exception as e:
            self.logger.error(f"Error finalizing version {version_id}: {e}")
            raise
    
    def get_current_version(self) -> Optional[str]:
        """Get the current active version ID"""
        return self.redis.get(self.VERSION_KEY)
    
    def get_content_hash(self, content_id: str, version_id: Optional[str] = None) -> Optional[str]:
        """Get content hash for specific version"""
        if version_id is None:
            version_id = self.get_current_version()
            
        if not version_id:
            return None
            
        return self.redis.hget(f"version:{version_id}:content", content_id)
    
    def has_content_changed(self, content_id: str, new_hash: str) -> bool:
        """Check if content has changed from current version"""
        current_hash = self.get_content_hash(content_id)
        return current_hash != new_hash