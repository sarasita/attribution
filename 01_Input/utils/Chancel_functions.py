
from pathlib import Path
import os
import sys
sys.path.append(os.path.abspath(''))

import pandas as pd 
import numpy as np
import pycountry

from config.config import (WID_DATA_PROCESSED, 
                    SCALING_DATA_DIR,
                    CHANCEL_DATA_DIR,
                    EU27_ids) 

from tqdm import tqdm


def average_pcapt_emissions_by_country(file = CHANCEL_DATA_DIR / 'carbon-export-raw-scenarios-1-a.dta'):
    ''' 
    Aggregate original chancel data to country level (i.e. p0p100 emissions)
    '''
    chancel_df  = pd.read_stata(file)
    
    # chancel data states emissions for each percentiles 
    # extract all percentile steps and sum them together with weights 
    # representing the number of people between two percentiles
    p_steps = np.append(np.sort(np.unique(chancel_df.p)), 1)
    intervals = p_steps[1:]-p_steps[:-1]
    interval_dict = dict(zip(p_steps[:-1], intervals)) 
    chancel_df['weight'] = chancel_df['p'].map(interval_dict)
    
    # aggregate to average per capita emissions on country level 
    average_country_df = chancel_df.loc[:, ['iso', 'year']].copy()
    average_country_df = average_country_df[average_country_df.year.isin(np.arange(1990,2020))]
    average_country_df['average_pcapt'] = chancel_df['lpfghgmulti10']*chancel_df['weight']
    average_country_df = average_country_df.groupby(['iso', 'year']).sum().reset_index()
    
    return(average_country_df)

def average_total_emissions_by_country(file_emissions = CHANCEL_DATA_DIR / 'carbon-export-raw-scenarios-1-a.dta',
                                       file_population = WID_DATA_PROCESSED / 'population' / 'global_population.csv'):
    
    average_country_df = average_pcapt_emissions_by_country(file = file_emissions)
    global_population_df = pd.read_csv(file_population, sep = ';', index_col = 0)

    country_codes = [idx for idx in average_country_df.iso.unique() if idx in global_population_df.columns]

    global_population_df = global_population_df.loc[:, country_codes].copy()
    average_country_df = average_country_df[average_country_df.iso.isin(country_codes)].copy()
    
    average_country_df['total_co2e_emissions_all'] = average_country_df.apply(lambda row: row['average_pcapt'] * global_population_df.loc[row['year'], row['iso']], axis=1)
    average_country_df['world_total_co2e'] = average_country_df.groupby('year')['total_co2e_emissions_all'].transform('sum')
    average_country_df['world_rel_share'] = average_country_df['total_co2e_emissions_all']/average_country_df['world_total_co2e']
    return(average_country_df)

def country_to_global_coefficients(file_emissions = CHANCEL_DATA_DIR / 'carbon-export-raw-scenarios-1-a.dta', 
                                   file_population = WID_DATA_PROCESSED / 'population' / 'global_population.csv'):
    
    average_country_df = average_total_emissions_by_country(file_emissions = file_emissions, file_population = file_population)
    
    coefficient_df = pd.DataFrame(index = np.arange(1990,2020), columns = average_country_df.iso.unique())

    for iso in coefficient_df.columns: 
        if iso == 'ET': 
            val_1994 = average_country_df.loc[average_country_df.iso == iso, 'world_rel_share'].values[0]
            new_vals = np.array([val_1994]*4 + list(average_country_df.loc[average_country_df.iso == iso, 'world_rel_share'].values))
            coefficient_df.loc[:, iso] = new_vals
        else: 
            coefficient_df.loc[:, iso] = average_country_df.loc[average_country_df.iso == iso, 'world_rel_share'].values 

    Path(SCALING_DATA_DIR).mkdir(parents=True, exist_ok=True)
    coefficient_df.to_csv(SCALING_DATA_DIR / 'country_to_global_scaling_coefficients.csv', sep = ';')
    
    return()

def region_to_global_coefficients(file_country_coeffs = SCALING_DATA_DIR / 'country_to_global_scaling_coefficients.csv', region_ids = EU27_ids, country_ids = ['CN', 'IN', 'US']):
    country_coefficient_df = pd.read_csv(file_country_coeffs, sep = ';', index_col = 0)
    regional_coefficients = country_coefficient_df.loc[:, country_ids].copy()
    regional_coefficients.loc[:, 'EU27'] = country_coefficient_df.loc[:, EU27_ids].sum(axis = 1)
    regional_coefficients.loc[:, 'World'] = 1
    
    Path(SCALING_DATA_DIR).mkdir(parents=True, exist_ok=True)
    regional_coefficients.to_csv(SCALING_DATA_DIR / 'region_to_global_scaling_coefficients.csv', sep = ';')
    return()

