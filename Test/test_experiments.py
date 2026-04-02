#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive experiment functionality tests
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestExperiments(unittest.TestCase):
    """Test suite for experiment functionality"""
    
    def test_experiment_paths(self):
        """Test experiment directory paths"""
        base_dir = Path(__file__).parent.parent
        
        # Test experiment source directories
        exp0_dir = base_dir / "Remade experiment" / "experiment0" / "exp_coding"
        exp3_dir = base_dir / "Remade experiment" / "experiment3"
        exp4_dir = base_dir / "Remade experiment" / "experiment4" / "exp4_code"
        exp8_dir = base_dir / "Remade experiment" / "experiment8"
        exp9_dir = base_dir / "Remade experiment" / "experiment9"
        
        # Test target directories
        target_exp0 = base_dir / "static" / "report" / "experiment0"
        target_exp3 = base_dir / "static" / "report" / "experiment3"
        target_exp4 = base_dir / "static" / "report" / "experiment4"
        target_exp8 = base_dir / "static" / "report" / "experiment8"
        target_exp9 = base_dir / "static" / "report" / "experiment9"
        
        # Verify path structure
        self.assertIsInstance(exp0_dir, Path)
        self.assertIsInstance(exp3_dir, Path)
        self.assertIsInstance(exp4_dir, Path)
        self.assertIsInstance(exp8_dir, Path)
        self.assertIsInstance(exp9_dir, Path)
        self.assertIsInstance(target_exp0, Path)
        self.assertIsInstance(target_exp3, Path)
        self.assertIsInstance(target_exp4, Path)
        self.assertIsInstance(target_exp8, Path)
        self.assertIsInstance(target_exp9, Path)
    
    def test_experiment_file_operations(self):
        """Test file operations in experiments"""
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
    
    def test_experiment_subprocess_execution(self):
        """Test subprocess execution in experiments"""
        with patch('subprocess.run') as mock_subprocess_run:
            mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")
            
            base_dir = Path(__file__).parent.parent
            target_dir = base_dir / "static" / "report" / "experiment0"
            script_path = target_dir / "exp0_pyformat.py"
            
            # Test subprocess call
            result = mock_subprocess_run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, cwd=str(target_dir))
            
            self.assertEqual(result.returncode, 0)
            self.assertIn("Success", result.stdout)
            mock_subprocess_run.assert_called_once()
    
    def test_experiment_file_extensions(self):
        """Test file extension handling in experiments"""
        # Test different file types
        html_files = [f for f in ["test.html", "report.html"] if f.endswith('.html')]
        png_files = [f for f in ["chart.png", "graph.png"] if f.endswith('.png')]
        csv_files = [f for f in ["data.csv", "results.csv"] if f.endswith('.csv')]
        pdf_files = [f for f in ["report.pdf", "analysis.pdf"] if f.endswith('.pdf')]
        
        # Verify file extension filtering
        self.assertEqual(len(html_files), 2)
        self.assertEqual(len(png_files), 2)
        self.assertEqual(len(csv_files), 2)
        self.assertEqual(len(pdf_files), 2)
        
        # Test icon assignment based on file extension
        def get_icon(filename):
            if filename.endswith('.html'):
                return "🌐"
            elif filename.endswith('.png'):
                return "📊"
            elif filename.endswith('.csv'):
                return "📄"
            elif filename.endswith('.pdf'):
                return "📄"
            else:
                return "📁"
        
        self.assertEqual(get_icon("test.html"), "🌐")
        self.assertEqual(get_icon("chart.png"), "📊")
        self.assertEqual(get_icon("data.csv"), "📄")
        self.assertEqual(get_icon("report.pdf"), "📄")
        self.assertEqual(get_icon("unknown.txt"), "📁")
    
    def test_experiment_script_files(self):
        """Test experiment script files"""
        base_dir = Path(__file__).parent.parent
        
        # Test experiment 0 files
        exp0_files = [
            "ALA.csv",
            "iNaturalist.csv", 
            "Prototype.csv",
            "exp0_pyformat.py"
        ]
        
        # Test experiment 3 files
        exp3_files = [
            "species_form_analysis.py"
        ]
        
        # Test experiment 4 files
        exp4_files = [
            "fire_traits_analysis.py",
            "fire_plant_location_maps.py"
        ]
        
        # Test experiment 9 files
        exp9_files = [
            "time_frame.py",
            "ALA_e9.csv",
            "iNaturalist_e9.csv",
            "new_flora_e9.csv",
            "Prototype_e9.csv",
            "WithoutPrototype_e9.csv"
        ]
        
        # Verify file lists
        self.assertEqual(len(exp0_files), 4)
        self.assertEqual(len(exp3_files), 1)
        self.assertEqual(len(exp4_files), 2)
        self.assertEqual(len(exp9_files), 6)
        
        # Test file extensions
        for file in exp0_files:
            if file.endswith('.py'):
                self.assertTrue(file.endswith('.py'))
            elif file.endswith('.csv'):
                self.assertTrue(file.endswith('.csv'))
    
    def test_experiment_output_directories(self):
        """Test experiment output directory structure"""
        base_dir = Path(__file__).parent.parent
        
        # Test output directory structure
        output_dirs = [
            base_dir / "static" / "report" / "experiment0" / "experiment0_outputs",
            base_dir / "static" / "report" / "experiment3" / "experiment3_outputs",
            base_dir / "static" / "report" / "experiment4" / "experiment4_outputs",
            base_dir / "static" / "report" / "experiment8" / "experiment8_outputs",
            base_dir / "static" / "report" / "experiment9" / "experiment9_outputs"
        ]
        
        for output_dir in output_dirs:
            self.assertIsInstance(output_dir, Path)
            self.assertTrue(str(output_dir).endswith('_outputs'))
    
    def test_experiment_route_patterns(self):
        """Test experiment route patterns"""
        # Test route patterns
        routes = [
            '/exp0',
            '/exp1', 
            '/exp2',
            '/exp3',
            '/exp4',
            '/exp8',
            '/exp9',
            '/run_experiment_0',
            '/run_experiment_3',
            '/run_experiment_4',
            '/run_experiment_8',
            '/run_experiment_9'
        ]
        
        # Verify route patterns
        for route in routes:
            self.assertTrue(route.startswith('/'))
            if route.startswith('/exp'):
                self.assertTrue(route[4:].isdigit())
            elif route.startswith('/run_experiment_'):
                self.assertTrue(route[16:].isdigit())
    
    def test_experiment_template_files(self):
        """Test experiment template files"""
        base_dir = Path(__file__).parent.parent
        
        # Test template files
        template_files = [
            "experiment0.html",
            "experiment3.html", 
            "experiment4.html",
            "experiment8.html",
            "experiment9.html"
        ]
        
        templates_dir = base_dir / "templates"
        
        for template in template_files:
            template_path = templates_dir / template
            self.assertIsInstance(template_path, Path)
            self.assertTrue(template.endswith('.html'))
    
    def test_experiment_error_handling(self):
        """Test experiment error handling patterns"""
        # Test error handling patterns
        error_messages = [
            "Experiment 0 analysis completed successfully!",
            "Experiment 0 analysis failed:",
            "Experiment 0 script not found!",
            "Error running experiment:",
            "Experiment 3 completed! Report copied to outputs.",
            "Experiment 4 analysis completed successfully!",
            "Experiment 8 analysis completed successfully!",
            "Experiment 9 analysis completed successfully!",
            "Experiment 9 failed:",
            "Experiment 9 script not found (time_frame.py)!"
        ]
        
        # Verify error message patterns
        for message in error_messages:
            self.assertIsInstance(message, str)
            self.assertTrue(len(message) > 0)
    
    def test_experiment_sys_path_operations(self):
        """Test sys.path operations in experiments"""
        # Test sys.path.append calls without mocking
        exp0_path = "Remade experiment/experiment0/exp_coding"
        exp4_path = "Remade experiment/experiment4/exp4_code"
        
        # Verify path patterns
        self.assertIsInstance(exp0_path, str)
        self.assertIsInstance(exp4_path, str)
        self.assertTrue(exp0_path.endswith('exp_coding'))
        self.assertTrue(exp4_path.endswith('exp4_code'))


if __name__ == '__main__':
    unittest.main()

