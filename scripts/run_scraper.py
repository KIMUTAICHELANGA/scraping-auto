import click
from src.config.settings import WEBSITE_URL, CHECK_INTERVAL_HOURS
from src.scraper.website_monitor import WebsiteMonitor

@click.command()
@click.option('--url', default=WEBSITE_URL, help='Website URL to monitor')
@click.option('--interval', default=CHECK_INTERVAL_HOURS, help='Check interval in hours')
def main(url: str, interval: int):
    """Run the website monitor"""
    monitor = WebsiteMonitor(url)
    monitor.run(check_interval_hours=interval)

if __name__ == "__main__":
    main()