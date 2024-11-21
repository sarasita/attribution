"""
Configuration shared across notebooks
"""

from __future__ import annotations

from pathlib import Path

RUN_ID = "0001"

"""
ID for this run.

The paths are set up so that, if you increment the run ID,
basically everything has to be done from scratch.
This might not be the behaviour you want exactly,
but it will at least show you a pattern
for doing multiple runs with different configuration,
which you can then tweak.
"""

DATA_DIR = Path(__file__).parent.parent / "data" / RUN_ID

RCMIP_EMISSIONS_FNAME = "rcmip-emissions-annual-means-v5-1-0.csv"
RCMIP_EMISSIONS_RAW_DIR = DATA_DIR / "raw" / "rcmip"
RCMIP_EMISSIONS_URL = "https://rcmip-protocols-au.s3-ap-southeast-2.amazonaws.com/v5.1.0/rcmip-emissions-annual-means-v5-1-0.csv"
RCMIP_EMISSIONS_FILE_HASH = (
    "2af9f90c42f9baa813199a902cdd83513fff157a0f96e1d1e6c48b58ffb8b0c1"
)

RCMIP_SCENARIO_EMISSIONS_CLEAN = (
    DATA_DIR
    / "interim"
    / "rcmip"
    / "clean_scenario_rcmip-emissions-annual-means-v5-1-0.csv"
)

ATTRIBUTION_EMISSIONS_CLEAN = (
    DATA_DIR / "interim" / "attribution-emissions" / "clean_emissions-attribution.csv"
)

# @Carl, there will probably be some mucking around here for you too
# deciding which baselines you care about.
BASELINE_SCENARIOS = [
    "ssp119",
    "ssp245",
    "ssp585",
]

SEL_BASELINE = "ssp245"

BASELINE_ATTRIBUTION_SCENARIO_SEPARATOR = "___"

EMISSIONS_BASELINE     = DATA_DIR / "interim" / "attribution-emissions" / "emissions-baseline.csv"
ATTRIBUTION_EMISSIONS  = DATA_DIR / "interim" /  "emissions-to-run" / "attribution-emissions.csv"
ATTRIBUTION_EMISSIONS_SENSITIVITY_LOW  = DATA_DIR / "interim" /  "emissions-to-run" / "attribution-emissions_sensitivity-low.csv"
ATTRIBUTION_EMISSIONS_SENSITIVITY_HI  = DATA_DIR / "interim" /  "emissions-to-run" / "attribution-emissions_sensitivity-high.csv"
ATTRIBUTION_EMISSIONS_ADDITIONAL  = DATA_DIR / "interim" /  "emissions-to-run" / "attribution-emissions_additional.csv"
ATTRIBUTION_EMISSIONS_REGION  = DATA_DIR / "interim" /  "emissions-to-run" / "attribution-emissions_region-total.csv"

INVERSE_ATTRIBUTION_EMISSIONS = DATA_DIR / "interim" /  "emissions-to-run" / "inverse-attribution-emissions.csv"

SCALING_DIR =  Path("/Users/schoens/Documents/PhD/IIASA/05_Data/Scaling")

EMISSIONS_TO_RUN_FILES = [
    ATTRIBUTION_EMISSIONS,
    ATTRIBUTION_EMISSIONS_SENSITIVITY_LOW ,
    ATTRIBUTION_EMISSIONS_SENSITIVITY_HI,
    INVERSE_ATTRIBUTION_EMISSIONS, 
    ATTRIBUTION_EMISSIONS_ADDITIONAL,
    ATTRIBUTION_EMISSIONS_REGION
]

MAGICC_RESULT_FILES = [
    DATA_DIR / "interim" / "magicc-output" / "magicc-results-attribution-standard.csv",
    DATA_DIR / "interim" / "magicc-output" / "magicc-results-attribution-sensitivity-co2.csv",
    DATA_DIR / "interim" / "magicc-output" / "magicc-results-attribution-sensitivity-ch4.csv",
    DATA_DIR / "interim" / "magicc-output" / "magicc-results-inverse-attribution.csv",
    DATA_DIR / "interim" / "magicc-output" / "magicc-results-attribution-additional.csv",
    DATA_DIR / "interim" / "magicc-output" / "magicc-results-attribution-region-total.csv",
]
