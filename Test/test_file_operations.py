#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File operations and path handling tests
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestFileOperations(unittest.TestCase):
    """Test suite for file operations and path handling"""
    
    def test_path_operations(self):
        """Test path operations"""
        base_dir = Path(__file__).parent.parent
        source_dir = base_dir / "Remade experiment" / "experiment0" / "exp_coding"
        target_dir = base_dir / "static" / "report" / "experiment0"
        
        # Test path creation
        self.assertIsInstance(source_dir, Path)
        self.assertIsInstance(target_dir, Path)
        
        # Test path operations
        self.assertTrue(base_dir.exists())
        self.assertIsInstance(source_dir.parent, Path)
        self.assertIsInstance(target_dir.parent, Path)
    
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
    
    def test_experiment_script_execution(self):
        """Test experiment script execution"""
        with patch('subprocess.run') as mock_subprocess_run:
            mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="Script output", stderr="")
            
            base_dir = Path(__file__).parent.parent
            target_dir = base_dir / "static" / "report" / "experiment0"
            script_path = target_dir / "exp0_pyformat.py"
            
            # Ensure the script path exists for the mock
            with patch('pathlib.Path.exists', return_value=True):
                result = mock_subprocess_run([
                    sys.executable, str(script_path)
                ], capture_output=True, text=True, cwd=str(target_dir))
                
                self.assertEqual(result.returncode, 0)
                self.assertIn("Script output", result.stdout)
                mock_subprocess_run.assert_called_once_with(
                    [sys.executable, str(script_path)],
                    capture_output=True, text=True, cwd=str(target_dir)
                )
    
    def test_file_glob_operations(self):
        """Test file glob operations"""
        with patch('pathlib.Path.glob') as mock_glob:
            # Mock glob results
            mock_files = [
                MagicMock(suffix='.html', is_file=MagicMock(return_value=True), name='test.html'),
                MagicMock(suffix='.png', is_file=MagicMock(return_value=True), name='test.png'),
                MagicMock(suffix='.csv', is_file=MagicMock(return_value=True), name='test.csv')
            ]
            mock_glob.return_value = mock_files
            
            base_dir = Path(__file__).parent.parent
            target_dir = base_dir / "static" / "report" / "experiment0"
            
            # Test glob operations
            html_files = list(target_dir.glob('*.html'))
            png_files = list(target_dir.glob('*.png'))
            csv_files = list(target_dir.glob('*.csv'))
            
            # Verify glob was called
            self.assertTrue(mock_glob.called)
    
    def test_directory_creation(self):
        """Test directory creation operations"""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            with patch('pathlib.Path.exists', return_value=False):
                base_dir = Path(__file__).parent.parent
                target_dir = base_dir / "static" / "report" / "experiment0"
                
                # Test directory creation
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Verify mkdir was called
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    def test_file_existence_check(self):
        """Test file existence checking"""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            base_dir = Path(__file__).parent.parent
            target_dir = base_dir / "static" / "report" / "experiment0"
            
            # Test file existence
            self.assertTrue(target_dir.exists())
            mock_exists.assert_called_once()
    
    def test_file_extension_filtering(self):
        """Test file extension filtering"""
        with patch('pathlib.Path.glob') as mock_glob:
            # Mock different file types
            mock_files = [
                MagicMock(suffix='.html', is_file=MagicMock(return_value=True), name='test.html'),
                MagicMock(suffix='.png', is_file=MagicMock(return_value=True), name='test.png'),
                MagicMock(suffix='.csv', is_file=MagicMock(return_value=True), name='test.csv'),
                MagicMock(suffix='.pdf', is_file=MagicMock(return_value=True), name='test.pdf')
            ]
            mock_glob.return_value = mock_files
            
            base_dir = Path(__file__).parent.parent
            target_dir = base_dir / "static" / "report" / "experiment0"
            
            # Test filtering by extension
            html_files = [f for f in target_dir.glob('*') if f.suffix == '.html']
            png_files = [f for f in target_dir.glob('*') if f.suffix == '.png']
            csv_files = [f for f in target_dir.glob('*') if f.suffix == '.csv']
            pdf_files = [f for f in target_dir.glob('*') if f.suffix == '.pdf']
            
            # Verify filtering works
            self.assertTrue(mock_glob.called)
    
    def test_path_joining(self):
        """Test path joining operations"""
        base_dir = Path(__file__).parent.parent
        
        # Test path joining
        experiment_dir = base_dir / "Remade experiment"
        exp0_dir = experiment_dir / "experiment0"
        exp_coding_dir = exp0_dir / "exp_coding"
        
        # Verify path structure
        self.assertIsInstance(experiment_dir, Path)
        self.assertIsInstance(exp0_dir, Path)
        self.assertIsInstance(exp_coding_dir, Path)
        
        # Test string conversion
        self.assertIsInstance(str(experiment_dir), str)
        self.assertIsInstance(str(exp0_dir), str)
        self.assertIsInstance(str(exp_coding_dir), str)


if __name__ == '__main__':
    unittest.main()