print('========================================================================')
print('Python WRF-GHG: IC from CAMS')
print('Michal Galkowski, MPI-BGC Jena')
print('modified by David Ho, MPI-BGC Jena')
print('For handling CAMS product from Santiago,')
print('Translated for python by Noelia Rojas, IFUSP Brazil')
print('over the Amazon domain.')

import numpy as np
import pandas as pd
import netCDF4 as cdf
import xarray as xr 
from datetime import datetime, timedelta
import scipy.io
import os,time

#Setting important paths to files and directories
wrfinput_dir_path = '../input/wrf_inputs/'
indices_coeffs    = '../input/bck_ghg/'
requested_domains = [ "d01","d02","d03"]
sim_time          = '2023-01-01 00:00:00','2023-01-07 00:00:00'       # check this!!

dates           = pd.to_datetime(sim_time[0]).strftime('%Y-%m-%d')
year            = pd.to_datetime(sim_time[0]).strftime('%Y')
month           = pd.to_datetime(sim_time[0]).strftime('%m')
day             = pd.to_datetime(sim_time[0]).strftime('%d')


wrfinput_path = os.path.join(wrfinput_dir_path,'wrfinput_d01')
print(wrfinput_path)
wrfinput = xr.open_dataset(wrfinput_path);
simstart_time = datetime.strptime(wrfinput['Times'].values[0].decode("utf-8"), "%Y-%m-%d_%H:%M:%S")  ## UTC 
simstart_time = simstart_time.strftime("%Y%m%d")

source = input("What's CAMS do you use? (GACF or inversion): ")
if source == "GACF":
    CAMS_data_dir_path   = '../input/bck_ghg/CAMS-GACF/unzips/';
    name_CAMS_file       = 'CAMS_GACF_large_ch4_'+simstart_time+'.nc'
else:
    CAMS_data_dir_path   = '../input/bck_ghg/CAMS/unzips/invr/';
    name_CAMS_file   = 'cams73_latest_ch4_conc_surface_satellite_inst_'+simstart_time[:-2]+'.nc';
CAMS_interpolation_indices_file_path = os.path.join(indices_coeffs,'interp_indices_'+str(source)+'_'+str(requested_domains[0])+'.txt.npz')

#Based on the initial day, set the CAMS filenames to be read.
path_CAMS_ml_file   = os.path.join(CAMS_data_dir_path+name_CAMS_file)
path_CAMS_lnsp_file = os.path.join(CAMS_data_dir_path+name_CAMS_file)

print('Getting CAMS '+str(source)+' latitudes and longitudes from:\n', path_CAMS_ml_file)

cams_lat = xr.open_dataset(path_CAMS_ml_file)['latitude']
cams_lon = xr.open_dataset(path_CAMS_ml_file)['longitude']

mesh_lat,mesh_lon = np.meshgrid(cams_lat,cams_lon)
cams_times = xr.open_dataset(path_CAMS_ml_file)['time']
cams_dates = [pd.to_datetime(cams_times.values[i]).strftime('%Y-%m-%d %H:%M:%S') for i in range(len(cams_times))]

# Convert cams_dates and simstart_time to Unix timestamps
cams_timestamps = [np.array([datetime.timestamp(datetime.strptime(i, '%Y-%m-%d %H:%M:%S'))],dtype=np.int64)[0] for i in cams_dates]
simstart_timestamp = np.array([datetime.timestamp(datetime.strptime(simstart_time, "%Y%m%d"))],dtype=np.int64)

# Check if one of the times is the same as simstart time:
cams_time_idx = np.where(simstart_timestamp[0] == cams_timestamps)[0][0]
simstart_time = datetime.strptime(simstart_time, "%Y%m%d").strftime("%Y-%m-%d %H:%M:%S")
print( 'CAMS '+str(source)+' file contains the values for ',simstart_time,' at index no.', str(int(cams_time_idx)+1)) 

#Important info on differences between sp and lnsp in IFS
#http://www.iup.uni-bremen.de/~hilboll/blog/2018/12/understanding-surface-pressure-in-ecmwf-era5-reanalysis-data/

print('Getting CAMS '+str(source)+' lnsp (ln of surface pressure) from:\n ',path_CAMS_lnsp_file)

nc_file = cdf.Dataset(path_CAMS_lnsp_file, 'r') 
if source == "GACF":
    IFS_L137_ab_file  = os.path.join(indices_coeffs,'ecmwf_coeffs_L137.csv')
    rawin=np.genfromtxt(IFS_L137_ab_file,delimiter=",",skip_header=1,dtype='<U25', encoding=None)
    a = rawin[:, 1] ; b = rawin[:, 2]
    cams_lnsp = nc_file.variables['lnsp'][cams_time_idx,:,:,:]    ## (time, level, latitude, longitude)
    cams_pressure = np.exp(cams_lnsp);
    gas = 'ch4_c'
    conv_ch4 = (28.97/16.01)*1e6
    conv_co = (28.97/28.01)*1e6
else:
    a = nc_file.variables['hyai'][:]; b = nc_file.variables['hybi'][:]
    cams_pressure = nc_file.variables['ps'][cams_time_idx,:,:]    ## (time, latitude, longitude)
    gas = 'CH4'
    conv_ch4 = 1e-9*1e6

cams_ch4 = cdf.Dataset(path_CAMS_ml_file,'r').variables[gas][cams_time_idx,:,:,:]*conv_ch4;   # (lev,lat,lon)  == (137, 451, 900)
#cams_co  = cdf.Dataset(path_CAMS_ml_file,'r').variables['co'][cams_time_idx,:,:,:]*(28.97/28.01)*1e6;
#cams_co2 = ncread( path_CAMS_ml_file, 'co2', nc_start_vector, nc_count_vector  ) * (28.97/44.01)*1e6;


