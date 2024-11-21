"""
Single wrapper function for accessing training data 
"""

# setting paths correctly 
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

# setting paths such that execution works from console & interactive shell 
import config.settings as cset
import config.constants as ccon

from utils.load_data import load_and_prepare_land_dataset, load_land_gmt_dataset

# functions 

def get_input_data(model_id, run_id_training = None):
    '''
    Function for opening training data needed to train MESMER-M-TP.
    For the specified model and ensemble member, temperature and 
    precipitation data along with global mean temperature estimates
    across all available scenarios is loaded in 

    Parameters
    ----------
    model_id : string
        Name of the Earth System Model 
    run_id_training : list of strings
        List of strings identifiyng scenario-ensemble member combinations for processing
    vars_ : list of strings 
        Names of variables 
    compute_anomalies: binary
        If set to True, temperature data will be converted to anomalies relative to the 
        reference period specified in the configs.constants file 

    Returns
    -------
   ds_return : xarrax.dataset
        Dataset containing a monthly field timeseries of all input variables over land 
    '''
    
    print('Preparing input data')
    
    if run_id_training is None: 
        run_id_training  = cset.model_training_mapping[model_id]
    
    # Load pre-processed and stored GMT data and extract meta data 
    GMT_ds          = xr.open_dataset(ccon.PROCESSED_DIR / f'{model_id}/GMT/{model_id}_GMT-LO_processed.nc').load()
    c_ssp_ids       = GMT_ds['abs_gmt'].sel(run_id = run_id_training).dropna(dim = 'year', how = 'all').ssp_id.values
    n_c_ssp_ids     = len(c_ssp_ids)-1 
    n_years         = 165 + n_c_ssp_ids*86
    
    print('- Local temperature and precipitation')
    # loading local temperature and precipitation data 
    ds_esm          = load_and_prepare_land_dataset(model_id, [f'{ssp_id}_{run_id_training}' for ssp_id in c_ssp_ids], ['tas', 'pr']).load()
   
    # put this part in function for conversion between xarray and numpy 
    tas_hist        = ds_esm['tas_rel'].sel(run_id = run_id_training, ssp_id = 'historical').stack(coords = ('lat', 'lon')).dropna(dim = 'coords', how = 'all').dropna('time').values
    pr_hist         = ds_esm['pr'].sel(run_id = run_id_training, ssp_id = 'historical').stack(coords = ('lat', 'lon')).dropna(dim = 'coords', how = 'all').dropna('time').values
    
    tas_ssp         = ds_esm['tas_rel'].sel(run_id = run_id_training, ssp_id = c_ssp_ids[1:]).dropna('time', how = 'all').stack(coords = ('lat', 'lon')).dropna(dim = 'coords', how = 'all').values
    pr_ssp          = ds_esm['pr'].sel(run_id = run_id_training, ssp_id = c_ssp_ids[1:]).dropna('time', how = 'all').stack(coords = ('lat', 'lon')).dropna(dim = 'coords', how = 'all').values
    
    del ds_esm
    
    tas_all         = np.zeros((12*(ccon.n_hist_years + n_c_ssp_ids*ccon.n_ssp_years), ccon.n_sindex))
    abs_pr_all      = np.zeros((12*(ccon.n_hist_years + n_c_ssp_ids*ccon.n_ssp_years), ccon.n_sindex))
    
    tas_all[:ccon.n_hist_years*12, :]     = tas_hist
    abs_pr_all[:ccon.n_hist_years*12, :]  = pr_hist
    
    for s in range(n_c_ssp_ids):
        tas_all[12*(ccon.n_hist_years + s*ccon.n_ssp_years):12*(ccon.n_hist_years + (s+1)*ccon.n_ssp_years),:]     = tas_ssp[s, :, :]
        abs_pr_all[12*(ccon.n_hist_years + s*ccon.n_ssp_years):12*(ccon.n_hist_years + (s+1)*ccon.n_ssp_years),:]  = pr_ssp[s, :, :]
    
    del tas_hist, pr_hist, tas_ssp, pr_ssp
    
    print('- Global variables')
    GMT                           = np.zeros((ccon.n_hist_years + (len(c_ssp_ids)-1)*ccon.n_ssp_years))
    GMT_trend                     = np.zeros((ccon.n_hist_years + (len(c_ssp_ids)-1)*ccon.n_ssp_years))

    GMT[:ccon.n_hist_years]       = GMT_ds['rel_gmt'].sel(run_id = run_id_training, ssp_id = 'historical').dropna('year').values
    GMT[ccon.n_hist_years:]       = GMT_ds['rel_gmt'].sel(run_id = run_id_training, ssp_id = c_ssp_ids[1:]).dropna('year').values.flatten()
    
    GMT_trend[:ccon.n_hist_years] = GMT_ds['rel_gmt_trend'].sel(run_id = run_id_training, ssp_id = 'historical').dropna('year').values
    GMT_trend[ccon.n_hist_years:] = GMT_ds['rel_gmt_trend'].sel(run_id = run_id_training, ssp_id = c_ssp_ids[1:]).dropna('year').values.flatten()
    
    GMT_var                        = GMT - GMT_trend 
    
    return(tas_all, abs_pr_all, GMT, GMT_trend, GMT_var)