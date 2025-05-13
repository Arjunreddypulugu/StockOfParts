import streamlit as st

# Try to get secrets from Streamlit Cloud
try:
    # Connection string for SQLAlchemy with pymssql
    SERVER = st.secrets.get("db_server", "")
    DATABASE = st.secrets.get("db_database", "")
    USERNAME = st.secrets.get("db_username", "")
    PASSWORD = st.secrets.get("db_password", "")
    
    # SQLAlchemy connection string
    CONNECTION_STRING = f"mssql+pymssql://{USERNAME}:{PASSWORD}@{SERVER}/{DATABASE}"
    
    TABLE_NAME = st.secrets.get("db_table", "StockOfParts")
except:
    # Fallback configuration for local development or demo mode
    SERVER = ""
    DATABASE = ""
    USERNAME = ""
    PASSWORD = ""
    
    # Empty connection string for demo mode
    CONNECTION_STRING = ""
    
    TABLE_NAME = "StockOfParts" 