#Now execute the caluclation per-domain
for domain_idx in range(len(requested_domains)):
    print('Processing domain:', requested_domains[domain_idx]);

    #Load CAMS interpolation indices for this domain
    print('Loading in the pre-calculated nearest-neighbour interipolation indices.');
    interpolation_indices = np.load(CAMS_interpolation_indices_file_path)[f'cams_indices_{requested_domains[domain_idx]}']

    # Load wrfinput file for the current domain
    wrfinput_path = os.path.join(wrfinput_dir_path, f'wrfinput_{requested_domains[domain_idx]}')
    wrf_xlat  = xr.open_dataset(wrfinput_path)['XLAT'].values[0];
    wrf_xlong = xr.open_dataset(wrfinput_path)['XLONG'].values[0];

    # Set offsets as initial values of biogenic tracers
    dummy_3d_scalar_field = xr.open_dataset(wrfinput_path)['CO2_BIO'].values[0];    ## (lev,sn,ew) == (50,294,591)

    n_vertical_levels = dummy_3d_scalar_field.shape[0]
    n_sn = dummy_3d_scalar_field.shape[1]
    n_ew = dummy_3d_scalar_field.shape[2]

    co2_bio_init = 400 * np.ones((n_vertical_levels,n_sn,n_ew))
    ch4_bio_init = 1.8 * np.ones((n_vertical_levels,n_sn,n_ew))
    ch4_soil_uptake_init = 1.8 * np.ones((n_vertical_levels,n_sn,n_ew))

    #Write the values already:
    ncid = cdf.Dataset(wrfinput_path, 'r+')
    ncid.variables['CO2_BIO'][0] = co2_bio_init
    ncid.variables['CH4_BIO'][0] = ch4_bio_init
    ncid.variables['CH4_BIO_SOIL'][0] = ch4_soil_uptake_init
    ncid.close()

    #Proceed to CAMS fields
    #For vertical assignment, nearest neighbour method will be used.
    print( 'Calculating pressures' );

    wrf_pressure = xr.open_dataset(wrfinput_path)['PB'].values[0] + xr.open_dataset(wrfinput_path)['P'].values[0];
    wrf_init_CH4_BCK = np.zeros((dummy_3d_scalar_field.shape))  + (-999.)
    #wrf_init_CO_BCK = np.zeros((dummy_3d_scalar_field.shape))  + (-999.)
    #wrf_init_CO2_BCK = np.full(dummy_3d_scalar_field.shape, -999.)

    for lat_idx in range(n_sn):
        print(f'Processing latitude band {lat_idx}/{n_sn}');
        for lon_idx in range(n_ew):
            #Get CAMS surface pressure
            if source == "GACF":
                surface_pressure = cams_pressure[0,interpolation_indices[lat_idx,lon_idx, 0].astype(int), interpolation_indices[lat_idx,lon_idx,1].astype(int)]
            else:
                surface_pressure = cams_pressure[interpolation_indices[lat_idx,lon_idx, 0].astype(int), interpolation_indices[lat_idx,lon_idx,1].astype(int)]
            cams_v_pressures = surface_pressure.data * b.astype(float) +a.astype(float)
            
	    #Get WRF levels
            wrf_v_pressures  = np.squeeze(wrf_pressure[:,lat_idx,lon_idx]); 
            for lvl_idx in range(n_vertical_levels):
                difference = np.abs(cams_v_pressures - wrf_v_pressures[lvl_idx]);
                
                #min() added as there was a case where two levels had the same difference
                cams_nearest_lvl_idx = min(np.where(difference == min(difference)))[0];

                # Find the indices of the nearest horizontal grid points for the specified longitude and latitude
                lat_idx_nearest = int(interpolation_indices[lat_idx, lon_idx, 1])
                lon_idx_nearest = int(interpolation_indices[lat_idx, lon_idx, 0])
                
               #print(np.array([cams_nearest_lvl_idx, lat_idx_nearest, lon_idx_nearest]))
                #Create a 1D NumPy array containing the indices of the nearest horizontal grid points and the nearest vertical level
                cams_indices = np.array([cams_nearest_lvl_idx, lat_idx_nearest, lon_idx_nearest])

                wrf_init_CH4_BCK[lvl_idx,lat_idx,lon_idx] = cams_ch4[cams_nearest_lvl_idx, lat_idx_nearest, lon_idx_nearest];
                #wrf_init_CO_BCK[lvl_idx,lat_idx,lon_idx]  = cams_co[cams_nearest_lvl_idx, lat_idx_nearest, lon_idx_nearest];
                #wrf_init_CO2_BCK( lon_idx, lat_idx, lvl_idx ) = cams_co2( interpolation_indices( lon_idx, lat_idx, 1), interpolation_indices( lon_idx, lat_idx, 2), cams_nearest_lvl_idx );

    print('Writing values from CAMS for CH4_BCK, CO_BCK and CO2_BCK fields of wrfinput:')
    #Write the values already:
    ncid = cdf.Dataset(wrfinput_path, 'r+')
    #ncid.variables['CO2_BCK'][0] = wrf_init_CO2_BCK
    ncid.variables['CH4_BCK'][0] = wrf_init_CH4_BCK
    #ncid.variables['CO_BCK'][0] = wrf_init_CO_BCK
    ncid.close()

print('Script completed.');
