import fromHapiToCDF
import fromHapiToSpaceData

import os
import hapiclient
import spacepy.pycdf

'''
# https://jfaden.net/HapiServerDemo/hapi/info?id=specBins.ref
# uses common reference to the bins object
server = 'https://jfaden.net/HapiServerDemo/hapi'
dataset = 'specBins.ref'
start = '2016-001T00:00:00.000Z'
stop = '2016-001T24:00:00.000Z'
parameters = 'counts,flux'
'''

'''
# vap+hapi:https://jfaden.net/HapiServerDemo/hapi?id=Spectrum&timerange=2016-07-28+23:06:35.930328+to+23:36:24.069672
# simple spectrogram
server = 'https://jfaden.net/HapiServerDemo/hapi'
dataset = 'Spectrum'
start = '2016-07-28T23:10:00.000Z'
stop = '2016-07_28T23:20:00.000Z'
parameters = ''
'''

# vap+hapi:https://cdaweb.gsfc.nasa.gov/hapi?id=PO_H0_HYD&parameters=Time,ELECTRON_DIFFERENTIAL_ENERGY_FLUX&timerange=2008-03-30
server = 'https://cdaweb.gsfc.nasa.gov/hapi'
dataset = 'PO_H0_HYD'
start = '2008-03-30Z'
stop = '2008-03-31Z'
parameters = 'ELECTRON_DIFFERENTIAL_ENERGY_FLUX'

filename = '/home/jbf/tmp/202207/hapi/po_h0_hyd_20080330_v01.cdf'

opts = {'logging': True, 'format': 'csv', 'usecache': True}
hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)

cdf2 = spacepy.pycdf.CDF(filename)
print('--cdf2---')
print(cdf2)
print(type(cdf2['EPOCH']))
print('---------')

simpleSpectrogram = fromHapiToSpaceData.to_SpaceData(hapidata)
import spacepy.datamodel as dm
dm.toJSONheadedASCII( '/tmp/jbf/simpleSpectrogram.txt', simpleSpectrogram )

print( '-----------------------------------------------' )