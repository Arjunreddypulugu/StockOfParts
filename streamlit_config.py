import streamlit as st

# Try to get secrets from Streamlit Cloud
try:
    DB_CONFIG = {
        'driver': st.secrets.get("db_driver", "ODBC Driver 17 for SQL Server"),
        'server': st.secrets.get("db_server", ""),
        'database': st.secrets.get("db_database", ""),
        'username': st.secrets.get("db_username", ""),
        'password': st.secrets.get("db_password", "")
    }
    
    TABLE_NAME = st.secrets.get("db_table", "StockOfParts")
except:
    # Fallback configuration for local development or demo mode
    DB_CONFIG = {
        'driver': "ODBC Driver 17 for SQL Server",
        'server': "",
        'database': "",
        'username': "",
        'password': ""
    }
    
    TABLE_NAME = "StockOfParts" 