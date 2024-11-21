
#%%
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

threshold_path = Path('/mnt/PROVIDE/sarah/income_decile/result/thresholds/')
tas_emus_path = Path(f'/mnt/PROVIDE/sarah/income_decile/emus/tas/')
frequency_path = Path('/mnt/PROVIDE/sarah/income_decile/result/frequency_change/')

sel_scenarios = ['ssp245', 
                'CN_p90p100_equal-scaling', 'IN_p90p100_equal-scaling', 'EU27_p90p100_equal-scaling', 'US_p90p100_equal-scaling', 'World_p90p100_equal-scaling',
                'CN_p99p100_equal-scaling', 'IN_p99p100_equal-scaling', 'EU27_p99p100_equal-scaling', 'US_p99p100_equal-scaling', 'World_p99p100_equal-scaling',
                'World_p90p100_CH4-scaling', 'World_p90p100_CO2-scaling'
                ]

def count_exceedances(scen, model_id, i_run, thresholds_cold, thresholds_hot):
    if scen == 'ssp245': 
        tas_trend = joblib.load(tas_emus_path / f'trend/ssp245/presentday/{model_id}/tas-emu-trend-present_{model_id}_ssp245_{str(i_run).zfill(3)}.pkl').reshape(-1,12,ccon.n_sindex)[-1:, :, :]
        tas_var   = joblib.load(tas_emus_path / f'var/{model_id}/tas-emu-var_{model_id}_across-scen_{str(i_run).zfill(3)}.pkl').reshape(-1,12,ccon.n_sindex)[-1, :, :]
    else: 
        tas_trend = joblib.load(tas_emus_path / f'trend/{scen}/{model_id}/tas-emu-trend-present_{model_id}_{scen}_{str(i_run).zfill(3)}.pkl').reshape(-1,12,ccon.n_sindex)[-1:, :, :]
        tas_var   = joblib.load(tas_emus_path / f'var/{model_id}/tas-emu-var_{model_id}_across-scen_{str(i_run).zfill(3)}.pkl').reshape(-1,12,ccon.n_sindex)[-1:, :, :]      
    
    tas_present = tas_trend+tas_var
    hot_counts  = [np.sum(tas_present >= thresholds_hot[i_q, :, :], axis = 0) for i_q in range(3)]
    cold_counts = [np.sum(tas_present <= thresholds_cold[i_q, :, :], axis = 0) for i_q in range(3)]
      
    return(hot_counts, cold_counts)

for model_id in cset.model_ids[11:]: 
    print(model_id)
    try: 
        tas_thresholds_cold = joblib.load(threshold_path / 'tas' / f'{model_id}' / f'tas-thresholds-cold_{model_id}.pkl')
        tas_thresholds_hot  = joblib.load(threshold_path / 'tas' / f'{model_id}' / f'tas-thresholds-hot_{model_id}.pkl')
        
        Path(frequency_path / 'tas' / f'{model_id}').mkdir(parents = True, exist_ok = True)
        
        for scen in sel_scenarios:
            result_counts_raw = Parallel(n_jobs = -1)(delayed(count_exceedances)(scen, model_id, i_run, tas_thresholds_cold, tas_thresholds_hot) for i_run in tqdm(range(600), total = 600))
            
            hot_counts = np.array([result_counts_raw[i_run][0] for i_run in range(600)]).sum(axis = 0)/600*100
            cold_counts = np.array([result_counts_raw[i_run][1] for i_run in range(600)]).sum(axis = 0)/600*100
            
            del result_counts_raw
            
            joblib.dump(hot_counts, frequency_path / 'tas' / f'{model_id}' / f'tas-presentday-frequencies-hot_{scen}_{model_id}.pkl')
            joblib.dump(cold_counts, frequency_path / 'tas' / f'{model_id}' / f'tas-presentday-frequencies-cold_{scen}_{model_id}.pkl')
    except:
        print(f'Failed for {model_id}')    
