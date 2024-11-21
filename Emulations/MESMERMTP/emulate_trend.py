
#################################
#       Import Statements       #
#################################
# setting paths correctly 
import os
import sys
# computation
import xarray as xr
import numpy as np
import pandas as pd
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

from Emulations.MESMERMTP.utils.prepare_input import get_input_data

#%%

# parallelizing
from joblib import Parallel, delayed

# response module
from sklearn.linear_model import LinearRegression

# variability module 
# - mapping to normal distribution 
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.preprocessing import PowerTransformer
from numpy.random import multivariate_normal
# - fitting AR process
from scipy.optimize import curve_fit
def lin_func(x, a, b):
    return(a * x + b)
def execute_bounded_linfit(x,y):
    return(curve_fit(lin_func, x, y, bounds=([-1,-np.inf], [1, np.inf]))[0])


#%%

if __name__ == '__main__':
    for model_id in tqdm(cset.model_ids[:], total = cset.n_models):
    # for model_id in ['ACCESS-ESM1-5', 'CanESM5', 'MPI-ESM1-2-LR']:
        try:
            print(model_id)
            run_id_training = cset.model_training_mapping[model_id]
            
            trend_parameter_path = cset.OUTPUT_DIR / f'calib/tas/tas_trend/{model_id}/'
            
            LinReg = joblib.load(trend_parameter_path / 'LinReg_object.pkl')

            magicc_output_df      = pd.read_csv(cfg.PROCESSED_GMT_DIR / 'MAGICC-GMT_processed.csv', index=False)
            sel_columns           = [f'{year}-01-01 00:00:00' for year in np.arange(1850,1901)] + [f'{year}-01-01 00:00:00' for year in np.arange(2000,2021)] 
            attribution_scenarios = np.unique(magicc_output_df.scenario)
            
            sel_scenarios = ['ssp245', 
                            'CN_p90p100_equal-scaling', 'IN_p90p100_equal-scaling', 'EU27_p90p100_equal-scaling', 'US_p90p100_equal-scaling', 'World_p90p100_equal-scaling',
                            'CN_p99p100_equal-scaling', 'IN_p99p100_equal-scaling', 'EU27_p99p100_equal-scaling', 'US_p99p100_equal-scaling', 'World_p99p100_equal-scaling',
                            'World_p90p100_CH4-scaling', 'World_p90p100_CO2-scaling'
                            ]
            
            for scen in tqdm(sel_scenarios, total  = len(sel_scenarios)): 
                sub_df = magicc_output_df[(magicc_output_df.scenario == scen)]
                for i_run in range(600): 
                    GMT_trend = sub_df.loc[:, sel_columns].iloc[i_run,:].values.flatten()
                    GMT_var   = joblib.load(cset.OUTPUT_DIR / 'emus' / 'gmt_emus_LO' / 'var' / model_id / f'GMT-var_{model_id}_ssp245_{run_id_training}_{str(i_run).zfill(3)}.pkl')[:len(GMT_trend)]
                    tas_trend = LinReg.predict(np.array([GMT_trend, GMT_var]).T).reshape(-1, ccon.n_sindex)
                    
                    if scen == 'ssp245': 
                        hist_path = Path(f'/mnt/PROVIDE/sarah/income_decile/emus/tas/trend/{scen}/hist/{model_id}/')
                        hist_path.mkdir(parents = True, exist_ok = True)
                        present_path = Path(f'/mnt/PROVIDE/sarah/income_decile/emus/tas/trend/{scen}/presentday/{model_id}/')
                        present_path.mkdir(parents = True, exist_ok = True)
                        joblib.dump(tas_trend[:51*12], hist_path / f'tas-emu-trend-hist_{model_id}_{scen}_{str(i_run).zfill(3)}.pkl')
                        joblib.dump(tas_trend[51*12:], present_path / f'tas-emu-trend-present_{model_id}_{scen}_{str(i_run).zfill(3)}.pkl')
                    else: 
                        present_path = Path(f'/mnt/PROVIDE/sarah/income_decile/emus/tas/trend/{scen}/{model_id}/')
                        present_path.mkdir(parents = True, exist_ok = True)
                        joblib.dump(tas_trend[51*12:], present_path / f'tas-emu-trend-present_{model_id}_{scen}_{str(i_run).zfill(3)}.pkl')
        except: 
            print(f'Failed for {model_id}')