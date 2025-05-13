import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# Display app header
st.title("Barcode Data Entry System")
st.subheader("Enter part information manually")

# Initialize success flag in session state if not present
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False

# Initialize connection
@st.cache_resource
def init_connection():
    try:
        # Create SQLAlchemy connection string
        password = quote_plus(st.secrets["database"]["db_password"])  # URL encode the password
        conn_str = f"mssql+pymssql://VDRSAdmin:{password}@vdrsapps.database.windows.net/{st.secrets['database']['db_database']}"
        
        # Create engine
        engine = create_engine(conn_str)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            
        return engine
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

# Get table name from secrets
try:
    TABLE_NAME = st.secrets["database"]["db_table"]
except:
    TABLE_NAME = "StockOfParts"

# Perform query
def run_query(query, params=None):
    engine = init_connection()
    if not engine:
        return None
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params if params else {})
            conn.commit()
            
            if query.strip().upper().startswith("SELECT"):
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                return rows
            return True
            
    except Exception as e:
        st.error(f"Query error: {str(e)}")
        return None

# Create table if it doesn't exist
def create_table():
    query = f"""
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{TABLE_NAME}')
    BEGIN
        CREATE TABLE {TABLE_NAME} (
            SKU VARCHAR(255),
            manufacturer VARCHAR(255),
            manufacturer_part_number VARCHAR(255),
            nth_entry INT
        )
    END
    """
    return run_query(query)

# Get next nth_entry value for a SKU
def get_next_nth_entry(sku):
    query = f"""
    SELECT COUNT(*) as entry_count
    FROM {TABLE_NAME} WITH (NOLOCK)
    WHERE SKU = :sku
    """
    try:
        result = run_query(query, {"sku": sku})
        if result and result[0]:
            count = int(result[0]['entry_count'])
            return count + 1
        return 1
    except Exception as e:
        st.error(f"Error getting next nth_entry: {str(e)}")
        return 1

# Insert new entry
def insert_entry(sku, manufacturer, part_number):
    try:
        # Get the next nth_entry value
        next_entry = get_next_nth_entry(sku)
        
        # Insert the new record
        query = f"""
        INSERT INTO {TABLE_NAME} (SKU, manufacturer, manufacturer_part_number, nth_entry) 
        VALUES (:sku, :manufacturer, :part_number, :nth_entry)
        """
        params = {
            "sku": sku,
            "manufacturer": manufacturer,
            "part_number": part_number,
            "nth_entry": next_entry
        }
        return run_query(query, params)
    except Exception as e:
        st.error(f"Error inserting entry: {str(e)}")
        return False

# Get all entries
def get_all_entries():
    query = f"""
    SELECT SKU, manufacturer, manufacturer_part_number, nth_entry 
    FROM {TABLE_NAME} WITH (NOLOCK)
    ORDER BY SKU, nth_entry DESC
    """
    try:
        result = run_query(query)
        if result:
            return pd.DataFrame(result)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error getting entries: {str(e)}")
        return pd.DataFrame()

# Create the table if it doesn't exist
create_table()

# If form was just submitted successfully, clear the session state
if st.session_state.form_submitted:
    st.session_state.form_submitted = False
    st.rerun()

# Create form for data entry
with st.form("data_entry_form"):
    # SKU input
    sku = st.text_input("SKU (e.g., 999.000.932)", key="sku_input", value="")
    
    # Manufacturer input
    manufacturer = st.text_input("Manufacturer (e.g., Siemens, Schneider, Pils)", key="manufacturer_input", value="")
    
    # Manufacturer part number input
    part_number = st.text_input("Manufacturer Part Number (e.g., L24DF3)", key="part_number_input", value="")
    
    # Submit button
    submit_button = st.form_submit_button("Submit")
    
    if submit_button:
        if not sku or not manufacturer or not part_number:
            st.error("Please fill in all fields.")
        else:
            if insert_entry(sku, manufacturer, part_number):
                st.success("Data saved successfully!")
                st.session_state.form_submitted = True
                st.rerun()

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