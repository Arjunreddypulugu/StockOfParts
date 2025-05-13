import pyodbc
from config import DB_CONFIG, TABLE_NAME

def get_connection():
    """Establish and return a database connection"""
    try:
        conn_str = f"DRIVER={{{DB_CONFIG['driver']}}};" \
                   f"SERVER={DB_CONFIG['server']};" \
                   f"DATABASE={DB_CONFIG['database']};" \
                   f"UID={DB_CONFIG['username']};" \
                   f"PWD={DB_CONFIG['password']}"
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as err:
        print(f"Error connecting to database: {err}")
        return None

def create_table_if_not_exists():
    """Create the parts inventory table if it doesn't exist"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Check if table exists
            cursor.execute(f"""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{TABLE_NAME}')
            BEGIN
                CREATE TABLE {TABLE_NAME} (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    SKU VARCHAR(255),
                    manufacturer VARCHAR(255),
                    manufacturer_part_number VARCHAR(255),
                    nth_entry INT
                )
            END
            """)
            conn.commit()
            print(f"Table {TABLE_NAME} is ready")
        except pyodbc.Error as err:
            print(f"Error creating table: {err}")
        finally:
            cursor.close()
            conn.close()

def count_sku_entries(sku):
    """Count how many times a SKU appears in the database"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE SKU = ?"
            cursor.execute(query, (sku,))
            count = cursor.fetchone()[0]
            return count
        except pyodbc.Error as err:
            print(f"Error counting SKU entries: {err}")
            return 0
        finally:
            cursor.close()
            conn.close()
    return 0

def insert_entry(sku, manufacturer, manufacturer_part_number, nth_entry):
    """Insert a new entry into the database"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = f"INSERT INTO {TABLE_NAME} (SKU, manufacturer, manufacturer_part_number, nth_entry) VALUES (?, ?, ?, ?)"
            cursor.execute(query, (sku, manufacturer, manufacturer_part_number, nth_entry))
            conn.commit()
            return True
        except pyodbc.Error as err:
            print(f"Error inserting entry: {err}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False 