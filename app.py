import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import streamlit.components.v1 as components
import time
import json

# Display app header
st.title("Barcode Data Entry System")
st.subheader("Enter part information manually or scan barcodes")

# Initialize session state variables
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'scanned_sku' not in st.session_state:
    st.session_state.scanned_sku = ""
if 'scanned_part_number' not in st.session_state:
    st.session_state.scanned_part_number = ""

# Callback to update session state when barcode is scanned
def on_barcode_detected(barcode_value, target_field):
    if target_field == "sku":
        st.session_state.scanned_sku = barcode_value
    else:
        st.session_state.scanned_part_number = barcode_value
    st.rerun()

# HTML/JS for barcode scanning using HTML5-QRCode
def barcode_scanner_html(target_field):
    component_id = f"barcode-scanner-{target_field}"
    callback_name = f"on_barcode_detected_{target_field}"
    
    return f"""
    <div style="width: 100%;">
        <div id="{component_id}" style="width: 100%;"></div>
        <button id="stop-{component_id}" style="display:none; background-color: #f44336; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px;">
            Stop Scanner
        </button>
    </div>
    
    <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
    <script>
        // Function to send data back to Streamlit
        function sendToStreamlit(data) {{
            const targetField = "{target_field}";
            if (targetField && data) {{
                // Store in sessionStorage as backup
                sessionStorage.setItem(`scanned_${{targetField}}`, data);
                
                // Send via window.parent.postMessage
                window.parent.postMessage({{
                    type: "streamlit:setComponentValue",
                    key: `scanned_${{targetField}}`,
                    value: data
                }}, "*");
                
                // Use URL parameters as fallback
                const url = new URL(window.location.href);
                url.searchParams.set(`${{targetField}}_value`, data);
                window.location.href = url.toString();
            }}
        }}
        
        // Initialize the scanner when the component is ready
        const html5QrcodeScanner = new Html5QrcodeScanner(
            "{component_id}", 
            {{ 
                fps: 10, 
                qrbox: 250,
                rememberLastUsedCamera: true,
                showTorchButtonIfSupported: true
            }}
        );
        
        // Define success callback
        function onScanSuccess(decodedText, decodedResult) {{
            console.log(`Scan result: ${{decodedText}}`, decodedResult);
            
            // Stop the scanner
            html5QrcodeScanner.clear();
            
            // Display the result
            document.getElementById("{component_id}").innerHTML = 
                `<div style="padding: 20px; background-color: #dff0d8; border-radius: 5px; margin-top: 20px;">
                    <h3 style="color: #3c763d;">Barcode Detected!</h3>
                    <p style="font-size: 18px;"><strong>Value:</strong> ${{decodedText}}</p>
                </div>`;
            
            // Send the value back to Streamlit
            sendToStreamlit(decodedText);
        }}
        
        // Render the scanner
        html5QrcodeScanner.render(onScanSuccess);
        
        // Add stop button functionality
        const stopButton = document.getElementById("stop-{component_id}");
        stopButton.style.display = "block";
        stopButton.addEventListener("click", () => {{
            html5QrcodeScanner.clear();
            document.getElementById("{component_id}").innerHTML = 
                '<div style="padding: 20px; background-color: #f8f9fa; border-radius: 5px;">Scanner stopped</div>';
        }});
    </script>
    """

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
            is_duplicate VARCHAR(255)
        )
    END
    """
    return run_query(query)

# Helper function to get all existing SKUs
def get_all_skus():
    query = f"SELECT SKU FROM {TABLE_NAME}"
    result = run_query(query)
    if result:
        # Convert all SKUs to lowercase strings and strip whitespace
        return [str(row['SKU']).strip().lower() for row in result]
    return []

# Insert new entry
def insert_entry(sku, manufacturer, part_number):
    try:
        # DIRECT SQL APPROACH - Use a CASE statement in the INSERT query itself
        # This will set is_duplicate based on whether the SKU already exists in the table
        insert_query = f"""
        INSERT INTO {TABLE_NAME} (SKU, manufacturer, manufacturer_part_number, is_duplicate) 
        VALUES (
            :sku, 
            :manufacturer, 
            :part_number, 
            CASE 
                WHEN EXISTS (SELECT 1 FROM {TABLE_NAME} WHERE SKU = :sku) THEN 'yes' 
                ELSE 'no' 
            END
        )
        """
        
        success = run_query(insert_query, {
            "sku": sku,
            "manufacturer": manufacturer,
            "part_number": part_number
        })
        
        # Debug: Print the full table after insert
        if success:
            st.write("Insert successful!")
            full_table_query = f"SELECT * FROM {TABLE_NAME}"
            full_table = run_query(full_table_query)
            st.write("Full table after insert:", full_table)
        
        return success
    except Exception as e:
        st.error(f"Error inserting entry: {str(e)}")
        return False

# Get all entries
def get_all_entries():
    query = f"SELECT * FROM {TABLE_NAME}"
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

# Check URL parameters for barcode values
if st.query_params:
    if 'sku_value' in st.query_params:
        st.session_state.scanned_sku = st.query_params['sku_value']
        del st.query_params['sku_value']
    
    if 'part_number_value' in st.query_params:
        st.session_state.scanned_part_number = st.query_params['part_number_value']
        del st.query_params['part_number_value']

# If form was just submitted successfully, clear the session state
if st.session_state.form_submitted:
    st.session_state.form_submitted = False
    st.rerun()

# Create form for data entry
with st.form("data_entry_form"):
    # SKU input with barcode scanner
    st.subheader("SKU")
    sku = st.text_input("Enter SKU manually (e.g., 999.000.932)", key="sku_input", value=st.session_state.scanned_sku)
    
    # Add barcode scanner for SKU
    st.write("Or scan barcode:")
    st.components.v1.html(barcode_scanner_html("sku"), height=400)
    
    # Manufacturer input
    manufacturer = st.text_input("Manufacturer (e.g., Siemens, Schneider, Pils)", key="manufacturer_input", value="")
    
    # Manufacturer part number input with barcode scanner
    st.subheader("Manufacturer Part Number")
    part_number = st.text_input("Enter Manufacturer Part Number manually (e.g., L24DF3)", key="part_number_input", value=st.session_state.scanned_part_number)
    
    # Add barcode scanner for Manufacturer Part Number
    st.write("Or scan barcode:")
    st.components.v1.html(barcode_scanner_html("part_number"), height=400)
    
    # Submit button
    submit_button = st.form_submit_button("Submit")
    
    if submit_button:
        if not sku or not manufacturer or not part_number:
            st.error("Please fill in all fields.")
        else:
            if insert_entry(sku, manufacturer, part_number):
                st.success("Data saved successfully!")
                # Clear the scanned values after submission
                st.session_state.scanned_sku = ""
                st.session_state.scanned_part_number = ""
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