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

#Setting important paths to files and directories
wrfbdy_dir_path = '../input/wrf_inputs/'
CAMS_data_dir_path   ='../input/bck_ghg/CAMS/unzips/'
CAMS_interpolation_indices_file_path = '../input/bck_ghg/interp_indices.txt.npz'
IFS_L137_ab_file  = '../input/bck_ghg/ecmwf_coeffs_L137.csv'

requested_domains = [ "d01", "d02","d03","d04"]
sim_time       = '2022-08-01 00:00:00','2022-08-15 23:00:00'       # check this!!

dates          = pd.to_datetime(sim_time[0]).strftime('%Y-%m-%d')
year            = pd.to_datetime(sim_time[0]).strftime('%Y')
month           = pd.to_datetime(sim_time[0]).strftime('%m')
day             = pd.to_datetime(sim_time[0]).strftime('%d')

#Prepare wrfbdy parameters shapes
wrfbdy_path = os.path.join(wrfbdy_dir_path,'wrfbdy_d01')
wrfbdy = xr.open_dataset(wrfbdy_path);

#simstart and simend times will be calculated from Times vector element available in wrfbdy_d01
# Define the initial boundary date and interval in hours
boundary_dates = [datetime.strptime(d.decode("utf-8"), '%Y-%m-%d_%H:%M:%S') for d in wrfbdy['Times'].values]  ## UTC 

bdy_interval_seconds = (boundary_dates[1] - boundary_dates[0]).total_seconds()
bdy_interval_hours = bdy_interval_seconds / 3600

boundary_dates.append(boundary_dates[-1] + timedelta(hours=bdy_interval_hours))   #### add a time
boundary_date = [d.strftime("%Y%m%d") for d in boundary_dates ]

simstart_time = boundary_date[0]
simend_time = boundary_date[-1]

# In case manual setup is needed, execute the following lines:
# Frequency of the boundary is set in WRF namelist.input
# as interval_seconds in the &time_control section
# This value must be equal to that one.
# bdy_interval_seconds = 10800;

# To each boundary date, assign a CAMS filename from which it will be read from:
CAMS_ml_filenames  = [os.path.join(CAMS_data_dir_path+'CAMS_GACF_large_co_ch4_'+d+'.nc') for d in boundary_date]
CAMS_lnsp_filenames = [os.path.join(CAMS_data_dir_path+'CAMS_GACF_large_co_ch4_'+d+'.nc') for d in boundary_date]

# If CAMS product also comes with the a, b coefficients.
##Am = double( ncread( CAMS_ml_filenames( 1, : ), 'hyam' ) );
##Bm = double( ncread( CAMS_ml_filenames( 1, : ), 'hybm' ) );

# Pressures are not available in the wrfbdy_d01 - only perturbation
# geopotential. Will use pressures from wrfinput, with the assumption
# that they do not change (close enough).

wrfinput_path = os.path.join(wrfbdy_dir_path, 'wrfinput_d01')
##wrfinput_path = sprintf( '%swrfinput_d01_%4d-%02d-%02d', realoutput_path, year ,month, day );
print('Reading WRF pressures for d01')

wrf_pressure = xr.open_dataset(wrfinput_path)['PB'].values[0] + xr.open_dataset(wrfinput_path)['P'].values[0];
      
# Important: boundaries are defined for each tracer with the
# suffix added to the variable name. Suffix codes are:
# _BXS, _BXE, BYS, BYE, denoting 'Boundary X Start',
# 'Boundary X-End', and similar for Y.
# Note that BXS means the WEST boundary (left?), and not south/bottom.
# Dimensions order is not obvious, be careful with that:
# Order: [N_WE] (or SN), [N_VERT_LVLS], [N_BOUNDARY_POINTS = 5 usually] and [TIME]

# Creating two dummy arrays that will be used as templates,
# one for WE boundaries and one for NS, as
# these have different sizes.
dummy_3d_scalar_field = np.zeros((xr.open_dataset(wrfinput_path)['CO2_BIO'][0].shape)) + (-999.)
dummy_4d_X_scalar_field = np.zeros((xr.open_dataset(wrfbdy_path)['CO2_BIO_BXS'].shape)) + (-999.)  ### (bdy_width: 5,bottom_top: 50,south_north: 160)
dummy_4d_Y_scalar_field = np.zeros((xr.open_dataset(wrfbdy_path)['CO2_BIO_BYS'].shape)) + (-999.)  ### (bdy_width: 5,bottom_top: 50,west_east: 347)

