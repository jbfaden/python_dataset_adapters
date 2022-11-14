import os.path
import datetime
import re

import spacepy.pycdf
from hapiclient.hapitime import hapitime2datetime


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
    else:
        ranges = bins['ranges']

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
            cdf[name] = hapitime2datetime(data[m['name']])
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
                    handle_bins(cdf, b['name'], b)
                    v.attrs['DEPEND_%d' % idep] = b['name']
                    idep = idep + 1
            v.attrs['UNITS'] = ' ' if m['units'] is None else m['units']
            v.attrs['DEPEND_0'] = meta['parameters'][0]['name']
            v.attrs['VAR_TYPE'] = 'data'

        if 'description' in m:
            cdf[name].attrs['CATDESC'] = m['description']

    cdf.attrs['Author'] = 'fromHapiToCDF'
    cdf.attrs['CreateDate'] = datetime.datetime.now()

    cdf.close()

