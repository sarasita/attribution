# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Clean attribution emissions
#
# This is where you will have the most work to do. Basically, you need to set up all the different kinds of emissions for which you want to do attribution runs. Your notebook will probably look completely different to this, but this at least shows you the kind of data you want to write out and how it needs to be shaped.

# %%
import matplotlib.pyplot as plt
import numpy as np
import scmdata
import pandas as pd

from notebooks.config import (ATTRIBUTION_EMISSIONS_CLEAN,
                                 EMISSIONS_BASELINE, 
                                 SCALING_DIR,
                                 INVERSE_ATTRIBUTION_EMISSIONS,
                                 )


#%%
baseline_df = pd.read_csv(EMISSIONS_BASELINE)
attribution_emissions_df = baseline_df.copy()

groups     = ['p90p100', 'p99p100', 'p999p100', 'p0p50', 'p50p90']
group_size =  dict(zip(groups, [0.1, 0.01, 0.001, 0.5, 0.4]))

regionsl_group_sizes = {'World': group_size, 
                        'CN': dict(zip(groups, np.array([0.1, 0.01, 0.001, 0.5, 0.4])*0.206)), 
                        'EU27': dict(zip(groups, np.array([0.1, 0.01, 0.001, 0.5, 0.4])*0.0616)), 
                        'IN': dict(zip(groups, np.array([0.1, 0.01, 0.001, 0.5, 0.4])*0.17)), 
                        'US': dict(zip(groups, np.array([0.1, 0.01, 0.001, 0.5, 0.4])*0.0449))
                        }
# group sizes are different for regional and global emissions
scaling_assumption = 'equal'

for region in ['World', 'CN', 'EU27', 'IN', 'US']:
    # time horizon over which to remove 
    columns_list = [f'{year}-01-01 00:00:00' for year in np.arange(1990,2020)]

    scaling_region_to_global_df = pd.read_csv(SCALING_DIR / f"region_to_global_scaling_coefficients.csv", sep = ';', index_col = 0)
    scaling_within_country_df   = pd.read_csv(SCALING_DIR / "within_countries" / f"{region}_scaling.csv", sep = ',', index_col = 0)

    for group in groups:
        # get total budgets 
        co2_upscaled = baseline_df.loc[baseline_df.variable == 'Emissions|CO2|MAGICC Fossil and Industrial',
                                    columns_list].values.flatten() * scaling_region_to_global_df.loc[:, region].values*scaling_within_country_df.loc[:, group].values * 1/(regionsl_group_sizes[region][group])
        ch4_upscaled = baseline_df.loc[baseline_df.variable == 'Emissions|CH4',
                                        columns_list].values.flatten() * scaling_region_to_global_df.loc[:, region].values*scaling_within_country_df.loc[:, group].values * 1/(regionsl_group_sizes[region][group])
        n2o_upscaled = baseline_df.loc[baseline_df.variable == 'Emissions|N2O',
                                        columns_list].values.flatten() * scaling_region_to_global_df.loc[:, region].values*scaling_within_country_df.loc[:, group].values * 1/(regionsl_group_sizes[region][group])

        tmp_df = baseline_df.copy()
        tmp_df.loc[:, 'scenario'] = f'everyon-like_{region}_{group}'
        tmp_df.loc[tmp_df.variable == 'Emissions|CO2|MAGICC Fossil and Industrial',
                                    columns_list] = co2_upscaled
        tmp_df.loc[tmp_df.variable == 'Emissions|CH4',
                                    columns_list] = ch4_upscaled
        tmp_df.loc[tmp_df.variable == 'Emissions|N2O',
                                    columns_list] = n2o_upscaled

        attribution_emissions_df = pd.concat([attribution_emissions_df, tmp_df], ignore_index=True)

attribution_emissions_df.to_csv(INVERSE_ATTRIBUTION_EMISSIONS)

