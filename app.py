import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import streamlit.components.v1 as components
import time

# Display app header
st.title("Barcode Data Entry System")
st.subheader("Enter part information manually or scan barcodes")

# Initialize success flag in session state if not present
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False

# Initialize session state for barcode values
if 'scanned_sku' not in st.session_state:
    st.session_state.scanned_sku = ""
if 'scanned_part_number' not in st.session_state:
    st.session_state.scanned_part_number = ""
if 'update_sku' not in st.session_state:
    st.session_state.update_sku = ""
if 'update_part_number' not in st.session_state:
    st.session_state.update_part_number = ""

# Callback functions for barcode scanning
def update_sku(barcode_value):
    st.session_state.scanned_sku = barcode_value
    st.rerun()

def update_part_number(barcode_value):
    st.session_state.scanned_part_number = barcode_value
    st.rerun()

# HTML/JS for barcode scanning
def barcode_scanner(callback_name, field_name):
    return f"""
    <div style="margin-bottom: 20px;">
        <button id="start-scanner-{field_name}" style="background-color: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 10px;">
            Start Scanner for {field_name}
        </button>
        <div id="scanner-container-{field_name}" style="display: none;">
            <div id="reader-{field_name}" style="width: 100%;"></div>
            <button id="stop-scanner-{field_name}" style="background-color: #f44336; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px;">
                Stop Scanner
            </button>
        </div>
        <div id="scanned-result-{field_name}" style="margin-top: 10px; font-weight: bold;"></div>
    </div>

    <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
    <script>
        const startScannerBtn{field_name} = document.getElementById('start-scanner-{field_name}');
        const stopScannerBtn{field_name} = document.getElementById('stop-scanner-{field_name}');
        const scannerContainer{field_name} = document.getElementById('scanner-container-{field_name}');
        const scannedResult{field_name} = document.getElementById('scanned-result-{field_name}');
        let html5QrCode{field_name};

        function updateStreamlitField(value) {{
            // Direct approach - set the value in session state
            window.parent.postMessage({{
                type: "streamlit:setComponentValue",
                value: value,
                dataType: "string",
                key: "{callback_name}"
            }}, "*");
            
            // Also try the callback approach
            window.parent.postMessage({{
                type: "streamlit:componentCommunication",
                data: {{
                    type: "{callback_name}",
                    value: value
                }}
            }}, "*");
        }}

        startScannerBtn{field_name}.addEventListener('click', function() {{
            scannerContainer{field_name}.style.display = 'block';
            startScannerBtn{field_name}.style.display = 'none';
            
            html5QrCode{field_name} = new Html5Qrcode("reader-{field_name}");
            html5QrCode{field_name}.start(
                {{ facingMode: "environment" }}, 
                {{
                    fps: 10,
                    qrbox: 250
                }},
                (decodedText, decodedResult) => {{
                    console.log(`Scan result: ${{decodedText}}`, decodedResult);
                    html5QrCode{field_name}.stop();
                    scannerContainer{field_name}.style.display = 'none';
                    startScannerBtn{field_name}.style.display = 'block';
                    
                    // Display the scanned result
                    scannedResult{field_name}.innerText = `Scanned: ${{decodedText}}`;
                    
                    // Try multiple approaches to update the Streamlit field
                    updateStreamlitField(decodedText);
                    
                    // Force a page reload after a short delay
                    setTimeout(() => {{
                        window.parent.location.reload();
                    }}, 500);
                }},
                (errorMessage) => {{
                    console.log(`QR Code scanning error: ${{errorMessage}}`);
                }}
            ).catch((err) => {{
                console.log(`Unable to start scanner: ${{err}}`);
            }});
        }});

        stopScannerBtn{field_name}.addEventListener('click', function() {{
            if (html5QrCode{field_name}) {{
                html5QrCode{field_name}.stop().then(() => {{
                    scannerContainer{field_name}.style.display = 'none';
                    startScannerBtn{field_name}.style.display = 'block';
                }}).catch((err) => {{
                    console.log(`Error stopping scanner: ${{err}}`);
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

# If form was just submitted successfully, clear the session state
if st.session_state.form_submitted:
    st.session_state.form_submitted = False
    st.rerun()

# Create form for data entry
with st.form("data_entry_form"):
    # SKU input with barcode scanner
    st.subheader("SKU")
    
    # Check if we have a scanned value from the component
    if st.session_state.update_sku:
        st.session_state.scanned_sku = st.session_state.update_sku
        st.session_state.update_sku = ""
    
    sku = st.text_input("Enter SKU manually (e.g., 999.000.932)", key="sku_input", value=st.session_state.scanned_sku)
    
    # Add barcode scanner for SKU
    st.write("Or scan barcode:")
    components.html(barcode_scanner("update_sku", "SKU"), height=300)
    
    # Manufacturer input
    manufacturer = st.text_input("Manufacturer (e.g., Siemens, Schneider, Pils)", key="manufacturer_input", value="")
    
    # Manufacturer part number input with barcode scanner
    st.subheader("Manufacturer Part Number")
    
    # Check if we have a scanned value from the component
    if st.session_state.update_part_number:
        st.session_state.scanned_part_number = st.session_state.update_part_number
        st.session_state.update_part_number = ""
    
    part_number = st.text_input("Enter Manufacturer Part Number manually (e.g., L24DF3)", key="part_number_input", value=st.session_state.scanned_part_number)
    
    # Add barcode scanner for Manufacturer Part Number
    st.write("Or scan barcode:")
    components.html(barcode_scanner("update_part_number", "Part_Number"), height=300)
    
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

# Register the callback functions
components.html(
    """
    <script>
    window.addEventListener('message', function(event) {
        if (event.data.type === 'streamlit:callback') {
            if (event.data.callback_name === 'update_sku') {
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: event.data.args[0],
                    dataType: 'str',
                    key: 'sku_input'
                }, '*');
            } else if (event.data.callback_name === 'update_part_number') {
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: event.data.args[0],
                    dataType: 'str',
                    key: 'part_number_input'
                }, '*');
            }
        }
    });
    </script>
    """,
    height=0,
)

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