def within_country_scaling(file_emissions = CHANCEL_DATA_DIR / 'carbon-export-raw-scenarios-1-a.dta'):
    # data for individual groups in country
    chancel_df = pd.read_stata(file_emissions)
    p_steps = np.append(np.sort(np.unique(chancel_df.p)), 1)
    intervals = p_steps[1:]-p_steps[:-1]
    interval_dict = dict(zip(p_steps[:-1], intervals)) 
    chancel_df['weight'] = chancel_df['p'].map(interval_dict)
    chancel_df = chancel_df[chancel_df.year.isin(np.arange(1990,2020))]
    
    # total data for country
    average_country_df = average_pcapt_emissions_by_country(file = file_emissions)
    
    Path(SCALING_DATA_DIR / 'within_countries').mkdir(parents = True, exist_ok = True)

    groups = ['p0p50', 'p50p90', 'p90p100', 'p90p95', 'p95p99', 'p99p100', 'p999p100', 'p9999p100', 'p95p100', 'p80p100', 'p70p100', 'p60p100', 'p50p100', 'p10p100', 'p0p100']
    bounds = [(0,0.5), (0.5,0.9), (0.9,0.99999), (0.9,0.95), (0.95,0.99), (0.99,0.99999), (0.999,0.99999), (0.9999,0.99999), (0.95,0.99999), (0.8,0.99999), (0.7,0.99999), (0.6,0.99999), (0.5, 0.99999), (0.1, 0.99999), (0, 0.99999)]

    output_df = pd.DataFrame(index = np.arange(1990,2020), columns = ['year', 'iso'] + groups)
    output_df.loc[:, 'year']    = np.arange(1990,2020)

    for iso in ['CN', 'IN', 'US']:
        output_df.loc[:, 'iso'] = iso
        for i in range(len(groups)):
            # partially aggregate by group & devide by total emissions
            bounds_tmp = bounds[i]
            group_tmp  = groups[i] 
            sub_df                     = chancel_df[chancel_df.iso == iso]
            pgroup_df                  = sub_df[(sub_df.p >= bounds_tmp[0]) & (sub_df.p < bounds_tmp[1])].copy()
            pgroup_df['average_pcapt'] = pgroup_df['lpfghgmulti10']*pgroup_df['weight']
            pgroup_df                  = pgroup_df.groupby(['iso', 'year']).sum().reset_index().loc[:, ['iso', 'year', 'average_pcapt']]
            pgroup_df['average_pcapt'] = pgroup_df['average_pcapt'].values/average_country_df[average_country_df.iso == iso]['average_pcapt'].values
            output_df.loc[:, group_tmp] = pgroup_df['average_pcapt'].values
        output_df.to_csv(SCALING_DATA_DIR / 'within_countries' / f'{iso}_scaling.csv', index = False)
    return()

