import mysql.connector

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'helpdesk'
}

def get_connection():
    return mysql.connector.connect(**db_config)
