# Load environment variables first
from dotenv import load_dotenv
import os

load_dotenv()

# Force PyExecJS to use Node.js
os.environ["EXECJS_RUNTIME"] = "Node"

from app import create_app
import pymysql

pymysql.install_as_MySQLdb()

n_app = create_app()

if __name__ == '__main__':
    with n_app.app_context():
        # Enforce that FLASK_HOST and FLASK_PORT are defined in environment variables
        host = os.getenv("FLASK_HOST")
        port_str = os.getenv("FLASK_PORT")

        if not host:
             raise ValueError("FLASK_HOST environment variable is missing. Please set it in your .env file.")
        
        if not port_str:
             raise ValueError("FLASK_PORT environment variable is missing. Please set it in your .env file.")

        try:
            port = int(port_str)
        except ValueError:
             raise ValueError(f"FLASK_PORT environment variable must be an integer, got '{port_str}'")

        n_app.run(host=host, port=port)
