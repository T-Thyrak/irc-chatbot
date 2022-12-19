import os
import mysql.connector

from rich.console import Console
from dotenv import load_dotenv

load_dotenv()

console = Console()


def is_in_venv():
    console.print("Checking if in virtual environment... ", end="")
    has_venv = os.environ.get('VIRTUAL_ENV') is not None

    if has_venv:
        console.print("[green]Yes[/green]")
    else:
        console.print("[red]No[/red]")
        
    return has_venv


def has_database_connection():
    console.print("Checking if database connection is working... ", end="")
    
    try:
        db_conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            user=os.getenv("DB_USER"),
            passwd=os.getenv("DB_PASS"),
            db=os.getenv("DB_NAME"),
        )
        
        cursor = db_conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchall()
        cursor.close()
        db_conn.close()
        
        console.print("[green]Yes[/green]")
        return True
    except mysql.connector.errors.DatabaseError:
        console.print("[red]No[/red]")
        return False


def main() -> None:
    tests = [
        is_in_venv(),
        has_database_connection(),
    ]
    
    if all(tests):
        console.print("[green]All tests passed![/green]")
    else:
        console.print("[red]Some tests failed![/red]")
    pass

if __name__ == '__main__':
    main()