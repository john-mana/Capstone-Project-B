#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple tests for query.py functionality
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestQuerySimple(unittest.TestCase):
    """Simple test suite for query.py functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock database session
        self.mock_session = MagicMock()
        
        # Mock query results
        self.mock_species_result = MagicMock()
        self.mock_species_result.scientific_name = 'Acacia longifolia'
        
        self.mock_occurrence_result = MagicMock()
        self.mock_occurrence_result.dataset_name = 'Test Dataset'
        self.mock_occurrence_result.reserve_name = 'Test Reserve'
        self.mock_occurrence_result.locality = 'Test Locality'
        self.mock_occurrence_result.habitat = 'Forest'
        self.mock_occurrence_result.basis_of_record = 'HumanObservation'
        self.mock_occurrence_result.year = 2023
        self.mock_occurrence_result.owner_institution_code = 'TEST'
        
        self.mock_fauna_result = MagicMock()
        self.mock_fauna_result.genus = 'Pteropus'
        self.mock_fauna_result.species = 'poliocephalus'
        self.mock_fauna_result.family = 'Pteropodidae'
        self.mock_fauna_result.vernacular_name = 'Grey-headed Flying-fox'
        self.mock_fauna_result.class_name = 'Mammalia'
        self.mock_fauna_result.exotic = False
        self.mock_fauna_result.rare_endangered = False
        self.mock_fauna_result.local_rare_endangered = False
        self.mock_fauna_result.year = 2023
        self.mock_fauna_result.reserve_name = 'Test Reserve'
        
        self.mock_reserve_result = MagicMock()
        self.mock_reserve_result.reserve_name = 'Test Reserve'
        
        self.mock_local_species_result = MagicMock()
        self.mock_local_species_result.planted_native = 'Planted Native'
        
        # Mock query objects
        self.mock_query = MagicMock()
        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.join.return_value = self.mock_query
        self.mock_query.outerjoin.return_value = self.mock_query
        self.mock_query.order_by.return_value = self.mock_query
        self.mock_query.group_by.return_value = self.mock_query
        self.mock_query.all.return_value = [self.mock_species_result]
        self.mock_query.count.return_value = 10
        self.mock_query.scalar.return_value = 5
        self.mock_query.limit.return_value = self.mock_query
        
        # Simple mock for session.query
        self.mock_session.query.return_value = self.mock_query
    
    def test_get_unique_species(self):
        """Test get_unique_species function"""
        from query import get_unique_species
        
        result = get_unique_species(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'Acacia longifolia')
    
    def test_get_unique_reserves(self):
        """Test get_unique_reserves function"""
        from query import get_unique_reserves
        
        # Mock reserve result
        self.mock_query.all.return_value = [self.mock_reserve_result]
        
        result = get_unique_reserves(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'Test Reserve')
    
    def test_get_unique_datasets_with_coords(self):
        """Test get_unique_datasets_with_coords function"""
        from query import get_unique_datasets_with_coords
        
        # Mock dataset result
        self.mock_query.all.return_value = [self.mock_occurrence_result]
        
        result = get_unique_datasets_with_coords(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'Test Dataset')
    
    def test_get_unique_planted_natives(self):
        """Test get_unique_planted_natives function"""
        from query import get_unique_planted_natives
        
        # Mock local species result
        self.mock_query.all.return_value = [self.mock_local_species_result]
        
        result = get_unique_planted_natives(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'Planted Native')
    
    def test_get_unique_years(self):
        """Test get_unique_years function"""
        from query import get_unique_years
        
        # Mock year result
        mock_year_result = MagicMock()
        mock_year_result.year = 2023
        self.mock_query.all.return_value = [mock_year_result]
        
        result = get_unique_years(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 2023)
    
    def test_get_unique_localities(self):
        """Test get_unique_localities function"""
        from query import get_unique_localities
        
        # Mock locality result
        mock_locality_result = MagicMock()
        mock_locality_result.locality = 'Test Locality'
        self.mock_query.all.return_value = [mock_locality_result]
        
        result = get_unique_localities(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'Test Locality')
    
    def test_get_unique_habitats(self):
        """Test get_unique_habitats function"""
        from query import get_unique_habitats
        
        # Mock habitat result
        mock_habitat_result = MagicMock()
        mock_habitat_result.habitat = 'Forest'
        self.mock_query.all.return_value = [mock_habitat_result]
        
        result = get_unique_habitats(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'Forest')
    
    def test_get_unique_basis_of_record(self):
        """Test get_unique_basis_of_record function"""
        from query import get_unique_basis_of_record
        
        # Mock basis of record result
        mock_basis_result = MagicMock()
        mock_basis_result.basis_of_record = 'HumanObservation'
        self.mock_query.all.return_value = [mock_basis_result]
        
        result = get_unique_basis_of_record(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'HumanObservation')
    
    def test_get_unique_threatened_species_statuses(self):
        """Test get_unique_threatened_species_statuses function"""
        from query import get_unique_threatened_species_statuses
        
        # Mock threatened species result
        mock_threatened_result = MagicMock()
        mock_threatened_result.threatened_species_status = 'Vulnerable'
        self.mock_query.all.return_value = [mock_threatened_result]
        
        result = get_unique_threatened_species_statuses(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'Vulnerable')
    
    def test_get_unique_owner_institution_codes(self):
        """Test get_unique_owner_institution_codes function"""
        from query import get_unique_owner_institution_codes
        
        # Mock owner institution code result
        mock_owner_result = MagicMock()
        mock_owner_result.owner_institution_code = 'TEST'
        self.mock_query.all.return_value = [mock_owner_result]
        
        result = get_unique_owner_institution_codes(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'TEST')
    
    def test_get_unique_datasets(self):
        """Test get_unique_datasets function"""
        from query import get_unique_datasets
        
        # Mock dataset result
        mock_dataset_result = MagicMock()
        mock_dataset_result.dataset_name = 'Test Dataset'
        self.mock_query.all.return_value = [mock_dataset_result]
        
        result = get_unique_datasets(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'Test Dataset')
    
    def test_get_options_occurrences(self):
        """Test get_options_occurrences function"""
        from query import get_options_occurrences
        
        # Mock all the individual functions
        with patch('query.get_unique_species') as mock_species, \
             patch('query.get_unique_datasets') as mock_datasets, \
             patch('query.get_unique_reserves') as mock_reserves, \
             patch('query.get_unique_localities') as mock_localities, \
             patch('query.get_unique_habitats') as mock_habitats, \
             patch('query.get_unique_basis_of_record') as mock_basis, \
             patch('query.get_unique_planted_natives') as mock_planted, \
             patch('query.get_unique_years') as mock_years, \
             patch('query.get_unique_owner_institution_codes') as mock_owner, \
             patch('query.get_unique_threatened_species_statuses') as mock_threatened:
            
            # Set up mock return values
            mock_species.return_value = ['Species1', 'Species2']
            mock_datasets.return_value = ['Dataset1', 'Dataset2']
            mock_reserves.return_value = ['Reserve1', 'Reserve2']
            mock_localities.return_value = ['Locality1', 'Locality2']
            mock_habitats.return_value = ['Habitat1', 'Habitat2']
            mock_basis.return_value = ['Basis1', 'Basis2']
            mock_planted.return_value = ['Planted1', 'Planted2']
            mock_years.return_value = [2020, 2021]
            mock_owner.return_value = ['Owner1', 'Owner2']
            mock_threatened.return_value = ['Status1', 'Status2']
            
            result = get_options_occurrences(self.mock_session)
            
            # Verify result structure
            self.assertIsInstance(result, dict)
            self.assertIn('speciesOptions', result)
            self.assertIn('datasetOptions', result)
            self.assertIn('reserveOptions', result)
            self.assertIn('localityOptions', result)
            self.assertIn('habitatOptions', result)
            self.assertIn('basisOptions', result)
            self.assertIn('plantedNativeOptions', result)
            self.assertIn('yearOptions', result)
            self.assertIn('ownerInstitutionCodeOptions', result)
            self.assertIn('threatenedStatusOptions', result)
            
            # Verify all options are sorted lists
            for key, value in result.items():
                self.assertIsInstance(value, list)
                self.assertEqual(value, sorted(value))
    
    def test_get_observations_query_basic(self):
        """Test get_observations_query function with basic parameters"""
        from query import get_observations_query
        
        result = get_observations_query(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsNotNone(result)
    
    def test_get_observations_query_with_filters(self):
        """Test get_observations_query function with various filters"""
        from query import get_observations_query
        
        # Test with species filter
        result = get_observations_query(self.mock_session, species='Acacia longifolia')
        self.assertIsNotNone(result)
        
        # Test with dataset filter
        result = get_observations_query(self.mock_session, dataset='Test Dataset')
        self.assertIsNotNone(result)
        
        # Test with reserve filter (string)
        result = get_observations_query(self.mock_session, reserve='Test Reserve')
        self.assertIsNotNone(result)
        
        # Test with reserve filter (list)
        result = get_observations_query(self.mock_session, reserve=['Test Reserve', 'Another Reserve'])
        self.assertIsNotNone(result)
        
        # Test with locality filter
        result = get_observations_query(self.mock_session, locality='Test Locality')
        self.assertIsNotNone(result)
        
        # Test with habitat filter
        result = get_observations_query(self.mock_session, habitat='Forest')
        self.assertIsNotNone(result)
        
        # Test with basis_of_record filter
        result = get_observations_query(self.mock_session, basis_of_record='HumanObservation')
        self.assertIsNotNone(result)
        
        # Test with year range filters
        result = get_observations_query(self.mock_session, start_year=2020, end_year=2023)
        self.assertIsNotNone(result)
        
        # Test with planted_native filter
        result = get_observations_query(self.mock_session, planted_native='Native')
        self.assertIsNotNone(result)
        
        # Test with rare filter
        result = get_observations_query(self.mock_session, rare='Vulnerable')
        self.assertIsNotNone(result)
        
        # Test with owner_institution_code filter
        result = get_observations_query(self.mock_session, owner_institution_code='TEST')
        self.assertIsNotNone(result)
    
    def test_get_observations_basic(self):
        """Test get_observations function with basic parameters"""
        from query import get_observations
        
        # Mock the to_dict method
        self.mock_occurrence_result.to_dict.return_value = {
            'scientific_name': 'Acacia longifolia',
            'dataset_name': 'Test Dataset',
            'reserve_name': 'Test Reserve'
        }
        
        # Mock query to return occurrence result
        self.mock_query.all.return_value = [self.mock_occurrence_result]
        
        result = get_observations(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        # The result should be the return value of to_dict()
        self.assertEqual(result[0], {
            'scientific_name': 'Acacia longifolia',
            'dataset_name': 'Test Dataset',
            'reserve_name': 'Test Reserve'
        })
    
    def test_get_observations_with_filters(self):
        """Test get_observations function with various filters"""
        from query import get_observations
        
        # Mock the to_dict method
        self.mock_occurrence_result.to_dict.return_value = {
            'scientific_name': 'Acacia longifolia',
            'dataset_name': 'Test Dataset',
            'reserve_name': 'Test Reserve'
        }
        
        # Mock query to return occurrence result
        self.mock_query.all.return_value = [self.mock_occurrence_result]
        
        # Test with various filters
        result = get_observations(
            self.mock_session,
            species='Acacia longifolia',
            dataset='Test Dataset',
            reserve='Test Reserve',
            planted_native='Native',
            rare='Vulnerable',
            start_year=2020,
            end_year=2023
        )
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        # The result should be the return value of to_dict()
        self.assertEqual(result[0], {
            'scientific_name': 'Acacia longifolia',
            'dataset_name': 'Test Dataset',
            'reserve_name': 'Test Reserve'
        })
    
    def test_get_overall_statistics(self):
        """Test get_overall_statistics function"""
        from query import get_overall_statistics
        
        # Mock scalar results
        self.mock_query.scalar.return_value = 5
        
        result = get_overall_statistics(self.mock_session)
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn('total_flora_occurrences', result)
        self.assertIn('distinct_flora_species', result)
        self.assertIn('flora_occurrences_with_coords', result)
        self.assertIn('distinct_flora_datasets', result)
        self.assertIn('distinct_flora_reserves', result)
        self.assertIn('total_fauna_records', result)
        self.assertIn('distinct_fauna_species', result)
        self.assertIn('distinct_fauna_genera', result)
        self.assertIn('distinct_fauna_families', result)
        self.assertIn('distinct_fauna_reserves', result)
        self.assertIn('top_5_flora_species', result)
        self.assertIn('flora_occurrences_by_basis', result)
    
    def test_get_overall_statistics_fauna_error(self):
        """Test get_overall_statistics function with fauna error"""
        from query import get_overall_statistics
        
        # Mock fauna query to raise exception
        def mock_query_side_effect(*args, **kwargs):
            # Check if this is a fauna-related query by looking at the first argument
            if len(args) > 0 and hasattr(args[0], '__name__') and args[0].__name__ == 'Fauna':
                raise Exception("Fauna table not found")
            return self.mock_query
        
        self.mock_session.query.side_effect = mock_query_side_effect
        
        with patch('sys.stderr') as mock_stderr:
            result = get_overall_statistics(self.mock_session)
            
            # Verify fauna stats are set to 'N/A'
            self.assertEqual(result['total_fauna_records'], 'N/A')
            self.assertEqual(result['distinct_fauna_species'], 'N/A')
            self.assertEqual(result['distinct_fauna_genera'], 'N/A')
            self.assertEqual(result['distinct_fauna_families'], 'N/A')
            self.assertEqual(result['distinct_fauna_reserves'], 'N/A')
            
            # Verify error was printed to stderr
            mock_stderr.write.assert_called()
    
    def test_get_unique_fauna_genera(self):
        """Test get_unique_fauna_genera function"""
        from query import get_unique_fauna_genera
        
        # Mock fauna result
        self.mock_query.all.return_value = [self.mock_fauna_result]
        
        result = get_unique_fauna_genera(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'Pteropus')
    
    def test_get_unique_fauna_species(self):
        """Test get_unique_fauna_species function"""
        from query import get_unique_fauna_species
        
        # Mock fauna result
        self.mock_query.all.return_value = [self.mock_fauna_result]
        
        result = get_unique_fauna_species(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'poliocephalus')
    
    def test_get_unique_fauna_families(self):
        """Test get_unique_fauna_families function"""
        from query import get_unique_fauna_families
        
        # Mock fauna result
        self.mock_query.all.return_value = [self.mock_fauna_result]
        
        result = get_unique_fauna_families(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'Pteropodidae')
    
    def test_get_unique_fauna_vernacular_names(self):
        """Test get_unique_fauna_vernacular_names function"""
        from query import get_unique_fauna_vernacular_names
        
        # Mock fauna result
        self.mock_query.all.return_value = [self.mock_fauna_result]
        
        result = get_unique_fauna_vernacular_names(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'Grey-headed Flying-fox')
    
    def test_get_unique_fauna_class_names(self):
        """Test get_unique_fauna_class_names function"""
        from query import get_unique_fauna_class_names
        
        # Mock fauna result
        self.mock_query.all.return_value = [self.mock_fauna_result]
        
        result = get_unique_fauna_class_names(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'Mammalia')
    
    def test_get_unique_fauna_rare_endangered_statuses(self):
        """Test get_unique_fauna_rare_endangered_statuses function"""
        from query import get_unique_fauna_rare_endangered_statuses
        
        # Mock fauna result
        self.mock_query.all.return_value = [self.mock_fauna_result]
        
        result = get_unique_fauna_rare_endangered_statuses(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], False)
    
    def test_get_unique_fauna_local_rare_endangered_statuses(self):
        """Test get_unique_fauna_local_rare_endangered_statuses function"""
        from query import get_unique_fauna_local_rare_endangered_statuses
        
        # Mock fauna result
        self.mock_query.all.return_value = [self.mock_fauna_result]
        
        result = get_unique_fauna_local_rare_endangered_statuses(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], False)
    
    def test_get_unique_fauna_exotic_statuses(self):
        """Test get_unique_fauna_exotic_statuses function"""
        from query import get_unique_fauna_exotic_statuses
        
        # Mock fauna result
        self.mock_query.all.return_value = [self.mock_fauna_result]
        
        result = get_unique_fauna_exotic_statuses(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], False)
    
    def test_get_unique_fauna_years(self):
        """Test get_unique_fauna_years function"""
        from query import get_unique_fauna_years
        
        # Mock fauna year result
        mock_fauna_year_result = MagicMock()
        mock_fauna_year_result.year = 2023
        self.mock_query.all.return_value = [mock_fauna_year_result]
        
        result = get_unique_fauna_years(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 2023)
    
    def test_get_unique_fauna_reserve_names(self):
        """Test get_unique_fauna_reserve_names function"""
        from query import get_unique_fauna_reserve_names
        
        # Mock fauna result
        self.mock_query.all.return_value = [self.mock_fauna_result]
        
        result = get_unique_fauna_reserve_names(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'Test Reserve')
    
    def test_get_options_fauna(self):
        """Test get_options_fauna function"""
        from query import get_options_fauna
        
        # Mock all the individual functions
        with patch('query.get_unique_fauna_genera') as mock_genera, \
             patch('query.get_unique_fauna_species') as mock_species, \
             patch('query.get_unique_fauna_families') as mock_families, \
             patch('query.get_unique_fauna_vernacular_names') as mock_vernacular, \
             patch('query.get_unique_fauna_class_names') as mock_class, \
             patch('query.get_unique_fauna_rare_endangered_statuses') as mock_rare, \
             patch('query.get_unique_fauna_local_rare_endangered_statuses') as mock_local_rare, \
             patch('query.get_unique_fauna_exotic_statuses') as mock_exotic, \
             patch('query.get_unique_fauna_years') as mock_years, \
             patch('query.get_unique_fauna_reserve_names') as mock_reserves:
            
            # Set up mock return values
            mock_genera.return_value = ['Genus1', 'Genus2']
            mock_species.return_value = ['Species1', 'Species2']
            mock_families.return_value = ['Family1', 'Family2']
            mock_vernacular.return_value = ['Vernacular1', 'Vernacular2']
            mock_class.return_value = ['Class1', 'Class2']
            mock_rare.return_value = [True, False]
            mock_local_rare.return_value = [True, False]
            mock_exotic.return_value = [True, False]
            mock_years.return_value = [2020, 2021]
            mock_reserves.return_value = ['Reserve1', 'Reserve2']
            
            result = get_options_fauna(self.mock_session)
            
            # Verify result structure
            self.assertIsInstance(result, dict)
            self.assertIn('genusOptions', result)
            self.assertIn('speciesOptions', result)
            self.assertIn('familyOptions', result)
            self.assertIn('vernacularNameOptions', result)
            self.assertIn('classNameOptions', result)
            self.assertIn('rareEndangeredOptions', result)
            self.assertIn('localRareEndangeredOptions', result)
            self.assertIn('exoticOptions', result)
            self.assertIn('yearOptions', result)
            self.assertIn('reserveNameOptions', result)
            
            # Verify all options are sorted lists
            for key, value in result.items():
                self.assertIsInstance(value, list)
                self.assertEqual(value, sorted(value))
    
    def test_get_fauna_query_basic(self):
        """Test get_fauna_query function with basic parameters"""
        from query import get_fauna_query
        
        result = get_fauna_query(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsNotNone(result)
    
    def test_get_fauna_query_with_filters(self):
        """Test get_fauna_query function with various filters"""
        from query import get_fauna_query
        
        # Test with genus filter
        result = get_fauna_query(self.mock_session, genus='Pteropus')
        self.assertIsNotNone(result)
        
        # Test with species filter
        result = get_fauna_query(self.mock_session, species='poliocephalus')
        self.assertIsNotNone(result)
        
        # Test with family filter
        result = get_fauna_query(self.mock_session, family='Pteropodidae')
        self.assertIsNotNone(result)
        
        # Test with vernacular_name filter
        result = get_fauna_query(self.mock_session, vernacular_name='Flying-fox')
        self.assertIsNotNone(result)
        
        # Test with class_name filter
        result = get_fauna_query(self.mock_session, class_name='Mammalia')
        self.assertIsNotNone(result)
        
        # Test with boolean filters
        result = get_fauna_query(self.mock_session, rare_endangered='true')
        self.assertIsNotNone(result)
        
        result = get_fauna_query(self.mock_session, local_rare_endangered='false')
        self.assertIsNotNone(result)
        
        result = get_fauna_query(self.mock_session, exotic='false')
        self.assertIsNotNone(result)
        
        # Test with year filter
        result = get_fauna_query(self.mock_session, year=2023)
        self.assertIsNotNone(result)
        
        # Test with reserve_name filter (string)
        result = get_fauna_query(self.mock_session, reserve_name='Test Reserve')
        self.assertIsNotNone(result)
        
        # Test with reserve_name filter (list)
        result = get_fauna_query(self.mock_session, reserve_name=['Test Reserve', 'Another Reserve'])
        self.assertIsNotNone(result)
    
    def test_get_fauna_query_year_conversion_error(self):
        """Test get_fauna_query function with year conversion error"""
        from query import get_fauna_query
        
        # Test with invalid year that should trigger ValueError
        result = get_fauna_query(self.mock_session, year='invalid_year')
        
        # Should still return a query object
        self.assertIsNotNone(result)
    
    def test_get_fauna_query_reserve_name_list_empty(self):
        """Test get_fauna_query function with empty reserve name list"""
        from query import get_fauna_query
        
        # Test with empty list
        result = get_fauna_query(self.mock_session, reserve_name=[])
        
        # Should still return a query object
        self.assertIsNotNone(result)
        
        # Test with list containing empty strings
        result = get_fauna_query(self.mock_session, reserve_name=['', '  ', 'Test Reserve'])
        
        # Should still return a query object
        self.assertIsNotNone(result)
    
    def test_get_fauna_query_reserve_name_string_empty(self):
        """Test get_fauna_query function with empty reserve name string"""
        from query import get_fauna_query
        
        # Test with empty string
        result = get_fauna_query(self.mock_session, reserve_name='')
        
        # Should still return a query object
        self.assertIsNotNone(result)
        
        # Test with whitespace-only string
        result = get_fauna_query(self.mock_session, reserve_name='   ')
        
        # Should still return a query object
        self.assertIsNotNone(result)
    
    def test_get_flora_all_species_report(self):
        """Test get_flora_all_species_report function"""
        from query import get_flora_all_species_report
        
        # Mock the query result
        mock_row = MagicMock()
        mock_row._asdict.return_value = {
            'species_name': 'Acacia longifolia',
            'occurrence_count': 10,
            'total_individual_count': 50,
            'exotic': False,
            'planted_native': 'Planted Native'
        }
        self.mock_query.all.return_value = [mock_row]
        
        result = get_flora_all_species_report(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], dict)
    
    def test_get_fauna_all_species_report(self):
        """Test get_fauna_all_species_report function"""
        from query import get_fauna_all_species_report
        
        result = get_fauna_all_species_report(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], dict)
        
        # Verify result structure
        fauna_record = result[0]
        self.assertIn('Genus', fauna_record)
        self.assertIn('Species', fauna_record)
        self.assertIn('Vernacular Name', fauna_record)
        self.assertIn('Family', fauna_record)
        self.assertIn('Class Name', fauna_record)
        self.assertIn('Exotic', fauna_record)
        self.assertIn('Rare/Endangered', fauna_record)
        self.assertIn('Local Rare/Endangered', fauna_record)
        self.assertIn('Year', fauna_record)
        self.assertIn('Decimal Longitude', fauna_record)
        self.assertIn('Decimal Latitude', fauna_record)
        self.assertIn('Reserve Name', fauna_record)
    
    def test_get_summary_report_flora(self):
        """Test get_summary_report function for Flora"""
        from query import get_summary_report
        
        # Mock the query result
        mock_row = MagicMock()
        mock_row.source_file = 'Test Dataset'
        mock_row.location_name = 'Test Reserve'
        mock_row.total_species = 10
        mock_row.num_exotic_species = 2
        mock_row.num_listed_re = 1
        mock_row.num_planted_native = 3
        self.mock_query.all.return_value = [mock_row]
        
        result = get_summary_report(self.mock_session, 'Flora')
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], dict)
        
        # Verify result structure
        summary_record = result[0]
        self.assertIn('Source File', summary_record)
        self.assertIn('Location Name', summary_record)
        self.assertIn('Total Species', summary_record)
        self.assertIn('Number of Exotic Species', summary_record)
        self.assertIn('Number of Listed R&E', summary_record)
        self.assertIn('Number of Planted Native', summary_record)
    
    def test_get_summary_report_fauna(self):
        """Test get_summary_report function for Fauna"""
        from query import get_summary_report
        
        # Mock the query result
        mock_row = MagicMock()
        mock_row.class_name = 'Mammalia'
        mock_row.reserve_name = 'Test Reserve'
        mock_row.total_species = 5
        mock_row.num_exotic_species = 1
        mock_row.num_rare_endangered_species = 2
        mock_row.num_local_rare_endangered_species = 1
        self.mock_query.all.return_value = [mock_row]
        
        result = get_summary_report(self.mock_session, 'Fauna')
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], dict)
        
        # Verify result structure
        summary_record = result[0]
        self.assertIn('Class Name', summary_record)
        self.assertIn('Reserve Name', summary_record)
        self.assertIn('Total Species', summary_record)
        self.assertIn('Number of Exotic Species', summary_record)
        self.assertIn('Number of Rare/Endangered Species', summary_record)
        self.assertIn('Number of Local Rare/Endangered Species', summary_record)
    
    def test_get_summary_report_invalid_type(self):
        """Test get_summary_report function with invalid report type"""
        from query import get_summary_report
        
        result = get_summary_report(self.mock_session, 'Invalid')
        
        # Should return empty list for invalid report type
        self.assertEqual(result, [])
    
    def test_get_flora_report_by_reserve(self):
        """Test get_flora_report_by_reserve function"""
        from query import get_flora_report_by_reserve
        
        # Mock the query result
        mock_row = MagicMock()
        mock_row.reserve_name = 'Test Reserve'
        mock_row.num_occurrences = 100
        mock_row.num_distinct_species = 50
        self.mock_query.all.return_value = [mock_row]
        
        result = get_flora_report_by_reserve(self.mock_session)
        
        # Verify session.query was called
        self.mock_session.query.assert_called_once()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], dict)
        
        # Verify result structure
        report_record = result[0]
        self.assertIn('Reserve Name', report_record)
        self.assertIn('Number of Occurrences', report_record)
        self.assertIn('Number of Distinct Species', report_record)


if __name__ == '__main__':
    unittest.main()

