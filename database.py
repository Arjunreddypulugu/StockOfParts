import streamlit as st
import pandas as pd

# Try to import SQLAlchemy
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    st.warning("SQLAlchemy is not available. Database functionality will be disabled.")

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

def insert_entry(sku, manufacturer, manufacturer_part_number, is_duplicate):
    """Insert a new entry into the database"""
    if not SQLALCHEMY_AVAILABLE or not CONNECTION_STRING:
        return False
        
    engine = get_engine()
    if not engine:
        return False
        
    try:
        with engine.connect() as conn:
            query = text(f"""
                INSERT INTO {TABLE_NAME} (SKU, manufacturer, manufacturer_part_number, is_duplicate)
                VALUES (:sku, :manufacturer, :part_number, :is_duplicate)
            """)
            conn.execute(query, {
                "sku": sku,
                "manufacturer": manufacturer,
                "part_number": manufacturer_part_number,
                "is_duplicate": is_duplicate
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