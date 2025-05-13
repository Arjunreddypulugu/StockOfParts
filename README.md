# Barcode Data Entry System

A Streamlit application for entering and tracking inventory parts with barcode scanning capabilities.

## Features

- Manual data entry for SKU, manufacturer, and manufacturer part number
- Barcode scanning for SKU and manufacturer part number
- Automatic tracking of duplicate SKUs
- Database storage of all entries

## Requirements

- Python 3.7+
- SQL Server database (with ODBC Driver 17 for SQL Server)
- Webcam for barcode scanning

## Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/barcode-data-entry.git
cd barcode-data-entry
```

2. Install the required packages:
```
pip install -r requirements.txt
```

3. Configure the database:
   - The application is pre-configured to connect to the SQL Server database
   - If needed, edit the `config.py` file to adjust database connection parameters

## Usage

1. Start the application:
```
streamlit run app.py
```

2. Enter data:
   - Type SKU, manufacturer, and part number manually
   - Or use the "Scan" buttons to scan barcodes for SKU and part number
   - The application will automatically check if the SKU already exists
   
3. Submit the form to save the data to the database

## Troubleshooting

- If the barcode scanner doesn't work, make sure your webcam is properly connected and accessible
- For database connection issues, verify your SQL Server is accessible and the credentials in `config.py` are correct
- If you encounter "Driver not found" errors, ensure you have installed the ODBC Driver 17 for SQL Server 