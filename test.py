import unittest
import os

from fromHapiToSunPy import hapi_to_time_series
import fromHapiToCDF
import fromHapiToSpaceData
import hapiclient


def prepare_output_file(name):
    """create temporary directory and filename for testing.  This may create
    the directory and will delete the file if an old one is found within the
    directory."""
    outd = '/tmp/python_dataset_adapters/'
    if not os.path.exists(outd):
        os.mkdir(outd)
    filename = outd + name
    if os.path.exists(filename):
        print('deleting {}'.format(filename))
        os.remove(filename)
    return filename


class Test(unittest.TestCase):

    def test_from_hapi_to_cdf(self):
        """Reads data from HAPI and puts it into a CDF file at /tmp/fromHapiToCdf.cdf"""
        server = 'http://amda.irap.omp.eu/service/hapi'
        dataset = 'ace-swe-all'
        start = '2021-01-17T00:00:00Z'
        stop = '2021-01-17T23:59:47Z'
        parameters = 'sw_v_gse'

        filename = prepare_output_file('fromHapiToCdf.cdf')
        opts = {'logging': False, 'format': 'csv'}
        hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)
        fromHapiToCDF.to_CDF(hapidata, filename)
        print('Wrote ' + filename)

    def test_from_hapi_to_space_py(self):
        """Reads data from HAPI and puts it into a SpacePy SpaceData"""
        filename = prepare_output_file('fromHapiToCDFTest.txt')

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

        dm.toJSONheadedASCII(filename, cdf3)
        print('wrote ' + filename)

    def test_from_hapi_to_space_py_time_varying_channels(self):
        filename = prepare_output_file('complexSpectrogram.txt')

        # vap+hapi:https://jfaden.net/HapiServerDemo/hapi?id=SpectrumTimeVaryingChannels&parameters=Spectra&timerange=2016-07-28+22:00+to+24:00
        server = 'https://jfaden.net/HapiServerDemo/hapi'
        dataset = 'SpectrumTimeVaryingChannels'
        start = '2016-07-28T22:00'
        stop = '2016-07-28T24:00'
        parameters = ''

        opts = {'logging': True, 'format': 'csv', 'usecache': True}
        hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)

        complexSpectrogram = fromHapiToSpaceData.to_SpaceData(hapidata)
        import spacepy.datamodel as dm

        dm.toJSONheadedASCII(filename, complexSpectrogram)

        print('wrote to %s' % filename)
        print('-----------------------------------------------')

    def test_hapi_to_sunpy_scalars(self):
        """Reads scalars from HAPI server and creates SunPy TimeSeries"""
        server = 'https://cdaweb.gsfc.nasa.gov/hapi'
        dataset = 'OMNI2_H0_MRG1HR'
        start = '2022-01-01Z'
        stop = '2022-06-01Z'
        parameters = 'Time,Rot1800,KP1800,DST1800,AE1800'
        opts = {'logging': False, 'format': 'csv', 'usecache': True}
        hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)
        ts = hapi_to_time_series(hapidata)
        print( ts )
        # TODO: how does one get the metadata?


    def test_hapi_to_sunpy_vectors(self):
        """Reads scalar and vector from HAPI server and creates SunPy TimeSeries"""
        server = 'https://cdaweb.gsfc.nasa.gov/hapi'
        dataset = 'AC_H0_MFI'
        start = '2022-09-03Z'
        stop = '2022-09-04Z'
        parameters = 'Time,Magnitude,BGSM'
        opts = {'logging': False, 'format': 'csv', 'usecache': True}
        hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)
        print(hapi_to_time_series(hapidata))

    def test_hapi_to_time_series_spec_bins(self):
        """Reads spectrogram (data.ndim=2) from HAPI server and creates SunPy TimeSeries"""
        # https://jfaden.net/HapiServerDemo/hapi/info?id=specBins.ref
        server = 'https://jfaden.net/HapiServerDemo/hapi'
        dataset = 'specBins.ref'
        start = '2016-001T00:00:00.000Z'
        stop = '2016-001T24:00:00.000Z'
        parameters = ''
        opts = {'logging': False, 'format': 'csv', 'usecache': True}
        hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)
        print(hapi_to_time_series(hapidata))

    def test_hapi_to_time_series_ndim_3_data(self):
        """Reads data from HAPI server with ndim=3 and demos that it cannot be used."""
        server = 'https://jfaden.net/HapiServerDemo/hapi'
        dataset = 'SpectrogramRank2'
        start = '2014-01-09T00:00:00.000Z'
        stop = '2014-01-10T00:00:00.000Z'
        parameters = ''
        opts = {'logging': False, 'format': 'csv', 'usecache': True}
        data1, meta1 = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)
        print(type(data1[meta1['parameters'][0]['name']]))
        print(hapi_to_time_series((data1, meta1)))


if __name__ == '__main__':
    unittest.main()
