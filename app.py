import streamlit as st
import pandas as pd
import pymssql

# Display app header
st.title("Barcode Data Entry System")
st.subheader("Enter part information manually")

# Initialize connection
@st.cache_resource
def init_connection():
    try:
        return pymssql.connect(
            server=st.secrets["database"]["db_server"],
            database=st.secrets["database"]["db_database"],
            user=st.secrets["database"]["db_username"],
            password=st.secrets["database"]["db_password"]
        )
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

# Get table name from secrets
try:
    TABLE_NAME = st.secrets["database"]["db_table"]
except:
    TABLE_NAME = "StockOfParts"

# Perform query
@st.cache_data(ttl=600)
def run_query(query, params=None):
    conn = init_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(as_dict=True) as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            else:
                conn.commit()
                return True
    except Exception as e:
        st.error(f"Query error: {e}")
        return None

# Create table if it doesn't exist
def create_table():
    query = f"""
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
    """
    return run_query(query)

# Count SKU entries
def count_sku_entries(sku):
    query = f"SELECT COUNT(*) AS count FROM {TABLE_NAME} WHERE SKU = %s"
    result = run_query(query, (sku,))
    if result:
        return result[0]['count']
    return 0

# Insert new entry
def insert_entry(sku, manufacturer, part_number, nth_entry):
    query = f"""
    INSERT INTO {TABLE_NAME} (SKU, manufacturer, manufacturer_part_number, nth_entry) 
    VALUES (%s, %s, %s, %s)
    """
    return run_query(query, (sku, manufacturer, part_number, nth_entry))

# Get all entries
def get_all_entries():
    query = f"SELECT * FROM {TABLE_NAME} ORDER BY id DESC"
    result = run_query(query)
    if result:
        return pd.DataFrame(result)
    return pd.DataFrame()

# Create the table if it doesn't exist
create_table()

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