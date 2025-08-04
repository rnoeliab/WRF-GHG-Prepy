print("========================================================================")
print("Matlab WRF-GHG: IC from CAMS")
print("Michal Galkowski, MPI-BGC Jena")
print("modified by David Ho, MPI-BGC Jena")
print('Translated for python by Noelia Rojas, IFUSP Brazil')
print('over the Amazon domain.')

import numpy as np
import pandas as pd
import netCDF4 as cdf
import xarray as xr
from datetime import datetime, timedelta
import scipy.io
import os,time
import matplotlib.pyplot as plt


#Setting important paths to files and directories
wrfinput_dir_path = '/path-wrfinput/'
indices_coeffs    = '/path-indices/'
requested_domains = [ "d01","d02"]
sim_time          = '2023-01-01 00:00:00','2023-01-08 00:00:00'       # check this!!

dates           = pd.to_datetime(sim_time[0]).strftime('%Y-%m-%d')
year            = pd.to_datetime(sim_time[0]).strftime('%Y')
month           = pd.to_datetime(sim_time[0]).strftime('%m')
day             = pd.to_datetime(sim_time[0]).strftime('%d')

wrfinput_path = os.path.join(wrfinput_dir_path,'wrfinput_d01')
print(wrfinput_path)

with xr.open_dataset(wrfinput_path) as wrfinput:   ### modify
    simstart_time_dt = datetime.strptime(wrfinput['Times'].values[0].decode("utf-8"), "%Y-%m-%d_%H:%M:%S")  ## UTC
simstart_time = simstart_time_dt.strftime("%Y%m%d")

CAMS_data_dir_path   ='/path-CAMS-inversion/data/';
name_CAMS_file       = 'cams73_latest_co2_conc_satellite_inst_202301_upgrade.nc';
CAMS_interpolation_indices_file_path = os.path.join(indices_coeffs,'interp_indices_CO2.txt.npz')

path_CAMS_ml_file   = os.path.join(CAMS_data_dir_path+name_CAMS_file)
path_CAMS_lnsp_file = os.path.join(CAMS_data_dir_path+name_CAMS_file)

print('Getting CAMS-inversion  latitudes and longitudes from:\n', path_CAMS_ml_file)

# Abrimos CAMS dataset una sola vez para lat, lon y times
with xr.open_dataset(path_CAMS_ml_file) as cams_ds:    #### modify
    cams_lat = cams_ds['latitude'].values
    cams_lon = cams_ds['longitude'].values
    cams_times = cams_ds['time'].values

cams_dates = [pd.to_datetime(str(t)) for t in cams_times]

# Convert cams_dates and simstart_time to Unix timestamps
cams_timestamps = [int(datetime.timestamp(d.to_pydatetime())) for d in cams_dates]
simstart_timestamp = int(datetime.timestamp(datetime.strptime(simstart_time, "%Y%m%d")))

# Encontrar índice de tiempo CAMS que coincide con simstart
try:
    cams_time_idx = cams_timestamps.index(simstart_timestamp)
except ValueError:
    raise ValueError("simstart time no encontrado en CAMS timestamps")

simstart_time = datetime.strptime(simstart_time, "%Y%m%d").strftime("%Y-%m-%d %H:%M:%S")
print( 'CAMS file contains the values for ',simstart_time,' at index no.', str(int(cams_time_idx)+1))

print('Getting CAMS lnsp (ln of surface pressure) from:\n ',path_CAMS_lnsp_file)

with cdf.Dataset(path_CAMS_lnsp_file, 'r') as nc_file:
    a = nc_file.variables['ap'][:]
    b = nc_file.variables['bp'][:]
    cams_pressure = nc_file.variables['Psurf'][cams_time_idx,:,:]

with cdf.Dataset(path_CAMS_ml_file,'r') as nc_co2_file:
    cams_co2 = nc_co2_file.variables['CO2'][cams_time_idx,:,:,:]*1e6

