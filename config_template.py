# Database configuration
# For local development, rename this file to config.py and update the values below
# For Streamlit Cloud deployment, add these as secrets in the Streamlit Cloud dashboard

# SQL Server connection parameters
SERVER = "your_server_name.database.windows.net"
DATABASE = "your_database_name"
USERNAME = "your_username"
PASSWORD = "your_password"

# SQLAlchemy connection string
CONNECTION_STRING = f"mssql+pymssql://{USERNAME}:{PASSWORD}@{SERVER}/{DATABASE}"

# Table name
TABLE_NAME = "StockOfParts"

# Note: For Streamlit Cloud deployment, you may need to use st.secrets instead:
# 
# import streamlit as st
# 
# SERVER = st.secrets["db_server"]
# DATABASE = st.secrets["db_database"]
# USERNAME = st.secrets["db_username"]
# PASSWORD = st.secrets["db_password"]
# 
# CONNECTION_STRING = f"mssql+pymssql://{USERNAME}:{PASSWORD}@{SERVER}/{DATABASE}"
# TABLE_NAME = st.secrets["db_table"] 