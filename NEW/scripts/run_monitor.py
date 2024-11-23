import schedule
import time
import logging
from src.scraper.web_monitor import WebsiteMonitor
from src.data_processing.content_processor import ContentProcessor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_and_update():
    """Main function to check website and update content"""
    try:
        # Initialize components
        monitor = WebsiteMonitor(
            start_url=os.getenv('WEBSITE_URL', 'https://aphrc.org'),
            output_dir='data'
        )
        
        processor = ContentProcessor(
            redis_host=os.getenv('REDIS_HOST', 'localhost'),
            redis_port=int(os.getenv('REDIS_PORT', 6379)),
            redis_db=int(os.getenv('REDIS_DB', 0)),
            model_name=os.getenv('MODEL_NAME', 'all-MiniLM-L6-v2')
        )
        
        # Check for website changes
        changes_detected = monitor.check_for_updates()
        
        if changes_detected:
            logger.info("Changes detected, updating content...")
            # Get changed content and process it
            new_content = monitor.get_changed_content()
            processor.process_new_content(new_content)
            
            # Cleanup old content
            processor.cleanup_old_content(list(new_content.keys()))
            logger.info("Content update completed")
        else:
            logger.info("No changes detected")
            
    except Exception as e:
        logger.error(f"Error in check_and_update: {e}")

def main():
    # Set up scheduling
    interval_hours = int(os.getenv('CHECK_INTERVAL_HOURS', 24))
    logger.info(f"Setting up schedule to run every {interval_hours} hours")
    
    # Schedule the job
    schedule.every(interval_hours).hours.do(check_and_update)
    
    # Run immediately on startup
    logger.info("Running initial check...")
    check_and_update()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()