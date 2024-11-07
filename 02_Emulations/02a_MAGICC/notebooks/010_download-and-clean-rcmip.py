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
# # Download and clean RCMIP emissions

# %%
import pooch
import scmdata

from notebooks.config import (
    RCMIP_EMISSIONS_FILE_HASH,
    RCMIP_EMISSIONS_FNAME,
    RCMIP_EMISSIONS_RAW_DIR,
    RCMIP_EMISSIONS_URL,
    RCMIP_SCENARIO_EMISSIONS_CLEAN,
    SEL_BASELINE,
    EMISSIONS_BASELINE,
)

# %%
rcmip_raw_file = pooch.retrieve(
    RCMIP_EMISSIONS_URL,
    known_hash=RCMIP_EMISSIONS_FILE_HASH,
    fname=RCMIP_EMISSIONS_FNAME,
    path=RCMIP_EMISSIONS_RAW_DIR,
)


# %%

rcmip_raw = scmdata.ScmRun(rcmip_raw_file, lowercase_cols=True)

# %%

scenarios = rcmip_raw.filter(
    region="World",
    scenario=[
        "rcp26",
        "rcp45",
        "rcp60",
        "rcp85",
        "ssp119",
        "ssp126",
        "ssp245",
        "ssp534-over",
        "ssp585",
        "ssp370",
        "ssp434",
        "ssp460",
    ],
).drop_meta(["activity_id", "mip_era"])
scenarios.get_unique_meta("scenario")

# %%
scenarios

# %%
scenarios_openscm_runner = scmdata.run_append(
    [
        scenarios.filter(variable="Emissions|CO2|*").filter(
            variable="Emissions|CO2|*|*", keep=False
        ),
        scenarios.filter(variable="Emissions|CO2*", keep=False)
        .filter(variable="Emissions|*")
        .filter(variable="Emissions|*|*", keep=False),
        scenarios.filter(variable="Emissions|Montreal Gases|*"),
        scenarios.filter(variable="Emissions|F-Gases|*"),
    ]
)

assert (
    len(scenarios_openscm_runner.get_unique_meta("variable")) == 52
), scenarios_openscm_runner.get_unique_meta("variable")


def convert_variable_rcmip_to_openscmrunner(v: str) -> str:
    """
    Convert variable name from RCMIP conventions to OpenSCM-Runner conventions
    """
    if "Montreal Gases" in v:
        v = v.replace("Montreal Gases|", "")
        if "CFC" in v:
            return v.replace("CFC|", "")

        return v

    if "F-Gases" in v:
        v = v.replace("F-Gases|", "")

        if "HFC" in v:
            return v.replace("HFC|", "")

        if "PFC" in v:
            return v.replace("PFC|", "")

        if "CFC" in v:
            return v.replace("CFC|", "")

    return v

scenarios_openscm_runner["variable"] = scenarios_openscm_runner["variable"].apply(
    convert_variable_rcmip_to_openscmrunner
)
scenarios_openscm_runner

# %%
RCMIP_SCENARIO_EMISSIONS_CLEAN.parent.mkdir(parents=True, exist_ok=True)
scenarios_openscm_runner.to_csv(RCMIP_SCENARIO_EMISSIONS_CLEAN)

# %%

scenarios_openscm_runner.filter(scenario= SEL_BASELINE).to_csv(EMISSIONS_BASELINE)
