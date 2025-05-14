"""
Configuration template for the Barcode Data Entry System.
Rename this file to config.py and update the values with your actual database credentials.
"""

# Database configuration
DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',  # Change if using a different driver
    'server': 'your-server-name.database.windows.net',  # Azure SQL Server or your SQL Server address
    'database': 'your-database-name',  # Your database name
    'username': 'your-username',  # Database username
    'password': 'your-password',  # Database password
    'encrypt': 'yes',  # Set to 'yes' for Azure SQL, may be different for other servers
    'trust_server_certificate': 'no'  # Set to 'no' for Azure SQL, may be different for other servers
}

# Create a connection string from the config
CONNECTION_STRING = f"mssql+pymssql://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['server']}/{DB_CONFIG['database']}"

# Table name for storing part information
TABLE_NAME = 'StockOfParts'  # Change this to your actual table name

# Application settings
APP_SETTINGS = {
    'page_title': 'Barcode Data Entry System',
    'page_icon': '📊',  # Can be an emoji or a URL to an image
    'layout': 'wide',  # 'centered' or 'wide'
    'initial_sidebar_state': 'auto'  # 'auto', 'expanded', or 'collapsed'
}

# Barcode scanner settings
SCANNER_SETTINGS = {
    'fps': 10,  # Frames per second for the scanner
    'qr_box_size': 250,  # Size of the scanning box in pixels
    'scan_timeout': 30,  # Maximum time (seconds) to wait for a barcode scan
}

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