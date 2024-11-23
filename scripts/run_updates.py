import click
from src.config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB
from src.storage.version_manager import DataVersionManager
from src.data_processing.update_monitor import ContentUpdateMonitor

@click.command()
@click.option('--force', is_flag=True, help='Force update check')
def main(force: bool):
    """Check and process content updates"""
    version_manager = DataVersionManager()
    update_monitor = ContentUpdateMonitor(version_manager)
    
    # Get current version info
    current_version = version_manager.get_current_version()
    if current_version:
        click.echo(f"Current version: {current_version}")
    
    # Process any pending updates
    if update_monitor.process_updates() or force:
        click.echo("Updates processed successfully")
    else:
        click.echo("No updates needed")

if __name__ == "__main__":
    main()