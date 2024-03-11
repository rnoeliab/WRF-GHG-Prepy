#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 10 11:19:21 2023
@author: noelia
"""

import cdsapi
import os

print("Current directory:", os.getcwd())
os.chdir('../..')
newpath = os.getcwd() + '/input/bio_ghg/ch4_bio/'
print("New directory:", newpath)
os.chdir(newpath)


c = cdsapi.Client()

c.retrieve(
    'reanalysis-era5-single-levels-monthly-means',
    {
        'product_type': 'monthly_averaged_reanalysis',
        'variable': [
            'soil_temperature_level_1','soil_temperature_level_2', 
            'soil_temperature_level_3', 'soil_temperature_level_4'],
        'year': '2023',                 ###  here you must to change
        'month': [
            '01', '02', '03',
            '04', '05', '06',
            '07', '08', '09',
            '10', '11', '12',
        ],
        'time': '00:00',
        'area': [
            90, -180, -90,           #### here you must to change
            180,
        ],
        'format': 'netcdf',
    },
    'ERA_monthly_soiltemperature_2023.nc')    #### here you must to change
