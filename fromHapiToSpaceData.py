import os.path
import datetime
import re

import spacepy.pycdf
import spacepy.datamodel as datamodel
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

def handle_bins(data, name, bins):
    """
    Add non-time-varying bins variable

    Parameters
    ----------
    data : data
        the data to add the variable
    name : str
        the name of the variable
    bins : str
        the "bins" node of the HAPI response
    """
    if 'centers' in bins:
        o = bins['centers']
        if type(o) != str:  # string is just a reference to another variable
            centers = [float(v) for v in bins['centers']]
        else:
            return
    elif 'ranges' in bins:
        ranges = bins['ranges']
    else:
        raise Exception('Not supported')

    if 'centers' not in locals():
        centers = [a[0] + (a[1] - a[0]) / 2 for a in ranges]

    data[name] = datamodel.dmarray(input_array=centers)
    data[name].attrs['UNITS'] = bins['units']
    data[name].attrs['VAR_TYPE'] = 'support_data'

    if 'ranges' in locals():
        import numpy
        delta_plus_var = numpy.zeros(len(centers))
        for i in range(len(centers)):
            delta_plus_var[i] = ranges[i][1] - centers[i]
        delta_minus_var = numpy.zeros(len(centers))
        for i in range(len(centers)):
            delta_minus_var[i] = centers[i] - ranges[i][0]
        data[name + 'DeltaMinus'] = delta_minus_var
        data[name + 'DeltaPlus'] = delta_plus_var
        data[name].attrs['DELTA_PLUS_VAR'] = name + 'DeltaPlus'
        data[name].attrs['DELTA_MINUS_VAR'] = name + 'DeltaMinus'


def to_SpaceData(hapidata):
    """Reformat the response from the Python hapiclient to an object similar to a cdf.  The cdf
     will be similar to the object returned by reading a data.

    This is typically called using the  of the Python hapiclient.
    which is a tuple containing the data and the metadata from a HAPI
    call.  For example:

    hapidata = hapiclient.hapi(server, dataset, parameters, start, stop, **opts)
    data = to_Pydata( hapidata )

    Parameters
    ----------
    hapidata : tuple
        this is a two-element tuple containing the data and metadata returned by the HAPI server via the Python hapiclient.

    """

    data, meta = hapidata

    names = [m['name'] for m in meta['parameters']]

    result = datamodel.SpaceData()

    for i in range(len(names)):
        name = names[i]
        m = meta['parameters'][i]
        if i == 0:
            d = convert_times(data[m['name']])
            result[name] = datamodel.dmarray(d)
            result[name].attrs['VAR_TYPE'] = 'support_data'
        else:
            d = data[name]
            result[name] = datamodel.dmarray(d)
            v = result[name]
            if 'bins' in m:
                bins = m['bins']
                idep = 1
                if isinstance(bins, dict):
                    refstr = bins.get('$ref')
                    ref = re.match('\#\/definitions\/(.+)', refstr).group(1)
                    bins = meta['definitions'][ref]

                for b in bins:
                    # TODO: figure out why this works when multiple variables use the same bins.
                    handle_bins(result, b['name'], b)
                    v.attrs['DEPEND_%d' % idep] = b['name']
                    idep = idep + 1
            v.attrs['UNITS'] = ' ' if m['units'] is None else m['units']
            v.attrs['DEPEND_0'] = meta['parameters'][0]['name']
            v.attrs['VAR_TYPE'] = 'data'

        if 'description' in m:
            result[name].attrs['CATDESC'] = m['description']

    result.attrs = {'CreateDate': datetime.datetime.now()}

    return result