for domain in requested_domains:
    print(f'\nProcessing domain: {domain}')

    # Load interpolation indices only una vez
    interpolation_indices = np.load(CAMS_interpolation_indices_file_path)[f'cams_indices_{domain}']

    wrfinput_path = os.path.join(wrfinput_dir_path, f'wrfinput_{domain}')

    # Load wrfinput file for the current domain
    with xr.open_dataset(wrfinput_path) as ds:
        wrf_xlat  = ds['XLAT'].values[0]
        wrf_xlong = ds['XLONG'].values[0]
        dummy_3d_scalar_field = ds['CO2_BIO'].values[0]

        n_vertical_levels, n_sn, n_ew = dummy_3d_scalar_field.shape
        wrf_pressure = ds['PB'].values[0] + ds['P'].values[0]

    co2_bio_init = 400 * np.ones((n_vertical_levels, n_sn, n_ew))

    # Escribir CO2_BIO en modo escritura cerrando previamente el dataset xarray
    with cdf.Dataset(wrfinput_path, 'r+') as ncid:
        ncid.variables['CO2_BIO'][0] = co2_bio_init

    wrf_init_CO2_BCK = np.full_like(dummy_3d_scalar_field, -999.)

    print('Calculating pressures and interpolating CO2 background')

    for lat_idx in range(n_sn):
        print(f'Processing latitude band {lat_idx+1}/{n_sn}')
        for lon_idx in range(n_ew):
            surface_pressure = cams_pressure[interpolation_indices[lat_idx, lon_idx, 1].astype(int),
                                            interpolation_indices[lat_idx, lon_idx, 0].astype(int)]
            cams_v_pressures = surface_pressure * b + a
            wrf_v_pressures  = wrf_pressure[:, lat_idx, lon_idx]

            for lvl_idx in range(n_vertical_levels):
                difference = np.abs(cams_v_pressures - wrf_v_pressures[lvl_idx])
                cams_nearest_lvl_idx = np.argmin(difference)

                lat_idx_nearest = int(interpolation_indices[lat_idx, lon_idx, 1])
                lon_idx_nearest = int(interpolation_indices[lat_idx, lon_idx, 0])

                wrf_init_CO2_BCK[lvl_idx, lat_idx, lon_idx] = cams_co2[cams_nearest_lvl_idx, lat_idx_nearest, lon_idx_nearest]

    print('Writing values from CAMS for CO2_BCK field of wrfinput')

    with cdf.Dataset(wrfinput_path, 'r+') as ncid:
        ncid.variables['CO2_BCK'][0] = wrf_init_CO2_BCK



# === Start of CH4 Logic ===
CAMS_data_dir_path   ='/path-CAMS-inversion/data/';
name_CAMS_file       = 'cams73_latest_ch4_conc_surface_satellite_inst_202301.nc';
CAMS_interpolation_indices_file_path = os.path.join(indices_coeffs,'interp_indices_ch4.txt.npz')

path_CAMS_ml_file   = os.path.join(CAMS_data_dir_path+name_CAMS_file)
path_CAMS_lnsp_file = os.path.join(CAMS_data_dir_path+name_CAMS_file)

with xr.open_dataset(wrfinput_path) as wrfinput:   ### modify
    simstart_time_dt = datetime.strptime(wrfinput['Times'].values[0].decode("utf-8"), "%Y-%m-%d_%H:%M:%S")  ## UTC
simstart_time = simstart_time_dt.strftime("%Y%m%d")

print('Getting CAMS-inversion latitudes and longitudes from:\n', path_CAMS_ml_file)
# Abrimos CAMS dataset una sola vez para lat, lon y times
with xr.open_dataset(path_CAMS_ml_file) as cams_ds:
    cams_lat = cams_ds['latitude'].values
    cams_lon = cams_ds['longitude'].values
    cams_times = cams_ds['time'].values

cams_dates = [pd.to_datetime(str(t)) for t in cams_times]

# Convert cams_dates and simstart_time to Unix timestamps
cams_timestamps = [int(datetime.timestamp(d.to_pydatetime())) for d in cams_dates]
simstart_timestamp = int(datetime.timestamp(datetime.strptime(simstart_time, "%Y%m%d")))

# Check if one of the times is the same as simstart time:
# Encontrar índice de tiempo CAMS que coincide con simstart
try:
    cams_time_idx = cams_timestamps.index(simstart_timestamp)
except ValueError:
    raise ValueError("simstart time no encontrado en CAMS timestamps")

simstart_time = datetime.strptime(simstart_time, "%Y%m%d").strftime("%Y-%m-%d %H:%M:%S")
print( 'CAMS-inversion file contains the values for ',simstart_time,' at index no.', str(int(cams_time_idx)+1))

