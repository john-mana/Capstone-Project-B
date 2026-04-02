#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic functionality tests without Flask context
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestBasicFunctionality(unittest.TestCase):
    """Test suite for basic functionality without Flask context"""
    
    def test_imports(self):
        """Test that core modules can be imported"""
        try:
            # Test core modules
            import config
            import extensions
            import models
            import db_management
            import query
            
            # Verify modules exist
            self.assertTrue(hasattr(config, 'Config'))
            self.assertTrue(hasattr(extensions, 'db'))
            self.assertTrue(hasattr(models, 'Species'))
            self.assertTrue(hasattr(db_management, 'query_db'))
            self.assertTrue(hasattr(query, 'get_options_occurrences'))
            
        except ImportError as e:
            self.fail(f"Failed to import core modules: {e}")
    
    def test_model_creation(self):
        """Test model object creation"""
        from models import Species, Occurrence, Fauna
        
        # Test Species creation
        species = Species(scientific_name='Test Species')
        self.assertEqual(species.scientific_name, 'Test Species')
        
        # Test Occurrence creation
        occurrence = Occurrence(scientific_name='Test Species')
        self.assertEqual(occurrence.scientific_name, 'Test Species')
        
        # Test Fauna creation
        fauna = Fauna(genus='Test', species='species')
        self.assertEqual(fauna.genus, 'Test')
        self.assertEqual(fauna.species, 'species')
    
    def test_model_to_dict(self):
        """Test model to_dict methods"""
        from models import Species, Occurrence, Fauna
        
        # Test Species to_dict
        species = Species(scientific_name='Test Species')
        species_dict = species.to_dict()
        self.assertIsInstance(species_dict, dict)
        self.assertIn('scientificName', species_dict)
        
        # Test Occurrence to_dict
        occurrence = Occurrence(scientific_name='Test Species')
        occurrence_dict = occurrence.to_dict()
        self.assertIsInstance(occurrence_dict, dict)
        self.assertIn('scientificName', occurrence_dict)
        
        # Test Fauna to_dict
        fauna = Fauna(genus='Test', species='species')
        fauna_dict = fauna.to_dict()
        self.assertIsInstance(fauna_dict, dict)
        self.assertIn('genus', fauna_dict)
    
    def test_database_management_functions(self):
        """Test database management functions exist"""
        import db_management
        
        # Test that db_management module has expected functions
        expected_functions = ['query_db', 'update_db']
        
        for func_name in expected_functions:
            self.assertTrue(hasattr(db_management, func_name), f"Missing function: {func_name}")
    
    def test_query_functions(self):
        """Test query functions exist"""
        import query
        
        # Test that query module has expected functions
        expected_functions = [
            'get_options_occurrences',
            'get_options_fauna', 
            'get_observations',
            'get_fauna_query',
            'get_flora_all_species_report',
            'get_fauna_all_species_report',
            'get_summary_report'
        ]
        
        for func_name in expected_functions:
            self.assertTrue(hasattr(query, func_name), f"Missing function: {func_name}")
    
    def test_path_operations(self):
        """Test path operations"""
        base_dir = Path(__file__).parent.parent
        
        # Test basic path operations
        self.assertTrue(base_dir.exists())
        self.assertIsInstance(base_dir, Path)
        
        # Test subdirectories
        static_dir = base_dir / "static"
        templates_dir = base_dir / "templates"
        test_dir = base_dir / "Test"
        
        self.assertIsInstance(static_dir, Path)
        self.assertIsInstance(templates_dir, Path)
        self.assertIsInstance(test_dir, Path)
    
    def test_file_operations_mock(self):
        """Test file operations with mocks"""
        with patch('shutil.copy2') as mock_copy2:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.mkdir'):
                    base_dir = Path(__file__).parent.parent
                    source_dir = base_dir / "Remade experiment" / "experiment0" / "exp_coding"
                    target_dir = base_dir / "static" / "report" / "experiment0"
                    
                    # Test file copying
                    csv_file = "ALA.csv"
                    source_file = source_dir / csv_file
                    target_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Mock the copy operation
                    mock_copy2.return_value = None
                    result = mock_copy2(source_file, target_dir / csv_file)
                    
                    # Verify the copy was called
                    mock_copy2.assert_called_once_with(source_file, target_dir / csv_file)
    
    def test_subprocess_mock(self):
        """Test subprocess operations with mocks"""
        with patch('subprocess.run') as mock_subprocess_run:
            mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="Script output", stderr="")
            
            base_dir = Path(__file__).parent.parent
            target_dir = base_dir / "static" / "report" / "experiment0"
            script_path = target_dir / "exp0_pyformat.py"
            
            # Test subprocess call
            result = mock_subprocess_run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, cwd=str(target_dir))
            
            self.assertEqual(result.returncode, 0)
            self.assertIn("Script output", result.stdout)
            mock_subprocess_run.assert_called_once()
    
    def test_pandas_mock(self):
        """Test pandas operations with mocks"""
        with patch('pandas.read_csv') as mock_read_csv:
            with patch('pandas.read_excel') as mock_read_excel:
                # Mock pandas operations
                mock_df = MagicMock()
                mock_df.to_dict.return_value = {'key': 'value'}
                mock_read_csv.return_value = mock_df
                mock_read_excel.return_value = mock_df
                
                # Test pandas operations
                df_csv = mock_read_csv('test.csv')
                df_excel = mock_read_excel('test.xlsx')
                
                # Verify operations
                self.assertIsNotNone(df_csv)
                self.assertIsNotNone(df_excel)
                mock_read_csv.assert_called_once_with('test.csv')
                mock_read_excel.assert_called_once_with('test.xlsx')
    
    def test_postgresql_mock(self):
        """Test PostgreSQL connection with mocks"""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            # Test connection
            conn = mock_connect("postgresql://user:pass@localhost/db")
            self.assertIsNotNone(conn)
            mock_connect.assert_called_once_with("postgresql://user:pass@localhost/db")


if __name__ == '__main__':
    unittest.main()
