# -*- coding: utf-8 -*-
''' oscaar v2.0

Unit tests for dataBank class

'''
import unittest
import nose
from os.path import join, abspath, dirname
from oscaar.dataBank import dataBank

class TestDataBank(unittest.TestCase):
    ''' unit tests for the dataBank class '''

    _unit_test_par_file = './unit_tests.par'
    _unit_test_stars_regions_file = ' ../../oscaar/testFiles/stars.reg'


    def test_negative_create_dataBank(self):
        ''' simple init of the dataBank class '''
        try:
            ut_databank = dataBank('')
        except ValueError:
            # expected error
            assert True
        except Exception as ex:
            assert False, (
                'failed to create an instance of dataBank: {0}'.format(ex))


    def test_init_dataBank(self):
        ''' Test simple init of dataBank class with required setup. '''
        ut_databank = dataBank(self._unit_test_par_file)

        assert ut_databank is not None, (
            'dataBank was unexpectedly initialized to None')

        # confirm that attributes are set from parsing the .par file
        ut_path = dirname(abspath(__file__))

        expected_attributes = {
            'flatPath' : '../../oscaar/testFiles/masterFlat.fits', # ok as is for some reason
            'rawRegionsList' : '../../oscaar/testFiles/myReg.reg, ../../oscaar/testFiles/stars.reg',
            'regionsFileList' : ['../../oscaar/testFiles/myReg.reg'],
            'regionsFITSrefsList': [self._unit_test_stars_regions_file],
            'ingress' : float(2456293.9211805556),
            'egress' : float(2456293.960127315),
            'apertureRadii' : [4.5],
            'trackingZoom' : 15,
            'ccdGain' : 1.0,
            'trackPlots' : False,
            'photPlots' : False,
            'smoothConst' : 3,
            'darksPath' : [abspath(join(ut_path, p)) for p in [
                '../../oscaar/testFiles/simulatedImg-000d.fits',
                '../../oscaar/testFiles/simulatedImg-001d.fits',
                '../../oscaar/testFiles/simulatedImg-002d.fits']],
            'imagesPaths' : [abspath(join(ut_path, p)) for p in [
                '../../oscaar/testFiles/simulatedImg-000r.fits',
                '../../oscaar/testFiles/simulatedImg-001r.fits',
                '../../oscaar/testFiles/simulatedImg-002r.fits',
                '../../oscaar/testFiles/simulatedImg-003r.fits',
                '../../oscaar/testFiles/simulatedImg-004r.fits',
                '../../oscaar/testFiles/simulatedImg-005r.fits']],
            'timeKeyword' : 'JD',
            'outputPath' : abspath(join(ut_path, 'unit_test_results.pkl')),
            }

        for (attr, value) in expected_attributes.iteritems():
            if isinstance(value, list):
                assert sorted(getattr(ut_databank, attr)) == sorted(value), (
                    '{0} does not match:\nActual: {1}\nExpected: {2}'.format(
                        attr,
                        sorted(getattr(ut_databank, attr)),
                        sorted(value),
                    ))
            else:
                assert getattr(ut_databank, attr) == value, (
                    'Attribute <{0}>: {1} != {2}'.format(
                        attr, getattr(ut_databank, attr), value))

        assert isinstance(ut_databank, dataBank), (
            'returned dataBank should be a dataBank, but is {0}'\
            .format(type(ut_databank)))


    def test_allStarsDict_populated(self):
        ''' verify that the dataBank.allStarsDict is populated correctly. '''

        ut_databank = dataBank(self._unit_test_par_file)

        assert len(ut_databank.allStarsDict.keys()) == 3, (
            'allStarsDict expected 3 keys, got {0}'.format(
                len(ut_databank.keys())))

        expected_data_keys = [
            'chisq',
            'flag',
            'rawError',
            'rawFlux',
            'scaledError',
            'scaledFlux',
            'x-pos',
            'y-pos',
        ]

        for image_index in ut_databank.allStarsDict.keys():
            for data_key in expected_data_keys:
                assert ut_databank.allStarsDict[image_index][data_key] is not None, (
                        'allStarsDict[{0}][{1}] is missing data'.format(
                            image_index, data_key))


    def test_parseRegionsFile(self):
        ''' verify that dataBank.parseRegionsFile will parse correctly. '''
        ut_databank = dataBank(self._unit_test_par_file)

        x_list, y_list = ut_databank.parseRegionsFile(
            self._unit_test_stars_regions_file.strip())

        assert x_list is not None, (
            'parseRegionsFile returned x_list as None')
        assert y_list is not None, (
            'parseRegionsFile returned y_list as None')

        expected_x_list = [19.384944, 19.223439, 19.54645]
        expected_y_list = [19.170054, 59.54645, 99.438329]

        assert (x_list) == (expected_x_list), (
            'parseRegionsFile got wrong x_list, actual|expected:\n{0}\n{1}'.format(
            (x_list), (expected_x_list)))

        assert (y_list) == (expected_y_list), (
            'parseRegionsFile got wrong y_list, actual|expected:\n{0}\n{1}'.format(
            (y_list), (expected_y_list)))


    def test_centroidInitialGuess_one_regions_file(self):
        ''' verify dataBank.centroidInitialGuess when only one regions file
        has been submitted.
        '''
        raise NotImplementedError


    def test_centroidInitialGuess_multiple_regions_file(self):
        ''' verify dataBank.centroidInitialGuess when multiple regions file
        have been submitted.
        '''
        raise NotImplementedError


    def test_scaleFluxes_no_change_target_star(self):
        ''' verify dataBank.scaleFluxes will not change the flux or error
        of the target star.'''
        raise NotImplementedError


    def test_scaleFluxes_region_stars(self):
        ''' verify dataBank.scaleFluxes will correctly change the flux and error
        of all region stars other than the target star.'''
        raise NotImplementedError


    def test_calcChiSq(self):
        ''' verify dataBank.calcChiSq sets the dataBank *chisq values correctly
        for our test data.'''
        raise NotImplementedError


    def test_calcChiSq_multirad(self):
        ''' verify dataBank.calcChiSq_multirad sets the dataBank *chisq values
        correctly for our test data.'''
        raise NotImplementedError


if __name__ == '__main__':
    unittest.main()
