
'''
# https://jfaden.net/HapiServerDemo/hapi/info?id=specBins.ref
# uses common reference to the bins object
server = 'https://jfaden.net/HapiServerDemo/hapi'
dataset = 'specBins.ref'
start = '2016-001T00:00:00.000Z'
stop = '2016-001T24:00:00.000Z'
parameters = 'counts,flux'
'''

# '''
# vap+hapi:http://amda.irap.omp.eu/service/hapi?id=ace-swe-all&parameters=Time,sw_v_gse&timerange=2021-01-17
# uses common reference to the bins object
server = 'http://amda.irap.omp.eu/service/hapi'
dataset = 'ace-swe-all'
start = '2021-01-17T00:00:00Z'
stop = '2021-01-17T23:59:47Z'
parameters = 'sw_v_gse'
# '''

import fromHapiToCDF
import fromHapiToSpaceData

import os
import hapiclient
import spacepy.pycdf

filename = '/tmp/fromHapiToCDF.cdf'
if os.path.exists(filename):
    print('deleting {}'.format(filename))
    os.remove(filename)

opts = {'logging': True, 'format': 'csv'}
hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)
fromHapiToCDF.to_CDF(hapidata, filename)

print('wrote {}'.format(filename))

cdf2 = spacepy.pycdf.CDF(filename)
print('--cdf2---')
print(cdf2)
print(cdf2['Time'])
print('---------')

cdf3 = fromHapiToSpaceData.to_SpaceData(hapidata)
print('--cdf3---')
print(cdf3)
print(cdf3['Time'])
print('---------')
