import streamlit as st
import pandas as pd
import time
import pyodbc

# Database configuration
@st.cache_resource
def get_connection():
    try:
        # Get connection parameters from Streamlit secrets
        server = st.secrets["db_server"]
        database = st.secrets["db_database"]
        username = st.secrets["db_username"]
        password = st.secrets["db_password"]
        
        # Create connection string
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        
        # Connect to database
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {str(e)}")
        return None

# Table name from secrets
try:
    TABLE_NAME = st.secrets["db_table"]
except:
    TABLE_NAME = "StockOfParts"

def create_table_if_not_exists():
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
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
            cursor.close()
            return True
        except Exception as e:
            st.error(f"Error creating table: {str(e)}")
            return False
    return False

def count_sku_entries(sku):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE SKU = ?", (sku,))
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            st.error(f"Error counting SKU entries: {str(e)}")
            return 0
    return 0

def insert_entry(sku, manufacturer, part_number, nth_entry):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO {TABLE_NAME} (SKU, manufacturer, manufacturer_part_number, nth_entry) VALUES (?, ?, ?, ?)",
                (sku, manufacturer, part_number, nth_entry)
            )
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            st.error(f"Error inserting entry: {str(e)}")
            return False
    return False

def get_all_entries():
    conn = get_connection()
    if conn:
        try:
            query = f"SELECT * FROM {TABLE_NAME}"
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"Error getting entries: {str(e)}")
            return pd.DataFrame()
    return pd.DataFrame()

def main():
    # Page title and description
    st.title("Barcode Data Entry System")
    st.subheader("Enter part information manually or scan barcodes")
    
    # Create table if it doesn't exist
    table_exists = create_table_if_not_exists()
    
    # Create form for data entry
    with st.form("data_entry_form"):
        # SKU input
        sku = st.text_input("SKU (e.g., 999.000.932)", key="sku_input")
        
        # Manufacturer input
        manufacturer = st.text_input("Manufacturer (e.g., Siemens, Schneider, Pils)", key="manufacturer_input")
        
        # Manufacturer part number input
        part_number = st.text_input("Manufacturer Part Number (e.g., L24DF3)", key="part_number_input")
        
        # Display SKU count information
        if sku:
            count = count_sku_entries(sku)
            if count > 0:
                st.info(f"This SKU already exists {count} times in the database. This will be entry #{count + 1}.")
                nth_entry = count + 1
            else:
                st.success("This is a new SKU.")
                nth_entry = 1
        else:
            nth_entry = 1
        
        # Submit button
        submit_button = st.form_submit_button("Submit")
        
        if submit_button:
            if not sku or not manufacturer or not part_number:
                st.error("Please fill in all fields.")
            else:
                success = insert_entry(sku, manufacturer, part_number, nth_entry)
                if success:
                    st.success("Data successfully saved to the database!")
                    # Clear the form
                    st.session_state.sku_input = ""
                    st.session_state.manufacturer_input = ""
                    st.session_state.part_number_input = ""
                    st.rerun()
                else:
                    st.error("Failed to save data to the database. Please try again.")

    # Display entries
    df = get_all_entries()
    if not df.empty:
        st.subheader("Database Entries")
        st.dataframe(df)
        
        # Add a button to download as CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name="barcode_entries.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main() 