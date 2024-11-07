from utils.Chancel_functions import (country_to_global_coefficients, 
                                     region_to_global_coefficients,
                                     within_country_scaling,
                                     eu27_scaling,
                                     world_scaling)

if __name__ == '__main__':
    ### Data for functionality:
    print('Generating coeffcients that indicate which fraction of global emissions are attributable to a specific country')
    country_to_global_coefficients()
    print('Done!')
    print('Generating coeffcients that indicate which fraction of global emissions are attributable to a specific region')
    region_to_global_coefficients()
    print('Done!')    
    print('Generating scaling factors for within-country emissions')
    within_country_scaling()
    print('Done!')
    print('Generating scaling factors for EU emissions')
    eu27_scaling()
    print('Done!')
    print('Generating scaling factors for global emissions')
    world_scaling()
    print('Done!')

