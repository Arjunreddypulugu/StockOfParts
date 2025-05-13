import streamlit as st
import pandas as pd

# Try to import SQLAlchemy
try:
    from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, inspect
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    st.warning("SQLAlchemy is not available. Running in demo mode with local storage only.")

# Try to import from streamlit_config
try:
    from streamlit_config import CONNECTION_STRING, TABLE_NAME
except ImportError:
    try:
        from config import CONNECTION_STRING, TABLE_NAME
    except ImportError:
        st.error("Neither streamlit_config.py nor config.py found. Database functionality will be disabled.")
        SQLALCHEMY_AVAILABLE = False
        # Define dummy values
        CONNECTION_STRING = ""
        TABLE_NAME = "StockOfParts"

# Global engine variable
engine = None

def get_engine():
    """Get or create SQLAlchemy engine"""
    global engine
    
    if not SQLALCHEMY_AVAILABLE or not CONNECTION_STRING:
        return None
        
    if engine is None:
        try:
            engine = create_engine(CONNECTION_STRING)
        except SQLAlchemyError as e:
            st.error(f"Error creating database engine: {e}")
            return None
    
    return engine

def create_table_if_not_exists():
    """Create the parts inventory table if it doesn't exist"""
    if not SQLALCHEMY_AVAILABLE or not CONNECTION_STRING:
        st.warning("Database functionality is disabled. Running in demo mode.")
        return False
        
    engine = get_engine()
    if not engine:
        return False
        
    try:
        # Check if table exists
        with engine.connect() as conn:
            inspector = inspect(engine)
            if not inspector.has_table(TABLE_NAME):
                # Create table
                metadata = MetaData()
                Table(
                    TABLE_NAME, 
                    metadata,
                    Column('id', Integer, primary_key=True),
                    Column('SKU', String(255)),
                    Column('manufacturer', String(255)),
                    Column('manufacturer_part_number', String(255)),
                    Column('nth_entry', Integer)
                )
                metadata.create_all(engine)
                st.success(f"Table {TABLE_NAME} created successfully")
            return True
    except SQLAlchemyError as e:
        st.error(f"Error creating table: {e}")
        return False

def count_sku_entries(sku):
    """Count how many times a SKU appears in the database"""
    if not SQLALCHEMY_AVAILABLE or not CONNECTION_STRING:
        return 0
        
    engine = get_engine()
    if not engine:
        return 0
        
    try:
        with engine.connect() as conn:
            query = text(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE SKU = :sku")
            result = conn.execute(query, {"sku": sku})
            count = result.scalar()
            return count if count else 0
    except SQLAlchemyError as e:
        st.error(f"Error counting SKU entries: {e}")
        return 0

def insert_entry(sku, manufacturer, manufacturer_part_number, nth_entry):
    """Insert a new entry into the database"""
    if not SQLALCHEMY_AVAILABLE or not CONNECTION_STRING:
        return False
        
    engine = get_engine()
    if not engine:
        return False
        
    try:
        with engine.connect() as conn:
            query = text(f"""
                INSERT INTO {TABLE_NAME} (SKU, manufacturer, manufacturer_part_number, nth_entry) 
                VALUES (:sku, :manufacturer, :part_number, :nth_entry)
            """)
            conn.execute(query, {
                "sku": sku, 
                "manufacturer": manufacturer, 
                "part_number": manufacturer_part_number, 
                "nth_entry": nth_entry
            })
            conn.commit()
            return True
    except SQLAlchemyError as e:
        st.error(f"Error inserting entry: {e}")
        return False

def get_all_entries():
    """Get all entries from the database"""
    if not SQLALCHEMY_AVAILABLE or not CONNECTION_STRING:
        return pd.DataFrame()
        
    engine = get_engine()
    if not engine:
        return pd.DataFrame()
        
    try:
        query = text(f"SELECT * FROM {TABLE_NAME}")
        df = pd.read_sql(query, engine)
        return df
    except SQLAlchemyError as e:
        st.error(f"Error getting entries: {e}")
        return pd.DataFrame() 