n_vertical_levels = dummy_4d_X_scalar_field.shape[2]
n_sn = dummy_4d_X_scalar_field.shape[3]
n_ew = dummy_4d_Y_scalar_field .shape[3]

# Start with something simple: assign offsets for biogenic tracers
# for WRF-GHG:
ncid = cdf.Dataset(wrfbdy_path, 'r+')
co2_bio_offset_ppm = 400
ncid.variables['CO2_BIO_BXS'][:] = co2_bio_offset_ppm * np.ones(dummy_4d_X_scalar_field.shape)
ncid.variables['CO2_BIO_BXE'][:] = co2_bio_offset_ppm * np.ones(dummy_4d_X_scalar_field.shape)
ncid.variables['CO2_BIO_BYS'][:] = co2_bio_offset_ppm * np.ones(dummy_4d_Y_scalar_field.shape)
ncid.variables['CO2_BIO_BYE'][:] = co2_bio_offset_ppm * np.ones(dummy_4d_Y_scalar_field.shape)

ch4_bio_offset_ppm = 1.8
ncid.variables['CH4_BIO_BXS'][:] = co2_bio_offset_ppm * np.ones(dummy_4d_X_scalar_field.shape)
ncid.variables['CH4_BIO_BXE'][:] = co2_bio_offset_ppm * np.ones(dummy_4d_X_scalar_field.shape)
ncid.variables['CH4_BIO_BYS'][:] = co2_bio_offset_ppm * np.ones(dummy_4d_Y_scalar_field.shape)
ncid.variables['CH4_BIO_BYE'][:] = co2_bio_offset_ppm * np.ones(dummy_4d_Y_scalar_field.shape)
ncid.close()

# Next step is to fill the background fields using CAMS product values
# Precalculated interpolation indices will be needed
print("Loading in the pre-calculated nearest-neighbour interpolation indices.")
interpolation_indices = np.load(CAMS_interpolation_indices_file_path)['cams_indices_d01']

#Reading a and b parameters from the model config L137
rawin=np.genfromtxt(IFS_L137_ab_file,delimiter=",",skip_header=1,dtype='<U25', encoding=None)
a = rawin[:, 1] 
b = rawin[:, 2]

# Output fields need to be initialized
# NOTE: Initialization gives TOO SMALL time dimension (by 1)
# This will be expanded without warning or notice in the bck loop
# too later calculate tendencies
co2_bck_bxs = dummy_4d_X_scalar_field.copy()
co2_bck_bxe = dummy_4d_X_scalar_field.copy()
co2_bck_bys = dummy_4d_Y_scalar_field.copy()
co2_bck_bye = dummy_4d_Y_scalar_field.copy()

co2_bck_btxs = 0*dummy_4d_X_scalar_field.copy()
co2_bck_btxe = 0*dummy_4d_X_scalar_field.copy()
co2_bck_btys = 0*dummy_4d_Y_scalar_field.copy()
co2_bck_btye = 0*dummy_4d_Y_scalar_field.copy()

ch4_bck_bxs = dummy_4d_X_scalar_field.copy()
ch4_bck_bxe = dummy_4d_X_scalar_field.copy()
ch4_bck_bys = dummy_4d_Y_scalar_field.copy()
ch4_bck_bye = dummy_4d_Y_scalar_field.copy()

ch4_bck_btxs = 0*dummy_4d_X_scalar_field.copy()
ch4_bck_btxe = 0*dummy_4d_X_scalar_field.copy()
ch4_bck_btys = 0*dummy_4d_Y_scalar_field.copy()
ch4_bck_btye = 0*dummy_4d_Y_scalar_field.copy()

co_bck_bxs = dummy_4d_X_scalar_field.copy()
co_bck_bxe = dummy_4d_X_scalar_field.copy()
co_bck_bys = dummy_4d_Y_scalar_field.copy()
co_bck_bye = dummy_4d_Y_scalar_field.copy()

co_bck_btxs = 0*dummy_4d_X_scalar_field.copy()
co_bck_btxe = 0*dummy_4d_X_scalar_field.copy()
co_bck_btys = 0*dummy_4d_Y_scalar_field.copy()
co_bck_btye = 0*dummy_4d_Y_scalar_field.copy()