print('Getting CAMS-inversion lnsp (ln of surface pressure) from:\n ',path_CAMS_lnsp_file)

with cdf.Dataset(path_CAMS_lnsp_file, 'r') as nc_file:
    a = nc_file.variables['hyai'][:]
    b = nc_file.variables['hybi'][:]
    cams_pressure = nc_file.variables['ps'][cams_time_idx,:,:]
    conv_ch4 = 1e-9*1e6

with cdf.Dataset(path_CAMS_ml_file,'r') as nc_ch4_file:
    cams_ch4 = nc_ch4_file.variables['CH4'][cams_time_idx,:,:,:]*conv_ch4;   # (lev,lat,lon)  == (137, 451, 900)

#Now execute the caluclation per-domain
for domain in requested_domains:
    print(f'\nProcessing domain: {domain}')

    # Load interpolation indices only una vez
    print('Loading in the pre-calculated nearest-neighbour interipolation indices.');
    interpolation_indices = np.load(CAMS_interpolation_indices_file_path)[f'cams_indices_{domain}']

    # Load wrfinput file for the current domain
    wrfinput_path = os.path.join(wrfinput_dir_path, f'wrfinput_{domain}')
    # Abrir wrfinput una vez para lectura
    with xr.open_dataset(wrfinput_path) as ds:
        wrf_xlat  = ds['XLAT'].values[0]
        wrf_xlong = ds['XLONG'].values[0]
        dummy_3d_scalar_field = ds['CO2_BIO'].values[0];     ## (lev,sn,ew) == (50,294,591)

        n_vertical_levels, n_sn, n_ew = dummy_3d_scalar_field.shape
        wrf_pressure = ds['PB'].values[0] + ds['P'].values[0]

    co2_bio_init = 400 * np.ones((n_vertical_levels,n_sn,n_ew))
    ch4_bio_init = 1.8 * np.ones((n_vertical_levels,n_sn,n_ew))
    ch4_soil_uptake_init = 1.8 * np.ones((n_vertical_levels,n_sn,n_ew))

    #Write the values already:
    with cdf.Dataset(wrfinput_path, 'r+') as ncid:
        ncid.variables['CO2_BIO'][0] = co2_bio_init
        ncid.variables['CH4_BIO'][0] = ch4_bio_init
        ncid.variables['CH4_BIO_Soils'][0] = ch4_soil_uptake_init

    wrf_init_CH4_BCK =  np.full_like(dummy_3d_scalar_field, -999.)
    #wrf_init_CO_BCK = np.zeros((dummy_3d_scalar_field.shape))  + (-999.)
    #wrf_init_CO2_BCK = np.full(dummy_3d_scalar_field.shape, -999.)

    for lat_idx in range(n_sn):
        print(f'Processing latitude band {lat_idx+1}/{n_sn}')
        for lon_idx in range(n_ew):
            surface_pressure = cams_pressure[interpolation_indices[lat_idx, lon_idx, 0].astype(int),
                                            interpolation_indices[lat_idx, lon_idx, 1].astype(int)]
            cams_v_pressures = surface_pressure.data * b.astype(float) +a.astype(float)
            wrf_v_pressures  = wrf_pressure[:, lat_idx, lon_idx]

            for lvl_idx in range(n_vertical_levels):
                difference = np.abs(cams_v_pressures - wrf_v_pressures[lvl_idx])
                cams_nearest_lvl_idx = min(np.where(difference == min(difference)))[0];

                lat_idx_nearest = int(interpolation_indices[lat_idx, lon_idx, 1])
                lon_idx_nearest = int(interpolation_indices[lat_idx, lon_idx, 0])

                wrf_init_CH4_BCK[lvl_idx,lat_idx,lon_idx] = cams_ch4[cams_nearest_lvl_idx, lat_idx_nearest, lon_idx_nearest];
                #wrf_init_CO_BCK[lvl_idx,lat_idx,lon_idx]  = cams_co[cams_nearest_lvl_idx, lat_idx_nearest, lon_idx_nearest];
    print('Writing values from CAMS for CH4_BCK field of wrfinput')

    with cdf.Dataset(wrfinput_path, 'r+') as ncid:
        ncid.variables['CH4_BCK'][0] = wrf_init_CH4_BCK

print('Script completed.')
