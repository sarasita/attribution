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
                                 ATTRIBUTION_EMISSIONS,
                                 ATTRIBUTION_EMISSIONS_SENSITIVITY_LOW,
                                 ATTRIBUTION_EMISSIONS_SENSITIVITY_HI)


#%%
# time horizon over which to remove 
columns_list = [f'{year}-01-01 00:00:00' for year in np.arange(1990,2020)]

def adjust_emissions(baseline_df, region, group, scaling_assumption):
    """
    Adjust emissions for a region based on a scaling assumption."""
    scaling_region_to_global_df = pd.read_csv(SCALING_DIR / f"region_to_global_scaling_coefficients.csv", sep = ';', index_col = 0)
    scaling_within_country_df   = pd.read_csv(SCALING_DIR / "within_countries" / f"{region}_scaling.csv", sep = ',', index_col = 0)

    # get total budgets 
    co2_budget = baseline_df.loc[baseline_df.variable == 'Emissions|CO2|MAGICC Fossil and Industrial',
                                columns_list].copy().values.flatten()
    ch4_budget = 28 * baseline_df.loc[baseline_df.variable == 'Emissions|CH4',
                                    columns_list].copy().values.flatten()
    n2o_budget = 273 * 1/1000 * baseline_df.loc[baseline_df.variable == 'Emissions|N2O',
                                    columns_list].copy().values.flatten()
    co2e_removal = (co2_budget + ch4_budget + n2o_budget) * scaling_region_to_global_df.loc[:, region].values*scaling_within_country_df.loc[:, group].values
    
    # compute removal 
    # initialize return values
    co2_removed = np.zeros(co2_budget.shape)
    ch4_removed = np.zeros(co2_budget.shape)
    n2o_removed = np.zeros(co2_budget.shape)

    if scaling_assumption == 'equal': 
        co2_removed = co2_budget*scaling_region_to_global_df.loc[:, region].values*scaling_within_country_df.loc[:, group].values
        ch4_removed = ch4_budget*scaling_region_to_global_df.loc[:, region].values*scaling_within_country_df.loc[:, group].values/28
        n2o_removed = n2o_budget*scaling_region_to_global_df.loc[:, region].values*scaling_within_country_df.loc[:, group].values/273*1000
    elif scaling_assumption == 'CO2': 
        co2_budget_tmp = co2_budget.copy()
        
        # remove as much co2 as possible
        co2_budget_tmp[co2_budget_tmp > co2e_removal] = co2e_removal[co2_budget_tmp > co2e_removal]
        co2e_removal_left = co2e_removal-co2_budget_tmp    
        co2_removed = co2_budget_tmp 

        # distribute whatever is left equally between ch4 and n20
        ch4_removed = 1/2*co2e_removal_left/28
        n2o_removed = 1/2*co2e_removal_left/273*1000
    elif scaling_assumption == 'CH4':
        # remove ch4
        ch4_budget_tmp = ch4_budget.copy()
        ch4_budget_tmp[ch4_budget_tmp > co2e_removal] = co2e_removal[ch4_budget_tmp > co2e_removal]
        co2e_removal_left = co2e_removal-ch4_budget_tmp
        ch4_removed = ch4_budget_tmp/28
        
        # remove n20 
        n2o_budget_tmp = n2o_budget.copy()
        n2o_budget_tmp[n2o_budget_tmp > co2e_removal_left] = co2e_removal_left[n2o_budget_tmp > co2e_removal_left]
        co2e_removal_left = co2e_removal_left-n2o_budget_tmp
        n2o_removed = n2o_budget_tmp/273*1000
        
        #then co2
        co2_budget_tmp = co2_budget.copy()
        co2_budget_tmp[co2_budget_tmp > co2e_removal_left] = co2e_removal_left[co2_budget_tmp > co2e_removal_left]
        co2e_removal_left = co2e_removal_left-co2_budget_tmp
        co2_removed = co2_budget_tmp
    else: 
        print('scaling assumption not implemented') 

    # print(co2e_removal-(co2_removed+28*ch4_removed+273*1/1000*n2o_removed))

    return(co2_removed, ch4_removed, n2o_removed)

#%%

regions = ['World', 'CN', 'EU27', 'IN', 'US']
groups  = ['p90p100', 'p99p100', 'p999p100']

#%%

output_path_dict = dict(zip(['equal',
                             'CO2',
                             'CH4'
                             ], 
                            [ATTRIBUTION_EMISSIONS,
                             ATTRIBUTION_EMISSIONS_SENSITIVITY_LOW,
                             ATTRIBUTION_EMISSIONS_SENSITIVITY_HI
                             ])
                        )

for scaling_assumption in output_path_dict.keys():
    baseline_df = pd.read_csv(EMISSIONS_BASELINE)
    attribution_emissions_df = baseline_df.copy()
    
    for region in regions:
        for group in groups:
            co2_removed, ch4_removed, n2o_removed = adjust_emissions(baseline_df.copy(), region, group, scaling_assumption)
            tmp_df = baseline_df.copy()
            tmp_df.loc[:, 'scenario'] = f'{region}_{group}_{scaling_assumption}-scaling'
            tmp_df.loc[tmp_df.variable == 'Emissions|CO2|MAGICC Fossil and Industrial',
                                        columns_list] -= co2_removed
            tmp_df.loc[tmp_df.variable == 'Emissions|CH4',
                                        columns_list] -= ch4_removed
            tmp_df.loc[tmp_df.variable == 'Emissions|N2O',
                                        columns_list] -= n2o_removed
        
            attribution_emissions_df = pd.concat([attribution_emissions_df, tmp_df], ignore_index=True).copy()

    attribution_emissions_df.to_csv(output_path_dict[scaling_assumption])

