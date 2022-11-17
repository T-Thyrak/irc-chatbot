import os
from typing import Any
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def create_connection() -> mysql.connector.MySQLConnection:
    try:
        db_conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            user=os.getenv("DB_USER"),
            passwd=os.getenv("DB_PASS"),
            db=os.getenv("DB_NAME"),
        )
    except mysql.connector.errors.DatabaseError:
        db_conn = None
        print("\033[91m[ERROR]\033[0m Could not connect to database.")
    
    return db_conn

def start_commit(db_conn: mysql.connector.MySQLConnection) -> None:
    db_conn.start_transaction()
    
def end_commit(db_conn: mysql.connector.MySQLConnection) -> None:
    db_conn.commit()

def rollback(db_conn: mysql.connector.MySQLConnection) -> None:
    db_conn.rollback()


def execute_query(query: str, db_conn: mysql.connector.MySQLConnection, values: tuple[str | int | float] | list[tuple[str | int | float]] | None = None) -> None | Any:
    """Execute a query on the database.
    
    WARNING: This function does not make any attempt to sanitize the query. Please make sure that the query is safe before
    passing it to this function.

    Args:
        query (str): The query to execute.
        db_conn (mysql.connector.MySQLConnection): The database connection to use.
        values (tuple[str | int | float] | list[tuple[str | int | float]] | None, optional): The values to pass as arguments. Defaults to None.
    """
    cursor = db_conn.cursor()
    print(f"made cursor: {cursor}")
    cursor.execute(query, values)
    if values is not None:
        print(f"executed query: {query % values}")
    else:
        print(f"executed query: {query}")
    rt_result = cursor.fetchall()
    print(f"got result: {rt_result}")
    cursor.close()
    print(f"closed cursor: {cursor}")
    return rt_result
    
def destroy_connection(db_conn: mysql.connector.MySQLConnection) -> None:
    db_conn.close()