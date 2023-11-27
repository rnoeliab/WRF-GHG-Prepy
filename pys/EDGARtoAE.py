#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xarray as xr
import numpy as np
from pathlib import Path
import os

def add_date_datesec(edgar_file, year=2018):
    '''
    Add the 'date' and 'datesec' variables into
    edgar emission file

    Parameters
    ----------
    edgar_file : str
        edgar monthly emission file.
    year : int, optional
        year of the emission file. The default is 2015

    Returns
    -------
    edgar_date: xarray Dataset
        emission file with 'date' and 'datesec' variable
    '''
    month = int(edgar_file.split("2018_")[1].split("_")[0])
    time = np.array([month - 1])
    date = np.array([year * 10000 + month * 100 + 1])

    edgar_date = xr.open_dataset(edgar_file)
    var_name = list(edgar_date.data_vars)[0]
    edgar_date = edgar_date.rename({var_name:"emis_tot"})

    edgar_date["time"] = time
    edgar_date["date"] = xr.DataArray(date, dims=["time"])
    edgar_date["datesec"] = xr.DataArray(np.array([0]), dims=["time"])
    return edgar_date

def concat_sector_by_month(sector_path):
    '''
    Load and concat monthly emission into one netcdf

    Parameters
    ----------
    sector_path : str
        path of pollutant emission sector folder

    Returns
    -------
    year_emiss: xarray Dataset
        montly emission into one dataset

    '''
    sector = Path(sector_path)
    sector_files = [str(file) for file in list(sector.glob("*.nc"))]
    ds = {int(f.split("2018_")[1].split("_")[0]): add_date_datesec(f) 
            for f in sector_files}
    ds_sorted = dict(sorted(ds.items()))
    year_emiss = xr.concat(list(ds_sorted.values()), dim="time")
    return year_emiss

def join_pol_by_sector(pol_path, total=False):
    '''
    Read sector emissions and save them in one dict. If total = True
    it returns the total emission

    Parameters
    ----------
    pol_path : str
        Polutant emissions folder where sectors are
    total : Bool, optional
        sum all the sector emission. The default is False
    
    Returns
    -------
    pol_emi : xarray Dataset
       Total emission (sum of all sources)
    pol_by_sector: dictionary
        Dictionary with sectors monthtly emission in one dataset
    '''
    pol_folder = Path(pol_path)
    pol_sectors = [str(folder) for folder in pol_folder.glob("*/")]
    pol_by_sector = {sector.split("/")[-1]: concat_sector_by_month(sector) 
                     for sector in pol_sectors}
    if total:
        pol_emi = sum(pol_by_sector.values())
        pol_emi["date"] = pol_by_sector[list(pol_by_sector.keys())[1]].date
        return pol_emi
    else:
        return pol_by_sector

def group_sectors(pol_by_sector, sectors):
    '''
    Group emissions sector in a single group (i.e. IPCC 96)

    Parameters
    ----------
    pol_by_sector : dict
        Dictionary with sectors monthly emission in onde dataset
    sectors : list
        List of sectors to merge
    '''
    group = {sector: pol_by_sector[sector] for sector in sectors 
             if sector in pol_by_sector.keys()}
    group_total = sum(group.values())
    group_total["date"] = pol_by_sector[list(pol_by_sector.keys())[1]].date
    return group_total

def write_netcdf_toAE(emiss, pollutant, sec, prefix="v6.0_",
                      suffix=".0.1x0.1.nc"):
    '''
    Export emission dataset into netcdf

    Parameters
    ----------
    emiss : xarray Dataset
        Emission dataset to export to netcdf
    pollutatnt : str
        Name of emitted pollutant
    sec : str
        Sector       
    prefix : str, optional
        prefix used in anthro emiss. Default is "v6.0_"
    suffix : str, optional
        suffix to add to the file name. Default is ".0.1x0.1.nc"
    '''
    file_name = (prefix + pollutant + "_" + sec + "_2018" +  suffix)
#    print(file_name)
    emiss['emis_tot'].attrs['units'] = 'kg m-2 s-1'
#    emiss['emis_tot'].attrs['_FillValue'] = 0.
    emiss.to_netcdf(file_name, unlimited_dims={"time": True})

print("Current directory:", os.getcwd())
os.chdir('..')
newpath = os.getcwd() + '/input/anthr_ghg/'
print("New directory:", newpath)
os.chdir(newpath)
os.mkdir('data_total')
os.chdir(newpath+'data_total/')

gas = ["CO","CO2","CH4"]