# David:
# Indicator of 25 elements, from wrf time 00:00 ~ 23:00 (current day) + 00:00 (next day) => 25 timesteps
# indicating which wrf_time_idx should fill in with which CAMS_time_idx
#MA = [1,1,1,2,2,2,3,3,3,4,4,4,5,5,5,6,6,6,7,7,7,8,8,8,9];	# <- David: Handing hourly wrfbdy files from 3-hourly CAMS
#MA = [0, 0, 1, 1, 2, 2, 3, 3, 0]   				     	# <- David: Handing 3-hourly wrfbdy files from 6-hourly CAMS
#MA = [0, 1, 2, 3, 0]       

for time_idx in range(len(boundary_dates)):
    current_time = boundary_dates[time_idx]
    # Read CAMS files: ml and lnsp:
    path_CAMS_ml_file = CAMS_ml_filenames[time_idx]
    path_CAMS_lnsp_file = CAMS_lnsp_filenames[time_idx]

    # Read times from CAMS ml file
    # Times are given as hours since 1900-01-01 00:00:00 UTC
    cams_times = xr.open_dataset(path_CAMS_ml_file)['time']
    cams_dates = pd.to_datetime(cams_times).strftime("%Y-%m-%d %H:%M:%S")

    #Check if one of the times is the same as current time:
    posw = int(time.mktime(current_time.timetuple()))
    posc = [int(time.mktime(pd.to_datetime(d).timetuple())) for d in cams_times.values]

    reading_from  = path_CAMS_ml_file
    cams_time_idx = posc.index(posw) if posw in posc else None

    # Now read appripriate CAMS fields, but only for the selected time.
    cams_ch4 = cdf.Dataset(path_CAMS_ml_file,'r').variables['ch4_c'][cams_time_idx,:,:,:]*(28.97/16.01)*1e6;   # (lev,lat,lon)  == (137, 451, 900)
    cams_co  = cdf.Dataset(path_CAMS_ml_file,'r').variables['co'][cams_time_idx,:,:,:]*(28.97/28.01)*1e6;
    #cams_co2 = ncread( path_CAMS_ml_file, 'co2', nc_start_vector, nc_count_vector  ) * (28.97/44.01)*1e6;

    # Read surface pressure for current time
    nc_file = cdf.Dataset(path_CAMS_lnsp_file, 'r') 
    cams_lnsp = nc_file.variables['lnsp'][cams_time_idx,:,:,:]    ## (time, level, latitude, longitude)
    cams_pressure = np.exp(cams_lnsp);

    # Dummy background fields:
    wrf_init_CH4_BCK =  np.zeros(dummy_3d_scalar_field.shape) + (-999.)
    wrf_init_CO_BCK =  np.zeros(dummy_3d_scalar_field.shape) + (-999.)

    #Proceed to read the coordinates for each respective boundary
    # It's actually simpler to assign values after interpolating to the
    # whole domain. Not strictly speaking necessary, but works, so...

    # Version 2: Doing bands separately:
    # First: WEST and EAST boundaries (X)

    for lvl_idx in range(n_vertical_levels):
        print(f'YS & YE (BOTTOM and TOP), lvl {lvl_idx+1}/{n_vertical_levels}')
        for lat_idx in [i for i in range(5)] + [i for i in range(n_sn-5, n_sn)]:
            for lon_idx in range(n_ew):
                # Get CAMS surface pressure
                lat_idx_nearest = int(interpolation_indices[lat_idx, lon_idx, 1])
                lon_idx_nearest = int(interpolation_indices[lat_idx, lon_idx, 0])
                surface_pressure = cams_pressure[0,lat_idx_nearest, lon_idx_nearest]
                
                # Calculate CAMS vertical pressures for the available levels
                cams_v_pressures = surface_pressure.data * b.astype(float) +a.astype(float)

                # Get WRF levels
                wrf_v_pressures  = np.squeeze(wrf_pressure[:,lat_idx,lon_idx]); 
                # Find the nearest pressure level in CAMS for each WRF level
                difference = np.abs(cams_v_pressures - wrf_v_pressures[lvl_idx]);
                cams_nearest_lvl_idx = min(np.where(difference == min(difference)))[0];
                
                cams_indices = np.array([lon_idx_nearest, lat_idx_nearest,cams_nearest_lvl_idx])

                wrf_init_CH4_BCK[lvl_idx,lat_idx,lon_idx] = cams_ch4[cams_indices[2], cams_indices[1], cams_indices[0]];
                wrf_init_CO_BCK[lvl_idx,lat_idx,lon_idx]  = cams_co[cams_indices[2], cams_indices[1], cams_indices[0]];

    for lvl_idx in range(n_vertical_levels):
        print(f'XS and XE (LEFT and RIGHT), lvl {lvl_idx+1}/{n_vertical_levels}')
        for lon_idx in [i for i in range(5)] + [i for i in range(n_ew-5, n_ew)]:
            for lat_idx in range(n_sn):

                # Get CAMS surface pressure
                lat_idx_nearest = int(interpolation_indices[lat_idx, lon_idx, 1])
                lon_idx_nearest = int(interpolation_indices[lat_idx, lon_idx, 0])
                surface_pressure = cams_pressure[:,lat_idx_nearest, lon_idx_nearest]

                # Calculate CAMS vertical pressures for the available levels
                cams_v_pressures = surface_pressure.data * b.astype(float) +a.astype(float)

                # Get WRF levels
                wrf_v_pressures  = np.squeeze(wrf_pressure[:,lat_idx,lon_idx]); 
                # Find the nearest pressure level in CAMS for each WRF level
                difference = np.abs(cams_v_pressures - wrf_v_pressures[lvl_idx]);
                cams_nearest_lvl_idx = min(np.where(difference == min(difference)))[0];
                
                cams_indices = np.array([lon_idx_nearest, lat_idx_nearest,cams_nearest_lvl_idx])

                # Assign appropriate values to the boundaries
                wrf_init_CH4_BCK[lvl_idx,lat_idx,lon_idx] = cams_ch4[cams_indices[2], cams_indices[1], cams_indices[0]];
                wrf_init_CO_BCK[lvl_idx,lat_idx,lon_idx]  = cams_co[cams_indices[2], cams_indices[1], cams_indices[0]];

    if time_idx < len(boundary_dates)-1:
        # Full fields now interpolated.
        # Now need to save into respective boundary objects:
        ##  co2_bck_bxs( :, :, :, time_idx ) = permute( wrf_init_CO2_BCK(     1:5  ,      :   , : ), [2 3 1] );
        ##  co2_bck_bxe( :, :, :, time_idx ) = permute( wrf_init_CO2_BCK( end-4:end,      :   , : ), [2 3 1] );
        ##  co2_bck_bys( :, :, :, time_idx ) = permute( wrf_init_CO2_BCK(      :   ,     1:5  , : ), [1 3 2] );
        ##  co2_bck_bye( :, :, :, time_idx ) = permute( wrf_init_CO2_BCK(      :   , end-4:end, : ), [1 3 2] );

        ch4_bck_bxs[time_idx,:,:,:] = np.transpose(wrf_init_CH4_BCK[:,:,0:5], axes=(2, 0, 1))
        ch4_bck_bxe[time_idx,:,:,:] = np.transpose(wrf_init_CH4_BCK[:,:,-5:], axes=(2, 0, 1))
        ch4_bck_bys[time_idx,:,:,:] = np.transpose(wrf_init_CH4_BCK[:,0:5,:], axes=(1, 0, 2))
        ch4_bck_bye[time_idx,:,:,:] = np.transpose(wrf_init_CH4_BCK[:,-5:,:], axes=(1, 0, 2))
        
        co_bck_bxs[time_idx,:,:,:] = np.transpose(wrf_init_CO_BCK[:,:,0:5], axes=(2, 0, 1))
        co_bck_bxe[time_idx,:,:,:] = np.transpose(wrf_init_CO_BCK[:,:,-5:], axes=(2, 0, 1))
        co_bck_bys[time_idx,:,:,:] = np.transpose(wrf_init_CO_BCK[:,0:5,:], axes=(1, 0, 2))
        co_bck_bye[time_idx,:,:,:] = np.transpose(wrf_init_CO_BCK[:,-5:,:], axes=(1, 0, 2))
    else:
        ch4_bck_bxs = np.insert(ch4_bck_bxs, ch4_bck_bxs.shape[0], np.transpose(wrf_init_CH4_BCK[:,:,0:5], axes=(2, 0, 1)), 0)
        ch4_bck_bxe = np.insert(ch4_bck_bxe, ch4_bck_bxe.shape[0], np.transpose(wrf_init_CH4_BCK[:,:,-5:], axes=(2, 0, 1)), 0)
        ch4_bck_bys = np.insert(ch4_bck_bys, ch4_bck_bys.shape[0], np.transpose(wrf_init_CH4_BCK[:,0:5,:], axes=(1, 0, 2)), 0)
        ch4_bck_bye = np.insert(ch4_bck_bye, ch4_bck_bye.shape[0], np.transpose(wrf_init_CH4_BCK[:,-5:,:], axes=(1, 0, 2)), 0)


        co_bck_bxs = np.insert(co_bck_bxs, co_bck_bxs.shape[0], np.transpose(wrf_init_CO_BCK[:,:,0:5], axes=(2, 0, 1)), 0)
        co_bck_bxe = np.insert(co_bck_bxe, co_bck_bxe.shape[0], np.transpose(wrf_init_CO_BCK[:,:,-5:], axes=(2, 0, 1)), 0)
        co_bck_bys = np.insert(co_bck_bys, co_bck_bys.shape[0], np.transpose(wrf_init_CO_BCK[:,0:5,:], axes=(1, 0, 2)), 0)
        co_bck_bye = np.insert(co_bck_bye, co_bck_bye.shape[0], np.transpose(wrf_init_CO_BCK[:,-5:,:], axes=(1, 0, 2)), 0)

