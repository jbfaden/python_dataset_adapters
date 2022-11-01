import unittest

from fromHapiToSunPy import hapi_to_time_series
import fromHapiToCDF
import fromHapiToSpaceData
import os
import hapiclient


class Test( unittest.TestCase ):
    def test_hapi_to_time_series_scalars(self):
        # https://cdaweb.gsfc.nasa.gov/hapi/data?id=OMNI2_H0_MRG1HR&time.min=2022-01-01T00:00:00Z&time.max=2022-10-24T13:00:00Z&parameters=Time,Rot1800,KP1800,DST1800,AE1800
        server = 'https://cdaweb.gsfc.nasa.gov/hapi'
        dataset = 'OMNI2_H0_MRG1HR'
        start = '2022-01-01Z'
        stop = '2022-06-01Z'
        parameters = 'Time,Rot1800,KP1800,DST1800,AE1800'
        opts = {'logging': False, 'format': 'csv', 'usecache': True}
        hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)
        print( hapi_to_time_series(hapidata) )

    def test_hapi_to_time_series_vectors(self):
        # https://cdaweb.gsfc.nasa.gov/hapi/data?id=AC_H0_MFI&time.min=2022-09-03T00:00:00Z&time.max=2022-09-03T23:59:47Z&parameters=Time,BGSM
        server = 'https://cdaweb.gsfc.nasa.gov/hapi'
        dataset = 'AC_H0_MFI'
        start = '2022-09-03Z'
        stop = '2022-09-04Z'
        parameters = 'Time,Magnitude,BGSM'
        opts = {'logging': False, 'format': 'csv', 'usecache': True}
        hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)
        print( hapi_to_time_series(hapidata) )

    def test_fromHapiToCDF(self):
        # '''
        # vap+hapi:http://amda.irap.omp.eu/service/hapi?id=ace-swe-all&parameters=Time,sw_v_gse&timerange=2021-01-17
        # uses common reference to the bins object
        server = 'http://amda.irap.omp.eu/service/hapi'
        dataset = 'ace-swe-all'
        start = '2021-01-17T00:00:00Z'
        stop = '2021-01-17T23:59:47Z'
        parameters = 'sw_v_gse'
        # '''

        filename = '/tmp/fromHapiToCDF.cdf'
        if os.path.exists(filename):
            print('deleting {}'.format(filename))
            os.remove(filename)

        opts = {'logging': False, 'format': 'csv'}
        hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)
        fromHapiToCDF.to_CDF(hapidata, filename)
        print( 'Wrote '+filename )

    def test_fromHapiToSpacePy(self):
        server = 'http://amda.irap.omp.eu/service/hapi'
        dataset = 'ace-swe-all'
        start = '2021-01-17T00:00:00Z'
        stop = '2021-01-17T23:59:47Z'
        parameters = 'sw_v_gse'

        opts = {'logging': False, 'format': 'csv'}
        hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)

        cdf3 = fromHapiToSpaceData.to_SpaceData(hapidata)
        print('--cdf3---')
        print(cdf3)
        print(type(cdf3['Time']))
        print('---------')
        import spacepy.datamodel as dm

        filename = '/tmp/fromHapiToCDFTest.txt'
        if os.path.exists(filename):
            print('deleting {}'.format(filename))
            os.remove(filename)
        dm.toJSONheadedASCII(filename, cdf3)
        print('wrote '+filename)

if __name__ == '__main__':
    unittest.main()