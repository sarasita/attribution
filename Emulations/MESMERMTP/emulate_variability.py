
#%%
"""
Simple routine for generating temperature emulations.
"""

#################################
#       Import Statements       #
#################################
# setting paths correctly 
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
        print(model_id)
        run_id_training = cset.model_training_mapping[model_id]
        
        trend_parameter_path = cset.OUTPUT_DIR / f'calib/tas/tas_trend/{model_id}/'
        var_parameter_path   = cset.OUTPUT_DIR / f'calib/tas/tas_var/{model_id}/'

        std = joblib.load(var_parameter_path / 'std_object.pkl')
        pca = joblib.load(var_parameter_path / 'pca_object.pkl')
        pt  = joblib.load(var_parameter_path / 'pt_object.pkl')
        combi_params = joblib.load(var_parameter_path / 'ar_parameters.pkl')
        covs = joblib.load(var_parameter_path / 'cov-matrix_parameters.pkl')

        ssp_id   = 'ssp245'
        n_emus   = 600 
        n_years  = 72
        n_buffer = 10
        n_components = pca.n_components_

        # - variability / residuals 
        emu_innovs_pt  = np.zeros((n_emus, (n_years+n_buffer)*12, n_components))  
        for m in tqdm(range(12), total = 12):
            emu_innovs_pt[:, m::12, :] = multivariate_normal(mean = np.zeros((n_components)), cov = covs[m], size = (n_emus, n_years + n_buffer))

        emu_var_pt = np.copy(emu_innovs_pt)
        for t in range(12, (n_years + n_buffer)*12):
            emu_var_pt[:, t, :] = combi_params[t%12, :, 0]*emu_var_pt[:, t-1, :] + combi_params[t%12, :, 1] + emu_innovs_pt[:, t, :]

        storage_path = Path(f'/mnt/PROVIDE/sarah/income_decile/emus/tas/var/{model_id}/')
        storage_path.mkdir(parents = True, exist_ok = True)
        
        for i_emu in range(n_emus):
            emu_var_tmp = std.inverse_transform(pca.inverse_transform(pt.inverse_transform(emu_var_pt[i_emu, :, :][10*12:, :])))
            joblib.dump(emu_var_tmp, storage_path / f'tas-emu-var_{model_id}_across-scen_{str(i_emu).zfill(3)}.pkl')
    