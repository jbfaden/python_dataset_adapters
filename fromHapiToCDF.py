import os.path
import datetime
import re

import spacepy.pycdf
import hapiclient

# frompyfunc
# numpy.vectorize
# ticktock
# foo = numpy.vectorize(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))
# foo( '2020-02-02','2020-02-03')
# { x(i) : for i in iis } dictionary comprehension
# https://github.com/spacepy/spacepy/issues/523

def calculate_format_str(isotime):
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
        raise ValueError('date cannot have %d characters: %s' % (datelen, isotime))

    formForLength = {
        2: "%H",
        4: '%H%M',
        5: '%H:%M',
        6: '%H%M%S',
        8: '%H:%M:%S'
        # note case for 10 and up below
    }

    timelen = len(isotime) - datelen - 1

    if timelen > 9:
        timeform = "%H:%M:%S.%f"
    elif timelen < 1:
        timeform = ""
    else:
        timeform = formForLength[timelen]

    if timeform is None:
        raise ValueError("time cannot have {:d} characters: {:s}".format(datelen, isotime))
    elif len(timeform) == 0:
        return "{}{}".format(form, zstr)
    else:
        return "{}T{}{}".format(form, timeform, zstr)


def convert_times(isotime_array):
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
    if len(isotime_array) == 0:
        print('isotime_array has len 0')
        return isotime_array  # raise ValueError('isotime array is empty')
    form = calculate_format_str(isotime_array[0].decode('ascii'))
    return [datetime.datetime.strptime(isotime.decode('ascii'), form) for isotime in isotime_array]


def handle_bins(cdf, name, bins):
    """
    Add non-time-varying bins variable

    Parameters
    ----------
    cdf : CDF
        the cdf to add the variable
    name : str
        the name of the variable
    bins : str
        the "bins" node of the HAPI response
    """
    if 'centers' in bins:
        centers = [float(v) for v in bins['centers']]
    elif 'ranges' in bins:
        ranges = bins['ranges']
    else:
        raise Exception('Not supported')

    if 'centers' not in locals():
        centers = [a[0] + (a[1] - a[0]) / 2 for a in ranges]

    cdf[name] = centers
    cdf[name].attrs['UNITS'] = bins['units']
    cdf[name].attrs['VAR_TYPE'] = 'support_data'

    if 'ranges' in locals():
        import numpy
        delta_plus_var = numpy.zeros(len(centers))
        for i in range(len(centers)):
            delta_plus_var[i] = ranges[i][1] - centers[i]
        delta_minus_var = numpy.zeros(len(centers))
        for i in range(len(centers)):
            delta_minus_var[i] = centers[i] - ranges[i][0]
        cdf[name + 'DeltaMinus'] = delta_minus_var
        cdf[name + 'DeltaPlus'] = delta_plus_var
        cdf[name].attrs['DELTA_PLUS_VAR'] = name + 'DeltaPlus'
        cdf[name].attrs['DELTA_MINUS_VAR'] = name + 'DeltaMinus'

def to_CDF(hapidata, cdfname):
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
            cdf[name] = convert_times(data[m['name']])
            cdf[name].attrs['VAR_TYPE'] = 'support_data'
        else:
            cdf[name] = data[name]
            v = cdf[name]
            if 'bins' in m:
                bins = m['bins']
                idep = 1
                if isinstance(bins, dict):
                    refstr = bins.get('$ref')
                    ref = re.match('\#\/definitions\/(.+)', refstr).group(1)
                    bins = meta['definitions'][ref]

                for b in bins:
                    # TODO: figure out why this works when multiple variables use the same bins.
                    handle_bins(cdf, b['name'], b)
                    v.attrs['DEPEND_%d' % idep] = b['name']
                    idep = idep + 1
            v.attrs['UNITS'] = ' ' if m['units'] is None else m['units']
            v.attrs['DEPEND_0'] = meta['parameters'][0]['name']
            v.attrs['VAR_TYPE'] = 'data'

        if 'description' in m:
            cdf[name].attrs['CATDESC'] = m['description']
    cdf.attrs['Author'] = 'ConvertCDFWow'
    cdf.attrs['CreateDate'] = datetime.datetime.now()

    cdf.close()

