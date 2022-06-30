import os.path
import datetime

import spacepy.pycdf
import hapiclient

# frompyfunc
# numpy.vectorize
# ticktock
# foo = numpy.vectorize(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))
# foo( '2020-02-02','2020-02-03')
# { x(i) : for i in iis } dictionary comprehension
# https://github.com/spacepy/spacepy/issues/523

def my_hapitime_format_str(isotime):
    """
    Given an example time, return the format string which used with datetime.datetime.strptime
    will parse the isotime strings to datetimes.

    Parameters
    ----------
    isotime : str
        a HAPI isotime

    Return
    ------
    str
        a format string for datetime.datetime.strptime
    """
    isotime = isotime.decode('ascii')

    if isotime[-1] == 'Z':
        isotime = isotime[0:-1]
        zstr = 'Z'
    else:
        zstr = ''

    datelen = isotime.find('T')
    if datelen == -1:
        datelen = len(isotime)

    if datelen == 4:
        form = '%Y'
    elif datelen == 6:
        form = '%Y%m'
    elif datelen == 7:
        if isotime[4] == '-':
            form = '%Y-%m'
        else:
            form = '%Y%j'
    elif datelen == 8:
        if isotime[4] == '-':
            form = '%Y-%j'
        else:
            form = '%Y%m%d'
    elif datelen == 10:
        form = '%Y-%m-%d'
    else:
        raise Exception('date cannot have %d characters: %s' % (datelen, isotime))

    timelen = len(isotime) - datelen - 1
    timeform = ""
    if timelen > 0:
        if timelen == 2:
            timeform = '%H'
        elif timelen == 4:
            timeform = '%H%M'
        elif timelen == 5:
            timeform = '%H:%M'
        elif timelen == 6:
            timeform = '%H%M%S'
        elif timelen == 8:
            timeform = '%H:%M:%S'
        elif timelen > 10:
            timeform = "%H:%M:%S.%f"
        else:
            raise Exception("time cannot have %d characters: %s" % (datelen, isotime))

    return "{}T{}{}".format(form, timeform, zstr)


def convertTimes(isotimeArray):
    """
    Convert the times in the array of isotimes into datetime objects.
     Parameters
    ----------
    isotimeArray : array of str
        each element a HAPI isotime

    Return
    ------
    array of str
        a datetime object for each element
    """
    form = my_hapitime_format_str(isotimeArray[0])
    return [datetime.datetime.strptime(isotime.decode('ascii'), form) for isotime in isotimeArray]


# this goes away to avoid dependence.  Jon V says CDFFactory.fromHapi()
def toCDF(server, dataset, parameters, start, stop, cdfname):
    """
    Convenient method for reading from HAPI server into CDF file.  This will probably go away.
    """
    opts = {'logging': True}
    hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)
    toCDF(hapidata, cdfname)


def toCDF(hapidata, cdfname):
    """Reformat the response from the Python hapiclient to the CDF.

    This is typically called using the result of the Python hapiclient.
    which is a tuple containing the data and the metadata from a HAPI
    call.  For example:

    hapidata= hapiclient.hapi(server, dataset, parameters, start, stop, **opts)
    toCDF( hapidata, '/tmp/mydata.cdf' )

    Parameters
    ----------
    hapidata : tuple
        this is a two-element tuple containing the data and metadata returned by the HAPI server via the Python hapiclient.
    cdfname : str
        the name of the CDF file to write

    """

    data, meta = hapidata

    names = [m['name'] for m in meta['parameters']]

    cdf = spacepy.pycdf.CDF(cdfname, create=True)

    for i in range(len(names)):
        name = names[i]
        m = meta['parameters'][i]
        if i == 0:
            cdf[name] = convertTimes(data[m['name']])
            cdf[name].attrs['VAR_TYPE'] = 'support_data'
        else:
            cdf[name] = data[name]
            v = cdf[name]
            v.attrs['UNITS'] = ' ' if m['units'] is None else m['units']
            v.attrs['DEPEND_0'] = meta['parameters'][0]['name']
            v.attrs['VAR_TYPE'] = 'data'

        if 'description' in m:
            cdf[name].attrs['CATDESC'] = m['description']
    cdf.attrs['Author'] = 'ConvertCDFWow'
    cdf.attrs['CreateDate'] = datetime.datetime.now()

    cdf.close()

'''
server = 'https://cdaweb.gsfc.nasa.gov/hapi'
dataset = 'OMNI2_H0_MRG1HR'
start = '2003-09-01T00:00:00'
stop = '2003-12-01T00:00:00'
parameters = 'KP1800,DST1800'
'''

server = 'https://jfaden.net/HapiServerDemo/hapi'
dataset = 'Iowa City Conditions'
start = '2022-06-20T00:00:00.000Z'
stop = '2022-06-28T00:00:00.000Z'
parameters = 'Temperature,WindSpeed'

'''
# https://jfaden.net/HapiServerDemo/hapi/info?id=Spectrum
server = 'https://jfaden.net/HapiServerDemo/hapi'
dataset = 'Spectrum'
start = '2016-01-01T00:00:00.000Z'
stop = '2016-01-02T00:00:00.000Z'
parameters = ''
'''

filename = '/tmp/fromHapiToCDF.cdf'
if os.path.exists(filename):
    os.remove(filename)

opts = {'logging': True}
hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)
toCDF(hapidata, filename)

print('wrote {}'.format(filename))
