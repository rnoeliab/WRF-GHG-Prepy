#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 10 11:19:21 2023
@author: noelia
"""

import cdsapi
import os

print("Current directory:", os.getcwd())
os.chdir('..')
newpath = os.getcwd() + '/input/fire_ghg/'
print("New directory:", newpath)
os.chdir(newpath)

c = cdsapi.Client()

c.retrieve(
    'cams-global-fire-emissions-gfas',
    {
    'format':'netcdf',
    'variable':['altitude_of_plume_bottom', 
                'altitude_of_plume_top', 'injection_height', 
                'mean_altitude_of_maximum_injection', 
                'wildfire_flux_of_carbon_dioxide', 
                'wildfire_flux_of_methane',
                'wildfire_flux_of_carbon_monoxide'],
    'date':'2022-08-01/2022-08-31',     ### Change here
    },
    'gdas_fires.nc'               #### change here 
    )
    
    
