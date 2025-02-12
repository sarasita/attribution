
from pathlib import Path
import sys
import os 
sys.path.append(os.getcwd())

from Input.utils.WID_functions import (convert_all_to_ppp_euros,
                                 income_based_country_shares_to_aggregated_regions, 
                                 income_based_regional_shares_to_aggregated_regions,
                                 population_estimates, 
                                 generate_income_classification_df)

if __name__ == '__main__':
    ### Data for functionality:
    print('Converting WID country data to PPP Euros')
    convert_all_to_ppp_euros()
    print('Done!')
    
    print('Computing income-based country shares to World region for the wealthiest 10% and 1% for 1990,2000,2019 and 2019')
    income_based_country_shares_to_aggregated_regions(groups = ['p90p100', 'p99p100', 'p99.9p100'], 
                                                      years = [1990, 2000, 2010, 2019], 
                                                      region_ids = ['WO'])
    print('Done!')
    print('Generating a .csv with population stimates by country')
    population_estimates()
    print('Done!')
    
    ### Data for graphics: 
    print('Computing income-based regional shares to aggregated regions for the globally  wealthiest 10% and 1% for 1990,2000,2010,2019')
    income_based_regional_shares_to_aggregated_regions(groups = ['p90p100', 'p99p100', 'p99.9p100'], 
                                                       years = [1990, 2000, 2010, 2019], 
                                                       sel_regions = ['USA', 'EU27', 'IND', 'CHN', 'JPN', 'GBR', 'CAN', 'BRA'],
                                                       WID_region_id = 'WO')
    print('Done!')
    
    print('Classifying country income reative to global income distirbution')
    generate_income_classification_df(['p90p100', 'p99p100', 'p99.9p100'])
    print('Done!')

