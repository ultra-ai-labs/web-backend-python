import os
import sys
import subprocess
import shutil
from urllib.parse import urlparse, unquote

try:
    from dotenv import load_dotenv
    # Load environment variables
    load_dotenv()
except ImportError:
    # dotenv not installed, assume env vars are set in environment
    pass

def get_db_config():
    db_url = os.getenv("RELATION_DB_URL")
    if not db_url:
        print("Error: RELATION_DB_URL not found in .env")
        return None

    # Handle mysql+pymysql:// or similar which urlparse might not handle well for scheme
    # Actually urlparse handles scheme fine, but we want to ensure we extract creds correctly.
    # Standard connection strings like mysql://user:pass@host:port/db work with urlparse.
    
    try:
        # Pre-process to ensure urlparse handles it as a standard URL
        # Some drivers use mysql+driver://...
        if "://" in db_url:
            scheme, rest = db_url.split("://", 1)
            if "+" in scheme:
                # simplify scheme to just mysql (or http) so urlparse logic holds if needed, 
                # but urlparse generally ignores the scheme specifics for netloc parsing.
                pass
        
        parsed = urlparse(db_url)
        
        # Ensure we have a valid hostname
        if not parsed.hostname:
            # Fallback for some malformed URLs or if scheme is weird
            raise ValueError("Could not parse hostname from URL")

        return {
            "user": parsed.username,
            "password": unquote(parsed.password) if parsed.password else None,
            "host": parsed.hostname,
            "port": str(parsed.port) if parsed.port else "3306",
            "db_name": parsed.path.lstrip('/')
        }
    except Exception as e:
        print(f"Error parsing DB URL: {e}")
        return None

def init_db(sql_file_path=None):
    config = get_db_config()
    if not config:
        return

    print(f"Connecting to {config['host']}:{config['port']} as {config['user']}...")

    # Determine SQL file path
    if not sql_file_path:
        # Default to relative path: schema/media_crawler.sql
        base_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file_path = os.path.join(base_dir, "schema", "media_crawler.sql")
    
    if not os.path.exists(sql_file_path):
        print(f"SQL file not found: {sql_file_path}")
        return

    # Check if mysql client is available
    mysql_cmd = shutil.which("mysql")
    if not mysql_cmd:
        print("Error: 'mysql' command not found in PATH. Please install mysql-client.")
        return

    # Create Database
    # Note: Using -pPASSWORD is insecure on multi-user systems.
    # Using MYSQL_PWD environment variable is safer.
    env = os.environ.copy()
    if config['password']:
        env["MYSQL_PWD"] = config['password']
    
    create_db_args = [
        mysql_cmd,
        f"-h{config['host']}",
        f"-P{config['port']}",
        f"-u{config['user']}",
        "-e", f"CREATE DATABASE IF NOT EXISTS {config['db_name']} CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
    ]

    print(f"Creating database '{config['db_name']}' if not exists...")
    try:
        subprocess.run(create_db_args, env=env, check=True)
        print("Database created or already exists.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating database: {e}")
        print("Please check your database credentials in .env file.")
        return

    print(f"Importing {sql_file_path} into {config['db_name']}...")
    
    import_args = [
        mysql_cmd,
        f"-h{config['host']}",
        f"-P{config['port']}",
        f"-u{config['user']}",
        config['db_name']
    ]
    
    try:
        with open(sql_file_path, 'r') as f:
            subprocess.run(import_args, stdin=f, env=env, check=True)
        print("Database initialized successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error importing SQL: {e}")

if __name__ == "__main__":
    # Allow passing SQL file path as argument
    import argparse
    parser = argparse.ArgumentParser(description="Initialize database from SQL file.")
    parser.add_argument("--sql-file", help="Path to the SQL file to import", default=None)
    args = parser.parse_args()
    
    init_db(args.sql_file)

