#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive tests for db_management.py
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, date
from sqlalchemy import text

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestDbManagement(unittest.TestCase):
    """Test suite for db_management.py functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock Flask-SQLAlchemy db instance
        self.mock_db = MagicMock()
        self.mock_session = MagicMock()
        self.mock_db.session = self.mock_session
        
        # Mock query result
        self.mock_result = MagicMock()
        self.mock_row = MagicMock()
        self.mock_row._mapping = {'id': 1, 'name': 'Test', 'created_at': datetime(2023, 1, 1)}
        self.mock_result.fetchall.return_value = [self.mock_row]
        self.mock_session.execute.return_value = self.mock_result
    
    def test_query_db_basic(self):
        """Test basic query_db functionality"""
        from db_management import query_db
        
        # Test basic query
        result = query_db(self.mock_db, "SELECT * FROM test_table")
        
        # Verify session.execute was called
        self.mock_session.execute.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 1)
        self.assertEqual(result[0]['name'], 'Test')
    
    def test_query_db_with_args(self):
        """Test query_db with parameters"""
        from db_management import query_db
        
        args = {'id': 1, 'name': 'Test'}
        result = query_db(self.mock_db, "SELECT * FROM test_table WHERE id = :id", args)
        
        # Verify session.execute was called with correct parameters
        self.mock_session.execute.assert_called_once()
        self.assertIsInstance(result, list)
    
    def test_query_db_one_result(self):
        """Test query_db with one=True"""
        from db_management import query_db
        
        result = query_db(self.mock_db, "SELECT * FROM test_table", one=True)
        
        # Verify session.execute was called
        self.mock_session.execute.assert_called_once()
        self.assertIsInstance(result, dict)
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['name'], 'Test')
    
    def test_query_db_one_result_empty(self):
        """Test query_db with one=True and no results"""
        from db_management import query_db
        
        # Mock empty result
        self.mock_result.fetchall.return_value = []
        
        result = query_db(self.mock_db, "SELECT * FROM test_table", one=True)
        
        # Should return None for empty results
        self.assertIsNone(result)
    
    def test_query_db_date_processing(self):
        """Test query_db with date/datetime processing"""
        from db_management import query_db
        
        # Mock result with datetime
        mock_row_with_date = MagicMock()
        mock_row_with_date._mapping = {
            'id': 1, 
            'name': 'Test',
            'created_at': datetime(2023, 1, 1, 12, 30, 45),
            'birth_date': date(2023, 1, 1)
        }
        self.mock_result.fetchall.return_value = [mock_row_with_date]
        
        result = query_db(self.mock_db, "SELECT * FROM test_table")
        
        # Verify date processing
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['created_at'], '2023-01-01T12:30:45')
        self.assertEqual(result[0]['birth_date'], '2023-01-01')
    
    def test_query_db_exception_handling(self):
        """Test query_db exception handling"""
        from db_management import query_db
        
        # Mock exception
        self.mock_session.execute.side_effect = Exception("Database error")
        
        with patch('sys.stderr') as mock_stderr:
            result = query_db(self.mock_db, "SELECT * FROM test_table")
            
            # Should return empty list on exception
            self.assertEqual(result, [])
            # Should print error to stderr
            mock_stderr.write.assert_called()
    
    def test_query_db_paginated_basic(self):
        """Test basic query_db_paginated functionality"""
        from db_management import query_db_paginated
        
        result = query_db_paginated(self.mock_db, "SELECT * FROM test_table", 1, 10)
        
        # Verify session.execute was called with pagination
        self.mock_session.execute.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
    
    def test_query_db_paginated_with_args(self):
        """Test query_db_paginated with parameters"""
        from db_management import query_db_paginated
        
        args = {'category': 'test'}
        result = query_db_paginated(self.mock_db, "SELECT * FROM test_table WHERE category = :category", 2, 5, args)
        
        # Verify session.execute was called
        self.mock_session.execute.assert_called_once()
        self.assertIsInstance(result, list)
    
    def test_query_db_paginated_offset_calculation(self):
        """Test query_db_paginated offset calculation"""
        from db_management import query_db_paginated
        
        # Test different page numbers
        test_cases = [
            (1, 10, 0),   # Page 1, 10 per page, offset 0
            (2, 10, 10),  # Page 2, 10 per page, offset 10
            (3, 5, 10),   # Page 3, 5 per page, offset 10
            (5, 20, 80),  # Page 5, 20 per page, offset 80
        ]
        
        for page_num, per_page, expected_offset in test_cases:
            with self.subTest(page=page_num, per_page=per_page):
                # Reset mock for each test
                self.mock_session.reset_mock()
                
                result = query_db_paginated(self.mock_db, "SELECT * FROM test_table", page_num, per_page)
                
                # Verify session.execute was called with correct parameters
                self.mock_session.execute.assert_called_once()
                call_args = self.mock_session.execute.call_args
                # Check that the call was made with the correct parameters
                self.assertEqual(len(call_args[0]), 2)  # text(query), params
                self.assertIsInstance(call_args[0][1], dict)
                self.assertEqual(call_args[0][1]['limit'], per_page)
                self.assertEqual(call_args[0][1]['offset'], expected_offset)
    
    def test_query_db_paginated_exception_handling(self):
        """Test query_db_paginated exception handling"""
        from db_management import query_db_paginated
        
        # Mock exception
        self.mock_session.execute.side_effect = Exception("Database error")
        
        with patch('sys.stderr') as mock_stderr:
            result = query_db_paginated(self.mock_db, "SELECT * FROM test_table", 1, 10)
            
            # Should return empty list on exception
            self.assertEqual(result, [])
            # Should print error to stderr
            mock_stderr.write.assert_called()
    
    def test_update_db_basic(self):
        """Test basic update_db functionality"""
        from db_management import update_db
        
        result = update_db(self.mock_db, "UPDATE test_table SET name = :name WHERE id = :id", {'name': 'New Name', 'id': 1})
        
        # Verify session.execute and commit were called
        self.mock_session.execute.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.assertTrue(result)
    
    def test_update_db_with_dict_params(self):
        """Test update_db with dictionary parameters"""
        from db_management import update_db
        
        params = {'name': 'Test', 'id': 1}
        result = update_db(self.mock_db, "UPDATE test_table SET name = :name WHERE id = :id", params)
        
        # Verify session.execute was called with correct parameters
        self.mock_session.execute.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.assertTrue(result)
    
    def test_update_db_with_tuple_params(self):
        """Test update_db with tuple parameters"""
        from db_management import update_db
        
        params = ('Test', 1)
        result = update_db(self.mock_db, "UPDATE test_table SET name = ? WHERE id = ?", params)
        
        # Verify session.execute was called with tuple parameters
        self.mock_session.execute.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.assertTrue(result)
    
    def test_update_db_with_list_params(self):
        """Test update_db with list parameters"""
        from db_management import update_db
        
        params = ['Test', 1]
        result = update_db(self.mock_db, "UPDATE test_table SET name = ? WHERE id = ?", params)
        
        # Verify session.execute was called with list parameters
        self.mock_session.execute.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.assertTrue(result)
    
    def test_update_db_no_params(self):
        """Test update_db with no parameters"""
        from db_management import update_db
        
        result = update_db(self.mock_db, "UPDATE test_table SET name = 'Default'")
        
        # Verify session.execute and commit were called
        self.mock_session.execute.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.assertTrue(result)
    
    def test_update_db_exception_handling(self):
        """Test update_db exception handling"""
        from db_management import update_db
        
        # Mock exception
        self.mock_session.execute.side_effect = Exception("Database error")
        
        with patch('sys.stderr') as mock_stderr:
            result = update_db(self.mock_db, "UPDATE test_table SET name = :name", {'name': 'Test'})
            
            # Should return False on exception
            self.assertFalse(result)
            # Should call rollback
            self.mock_session.rollback.assert_called_once()
            # Should print error to stderr
            mock_stderr.write.assert_called()
    
    def test_update_db_commit_exception(self):
        """Test update_db when commit fails"""
        from db_management import update_db
        
        # Mock commit exception
        self.mock_session.commit.side_effect = Exception("Commit error")
        
        with patch('sys.stderr') as mock_stderr:
            result = update_db(self.mock_db, "UPDATE test_table SET name = :name", {'name': 'Test'})
            
            # Should return False on commit exception
            self.assertFalse(result)
            # Should call rollback
            self.mock_session.rollback.assert_called_once()
            # Should print error to stderr
            mock_stderr.write.assert_called()
    
    def test_query_db_empty_args(self):
        """Test query_db with empty args"""
        from db_management import query_db
        
        result = query_db(self.mock_db, "SELECT * FROM test_table", args={})
        
        # Verify session.execute was called
        self.mock_session.execute.assert_called_once()
        self.assertIsInstance(result, list)
    
    def test_query_db_paginated_empty_args(self):
        """Test query_db_paginated with empty args"""
        from db_management import query_db_paginated
        
        result = query_db_paginated(self.mock_db, "SELECT * FROM test_table", 1, 10, args={})
        
        # Verify session.execute was called
        self.mock_session.execute.assert_called_once()
        self.assertIsInstance(result, list)
    
    def test_update_db_empty_params(self):
        """Test update_db with empty params"""
        from db_management import update_db
        
        result = update_db(self.mock_db, "UPDATE test_table SET name = 'Default'", params={})
        
        # Verify session.execute and commit were called
        self.mock_session.execute.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.assertTrue(result)
    
    def test_query_db_multiple_rows(self):
        """Test query_db with multiple rows"""
        from db_management import query_db
        
        # Mock multiple rows
        mock_row1 = MagicMock()
        mock_row1._mapping = {'id': 1, 'name': 'Test1'}
        mock_row2 = MagicMock()
        mock_row2._mapping = {'id': 2, 'name': 'Test2'}
        self.mock_result.fetchall.return_value = [mock_row1, mock_row2]
        
        result = query_db(self.mock_db, "SELECT * FROM test_table")
        
        # Verify multiple rows returned
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 1)
        self.assertEqual(result[0]['name'], 'Test1')
        self.assertEqual(result[1]['id'], 2)
        self.assertEqual(result[1]['name'], 'Test2')
    
    def test_query_db_paginated_date_processing(self):
        """Test query_db_paginated with date/datetime processing"""
        from db_management import query_db_paginated
        
        # Mock result with datetime
        mock_row_with_date = MagicMock()
        mock_row_with_date._mapping = {
            'id': 1, 
            'name': 'Test',
            'created_at': datetime(2023, 1, 1, 12, 30, 45),
            'birth_date': date(2023, 1, 1)
        }
        self.mock_result.fetchall.return_value = [mock_row_with_date]
        
        result = query_db_paginated(self.mock_db, "SELECT * FROM test_table", 1, 10)
        
        # Verify date processing
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['created_at'], '2023-01-01T12:30:45')
        self.assertEqual(result[0]['birth_date'], '2023-01-01')
    
    def test_update_db_insert_operation(self):
        """Test update_db with INSERT operation"""
        from db_management import update_db
        
        params = {'name': 'New Record', 'email': 'test@example.com'}
        result = update_db(self.mock_db, "INSERT INTO test_table (name, email) VALUES (:name, :email)", params)
        
        # Verify session.execute and commit were called
        self.mock_session.execute.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.assertTrue(result)
    
    def test_update_db_delete_operation(self):
        """Test update_db with DELETE operation"""
        from db_management import update_db
        
        params = {'id': 1}
        result = update_db(self.mock_db, "DELETE FROM test_table WHERE id = :id", params)
        
        # Verify session.execute and commit were called
        self.mock_session.execute.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
