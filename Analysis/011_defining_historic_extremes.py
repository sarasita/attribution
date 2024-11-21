
#%%

import os
import sys
# computation
import xarray as xr
import numpy as np
import joblib
from joblib              import Parallel, delayed

# utils
from tqdm   import tqdm 
from pathlib import Path
import warnings

# plotting
import matplotlib.pyplot as plt
import cartopy.crs       as ccrs
import matplotlib as mpl
import seaborn as sns

# setting paths such that execution works from console & interactive shell 
import Emulations.MESMERMTP.config.settings as cset
import Emulations.MESMERMTP.config.constants as ccon
import config.config as cfg
#%%

tas_emus_path = Path(f'/mnt/PROVIDE/sarah/income_decile/emus/tas/')
def full_hist_temperature_emulation(scen, model_id, i_run):
    tas_trend = joblib.load(tas_emus_path / f'trend/{scen}/hist/{model_id}/tas-emu-trend-hist_{model_id}_{scen}_{str(i_run).zfill(3)}.pkl').reshape(-1,12,ccon.n_sindex)[:50, :, :]
    tas_var   = joblib.load(tas_emus_path / f'var/{model_id}/tas-emu-var_{model_id}_across-scen_{str(i_run).zfill(3)}.pkl').reshape(-1,12,ccon.n_sindex)[:50, :, :]
    return(tas_trend + tas_var)


threshold_path = Path('/mnt/PROVIDE/sarah/income_decile/result/thresholds/')

scen = 'ssp245'

for model_id in cset.model_ids:
    try: 
        print(model_id) 
        tas_historic = np.array(Parallel(n_jobs = -1)(delayed(full_hist_temperature_emulation)(scen, model_id, i_run) for i_run in tqdm(range(600), total = 600))).reshape(600*50, 12, 2652)
        
        tas_thresholds_cold  = np.quantile(tas_historic, q = [0.02, 0.01, 0.0001], axis = 0)
        tas_thresholds_hot   = np.quantile(tas_historic, q = [0.98, 0.99, 0.9999], axis = 0)  

        Path(threshold_path / 'tas' / f'{model_id}').mkdir(parents = True, exist_ok = True)

        joblib.dump(tas_thresholds_cold, threshold_path / 'tas' / f'{model_id}' / f'tas-thresholds-cold_{model_id}.pkl')
        joblib.dump(tas_thresholds_hot, threshold_path / 'tas' / f'{model_id}' / f'tas-thresholds-hot_{model_id}.pkl')

        del tas_historic, tas_thresholds_cold, tas_thresholds_hot 
    except:
        print(f'Failed for model {model_id}') 
