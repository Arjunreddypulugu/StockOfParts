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
    
    return f"""
    <div style="width: 100%;">
        <div id="scanner-container-{component_id}" style="display: none;">
            <div id="{component_id}" style="width: 100%;"></div>
        </div>
        <button id="start-{component_id}" style="background-color: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 10px;">
            Start Camera
        </button>
        <button id="stop-{component_id}" style="display: none; background-color: #f44336; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; margin-left: 10px;">
            Stop Camera
        </button>
        <div id="result-{component_id}" style="margin-top: 10px;"></div>
    </div>
    
    <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
    <script>
        let html5QrCode_{component_id};
        const startButton = document.getElementById("start-{component_id}");
        const stopButton = document.getElementById("stop-{component_id}");
        const scannerContainer = document.getElementById("scanner-container-{component_id}");
        const resultContainer = document.getElementById("result-{component_id}");
        
        // Function to send data back to Streamlit
        function updateStreamlitField(value) {{
            // Update URL parameters and reload
            const url = new URL(window.location.href);
            url.searchParams.set("{target_field}_value", value);
            window.location.href = url.toString();
        }}
        
        startButton.addEventListener("click", function() {{
            // Show scanner and stop button
            scannerContainer.style.display = "block";
            startButton.style.display = "none";
            stopButton.style.display = "inline-block";
            resultContainer.innerHTML = "Scanning... Point camera at barcode";
            
            // Initialize scanner
            html5QrCode_{component_id} = new Html5Qrcode("{component_id}");
            
            // Start scanning
            html5QrCode_{component_id}.start(
                {{ facingMode: "environment" }},  // Use back camera
                {{
                    fps: 10,
                    qrbox: 250
                }},
                (decodedText, decodedResult) => {{
                    // On successful scan
                    console.log(`Scan result: ${{decodedText}}`, decodedResult);
                    
                    // Stop scanning
                    html5QrCode_{component_id}.stop().then(() => {{
                        // Update UI
                        scannerContainer.style.display = "none";
                        startButton.style.display = "inline-block";
                        stopButton.style.display = "none";
                        resultContainer.innerHTML = `<div style="color: green; font-weight: bold;">Scanned: ${{decodedText}}</div>`;
                        
                        // Update Streamlit field
                        updateStreamlitField(decodedText);
                    }});
                }},
                (errorMessage) => {{
                    // Ignore errors
                }}
            ).catch((err) => {{
                console.error(`Unable to start scanning: ${{err}}`);
                resultContainer.innerHTML = `<div style="color: red;">Error starting camera: ${{err}}</div>`;
                startButton.style.display = "inline-block";
                stopButton.style.display = "none";
            }});
        }});
        
        stopButton.addEventListener("click", function() {{
            if (html5QrCode_{component_id}) {{
                html5QrCode_{component_id}.stop().then(() => {{
                    scannerContainer.style.display = "none";
                    startButton.style.display = "inline-block";
                    stopButton.style.display = "none";
                    resultContainer.innerHTML = "";
                }}).catch((err) => {{
                    console.error(`Error stopping scanner: ${{err}}`);
                }});
            }}
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
    col1, col2 = st.columns([3, 1])
    with col1:
        sku = st.text_input("Enter SKU manually or scan barcode", key="sku_input", value=st.session_state.scanned_sku)
    with col2:
        st.write("")
        st.write("")
        st.components.v1.html(barcode_scanner_html("sku"), height=200)
    
    # Manufacturer input
    manufacturer = st.text_input("Manufacturer (e.g., Siemens, Schneider, Pils)", key="manufacturer_input", value="")
    
    # Manufacturer part number input with barcode scanner
    st.subheader("Manufacturer Part Number")
    col1, col2 = st.columns([3, 1])
    with col1:
        part_number = st.text_input("Enter Part Number manually or scan barcode", key="part_number_input", value=st.session_state.scanned_part_number)
    with col2:
        st.write("")
        st.write("")
        st.components.v1.html(barcode_scanner_html("part_number"), height=200)
    
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