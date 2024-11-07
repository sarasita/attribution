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
# # Run MAGICC
#
# Before you can run this notebook, you will need to download both MAGICC and the probabilistic file from https://magicc.org/download/magicc7.
#
# You can save these wherever you wish.
#
# Then, you need to copy the `.env.sample` file in the root of the repository to a file called `.env` (i.e., go to the root of the repository, then do `cp .env.sample .env`).
#
# Edit the `.env` file so that the paths to the MAGICC executable, where to create the workers etc. reflect your specific setup.

# %%

import json
import os
import warnings

import dotenv
import logging
import matplotlib.pyplot as plt
import openscm_runner.run
import scmdata
import seaborn as sns
import tqdm.autonotebook as tqdman
from openscm_runner.adapters import MAGICC7

from notebooks_v2.config import EMISSIONS_TO_RUN_FILES, MAGICC_RESULT_FILES

#%%

if __name__ == '__main__':
    for EMISSIONS_TO_RUN, MAGICC_RESULTS_FILE in zip(EMISSIONS_TO_RUN_FILES[3:4], MAGICC_RESULT_FILES[3:4]):
        
        def main():
            # SCENARIO_BATCH_SIZE = 40
            # N_CFGS_TO_RUN = 5
            
            # The full config, will take a bit more time to run
            SCENARIO_BATCH_SIZE = 8
            N_CFGS_TO_RUN = 600
            
            # # %%

            MAGICC7.get_version()

            input_emissions = scmdata.ScmRun(EMISSIONS_TO_RUN)
            input_emissions

            with open(os.environ["MAGICC_CONFIG_FILE"]) as fh:
                cfgs_raw = json.load(fh)

            base_cfgs = [
                {
                    "run_id": c["paraset_id"],
                    **{k.lower(): v for k, v in c["nml_allcfgs"].items()},
                }
                for c in cfgs_raw["configurations"]
            ]

            # Figuring out what set of flags and how to set them to make MAGICC behave perfectly is a deep rabbit hole. I suspect that is more than we need/want for most applications.

            startyear = 1750
            common_cfg = {
                "startyear": startyear,
                "endyear": 2300,
                "co2_switchfromconc2emis_year": startyear,
                "ch4_switchfromconc2emis_year": startyear,
                "n2o_switchfromconc2emis_year": startyear,
                "fgas_switchfromconc2emis_year": startyear,
                "mhalo_switchfromconc2emis_year": startyear,
                "ch4_incl_ch4ox": 1,
                "ch4_lastbudgetyear": 1800,
                "ch4_budget_avgyears": 10,
                "ch4_feed_yrstart": 1800,
                "n2o_lastbudgetyear": 1800,
                "n2o_budget_avgyears": 10,
                "n2o_feed_yrstart": 1800,
                # This doesn't really work because the CH4 and N2O cycles go crazy.
                # "ch4_lastbudgetyear": startyear,
                # "ch4_budget_avgyears": 1,
                # "ch4_feed_yrstart": startyear,
                # "n2o_lastbudgetyear": startyear,
                # "n2o_budget_avgyears": 1,
                # "n2o_feed_yrstart": startyear,
                "out_dynamic_vars": [
                    "DAT_SURFACE_TEMP",
                    "DAT_CO2_CONC",
                    "DAT_CH4_CONC",
                    "DAT_N2O_CONC",
                ],
                "out_ascii_binary": "BINARY",
                "out_binary_format": 2,
            }

            run_config = [
                {
                    **common_cfg,
                    **base_cfg,
                }
                for base_cfg in base_cfgs[:N_CFGS_TO_RUN]
            ]
            len(run_config)

            # Run the scenarios in batches

            len(input_emissions.get_unique_meta("scenario"))

            scenario_batches = []
            tmp = []
            for i, sdf in enumerate(input_emissions.groupby("scenario")):
                if i > 0 and i % SCENARIO_BATCH_SIZE == 0:
                    scenario_batches.append(scmdata.run_append(tmp))
                    tmp = []

                tmp.append(sdf)
            else:
                scenario_batches.append(scmdata.run_append(tmp))

            for b in scenario_batches:
                print(len(b.get_unique_meta("scenario")))

            magicc_res_raw = []
            for scenario_batch in tqdman.tqdm(scenario_batches, desc="Scenario batch"):
                tmp = openscm_runner.run.run(
                    climate_models_cfgs={
                        "MAGICC7": run_config,
                    },
                    scenarios=scenario_batch,
                    output_variables=(
                        "Surface Air Temperature Change",
                        "Atmospheric Concentrations|CO2",
                        "Atmospheric Concentrations|CH4",
                        "Atmospheric Concentrations|N2O",
                    ),
                )
                magicc_res_raw.append(tmp)

            magicc_res_raw = scmdata.run_append(magicc_res_raw)
            magicc_res_raw
            magicc_res = magicc_res_raw.filter(region="World")
            for vdf in magicc_res.groupby("variable"):
                ax, _ = vdf.convert_unit(vdf.get_unique_meta("unit")[-1]).plumeplot(
                    quantile_over="run_id"
                )
                sns.move_legend(ax, loc="center left", bbox_to_anchor=(1.05, 0.5))
                plt.show()
            MAGICC_RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            magicc_res.to_csv(MAGICC_RESULTS_FILE)
            return()
        
        main()
