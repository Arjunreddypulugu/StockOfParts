import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
import streamlit as st
import sys
import os

# Add the current directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import app functions
from app import insert_entry, get_all_entries, get_all_skus

class TestBarcodeApp(unittest.TestCase):
    
    @patch('app.run_query')
    def test_insert_entry(self, mock_run_query):
        # Setup mock
        mock_run_query.return_value = True
        
        # Test the function
        result = insert_entry("123456", "Test Manufacturer", "ABC123")
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify run_query was called with the right parameters
        mock_run_query.assert_called_once()
        args, kwargs = mock_run_query.call_args
        
        # Check that the query contains the INSERT statement
        self.assertIn("INSERT INTO", args[0])
        
        # Check that the parameters are correct
        self.assertEqual(kwargs['params']['sku'], "123456")
        self.assertEqual(kwargs['params']['manufacturer'], "Test Manufacturer")
        self.assertEqual(kwargs['params']['part_number'], "ABC123")
    
    @patch('app.run_query')
    def test_get_all_skus(self, mock_run_query):
        # Setup mock
        mock_run_query.return_value = [{'SKU': '123'}, {'SKU': '456'}, {'SKU': '789'}]
        
        # Test the function
        result = get_all_skus()
        
        # Verify the result
        self.assertEqual(result, ['123', '456', '789'])
        
        # Verify run_query was called
        mock_run_query.assert_called_once()
    
    @patch('app.run_query')
    def test_get_all_entries(self, mock_run_query):
        # Setup mock
        mock_data = [
            {'SKU': '123', 'manufacturer': 'Test1', 'manufacturer_part_number': 'ABC', 'is_duplicate': 'no'},
            {'SKU': '456', 'manufacturer': 'Test2', 'manufacturer_part_number': 'DEF', 'is_duplicate': 'yes'}
        ]
        mock_run_query.return_value = mock_data
        
        # Test the function
        result = get_all_entries()
        
        # Verify the result is a DataFrame with the right data
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]['SKU'], '123')
        self.assertEqual(result.iloc[1]['manufacturer'], 'Test2')
        
        # Verify run_query was called
        mock_run_query.assert_called_once()

if __name__ == '__main__':
    unittest.main() 