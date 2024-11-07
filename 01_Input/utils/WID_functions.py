
from pathlib import Path
import os
import sys
sys.path.append(os.path.abspath(''))

import pandas as pd 
import numpy as np
import pycountry

from config.config import (WID_DATA_DIR, 
                    WID_DATA_PROCESSED, 
                    WID_ref_year, 
                    WID_missing_ptinc,
                    WID_skip_alpha2,
                    EU27_ids) 

from tqdm import tqdm


def convert_all_to_ppp_euros():
    '''
    Wrapper for converting WID data for each country into PPP Euros using the conversion rates provided by WID.world.
    '''
    
    Path(WID_DATA_PROCESSED / 'country').mkdir(parents=True, exist_ok=True)
    wid_countries = pd.read_csv(WID_DATA_DIR / 'WID_countries.csv', sep = ';', index_col = 0).dropna().astype(str)
    wid_alpha2    = wid_countries.index.unique()
    
    countries_with_missing_data =  []
    for alpha in tqdm(wid_alpha2, total = len(wid_alpha2)):
        try:
            country_conversion_to_ppp_euros(alpha)
        except:
            countries_with_missing_data.append(alpha)
    
    if len(countries_with_missing_data) > 0:
        print(f'The following countries have missing data: {countries_with_missing_data}')
        
    return()

def country_conversion_to_ppp_euros(alpha2, input_dir = WID_DATA_DIR, output_dir = WID_DATA_PROCESSED):
    '''
    All prices on WID.world are expressed in local currency relative to 2023. We convert 
    local 2023 currency into PPP Euros using the PPP rates provided by WID.world and 
    store the results in the processed directory 
    
    Args: 
        alpha2 (str): country code in ISO 3166-1 alpha-2 format
        input_dir (Path): directory where the raw WID data is stored
        output_dir (Path): directory where the processed data will be stored. Make sure that this directory exists prior to calling this function
    
    '''
    country_df = pd.read_csv(input_dir / f'WID_data_{alpha2}.csv', sep = ';')
    # convert into 2023 PPP Euros 
    # price index is already relative to 2023 --> convert local currency into EUR using PPP rates: 
    conversion_factor = country_df[country_df.variable.str.contains('xlceupi999') & (country_df.year == WID_ref_year)].value.values
    # Keeping WID world income variables: ptinc (pre-tax income)
    country_df.loc[(country_df.variable.str.contains('tptinc')) | (country_df.variable.str.contains('aptinc'))| (country_df.variable.str.contains('mptinc')), 'value'] /= conversion_factor
    # store: 
    country_df.to_csv(output_dir / 'country' / f'WID_data_{alpha2}.csv', sep = ';', index = False)
    return()