## Added by David Ho : linear interpolation and overwrite the missing timesteps
print("Begin linear interpolation for missing timesteps")
tmax_idx = len(boundary_dates)  # 9
boundary_dates = [d.strftime('%Y-%m-%d %H:%M:%S') for d in boundary_dates ]

for time_miss in range(0,tmax_idx-1, 2):
    print(f"overwriting {boundary_dates[time_miss]} with ({boundary_dates[time_miss+1]} + {boundary_dates[time_miss-1]})/2")

    ch4_bck_bxs[time_miss,:, :, :] = (ch4_bck_bxs[time_miss+1,:,:,:] + ch4_bck_bxs[time_miss-1,:,:,:])/2
    ch4_bck_bxe[time_miss,:, :, :] = (ch4_bck_bxe[time_miss+1,:,:,:] + ch4_bck_bxe[time_miss-1,:,:,:])/2
    ch4_bck_bys[time_miss,:, :, :] = (ch4_bck_bys[time_miss+1,:,:,:] + ch4_bck_bys[time_miss-1,:,:,:])/2
    ch4_bck_bye[time_miss,:, :, :] = (ch4_bck_bye[time_miss+1,:,:,:] + ch4_bck_bye[time_miss-1,:,:,:])/2

    co_bck_bxs[time_miss,:, :, :] = (co_bck_bxs[time_miss+1,:,:,:] + co_bck_bxs[time_miss-1,:,:,:])/2
    co_bck_bxe[time_miss,:, :, :] = (co_bck_bxe[time_miss+1,:,:,:] + co_bck_bxe[time_miss-1,:,:,:])/2
    co_bck_bys[time_miss,:, :, :] = (co_bck_bys[time_miss+1,:,:,:] + co_bck_bys[time_miss-1,:,:,:])/2
    co_bck_bye[time_miss,:, :, :] = (co_bck_bye[time_miss+1,:,:,:] + co_bck_bye[time_miss-1,:,:,:])/2

