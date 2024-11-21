
'''
Postprocessing of attribution results 
- recenter GMT results to 1850-1900 reference period
- rescale GMT results to be conistent with present-day warming (multiply by 0.85)
- combine all runs into a single dataframe 
'''

from pathlib import Path
import os
import sys
sys.path.append(os.path.abspath(''))

import pandas as pd 
import numpy as np

from tqdm import tqdm

import config.config as cfg 
from config.config import (MAGICC_OUTPUT_FILES)

sel_columns      = ['climate_model', 'model', 'region', 'run_id', 'scenario', 'unit', 'variable'] + [f'{int(iter)}-01-01 00:00:00' for iter in np.arange(1800, 2021,1)]
reference_period = pd.date_range(start='1850-01-01', end='1900-01-01', freq='YS')

if __name__ == '__main__':
    for i, MAGICC_OUTPUT_FILE in tqdm(enumerate(MAGICC_OUTPUT_FILES), total = len(MAGICC_OUTPUT_FILES)):
        # load data
        magicc_output_df = pd.read_csv(MAGICC_OUTPUT_FILE)
        # only keep surface air temperature 
        magicc_output_df = magicc_output_df[magicc_output_df.variable == 'Surface Air Temperature Change'].loc[:, sel_columns] 
        # select columns over reference period 
        reference_cols   = [col for col in magicc_output_df.columns if col in reference_period.strftime('%Y-%m-%d %H:%M:%S')]
        def recenter_row(row):
            # the seventh column in dataframe is where the numeric data starts 
            reference_mean = row[reference_cols].mean()
            return row[7:] - reference_mean
        
        # select columns with numeric (gmt) data
        numeric_cols = magicc_output_df.columns[7:]  # Assuming numeric data starts from the 8th column
        magicc_output_df[numeric_cols] = magicc_output_df.apply(recenter_row, axis=1)
        magicc_output_df[numeric_cols] *= 0.85*1/(magicc_output_df[magicc_output_df.scenario == 'ssp245'].loc[:, '1990-01-01 00:00:00':'2014-01-01 00:00:00'].mean().mean())
        if i == 0:
            magicc_output_combined_df = magicc_output_df.copy()
        else: 
            magicc_output_combined_df = pd.concat([magicc_output_combined_df, magicc_output_df[magicc_output_df.scenario != 'ssp245']], axis=0, ignore_index = True)

    # store datafrmae 
    Path(cfg.PROCESSED_GMT_DIR).mkdir(parents=True, exist_ok=True)
    magicc_output_combined_df.to_csv(cfg.PROCESSED_GMT_DIR / 'MAGICC-GMT_processed.csv', index=False) 

