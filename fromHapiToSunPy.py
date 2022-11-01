import astropy.units as u
from sunpy.timeseries import GenericTimeSeries
import hapiclient
from hapiclient.hapitime import hapitime2datetime
import pandas as pd


def hapi_to_time_series(hapidata):
    hdata, meta = hapidata
    names = [m['name'] for m in meta['parameters']]

    units = {}

    for i in range(len(names)):
        name = names[i]
        m = meta['parameters'][i]
        var_key = m['name']
        if i == 0:
            index_key = m['name']
            index = hapitime2datetime(hdata[index_key])
            df = pd.DataFrame(index=pd.DatetimeIndex(name=index_key, data=index))
        else:
            data = hdata[name]
            unit_str = ' ' if m['units'] is None else m['units']
            try:
                unit = u.Unit(unit_str)
            except ValueError:
                if unit_str in _known_units:
                    unit = _known_units[unit_str]
                else:
                    warn_user(f'astropy did not recognize units of "{unit_str}". '
                              'Assigning dimensionless units. '
                              'If you think this unit should not be dimensionless, '
                              'please raise an issue at https://github.com/sunpy/sunpy/issues')
                    unit = u.dimensionless_unscaled
            if data.ndim > 2:
                # Skip data with dimensions >= 3 and give user warning
                warn_user(
                    f'The variable "{var_key}" has been skipped because it has more than 2 dimensions,'
                    ' which is unsupported.')
            elif data.ndim == 2:
                for icol, col in enumerate(data.T):
                    df[var_key + f'_{icol}'] = col
                    units[var_key + f'_{icol}'] = unit
            else:
                df[var_key] = data
                units[var_key] = unit

    result = GenericTimeSeries(data=df, units=units, meta=meta)

    return result

