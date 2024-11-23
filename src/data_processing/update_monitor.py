import hashlib
from typing import Dict, Set
import json
import logging
from datetime import datetime

class ContentUpdateMonitor:
    def __init__(self, version_manager: DataVersionManager):
        self.version_manager = version_manager
        self.logger = logging.getLogger(__name__)
        self.current_updates: Dict[str, str] = {}
        
    def calculate_content_hash(self, content: str) -> str:
        """Calculate hash for content"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def track_content_update(self, content_id: str, content: str) -> bool:
        """Track content update and return whether it has changed"""
        new_hash = self.calculate_content_hash(content)
        has_changed = self.version_manager.has_content_changed(content_id, new_hash)
        
        if has_changed:
            self.current_updates[content_id] = new_hash
            self.logger.info(f"Content change detected for {content_id}")
            
        return has_changed
    
    def process_updates(self) -> bool:
        """Process all tracked updates"""
        if not self.current_updates:
            return False
            
        try:
            # Create new version
            new_version = self.version_manager.create_new_version()
            
            # Finalize version with updates
            self.version_manager.finalize_version(new_version, self.current_updates)
            
            # Clear tracked updates
            self.current_updates.clear()
            
            self.logger.info(f"Successfully processed updates in version {new_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing updates: {e}")
            raise