# Tendencies can be run separately.
# Here, using slightly modified code from Julia M.
tmax_idx = len(boundary_dates)
print('Assigning tendencies')

for time_idx in range(tmax_idx-1):
    # Separately for EAST and WEST (X)
    for x in range(n_sn):
        for lvl_idx in range(n_vertical_levels):
            for y in range(co2_bck_bxs.shape[1]):  # Usually 5

                ch4_bck_btxs[time_idx,y,lvl_idx,x] = (ch4_bck_bxs[time_idx+1,y,lvl_idx,x] - ch4_bck_bxs[time_idx,y,lvl_idx,x])/bdy_interval_seconds
                co_bck_btxs[time_idx,y,lvl_idx,x]  = (co_bck_bxs[time_idx+1,y,lvl_idx,x] - co_bck_bxs[time_idx,y,lvl_idx,x])/bdy_interval_seconds

                ch4_bck_btxe[time_idx,y,lvl_idx,x] = (ch4_bck_bxe[time_idx+1,y,lvl_idx,x] - ch4_bck_bxe[time_idx,y,lvl_idx,x])/bdy_interval_seconds
                co_bck_btxe[time_idx,y,lvl_idx,x]  = (co_bck_bxe[time_idx+1,y,lvl_idx,x] - co_bck_bxe[time_idx,y,lvl_idx,x])/bdy_interval_seconds


    for x in range(n_ew):
        for lvl_idx in range(n_vertical_levels):
            for y in range(co2_bck_bys.shape[1]):  # Usually 5

                ch4_bck_btys[time_idx,y,lvl_idx,x] = (ch4_bck_bys[time_idx+1,y,lvl_idx,x] - ch4_bck_bys[time_idx,y,lvl_idx,x])/bdy_interval_seconds
                co_bck_btys[time_idx,y,lvl_idx,x]  = (co_bck_bys[time_idx+1,y,lvl_idx,x] - co_bck_bys[time_idx,y,lvl_idx,x])/bdy_interval_seconds

                ch4_bck_btye[time_idx,y,lvl_idx,x] = (ch4_bck_bye[time_idx+1,y,lvl_idx,x] - ch4_bck_bye[time_idx,y,lvl_idx,x])/bdy_interval_seconds
                co_bck_btye[time_idx,y,lvl_idx,x]  = (co_bck_bye[time_idx+1,y,lvl_idx,x] - co_bck_bye[time_idx,y,lvl_idx,x])/bdy_interval_seconds