def eu27_scaling(file_emissions = CHANCEL_DATA_DIR / 'carbon-export-raw-scenarios-1-a.dta'):
    tmp_df        = pd.read_stata(file_emissions)
    tmp_df        = tmp_df[tmp_df.year.isin(np.arange(1990,2020))].copy()
    p_steps       = np.append(np.sort(np.unique(tmp_df.p)), 1)
    intervals     = p_steps[1:]-p_steps[:-1]
    interval_dict = dict(zip(p_steps[:-1], intervals)) 
    tmp_df['weight'] = tmp_df['p'].map(interval_dict)
    
    ps        = tmp_df.p.unique()
    eu27_df   = pd.DataFrame(columns = ['iso', 'year', 'p', 'popgroup', 'lpfghgmulti10'],
                            index = np.arange(len(np.arange(1990,2019))*len(ps))
                            )

    EU27_ids  = ['AT', 'BE', 'BG', 'CY', 'CZ', 'DE', 'DK', 'EE', 'ES', 'FI', 'FR', 'GR', 'HR', 'HU', 'IE', 'IT', 'LT', 'LU', 'LV', 'MT', 'NL', 'PL', 'PT', 'RO', 'SE', 'SI', 'SK']

    i = 0
    for year in np.arange(1990,2020):
        for p in ps: 
            sub_df    = tmp_df[tmp_df.iso.isin(EU27_ids) & (tmp_df.year == year)].sort_values('lpfghgmulti10')
            sub_df['cumulative_pop'] = sub_df['popgroup'].cumsum()
            
            total_pop = sub_df.loc[:, 'popgroup'].sum()

            # Assuming your dataframe is named df
            # Sort the dataframe by emissions value (lpfghgmulti10) in ascending order
            df_sorted = sub_df.sort_values(by='lpfghgmulti10').reset_index(drop=True)

            # Calculate cumulative population at the EU level
            df_sorted['cumulative_pop'] = df_sorted['popgroup'].cumsum()

            # Total population in the dataset (i.e., EU level)
            total_population = sub_df['popgroup'].sum()
            
            # Function to calculate emissions between two percentiles at the EU level
            def calculate_emissions_between_percentiles(df, lower_percentile, upper_percentile):
                # Target populations for the lower and upper percentiles
                lower_population = total_population * lower_percentile
                upper_population = total_population * upper_percentile

                # Handle the case where no entry satisfies both bounds
                if lower_population == upper_population:
                    nearest_row = df.iloc[(df['cumulative_pop'] - lower_population).abs().argsort()[:1]]
                    total_emissions = nearest_row['lpfghgmulti10'].values[0]
                    return total_emissions, total_emissions

                # Filter the data to include entries that fall within the percentile range
                df_between = df[(df['cumulative_pop'] > lower_population) & (df['cumulative_pop'] <= upper_population)]

                # Handle the case where no entry simultaneously satisfies both the lower and upper bounds
                if df_between.empty:
                    nearest_lower_row = df.iloc[(df['cumulative_pop'] - lower_population).abs().argsort()[:1]]
                    nearest_upper_row = df.iloc[(df['cumulative_pop'] - upper_population).abs().argsort()[:1]]
                    
                    lower_fraction = (nearest_lower_row['cumulative_pop'].values[0] - lower_population) / nearest_lower_row['popgroup'].values[0]
                    upper_fraction = (upper_population - nearest_upper_row['cumulative_pop'].values[0]) / nearest_upper_row['popgroup'].values[0]

                    total_emissions = (
                        lower_fraction * nearest_lower_row['lpfghgmulti10'].values[0] +
                        upper_fraction * nearest_upper_row['lpfghgmulti10'].values[0]
                    )
                    population_between = upper_population - lower_population
                    average_emissions = total_emissions / population_between
                    return total_emissions, average_emissions

                # Handle the portion of the first entry in the range
                if df_sorted['cumulative_pop'].iloc[df_between.index[0] - 1] < lower_population:
                    first_row = df_sorted.iloc[df_between.index[0] - 1]
                    remaining_lower_population = first_row['cumulative_pop'] - lower_population
                    df_between = pd.concat([pd.DataFrame({
                        'popgroup': [remaining_lower_population],
                        'lpfghgmulti10': [first_row['lpfghgmulti10']]
                    }), df_between])

                # Check if upper_percentile == 1 to avoid index out of bounds
                if upper_percentile < 1.0:
                    # Handle the portion of the last entry in the range
                    if df_between['cumulative_pop'].iloc[-1] < upper_population:
                        last_row = df_sorted.iloc[df_between.index[-1] + 1]
                        remaining_upper_population = upper_population - df_between['cumulative_pop'].iloc[-1]
                        df_between = pd.concat([df_between, pd.DataFrame({
                            'popgroup': [remaining_upper_population],
                            'lpfghgmulti10': [last_row['lpfghgmulti10']]
                        })])

                # Calculate the total emissions for the entries between the bounds
                total_emissions = (df_between['popgroup'] * df_between['lpfghgmulti10']).sum()

                # Calculate the population between the two percentiles
                population_between = upper_population - lower_population

                # Calculate the average emissions for the range
                average_emissions = total_emissions / population_between

                return total_emissions, average_emissions

            # Calculate the total emissions for the lowest 50% of the EU population
            total_emissions_p, average_emissions_p = calculate_emissions_between_percentiles(df_sorted, p, p+interval_dict[p])

            # # Calculate the average emissions for the lowest 50%
            eu27_df.loc[i, :] = ['EU27', year, p, total_population * (p+interval_dict[p]), average_emissions_p]
            i += 1
            
    Path(SCALING_DATA_DIR / 'within_countries').mkdir(parents = True, exist_ok = True)
    eu27_df.to_csv(SCALING_DATA_DIR / 'within_countries' / f'eu27_scaling_tmp.csv', index = False)
    return()


