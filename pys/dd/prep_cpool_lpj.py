#/pf/b/b301034/anaconda3/bin python

import numpy as np
import netCDF4 as cdf
import pandas as pd

print('STARTING WITH THE REGRID OF THE CARBON POOL BASED ON LPJ MODEL')
cpool_data  = cdf.Dataset('intermediate_cpool_regrid.nc')                              # 0.5 degrees entire world
cpool_fast  = np.array(cpool_data.variables[cpool_var]) 

wrf_i       = cdf.Dataset(wrf_geo_p)
wrf_lat     = np.array(wrf_i.variables['XLAT_M'])
wrf_lon     = np.array(wrf_i.variables['XLONG_M'])
wrf_lmask   = np.array(wrf_i.variables['LANDMASK'])

print('generating netcdf file for cpool based on wrf landmask..')

wrf_input     = wrf_i
dim_emi_items = list(wrf_input.dimensions.items())

date          = sim_time[0][0:10]
domain        = dom #wrf_input.getncattr('GRID_ID')
projection    = projection_wrf
units         = 'Kg m-2 month-1'
#filename      = cpool_out + 'cpool_fast_LPJ_cdo_d0%s_%s.nc'%(domain,date)
filename      = output_reg + 'CPOOL_d0%s_%s.nc'%(domain,pd.to_datetime(date).year)

dataset       = cdf.Dataset(filename,'w',format='NETCDF4_CLASSIC')
# Dimensions
lat           = dataset.createDimension(dim_emi_items[3][0], wrf_input.getncattr('SOUTH-NORTH_PATCH_END_UNSTAG'))
lon           = dataset.createDimension(dim_emi_items[2][0], wrf_input.getncattr('WEST-EAST_PATCH_END_UNSTAG'))
time          = dataset.createDimension('time', 1)

# Variables
latitudes     = dataset.createVariable('latitude', np.double, (dim_emi_items[3][0],dim_emi_items[2][0]))
longitudes    = dataset.createVariable('longitude', np.double, (dim_emi_items[3][0],dim_emi_items[2][0]))
cpool         = dataset.createVariable('CPOOL', np.double, ('time',dim_emi_items[3][0],dim_emi_items[2][0]))


# Attributes global
import time
dataset.description    = 'Carbon pool from LPJ. Regridded with cdo in mistral. The wrf LANDMASK is applied.'
dataset.history        = 'Created ' + time.ctime(time.time())

for i,j in enumerate(wrf_input.ncattrs()):
    if i == 0: continue
    dataset.setncattr(j,wrf_input.getncattr(j))

# Attributes variables
cpool.grid_mapping     = projection
latitudes.units        = 'degrees_north'
longitudes.units       = 'degrees_east'
cpool.units            = units

# data
latitudes[:,:]   = np.array(wrf_input.variables['XLAT_M'])
longitudes[:,:]  = np.array(wrf_input.variables['XLONG_M'])
cpool[:,:]       = (cpool_fast[0] * wrf_lmask[0]) / 1000

dataset.close()

print('DONE WITH THE REGRID OF THE CARBON POOL')