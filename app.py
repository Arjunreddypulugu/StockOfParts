import streamlit as st
import time
import pandas as pd
from barcode_scanner import scan_barcode
from database import create_table_if_not_exists, count_sku_entries, insert_entry, get_all_entries, SQLALCHEMY_AVAILABLE

def main():
    # Page title and description
    st.title("Barcode Data Entry System")
    st.subheader("Enter part information manually or scan barcodes")
    
    # Check if database functionality is available
    db_available = create_table_if_not_exists()
    
    if not db_available:
        st.warning("Database connection failed. Running in demo mode with local storage only.")
        # Initialize session state for local storage
        if 'entries' not in st.session_state:
            st.session_state.entries = []
    
    # Create form for data entry
    with st.form("data_entry_form"):
        # SKU input with barcode scan button
        col1, col2 = st.columns([3, 1])
        with col1:
            sku = st.text_input("SKU (e.g., 999.000.932)", key="sku_input")
        with col2:
            if st.form_submit_button("Scan SKU"):
                st.session_state.scan_target = "sku"
                st.session_state.scanning = True
                st.rerun()
        
        # Manufacturer input
        manufacturer = st.text_input("Manufacturer (e.g., Siemens, Schneider, Pils)", key="manufacturer_input")
        
        # Manufacturer part number input with barcode scan button
        col3, col4 = st.columns([3, 1])
        with col3:
            part_number = st.text_input("Manufacturer Part Number (e.g., L24DF3)", key="part_number_input")
        with col4:
            if st.form_submit_button("Scan Part #"):
                st.session_state.scan_target = "part_number"
                st.session_state.scanning = True
                st.rerun()
        
        # Display SKU count information
        if sku:
            if db_available:
                # Get count from database
                count = count_sku_entries(sku)
            else:
                # Count SKUs in local storage
                count = sum(1 for entry in st.session_state.entries if entry['sku'] == sku)
            
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
                success = False
                if db_available:
                    # Insert into database
                    success = insert_entry(sku, manufacturer, part_number, nth_entry)
                else:
                    # Add to local storage
                    st.session_state.entries.append({
                        'sku': sku,
                        'manufacturer': manufacturer,
                        'manufacturer_part_number': part_number,
                        'nth_entry': nth_entry
                    })
                    success = True
                
                if success:
                    st.success("Data successfully saved!")
                    # Clear the form
                    st.session_state.sku_input = ""
                    st.session_state.manufacturer_input = ""
                    st.session_state.part_number_input = ""
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to save data. Please try again.")

    # Display entries
    if db_available:
        # Get entries from database
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
    elif 'entries' in st.session_state and st.session_state.entries:
        # Display local entries
        st.subheader("Saved Entries (Local Storage)")
        df = pd.DataFrame(st.session_state.entries)
        st.dataframe(df)
        
        # Add a button to download as CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name="barcode_entries.csv",
            mime="text/csv"
        )
        
        # Add a button to clear local storage
        if st.button("Clear Local Storage"):
            st.session_state.entries = []
            st.rerun()

    # Handle barcode scanning
    if 'scanning' not in st.session_state:
        st.session_state.scanning = False
    
    if 'scan_target' not in st.session_state:
        st.session_state.scan_target = None
    
    if st.session_state.scanning:
        with st.spinner("Scanning barcode... Press 'q' to cancel."):
            barcode_data = scan_barcode()
            
            if barcode_data:
                if st.session_state.scan_target == "sku":
                    st.session_state.sku_input = barcode_data
                elif st.session_state.scan_target == "part_number":
                    st.session_state.part_number_input = barcode_data
                
                st.success(f"Barcode scanned: {barcode_data}")
            else:
                st.error("No barcode detected or scan was cancelled.")
            
            st.session_state.scanning = False
            st.session_state.scan_target = None
            st.rerun()

if __name__ == "__main__":
    main() 