def world_scaling(file_emissions = CHANCEL_DATA_DIR / 'regions_scenario_carbon_temp2-tab-a.dta'):
    aggregate_df   = pd.read_stata(file_emissions).loc[:, ['year', 'iso', 'p', 'amulti10']]
    world_df       = aggregate_df[(aggregate_df.iso == 'World') & (aggregate_df.p.isin(['p0p50', 'p50p90', 'p90p100', 'p90p95', 'p95p99', 'p99p100', 'p99.9p100', 'p99.99p100', 'p0p100', 'p95p100', 'p80p100', 'p70p100', 'p60p100', 'p50p100', 'p10p100']))].copy()
    world_average  = aggregate_df[(aggregate_df.p == 'p0p100') & (aggregate_df.iso == 'World')]
    total          = aggregate_df[(aggregate_df.p == 'p0p100') & (aggregate_df.iso == 'World')]

    # step 1: World region 
    conv_factors = dict(zip(['p0p50', 'p50p90', 'p90p100', 'p90p95', 'p95p99', 'p99p100', 'p99.9p100', 'p99.99p100', 'p95p100', 'p80p100', 'p70p100', 'p60p100', 'p50p100', 'p10p100', 'p0p100'], 
                            [0.5, 0.4, 0.1, 0.05, 0.04, 0.01, 0.001, 0.0001, 0.05, 0.2, 0.3, 0.4, 0.5, 0.9, 1]))
    group_names  =  dict(zip(['p0p50', 'p50p90', 'p90p100', 'p90p95', 'p95p99', 'p99p100', 'p99.9p100', 'p99.99p100', 'p95p100', 'p80p100', 'p70p100', 'p60p100', 'p50p100', 'p10p100', 'p0p100'], 
                            ['p0p50', 'p50p90', 'p90p100', 'p90p95', 'p95p99', 'p99p100', 'p999p100', 'p9999p100', 'p95p100', 'p80p100', 'p70p100', 'p60p100', 'p50p100', 'p10p100', 'p0p100']))

    result_df    = pd.DataFrame(index = np.arange(1990,2020), columns = ['year', 'iso'] + list(group_names.values()))
    result_df.loc[:, 'year'] = np.arange(1990,2020)
    result_df.loc[:, 'iso'] = 'World'
    for p in ['p0p50', 'p50p90', 'p90p100', 'p90p95', 'p95p99', 'p99p100', 'p99.9p100', 'p99.99p100', 'p95p100', 'p80p100', 'p70p100', 'p60p100', 'p50p100', 'p10p100', 'p0p100']: 
        conv_factor = conv_factors[p]
        
        if (p == 'p90p95'):
            aggregate_sub_df = aggregate_df[(aggregate_df.p == 'p0p50') & (aggregate_df.iso == 'World')].copy()
            aggregate_sub_df['p'] = 'p90p95'
            aggregate_sub_df.loc[:, 'amulti10'] = aggregate_df[aggregate_df.p.isin(['p90p91', 'p91p92', 'p92p93', 'p93p94', 'p94p95']) & (aggregate_df.iso == 'World')].loc[:, ['year', 'amulti10']].groupby('year').mean()['amulti10'].values
        elif (p == 'p95p99'):
            aggregate_sub_df = aggregate_df[(aggregate_df.p == 'p0p50') & (aggregate_df.iso == 'World')].copy()
            aggregate_sub_df['p'] = 'p95p99'
            aggregate_sub_df.loc[:, 'amulti10'] = aggregate_df[aggregate_df.p.isin(['p95p96', 'p96p97', 'p97p98', 'p98p99']) & (aggregate_df.iso == 'World')].loc[:, ['year', 'amulti10']].groupby('year').mean()['amulti10'].values
        else:     
            aggregate_sub_df = aggregate_df[(aggregate_df.p == p) & (aggregate_df.iso == 'World')]
            aggregate_sub_df.index = aggregate_sub_df.year
        
        percentage_df    = (aggregate_sub_df['amulti10'].values*conv_factor) / (total['amulti10'].values)
        # print(percentage_df)
        # get in correct format: 
        result_df.loc[:, group_names[p]] = percentage_df

    result_df.to_csv(SCALING_DATA_DIR / 'within_countries' / 'World_scaling.csv', index = False)
    return()