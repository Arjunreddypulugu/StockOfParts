# Database configuration
# For local development, rename this file to config.py and update the values below
# For Streamlit Cloud deployment, add these as secrets in the Streamlit Cloud dashboard

DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': 'your_server_name.database.windows.net',
    'database': 'your_database_name',
    'username': 'your_username',
    'password': 'your_password'
}

# Table name
TABLE_NAME = 'StockOfParts'

# Note: For Streamlit Cloud deployment, you may need to use st.secrets instead:
# 
# import streamlit as st
# 
# DB_CONFIG = {
#     'driver': st.secrets["db_driver"],
#     'server': st.secrets["db_server"],
#     'database': st.secrets["db_database"],
#     'username': st.secrets["db_username"],
#     'password': st.secrets["db_password"]
# }
# 
# TABLE_NAME = st.secrets["db_table"] 