#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Some functions to load and preprocess Earth System Model data stroed in NetCDF files. 
Functionalities are focused on temperature and precipitaaiton.
"""

import numpy as np
import xarray as xr
import warnings
import dask
dask.config.set({"array.slicing.split_large_chunks": True})

from pathlib import Path
import config.constants as constants

from utils.regionmaskcompat import mask_3D_frac_approx
import mplotutils as mpu
import regionmask
import copy

def load_and_prepare_land_dataset(model_id, run_names, vars_, compute_anomalies = True):
    """
    For a specific set of runs and variables from an earth system model, load the monthly LAND data and
    combine it into a single dataframe. Convert the data to anomalies if compute_anomalies is set to True 

    Parameters
    ----------
    model_id : string
        Name of the Earth System Model 
    run_names : list of strings
        List of strings identifiyng scenario-ensemble member combinations for processing
    vars_ : list of strings 
        Names of variables 
    compute_anomalies: binary
        If set to True, temperature data will be converted to anomalies relative to the 
        reference period specified in the configs.constants file 

    Returns
    -------
   ds_return : xarrax.dataset
        Dataset containing a monthly field timeseries of all input variables over land 
    """
    landseamask     = load_land_sea_area_mask()
    ds_orig         = load_and_prepare_original_datasets(model_id, run_names, vars_, compute_anomalies)
    return(apply_land_sea_are_mask(ds_orig, landseamask))

def load_and_prepare_original_datasets(model_id, run_names, vars_, compute_anomalies = True):
    """
    For a specific set of runs and variables from an earth system model, load the monthly data and
    combine it into a single dataframe. Convert the data to anomalies if compute_anomalies is set to True 

    Parameters
    ----------
    model_id : string
        Name of the Earth System Model 
    run_names : list of strings
        List of strings identifiyng scenario-ensemble member combinations for processing
    vars_ : list of strings 
        Names of variables 
    compute_anomalies: binary
        If set to True, temperature data will be converted to anomalies relative to the 
        reference period specified in the configs.constants file 

    Returns
    -------
   ds_return : xarrax.dataset
        Dataset containing a monthly field timeseries of all input variables 
    """
    n_runs = len(run_names)
    n_vars = len(vars_)

    list_ds = []
    for i in range(n_runs): 
        ds = xr.open_mfdataset([constants.DATA_DIR / f'{vars_[j]}/mon/g025/{vars_[j]}_mon_{model_id}_{run_names[i]}_g025.nc' for j in range(n_vars)], engine = 'netcdf4')[vars_]
    
        try: 
            ds = ds.drop(labels = 'height')
        except: 
            pass 

        ds          = ds.roll(lon = 72, roll_coords = True) 
        ds          = ds.assign_coords(lon=(((ds.lon + 180) % 360) - 180)) 
        ds          = ds.sortby(["lat", "lon"])

        # clean data-frame from negative precipitation values
        if 'pr' in vars_:
            min_non_zero = np.min(ds['pr'].values[ds['pr'].values > 0])
            ds['pr']     = ds['pr'].where(~(ds['pr'].values <= 0), min_non_zero/2)
            ds['pr'].where(~(ds['pr'].values < 0), 0)

        ssp_id = run_names[i].split('_')[0]
        run_id = run_names[i].split('_')[1]

        ds = ds.expand_dims(dim = dict(ssp_id = [ssp_id], run_id = [run_id]))
        list_ds.append(ds.load())
    
    ds_return = xr.merge(list_ds).load()
    del ds, list_ds
    
    if compute_anomalies == True: 
        ref_lower, ref_upper = constants.ref_period
        ds_sub               = ds_return.sel(ssp_id = 'historical').isel(time = slice(constants.ref_period[0]-1850, (constants.ref_period[1]-constants.ref_period[0])*12))
        ds_ref               = calculate_ref_value(ds_sub)
        for var in vars_:
            ds_return[f'{var}_rel'] = ds_return[f'{var}'] - ds_ref[f'{var}']
    return(ds_return)

def load_gmt_dataset(model_id, run_names):
    """
    For a specific run from an earth system model, process the temperature data 
    and output a dataframe containing area-weighted global mean temperature 
    estimates 

    Parameters
    ----------
    model_id : string
        Name of the Earth System Model 
    run_names : list of strings
        List of strings identifiyng scenario-ensemble member combinations for processing

    Returns
    -------
    gmt_ds : xarrax.DataSet
        DataSet containing a timesdries of global mean temperature for the 
        specified model_id and scenario-ensemble member combinations 
    """
    n_runs = len(run_names)

    list_ds = []
    for i in range(n_runs): 
        ds = xr.open_mfdataset([constant.DATA_DIR / f'tas/mon/g025/tas_mon_{model_id}_{run_names[i]}_g025.nc'], engine = 'netcdf4')['tas']
        
        try: 
            ds = ds.drop(labels = 'height')
        except: 
            pass 

        ds          = ds.roll(lon = 72, roll_coords = True) 
        ds          = ds.assign_coords(lon=(((ds.lon + 180) % 360) - 180)) 
        ds          = ds.sortby(["lat", "lon"])
        
        ds_mean         = area_weighted_global_average(ds)
        ds_abs_gmt      = day_weighted_annual_average(ds_mean)
        ds_abs_gmt.name = 'tas' 
        
        del ds, ds_mean

        ssp_id = run_names[i].split('_')[0]
        run_id = run_names[i].split('_')[1]

        ds_abs_gmt = ds_abs_gmt.expand_dims(dim = dict(ssp_id = [ssp_id], run_id = [run_id]))
        list_ds.append(ds_abs_gmt.load())
    
    ds_tmp = xr.merge(list_ds).load()
    
    gmt_ref         = ds_tmp['tas'].sel(ssp_id = 'historical').sel(year = slice(constants.ref_period[0], constants.ref_period[1])).mean(dim = 'year')
    
    gmt_ds          = xr.Dataset({'abs_gmt': ds_tmp['tas'], 'rel_gmt': ds_tmp['tas']- gmt_ref})    
    return(gmt_ds)


def load_land_gmt_dataset(model_id, run_names):
    """
    For a specific run from an earth system model, process the temperature data 
    and output a dataframe containing area-weighted global land mean temperature 
    estimates (same as load_gmt_dataset except a land-sea mask is applied)

    Parameters
    ----------
    model_id : string
        Name of the Earth System Model 
    run_names : list of strings
        List of strings identifiyng scenario-ensemble member combinations for processing

    Returns
    -------
    gmt_ds : xarrax.DataSet
        DataSet containing a timesdries of global land mean temperature for the 
        specified model_id and scenario-ensemble member combinations 
    """
    n_runs = len(run_names)

    list_ds = []
    for i in range(n_runs): 
        ds = xr.open_mfdataset([constants.DATA_DIR / f'tas/mon/g025/tas_mon_{model_id}_{run_names[i]}_g025.nc'], engine = 'netcdf4')['tas']
        
        try: 
            ds = ds.drop(labels = 'height')
        except: 
            pass 

        ds          = ds.roll(lon = 72, roll_coords = True) 
        ds          = ds.assign_coords(lon=(((ds.lon + 180) % 360) - 180)) 
        ds          = ds.sortby(["lat", "lon"])

        ssp_id = run_names[i].split('_')[0]
        run_id = run_names[i].split('_')[1]

        ds = ds.expand_dims(dim = dict(ssp_id = [ssp_id], run_id = [run_id]))
        list_ds.append(ds)
    
    ds_tmp = xr.merge(list_ds)

    # mask out land_area
    landseamask     = load_land_sea_area_mask()
    ds_land         = apply_land_sea_are_mask(ds_tmp, landseamask)['tas']

    # compute are-weighted annual mean     
    ds_landmean     = area_weighted_global_average(ds_land)
    ds_abs_gmt      = day_weighted_annual_average(ds_landmean)
    
    gmt_ref         = ds_abs_gmt.sel(ssp_id = 'historical').sel(year = slice(constants.ref_period[0], constants.ref_period[1])).mean(dim = 'year')
    
    gmt_ds          = xr.Dataset({'abs_gmt': ds_abs_gmt, 'rel_gmt': ds_abs_gmt - gmt_ref}) 
    return(gmt_ds)

def area_weighted_global_average(dataarray):
    """
    Computes an area weighted mean over the input dataarray. 
    Only works if dataarray has dimension <lat> and <lon>
    in coordinates. 
    
    Parameters
    ----------
    dataarray : xr.DataArray 
        XArray containing a variable and dimensions <lat> and <lon>

    Returns
    -------
    var_weighted_mean : xr.DataArray 
        Same as input arrray except containing an averaged version of 
        the input variable over dimensions <lat> and <lon>
    """
    weights             = np.cos(np.deg2rad(dataarray.lat))
    weights.name        = 'weights'
    var_weighted        = dataarray.weighted(weights)
    var_weighted_mean   = var_weighted.mean(('lon', 'lat'))
    return(var_weighted_mean)

def day_weighted_annual_average(dataarray):
    """
    Computes annual averaged from monthly data with weights (e.g. bc of leap years)
    
    Parameters
    ----------
    dataarray : xr.DataArray 
        XArray containing a variable and dimension time measured in months
        
    Returns
    -------
    dataarray_weighted : xr.DataArray 
        Same as input arrray except containing an averaged version of 
        the input variable over dimension time such that the output
        has yearly resoltuion 
    """
    month_length        = dataarray.time.dt.days_in_month
    weights             = month_length.groupby("time.year") / month_length.groupby("time.year").sum()
    # skipna false to keep missing values as nans and not as 0s 
    dataarray_weighted  = (dataarray * weights).groupby("time.year").sum(dim="time", skipna = False)
    return(dataarray_weighted)
    
def calculate_ref_value(dataarray):
    """
    Computes time average over reference period by first aggregating 
    monthly data to yearly data and then averaging over all
    years 
    
    Parameters
    ----------
    dataarray : xr.DataArray 
        XArray containing a variable and dimension time measured in months
        
    Returns
    -------
    ref_dataarray : xr.DataArray 
        Same as input arrray except containing an average of
        the input variable over dimension time 
    """
    month_length        = dataarray.time.dt.days_in_month
    weights             = month_length.groupby('time.year') / month_length.groupby('time.year').sum()
    dataarray_weighted  = (dataarray * weights).groupby('time.year').sum(dim="time")
    ref_dataarray       = dataarray_weighted.mean('year')
    return(ref_dataarray)

def load_land_sea_area_mask(path_lsm = '/home/ubuntu/sarah/files/mesmerdev/data/interim_invariant_lsmask_regrid.nc'):
    """
    Loading DataArray containing a land-sea binary which yields 1(0) at  
    locations over land (sea). 

    Parameters
    ----------
    path_lsm : string, optional
        Path to .nc file containing the land sea area mask.
        The default is '/home/ubuntu/sarah/files/mesmerdev/data/interim_invariant_lsmask_regrid.nc'.

    Returns
    -------
    landseamask  : xarray.DataArray
        DataArray containing the binary variable 'lsm' as a function of 
        latitude and longitude. Binary is 0 whenever coordinates correspond to
        a location over sea and 1 whenever coordiantes are located over land 

    """

    frac_l            = xr.open_mfdataset(path_lsm, engine = "netcdf4", combine='by_coords', decode_times=False)
    land_110          = regionmask.defined_regions.natural_earth_v5_0_0.land_110
    ls_raw            = mask_3D_frac_approx(land_110, frac_l.lon, frac_l.lat)[0]

    landseamask       = ls_raw.where(ls_raw.lat > -60, 0)
    landseamask       = landseamask.where(landseamask >= 1/3, 0)
    landseamask       = landseamask.where(landseamask < 1/3, 1)

    return(landseamask)

def apply_land_sea_are_mask(dataset, landseamask):
    """
    Set values of dataset to NaN over sea. 

    Parameters
    ----------
    dataset : xarray.DataSet
        Dataset containing all variables that should be masked using landseamask.
    landseamask : xarray.DataArray
        DataArray containing the binary variable 'lsm' as a function of 
        latitude and longitude. Binary is 0 whenever coordinates correspond to
        a location over sea and 1 whenever coordiantes are located over land 

    Returns
    -------
    lsm_dataset : xarrax.DataSet
        DataSet corresponds to the input dataset, but with all variable values
        over sea set to NaN 

    """
    if any(dataset.lat.values != landseamask.lat.values) or any(dataset.lon.values != landseamask.lon.values):
        warnings.warn('Coordinates of land-sea-are mask do not match the coordinates of the dataset you\'re trying to apply it to.')
    
    # apply lsm to dataframe, i.e. set all locations in dataset to NaN 
    # where the landseamask binary variable lsm is 1
    lsm_dataset        = dataset
    # lsm_dataset['lsm'] = landseamask
    lsm_dataset        = lsm_dataset.where(landseamask != 0)

    return(lsm_dataset)
