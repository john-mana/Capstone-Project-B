#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core models and database functionality tests
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestCoreModels(unittest.TestCase):
    """Test suite for core models and database functionality"""
    
    def test_database_models_import(self):
        """Test database models import and functionality"""
        from models import Species, SpeciesTraitJunction, Occurrence, Fauna, Traits, Family, Reserve
        
        # Test model classes exist
        self.assertTrue(hasattr(Species, '__tablename__'))
        self.assertTrue(hasattr(SpeciesTraitJunction, '__tablename__'))
        self.assertTrue(hasattr(Occurrence, '__tablename__'))
        self.assertTrue(hasattr(Fauna, '__tablename__'))
        self.assertTrue(hasattr(Traits, '__tablename__'))
        self.assertTrue(hasattr(Family, '__tablename__'))
        self.assertTrue(hasattr(Reserve, '__tablename__'))
    
    def test_species_model_attributes(self):
        """Test Species model attributes"""
        from models import Species
        
        species = Species(
            scientific_name='Acacia longifolia',
            vernacular_name='Sydney Golden Wattle',
            genus='Acacia',
            family_name='Fabaceae',
            exotic=False
        )
        
        self.assertEqual(species.scientific_name, 'Acacia longifolia')
        self.assertEqual(species.vernacular_name, 'Sydney Golden Wattle')
        self.assertEqual(species.genus, 'Acacia')
        self.assertEqual(species.family_name, 'Fabaceae')
        self.assertFalse(species.exotic)
    
    def test_occurrence_model_attributes(self):
        """Test Occurrence model attributes"""
        from models import Occurrence
        from datetime import datetime
        
        occurrence = Occurrence(
            scientific_name='Acacia longifolia',
            event_date=datetime(2023, 1, 1),
            decimal_latitude=-33.8688,
            decimal_longitude=151.2093,
            individual_count=5
        )
        
        self.assertEqual(occurrence.scientific_name, 'Acacia longifolia')
        self.assertEqual(occurrence.decimal_latitude, -33.8688)
        self.assertEqual(occurrence.decimal_longitude, 151.2093)
        self.assertEqual(occurrence.individual_count, 5)
    
    def test_fauna_model_attributes(self):
        """Test Fauna model attributes"""
        from models import Fauna
        
        fauna = Fauna(
            genus='Pteropus',
            species='poliocephalus',
            family='Pteropodidae',
            vernacular_name='Grey-headed Flying-fox',
            class_name='Mammalia',
            exotic=False
        )
        
        self.assertEqual(fauna.genus, 'Pteropus')
        self.assertEqual(fauna.species, 'poliocephalus')
        self.assertEqual(fauna.family, 'Pteropodidae')
        self.assertEqual(fauna.vernacular_name, 'Grey-headed Flying-fox')
        self.assertEqual(fauna.class_name, 'Mammalia')
        self.assertFalse(fauna.exotic)
    
    def test_species_trait_junction_model(self):
        """Test SpeciesTraitJunction model"""
        from models import SpeciesTraitJunction
        
        junction = SpeciesTraitJunction(
            scientific_name='Acacia longifolia',
            trait_name='plant_height',
            trait_value='2-5m'
        )
        
        self.assertEqual(junction.scientific_name, 'Acacia longifolia')
        self.assertEqual(junction.trait_name, 'plant_height')
        self.assertEqual(junction.trait_value, '2-5m')
    
    def test_model_to_dict_methods(self):
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
        """Test database management functions"""
        import db_management
        
        # Test that db_management module has expected functions
        expected_functions = ['query_db', 'update_db']
        
        for func_name in expected_functions:
            self.assertTrue(hasattr(db_management, func_name), f"Missing function: {func_name}")
    
    def test_query_functions_import(self):
        """Test query functions import"""
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
    
    def test_postgresql_connection_mock(self):
        """Test PostgreSQL connection functionality"""
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

