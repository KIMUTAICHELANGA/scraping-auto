import click
from src.config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB, MODEL_NAME
from src.data_processing.text_processor import TextProcessingPipeline

@click.command()
@click.option('--pdf-folder', default='data/pdf_files', help='PDF files folder')
@click.option('--scraped-data', default='data/scraped_data/scraped_data.json', help='Scraped data JSON file')
def main(pdf_folder: str, scraped_data: str):
    """Process PDFs and scraped data"""
    pipeline = TextProcessingPipeline(
        redis_host=REDIS_HOST,
        redis_port=REDIS_PORT,
        redis_db=REDIS_DB,
        model_name=MODEL_NAME
    )
    
    # Process PDFs
    pipeline.process_all_pdfs(pdf_folder)
    
    # Process scraped data
    with open(scraped_data, 'r') as f:
        data = json.load(f)
        pipeline.process_scraped_data(data)

if __name__ == "__main__":
    main()