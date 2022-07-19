import fromHapiToCDF
import fromHapiToSpaceData

import os
import hapiclient
import spacepy.pycdf

# vap+hapi:https://jfaden.net/HapiServerDemo/hapi?id=SpectrumTimeVaryingChannels&parameters=Spectra&timerange=2016-07-28+22:00+to+24:00
server = 'https://jfaden.net/HapiServerDemo/hapi'
dataset = 'SpectrumTimeVaryingChannels'
start = '2016-07-28T22:00'
stop = '2016-07-28T24:00'
parameters = ''

filename = '/home/jbf/tmp/202207/spectrogramRVDepend1.cdf'

opts = {'logging': True, 'format': 'csv', 'usecache': True}
hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)

cdf2 = spacepy.pycdf.CDF(filename)
print('--cdf2---')
print(cdf2)
print('---------')

complexSpectrogram = fromHapiToSpaceData.to_SpaceData(hapidata)
import spacepy.datamodel as dm
dm.toJSONheadedASCII( '/tmp/jbf/complexSpectrogram.txt', complexSpectrogram )

print( '-----------------------------------------------' )