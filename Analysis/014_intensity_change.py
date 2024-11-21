import os
import sys
os.chdir('/home/ubuntu/sarah/files/income_decile/')
sys.path.append('/home/ubuntu/sarah/files/income_decile/')
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

def full_counter_temperature_emulation(scen, model_id, i_run):
    tas_trend = joblib.load(tas_emus_path / f'trend/{scen}/{model_id}/tas-emu-trend-present_{model_id}_{scen}_{str(i_run).zfill(3)}.pkl').reshape(-1,12,ccon.n_sindex)[-1:, :, :]
    tas_var   = joblib.load(tas_emus_path / f'var/{model_id}/tas-emu-var_{model_id}_across-scen_{str(i_run).zfill(3)}.pkl').reshape(-1,12,ccon.n_sindex)[-1:, :, :]
    return(tas_trend + tas_var)

def full_presentday_temperature_emulation(model_id, i_run):
    tas_trend = joblib.load(tas_emus_path / f'trend/ssp245/presentday/{model_id}/tas-emu-trend-present_{model_id}_ssp245_{str(i_run).zfill(3)}.pkl').reshape(-1,12,ccon.n_sindex)[-1:, :, :]
    tas_var   = joblib.load(tas_emus_path / f'var/{model_id}/tas-emu-var_{model_id}_across-scen_{str(i_run).zfill(3)}.pkl').reshape(-1,12,ccon.n_sindex)[-1, :, :]
    return(tas_trend + tas_var)

intensity_path = Path('/mnt/PROVIDE/sarah/income_decile/result/intensity_change/')

sel_scenarios = ['ssp245', 
                'CN_p90p100_equal-scaling', 'IN_p90p100_equal-scaling', 'EU27_p90p100_equal-scaling', 'US_p90p100_equal-scaling', 'World_p90p100_equal-scaling',
                'CN_p99p100_equal-scaling', 'IN_p99p100_equal-scaling', 'EU27_p99p100_equal-scaling', 'US_p99p100_equal-scaling', 'World_p99p100_equal-scaling',
                'World_p90p100_CH4-scaling', 'World_p90p100_CO2-scaling'
                ]

for model_id in cset.model_ids[15:]:
    print(model_id) 
    for scen in tqdm(sel_scenarios, total = len(sel_scenarios)):
        try: 
            if scen == 'ssp245':
                tas_present = np.array(Parallel(n_jobs = -1)(delayed(full_presentday_temperature_emulation)(model_id, i_run) for i_run in tqdm(range(600), total = 600))).reshape(600*1, 12, 2652)
            else: 
                tas_present = np.array(Parallel(n_jobs = -1)(delayed(full_counter_temperature_emulation)(scen, model_id, i_run) for i_run in tqdm(range(600), total = 600))).reshape(600*1, 12, 2652)
            
            tas_thresholds_cold  = np.quantile(tas_present, q = [0.02, 0.01, 0.0001], axis = 0)
            tas_thresholds_hot   = np.quantile(tas_present, q = [0.98, 0.99, 0.9999], axis = 0)  

            Path(intensity_path / 'tas' / f'{model_id}').mkdir(parents = True, exist_ok = True)

            joblib.dump(tas_thresholds_cold, intensity_path / 'tas' / f'{model_id}' / f'tas-presentday-thresholds-cold_{scen}_{model_id}.pkl')
            joblib.dump(tas_thresholds_hot, intensity_path / 'tas' / f'{model_id}' / f'tas-presentday-thresholds-hot_{scen}_{model_id}.pkl')

            del tas_present, tas_thresholds_cold, tas_thresholds_hot 
        except:
            print(f'Failed for model {model_id} and {scen}') 
        

#%%
