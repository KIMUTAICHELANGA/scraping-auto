class TextProcessingPipeline:
    def __init__(self, redis_host: str = REDIS_HOST, redis_port: int = REDIS_PORT, 
                 redis_db: int = REDIS_DB, model_name: str = 'all-MiniLM-L6-v2'):
        # ... (previous initialization)
        self.version_manager = DataVersionManager(redis_host, redis_port, redis_db)
        self.update_monitor = ContentUpdateMonitor(self.version_manager)
        
    def store_text_and_embedding(self, key: str, text: str, source_type: str, metadata: Dict = None):
        """Store text and embedding with version tracking"""
        # Check if content has changed
        if self.update_monitor.track_content_update(key, text):
            # Store the original text with metadata
            text_data = {
                'text': text,
                'source_type': source_type,
                'metadata': json.dumps(metadata) if metadata else '{}',
                'updated_at': datetime.now().isoformat()
            }
            
            # Store text
            self.key_manager.redis_text.hset(f"text:{key}", mapping=text_data)
            
            # Create and store embeddings for chunks
            chunks = self.chunk_text(text)
            for i, chunk in enumerate(chunks):
                embedding = self.create_embedding(chunk)
                self.key_manager.redis_binary.hset(
                    f"embedding:{key}",
                    f"chunk_{i}",
                    embedding.tobytes()
                )
                
        return self.update_monitor.process_updates()