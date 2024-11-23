import click
from src.config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB
from src.storage.redis_cleanup import RedisCleanup

@click.command()
@click.option('--clean', is_flag=True, help='Clean the entire database')
@click.option('--force', is_flag=True, help='Skip confirmation when cleaning')
@click.option('--stats', is_flag=True, help='Show database statistics')
@click.option('--pattern', help='Delete keys matching pattern')
def main(clean: bool, force: bool, stats: bool, pattern: str):
    """Redis cleanup utility"""
    cleanup = RedisCleanup(
        redis_host=REDIS_HOST,
        redis_port=REDIS_PORT,
        redis_db=REDIS_DB
    )
    
    if stats:
        cleanup.show_database_stats()
    
    if pattern:
        cleanup.delete_keys_by_pattern(pattern)
    
    if clean:
        cleanup.clean_database(confirm=not force)

if __name__ == "__main__":
    main()