for g in gas:
    if str(g) == "CO":
        pol_path = newpath+"data_ghg/data_co"
        # Group sectors
        energy      = ["ENE", "REF_TRF", "IND", "RCO", "PRO"]
        transport   = ["TRO_noRES", "TNR_Other"]
        aviation    = ["TNR_Aviation_CDS", "TNR_Aviation_CRS", "TNR_Aviation_LTO"]
        shipping    = ["TNR_Ship"]
        industrial  = ["CHE", "IRO"]
        agriculture = ["AWB"]
        waste       = ["SWD_INC"]
        fires       = ["FFF"]
                
        tot_no_fire = ["ENE", "REF_TRF", "IND", "RCO", "PRO", "TRO_noRES", "TNR_Other",
                    "TNR_Aviation_CDS", "TNR_Aviation_CRS", "TNR_Aviation_LTO",
                    "TNR_Ship", "CHE", "IRO", "AWB", "SWD_INC"]
        
    elif str(g) == "CO2":
        pol_path = newpath+"data_ghg/data_co2_excl"
        # Group sectors
        energy      = ["ENE", "REF_TRF", "IND", "RCO", "PRO"]
        transport   = ["TRO_noRES", "TNR_Other"]
        aviation    = ["TNR_Aviation_CDS", "TNR_Aviation_CRS", "TNR_Aviation_LTO"]
        shipping    = ["TNR_Ship"]
        industrial  = ["CHE", "IRO"]
        agriculture = ["AGS"]
        waste       = ["SWD_INC"]
        fires       = ["FFF"]
        tot_no_fire = ["ENE", "REF_TRF", "IND", "RCO", "PRO", "TRO_noRES", "TNR_Other",
                    "TNR_Aviation_CDS", "TNR_Aviation_CRS", "TNR_Aviation_LTO",
                    "TNR_Ship","CHE", "IRO", "AGS","SWD_INC"]
    else:
        pol_path = newpath+"data_ghg/data_ch4"
        # Group sectors 
        energy      = ["ENE", "REF_TRF", "IND", "RCO", "PRO_COAL", "PRO", "PRO_OIL", "PRO_GAS"]
        transport   = ["TRO_noRES", "TNR_Other"]
        aviation    = ["TNR_Aviation_CDS", "TNR_Aviation_CRS", "TNR_Aviation_LTO"]
        shipping    = ["TNR_Ship"]
        industrial  = ["CHE", "IRO"]
        agriculture = ["ENF", "MNM", "AWB", "AGS"]
        waste       = ["SWD_LDF", "SWD_INC", "WWT"]
        fires       = ["FFF"]
        tot_no_fire = ["ENE", "REF_TRF", "IND", "RCO", "PRO_COAL", "PRO", "PRO_OIL", "PRO_GAS", "TRO_noRES", "TNR_Other",
                    "TNR_Aviation_CDS", "TNR_Aviation_CRS", "TNR_Aviation_LTO",
                    "TNR_Ship",
                    "CHE", "IRO",
                    "ENF", "MNM", "AWB", "AGS",
                    "SWD_LDF", "SWD_INC", "WWT"]
                    
    print("Processing in the ", pol_path)
    gas_all = join_pol_by_sector(pol_path, total=True)
                    
    write_netcdf_toAE(gas_all, str(g), "ALL")

    pol_sec = join_pol_by_sector(pol_path)
    pol_energy      = group_sectors(pol_sec, energy)
    pol_transport   = group_sectors(pol_sec, transport)
    pol_aviation    = group_sectors(pol_sec, aviation)
    pol_shipping    = group_sectors(pol_sec, shipping)
    pol_industrial  = group_sectors(pol_sec, industrial)
    pol_agriculture = group_sectors(pol_sec, agriculture)
    pol_waste       = group_sectors(pol_sec, waste)
    pol_fires       = group_sectors(pol_sec, fires)
    pol_tot_no_fire = group_sectors(pol_sec, tot_no_fire)

    write_netcdf_toAE(pol_energy, str(g), "ENERGY")
    write_netcdf_toAE(pol_transport, str(g), "TRANSPORT")
    write_netcdf_toAE(pol_aviation, str(g), "AVIATION")
    write_netcdf_toAE(pol_shipping, str(g), "SHIPPING")
    write_netcdf_toAE(pol_industrial, str(g), "INDUSTRIAL")
    write_netcdf_toAE(pol_agriculture, str(g), "AGRICULTURE")
    write_netcdf_toAE(pol_waste, str(g), "WASTE")
    write_netcdf_toAE(pol_fires, str(g), "FIRES")
    write_netcdf_toAE(pol_tot_no_fire, str(g), "TOTAL_NO_FIRES")
                    
                    