# Diagnostics:
#max(reshape(ch4_bck_bxs,[],1));
#min(reshape(ch4_bck_bxs,[],1)); # min shoulnd NOT be -999

# Finally, write everything out into wrfbdy_d01
print('Writing boundary fields into wrfbdy_d01 (CO2_BCK_BXS, CO2_BCK_BXE, etc.)')

# NOTE:
# Dimension of XXX_bck_bxs objects has been artificially expanded for times
# to calculate tendencies easily (loop above). Now the extra dimension is not
# needed anymore!
##ncwrite( wrfbdy_path, 'CO2_BCK_BXS', co2_bck_bxs( :, :, :, 1:(end-1) ) );
##ncwrite( wrfbdy_path, 'CO2_BCK_BXE', co2_bck_bxe( :, :, :, 1:(end-1) ) );
##ncwrite( wrfbdy_path, 'CO2_BCK_BYS', co2_bck_bys( :, :, :, 1:(end-1) ) );
##ncwrite( wrfbdy_path, 'CO2_BCK_BYE', co2_bck_bye( :, :, :, 1:(end-1) ) );

ncid = cdf.Dataset(wrfbdy_path, 'r+')

ncid.variables['CH4_BCK_BXS'][:] = ch4_bck_bxs[0:tmax_idx-1,:,:,:]
ncid.variables['CH4_BCK_BXE'][:] = ch4_bck_bxe[0:tmax_idx-1,:,:,:]
ncid.variables['CH4_BCK_BYS'][:] = ch4_bck_bys[0:tmax_idx-1,:,:,:]
ncid.variables['CH4_BCK_BYE'][:] = ch4_bck_bye[0:tmax_idx-1,:,:,:]

ncid.variables['CO_BCK_BXS'][:] = co_bck_bxs[0:tmax_idx-1,:,:,:]
ncid.variables['CO_BCK_BXE'][:] = co_bck_bxe[0:tmax_idx-1,:,:,:]
ncid.variables['CO_BCK_BYS'][:] = co_bck_bys[0:tmax_idx-1,:,:,:]
ncid.variables['CO_BCK_BYE'][:] = co_bck_bye[0:tmax_idx-1,:,:,:]

print('Writing boundary tendency fields into wrfbdy_d01 (CO2_BCK_BTXS, CO2_BCK_BTXE, etc.)')

ncid.variables['CH4_BCK_BTXS'][:] = ch4_bck_btxs
ncid.variables['CH4_BCK_BTXE'][:] = ch4_bck_btxe
ncid.variables['CH4_BCK_BTYS'][:] = ch4_bck_btys
ncid.variables['CH4_BCK_BTYE'][:] = ch4_bck_btye

ncid.variables['CO_BCK_BTXS'][:] = co_bck_btxs
ncid.variables['CO_BCK_BTXE'][:] = co_bck_btxe
ncid.variables['CO_BCK_BTYS'][:] = co_bck_btys
ncid.variables['CO_BCK_BTYE'][:] = co_bck_btye

ncid.close()
print('Script completed.')