def income_based_country_shares_to_aggregated_regions(groups, years, region_ids = ['WO']):
    '''
    Compute the contributions of individual countries to the wealthiest X% in a the specified regions
    and save as dataframe 
    
    Args:
        groups (list): List of income group ranges, e.g. 'p90p100' for top 10%, 'p99p100' for top 1%, p50p90 for middle 40%
        years (list): List of years to consider
        region_ids (list): List of region ids to consider. Default is 'WO' for world. See WID.world for available regions
    '''
    wid_countries = pd.read_csv(WID_DATA_DIR / 'WID_countries.csv', sep = ';', index_col = 0).dropna()
    
    for year in years: 
        for group in groups:
            wid_countries = pd.read_csv(WID_DATA_DIR / 'WID_countries.csv', sep = ';', index_col = 0).dropna()
            
            for region_id in region_ids: 
                if region_id == 'WO':
                    wid_alpha2    = wid_countries.index.unique()
                else: 
                    wid_alpha2    = wid_countries[wid_countries.region2 == region_id].index.unique()

                # the WID data is a bit messy --> only consider complete data 
                wid_alpha2    = [f for f in wid_alpha2 if (f != 'nan') & (~pd.isna(f)) & (f not in WID_skip_alpha2) & (f not in WID_missing_ptinc)]

                # regional aggregates are already in PPP Euros 
                region_df  = pd.read_csv(WID_DATA_DIR / f'WID_data_{region_id}.csv', sep = ';')
                
                # get threshold for wealthiest group, i.e. the minimum amount of money you need to have in order 
                # to still be considere among the wealthiest X% of the population
                threshold  = region_df[(region_df.variable.str.contains('tptinc')) & (region_df.percentile.str.contains(group)) & (region_df.year == year)].value.values[0]
                
                results_df = pd.DataFrame(index = wid_alpha2, columns = ['population_all', 'population_adults', 'fraction_of_population_in_group', 'population_in_group', 'adult_population_in_group'])
                
                countries_fail = []
                for alpha in wid_alpha2[:]: 
                    try: 
                        country_df = pd.read_csv(WID_DATA_PROCESSED / 'country' / f'WID_data_{alpha}.csv', sep = ';')
                        population       = country_df[(country_df.variable.str.contains('npopuli999')) & (country_df.year == year)].value.values[0]
                        adult_population = country_df[(country_df.variable.str.contains('npopuli992')) & (country_df.year == year)].value.values[0]
                        tmp_df      = country_df[(country_df.variable.str.contains('tptincj992')) & (country_df.year == year)]
                        percentiles = tmp_df[tmp_df.value >= threshold].percentile
                        fractions   = np.array([float(f.split('p')[1]) for f in percentiles])
                        f          = (100-np.min(fractions))/100
                        results_df.loc[alpha, :] = [population, adult_population, f, np.ceil(f*population), np.ceil(f*adult_population)]
                    except: 
                        countries_fail.append(alpha)   
                Path(WID_DATA_PROCESSED / 'wealthy_by_location').mkdir(parents=True, exist_ok=True)
                results_df.to_csv(WID_DATA_PROCESSED / 'wealthy_by_location' / f'WID_data_{region_id}_{group}_{year}.csv', sep = ';') 
    return()


def income_based_regional_shares_to_aggregated_regions(groups, years, sel_regions, WID_region_id = 'WO'):
    '''
    Compute the contributions of selected regions to the wealthiest X% in the specified regions
    '''
    bar_graph_data = pd.DataFrame(index = years, 
                                  columns = sel_regions)

    for group in groups: 
        for year in years: 
            country_shares_df = pd.read_csv(WID_DATA_PROCESSED / 'wealthy_by_location' / f'WID_data_{WID_region_id}_{group}_{year}.csv', sep = ';', index_col = 0) 

            eu27_totals = country_shares_df.loc[EU27_ids, :].sum(axis = 0)
            eu27_totals['fraction_of_population_in_group'] = eu27_totals['population_in_group']/eu27_totals['population_all']

            # replace EU27 country shares with a single EU27 estimate 
            country_shares_df = country_shares_df[~country_shares_df.index.isin(EU27_ids)]
            country_shares_df.loc['EU27',:] = eu27_totals

            isoa3 = dict(zip([f.alpha_2 for f in pycountry.countries], 
                            [f.alpha_3 for f in pycountry.countries]))
            isoa3['EU27'] = 'EU27'

            country_shares_df.loc[:, 'iso_a3']   = [isoa3[f] for f in country_shares_df.index]
            country_shares_df.loc[:, 'alpha_a2'] = country_shares_df.index
            country_shares_df.index = country_shares_df.iso_a3
            
            bar_graph_data.loc[year, sel_regions] = country_shares_df.loc[sel_regions, 'population_in_group']/country_shares_df.loc[:, 'population_in_group'].sum()*100

        bar_graph_data.rename(columns = {EU27_ids[0]: 'EU27'}, inplace = True)
        bar_graph_data.to_csv(WID_DATA_PROCESSED / 'wealthy_by_location' / f'WID_{WID_region_id}_{group}_data_bar_graph.csv', sep = ';')
    
    return()

