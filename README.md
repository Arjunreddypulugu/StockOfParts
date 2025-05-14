# Barcode Data Entry System

A Streamlit application for barcode-based data entry with SQL Server integration. This app allows users to scan barcodes for SKUs and part numbers, and store the data in a SQL Server database.

## Features

- Barcode scanning for SKU and part number fields
- Integration with SQL Server database
- Duplicate SKU detection
- Data export to CSV
- Mobile-friendly interface

## Installation

1. Clone this repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Create a `config.py` file based on the `config_template.py` file with your SQL Server credentials:

```python
# Database configuration
DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': 'your-server-name',
    'database': 'your-database-name',
    'username': 'your-username',
    'password': 'your-password'
}

# Table name
TABLE_NAME = 'StockOfParts'  # Change this to your actual table name
```

4. Alternatively, set up Streamlit secrets:

Create a `.streamlit/secrets.toml` file with:

```toml
[database]
db_driver = "ODBC Driver 17 for SQL Server"
db_server = "your-server-name"
db_database = "your-database-name"
db_username = "your-username"
db_password = "your-password"
db_table = "StockOfParts"
```

## Usage

1. Start the Streamlit app:

```bash
streamlit run app.py
```

2. The app will open in your default web browser.

3. To enter data:
   - Enter the SKU manually or click "Scan SKU" to scan a barcode
   - Enter the manufacturer name
   - Enter the part number manually or click "Scan Part #" to scan a barcode
   - Click "Submit" to save the data

4. The app will display all entered data in a table below the form.

5. You can download the data as a CSV file using the "Download Data as CSV" button.

## Barcode Scanning

The app supports scanning of various barcode formats including:
- QR codes
- Code 128
- Code 39
- UPC-A
- UPC-E
- EAN-8
- EAN-13
- And more

When you click a scan button:
1. The app will switch to the scanner page
2. Point your device's camera at the barcode
3. Once scanned, the value will be automatically populated in the form
4. If automatic detection doesn't work, you can enter the value manually and click "Use This Value"

## Database Structure

The app uses a SQL Server table with the following structure:

```sql
CREATE TABLE StockOfParts (
    SKU VARCHAR(255),
    manufacturer VARCHAR(255),
    manufacturer_part_number VARCHAR(255),
    is_duplicate VARCHAR(255)
)
```

## Troubleshooting

- **Camera access issues**: Make sure your browser has permission to access your camera.
- **Database connection errors**: Check your database credentials and ensure your SQL Server is accessible from your network.
- **Barcode scanning not working**: Try using the manual entry option as a fallback.

## Requirements

- Python 3.7+
- Streamlit 1.26.0+
- SQL Server database
- Web browser with camera access (for barcode scanning)
- Internet connection (for loading the HTML5 QR code library)

## License

This project is licensed under the MIT License - see the LICENSE file for details. 