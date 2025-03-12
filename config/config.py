"""
Configuration shared across notebooks
"""

from __future__ import annotations
from pathlib import Path

# -- GENERAL PATHS 
DATA_DIR = Path(__file__).parent.parent.parent.parent / "05_Data" 
CODE_DIR = Path(__file__).parent.parent
# GENERAL SETTINGS
EU27_ids     = ['AT', 'BE', 'BG', 'CY', 'CZ', 'DE', 'DK', 'EE', 'ES', 'FI', 'FR', 'GR', 'HR', 'HU', 'IE', 'IT', 'LT', 'LU', 'LV', 'MT', 'NL', 'PL', 'PT', 'RO', 'SE', 'SI', 'SK']

# -- CHANCEL DATA 
CHANCEL_DATA_DIR   = DATA_DIR / "Chancel" / "Data"

# -- WID DATA 
WID_DATA_DIR       = DATA_DIR / "WID" / "wid_all_data"
WID_DATA_PROCESSED = DATA_DIR / "WID" / "processed"
WID_ref_year       = 2023
# indicating missing data in the WID dataset 
WID_missing_ptinc = ['AN','AS','BL','BQ','CK','CS','DD','EH','FK','FO','GU','JO','KS','LR','MC','MF','MP','NU','PM','SH','SU','SV','TK','TL','VA','VI','WF','XI','ZZ']
WID_skip_alpha2   = ['XC', 'XE', 'XK', 'YU']

# PRE-PROCESSED DATA
SCALING_DATA_DIR = DATA_DIR / "Scaling"

# ADJUST
MAGICC_OUTPUT_DIR   = Path('/Users/schoens/Documents/PhD/IIASA/04_Code/gitlab/magicc-attribution/data/0001/interim/magicc-output')

MAGICC_OUTPUT_FILES = [
                       MAGICC_OUTPUT_DIR / "magicc-results-attribution-standard.csv",
                       MAGICC_OUTPUT_DIR / "magicc-results-attribution-sensitivity-co2.csv",
                       MAGICC_OUTPUT_DIR / "magicc-results-attribution-sensitivity-ch4.csv",
                       MAGICC_OUTPUT_DIR / "magicc-results-inverse-attribution.csv",
                       MAGICC_OUTPUT_DIR / "magicc-results-attribution-additional.csv",
                       MAGICC_OUTPUT_DIR / "magicc-results-attribution-region-total.csv",
                       ]

PROCESSED_GMT_DIR = Path('/Users/schoens/Documents/PhD/IIASA/05_Data/MAGICC/Processed/')
PROCESSED_GMT_FILE = PROCESSED_GMT_DIR / 'MAGICC-GMT_processed.csv'

# -- FINAL OUTCOMES
GRAPHICS_DIR = DATA_DIR.parent / '06_Graphics'
GRAPHICS_PAPER_MAIN_DIR = DATA_DIR.parent / '06_Graphics' / 'paper' / 'v2' / 'main'
GRAPHICS_PAPER_APPENDIX_DIR = DATA_DIR.parent / '06_Graphics' / 'paper' / 'v2' / 'appendix'
RESULTS_DIR  = DATA_DIR / 'Results'


# -- REGIONS 
regions = ['US', 'EU27', 'IN', 'CN']
region_naming_dict = {'CN': 'China', 
                    'IN': 'India',
                    'EU27': 'EU27',
                    'US': 'US'}
population_shares = [0.0449, 0.0616, 0.170, 0.206]


# -- VISUALIZATION
fontsize_small = 5
fontsize_medium = 6
fontsize_large = 7


group_colors = ['darkgray', 
                [1.        , 0.56862745, 0.40915033, 1.        ], 
                [0.38065359, 0.59686275, 0.59686275, 1.        ],
                [0.80915033, 0.41568627, 0.63137255, 1.        ]]

uncertainty_color = 'black'
sensitvitiy_color = 'saddlebrown'
symbols = ["o", 's', '*', 'D']


