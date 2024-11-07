import regionmask 
import xarray as xr
import numpy as np

ar6 = regionmask.defined_regions.ar6.land

def regional_data(df):
    mask = ar6.mask(df)
    weights = np.cos(np.deg2rad(df.lat))
    weights.name = "weights"
    df_agg = (df).groupby(mask).median('coords')
    df_glob = (df).median('coords').expand_dims(mask = [45])
    return(xr.concat([df_agg, df_glob], dim = 'mask'))

def abbrevs(x):
    if int(x) == 45: 
        return('global')
    else:
        return(ar6.abbrevs[int(x)])