import pandas as pd
import astropy.units as u
from sunpy.timeseries import GenericTimeSeries
from sunpy.util.exceptions import warn_user
from hapiclient.hapitime import hapitime2datetime

# This was copied from https://github.com/sunpy/sunpy/blob/main/sunpy/io/cdf.py, which
# contains a _known_units dictionary.  It is reused here, since the same
# units will appear in the CDAWeb HAPI server.  --Jeremy Faden
#
# Unfortunately (unlike e.g. FITS), there is no standard for the strings that
# CDF files use to represent units. To allow for this we maintain a dictionary
# mapping unit strings to their astropy unit equivalents.
#
# Please only add new entries if
#   1. A user identifies which specific mission/data source they are needed for
#   2. The mapping from the string to unit is un-ambiguous. If we get this
#      wrong then users will silently have the wrong units in their data!
_known_units = {'ratio': u.dimensionless_unscaled,
                'NOTEXIST': u.dimensionless_unscaled,
                'Unitless': u.dimensionless_unscaled,
                'unitless': u.dimensionless_unscaled,
                'Quality_Flag': u.dimensionless_unscaled,
                'None': u.dimensionless_unscaled,
                'none': u.dimensionless_unscaled,
                ' none': u.dimensionless_unscaled,
                'counts': u.dimensionless_unscaled,
                'cnts': u.dimensionless_unscaled,

                'microW m^-2': u.mW * u.m**-2,

                'years': u.yr,
                'days': u.d,

                '#/cc': u.cm**-3,
                '#/cm^3': u.cm**-3,
                'cm^{-3}': u.cm**-3,
                'particles cm^-3': u.cm**-3,
                'n/cc (from moments)': u.cm**-3,
                'n/cc (from fits)': u.cm**-3,
                'Per cc': u.cm**-3,
                '#/cm3': u.cm**-3,
                'n/cc': u.cm**-3,

                'km/sec': u.km / u.s,
                'km/sec (from fits)': u.km / u.s,
                'km/sec (from moments)': u.km / u.s,
                'Km/s': u.km / u.s,

                'Volts': u.V,

                'earth radii': u.earthRad,
                'Re': u.earthRad,
                'Earth Radii': u.earthRad,
                'Re (1min)': u.earthRad,
                'Re (1hr)': u.earthRad,

                'Degrees': u.deg,
                'degrees': u.deg,
                'Deg': u.deg,
                'deg (from fits)': u.deg,
                'deg (from moments)': u.deg,
                'deg (>200)': u.deg,

                'Deg K': u.K,
                'deg_K': u.K,
                '#/{cc*(cm/s)^3}': (u.cm**3 * (u.cm / u.s)**3)**-1,
                'sec': u.s,
                'Samples/s': 1 / u.s,

                'seconds': u.s,
                'nT GSE': u.nT,
                'nT GSM': u.nT,
                'nT DSL': u.nT,
                'nT SSL': u.nT,
                'nT (1min)': u.nT,
                'nT (3sec)': u.nT,
                'nT (1hr)': u.nT,
                'nT (>200)': u.nT,

                'msec': u.ms,
                'milliseconds': u.ms,

                '#/cm2-ster-eV-sec': 1 / (u.cm**2 * u.sr * u.eV * u.s),
                '#/(cm^2*s*sr*MeV/nuc)': 1 / (u.cm**2 * u.s * u.sr * u.MeV),
                '#/(cm^2*s*sr*Mev/nuc)': 1 / (u.cm**2 * u.s * u.sr * u.MeV),
                '#/(cm^2*s*sr*Mev/nucleon)': 1 / (u.cm**2 * u.s * u.sr * u.MeV),
                '#/(cm2-steradian-second-MeV/nucleon) ': 1 / (u.cm**2 * u.s * u.sr * u.MeV),
                '1/(cm2 Sr sec MeV/nucleon)': 1 / (u.cm**2 * u.sr * u.s * u.MeV),
                '1/(cm**2-s-sr-MeV)': 1 / (u.cm**2 * u.s * u.sr * u.MeV),
                '1/(cm**2-s-sr-MeV/nuc.)': 1 / (u.cm**2 * u.s * u.sr * u.MeV),
                '(cm^2 s sr MeV/n)^-1': 1 / (u.cm**2 * u.s * u.sr * u.MeV),
                'cm!E-2!Nsr!E-1!Nsec!E-1!N(MeV/nuc)!E-1!N': 1 / (u.cm**2 * u.s * u.sr * u.MeV),
                'cm!E-2!Nsr!E-1!Nsec!E-1!NMeV!E-1!N': 1 / (u.cm**2 * u.s * u.sr * u.MeV),
                '1/(cm^2 sec ster MeV)': 1 / (u.cm**2 * u.s * u.sr * u.MeV),
                '(cm^2 s sr MeV)^-1': 1 / (u.cm**2 * u.s * u.sr * u.MeV),
                'cnts/sec/sr/cm^2/MeV': 1 / (u.cm**2 * u.s * u.sr * u.MeV),

                'particles / (s cm^2 sr MeV)': 1 / (u.cm**2 * u.s * u.sr * u.MeV),
                'particles / (s cm^2 sr MeV/n)': 1 / (u.cm**2 * u.s * u.sr * u.MeV),
                'particles/(s cm2 sr MeV/n)': 1 / (u.cm**2 * u.s * u.sr * u.MeV),

                '1/(cm**2-s-sr)': 1 / (u.cm**2 * u.s * u.sr),
                '1/(SQcm-ster-s)': 1 / (u.cm**2 * u.s * u.sr),
                '1/(SQcm-ster-s)..': 1 / (u.cm**2 * u.s * u.sr),

                'photons cm^-2 s^-1': 1 / (u.cm**2 * u.s),

                'Counts/256sec': 1 / (256 * u.s),
                'Counts/hour': 1 / u.hr,
                'counts/min': 1 / u.min,
                'counts / s': 1/u.s,
                'counts/s': 1/u.s,
                'cnts/sec': 1/u.s,
                'counts s!E-1!N': 1/u.s,
                }

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