def population_estimates():
    '''
    Generating .csv with population estimates by country 
    '''
    years = np.arange(1990,2020)
    # total population estimate for world region (is off by 1% bc of aggregation mathod, otherwise fine)
    wid_alpha2    = [f.split('_')[2][:2] for f in os.listdir(WID_DATA_PROCESSED / 'country') if f.endswith('.csv')]

    global_population_df       = pd.DataFrame(index = years, 
                                              columns = wid_alpha2)
    global_adult_population_df = pd.DataFrame(index = years, 
                                              columns = wid_alpha2)

    countries_with_missing_data =  []
    for alpha in tqdm(wid_alpha2, total = len(wid_alpha2)): 
        try: 
            country_df = pd.read_csv(WID_DATA_PROCESSED / 'country' / f'WID_data_{alpha}.csv', sep = ';')
            population       = country_df[(country_df.variable.str.contains('npopuli999')) & (country_df.year.isin(years))].sort_values('year').value.values
            adult_population = country_df[(country_df.variable.str.contains('npopuli992')) & (country_df.year.isin(years))].sort_values('year').value.values
            global_population_df.loc[years, alpha] = population
            global_adult_population_df.loc[years, alpha] = adult_population
        except:
            countries_with_missing_data.append(alpha)

    # store: 
    Path(WID_DATA_PROCESSED / 'population').mkdir(parents = True, exist_ok = True)
    global_population_df.to_csv(WID_DATA_PROCESSED / 'population' / 'global_population.csv', sep = ';')
    global_adult_population_df.to_csv(WID_DATA_PROCESSED / 'population' / 'global_adult_population.csv', sep = ';')
    
    print(f'The following countries have missing data: {countries_with_missing_data}')
    print('Global population in 2019 was evaluated to be: ', global_population_df.loc[2019].sum(), ' it is therefore off by: ', np.round((global_population_df.loc[2019].sum()/7811293698-1)*100,2), '%')
    return()

def finding_lower_bound(region_tptinc_df, thrshld):
    '''
    Given a dataframe containing global income values by income groups (e.g. top 10 i.e. p90p100),
    find the lowest income group that has an income above the defined threshold 
    
    Args: 
        region_tptinc_df: DataFrame, containing income values by income groups for a specific region
        thrshld: float, threshold value for income
    
    Returns:
        float, the lowest income percentile that has an income above the threshold
    '''
    
    percentiles = region_tptinc_df[region_tptinc_df.value > thrshld].percentile.values
    lower_bound = [float(f.split('p')[1]) for f in percentiles]
    return(np.min(lower_bound))

def classify_countryincome_relative_to_global(alpha2, group):
    '''
    For a given country and income group, 
    find the percentage of the global population that has an income above this group
    for each year between 1990 and 2019 individually 
    '''
    global_df  = pd.read_csv(WID_DATA_DIR / f'WID_data_WO.csv', sep = ';')
    country_df = pd.read_csv(WID_DATA_PROCESSED / 'country' / f'WID_data_{alpha2}.csv', sep = ';', index_col = 0)
    
    global_groups = []
    for year in np.arange(1990,2020,1): 
        tmp_df = global_df[(global_df.variable == 'tptincj992') & (global_df.year == year)]
        thrshld = country_df[(country_df.variable == 'tptincj992') & (country_df.year == year) & (country_df.percentile == group)].value.values[0]
        global_groups.append(100-finding_lower_bound(tmp_df, thrshld))
        
    return(global_groups)

def generate_income_classification_df(groups):
    for group in groups: 
        country_threshold_df = pd.DataFrame(index = np.arange(1990,2020,1), columns = ['US', 'IN', 'CN'] + EU27_ids)
        for alpha2 in country_threshold_df .columns: 
            country_threshold_df[alpha2] = classify_countryincome_relative_to_global(alpha2, group)
        
        Path(WID_DATA_PROCESSED / 'income_classification').mkdir(parents=True, exist_ok=True)
        country_threshold_df.to_csv(WID_DATA_PROCESSED / 'income_classification' / f'WID_classified_income_{group}.csv', sep = ';')
    return()




