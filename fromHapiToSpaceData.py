import os.path
import datetime
import re
import time

import spacepy.pycdf
import spacepy.datamodel as datamodel
import hapiclient
import hapiclient.hapitime

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
            d = hapiclient.hapitime.hapitime2datetime(data[m['name']])
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
