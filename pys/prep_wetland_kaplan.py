#/pf/b/b301034/anaconda3/bin python

import numpy as np
import netCDF4 as cdf
import pandas as pd
#import ESMF
import sys
sys.path.append('/pf/b/b301034/anaconda3/envs/esmpy/lib/python3.6/site-packages/')
sys.path.append('/work/mj0143/b301034/Scrapbook_Analysis/Utils/python/regrid/')
#import regridding as re
import xesmf as xe
import xarray as xr
import warnings

print('STARTING WITH WETLAND REGRID-PREPROCESSING')
wet_data    = cdf.Dataset(path_wet)                              # 0.5 degrees entire world
wetland     = np.array(wet_data.variables[wet_var][7]) 
wet_lat     = np.array(wet_data.variables[lat]) 
wet_lon     = np.array(wet_data.variables[lon]) 

#wrf_i       = cdf.Dataset(wrf_inp)
wrf_geo     = cdf.Dataset(wrf_geo_p)

wrf_lat     = np.array(wrf_geo.variables['XLAT_M'])
wrf_lon     = np.array(wrf_geo.variables['XLONG_M'])
wrf_lmask   = np.array(wrf_geo.variables['LANDMASK'])
wrf_lat_c   = np.array(wrf_geo.variables['XLAT_C'])
wrf_lon_c   = np.array(wrf_geo.variables['XLONG_C'])

fill_value     = -9999.0 
wetland[wetland==fill_value] = 0

lon_res     = abs(wet_lon[1]-wet_lon[0])
lat_res     = abs(wet_lat[1]-wet_lat[0])
srclon_cen  = wet_lon
srclat_cen  = wet_lat

# I use different methods here, this depends on how the lat and lon comes from input.
# Here the latitudes were going from north to south and the np.arange can not start from + to -
# linspace can

srclat_cor  = np.linspace(wet_lat[0]+lat_res/2,wet_lat[-1]-lat_res/2,wet_lat.shape[0]+1)
srclon_cor  = np.arange(wet_lon[0]-lon_res/2,wet_lon[-1]+lon_res,lon_res)

grid_in     = {'lon':srclon_cen,'lat':srclat_cen, 'lon_b':srclon_cor,'lat_b':srclat_cor}
grid_out    = {'lon':wrf_lon[0],'lat':wrf_lat[0], 'lon_b':wrf_lon_c[0],'lat_b':wrf_lat_c[0]}
regridder   = xe.Regridder(grid_in,grid_out,regrid_method,reuse_weights=False)
wet_re      = regridder(wetland)   

print('generating netcdf file..')

wrf_input     = wrf_geo
dim_emi_items = list(wrf_input.dimensions.items())
source        = source
date          = pd.to_datetime(sim_time[0]).strftime('%Y-%m-%d')
domain        = dom
projection    = projection_wrf
units         = 'Inundated fraction'
filename      = wet_out + 'WETMAP_d0%s_%s.nc'%(domain,pd.to_datetime(date).year)
dataset       = cdf.Dataset(filename,'w',format='NETCDF4_CLASSIC')

# Dimensions
lat           = dataset.createDimension(dim_emi_items[3][0], wrf_input.getncattr('SOUTH-NORTH_PATCH_END_UNSTAG'))
lon           = dataset.createDimension(dim_emi_items[2][0], wrf_input.getncattr('WEST-EAST_PATCH_END_UNSTAG'))
time          = dataset.createDimension('time', 1)
# Variables
latitudes     = dataset.createVariable('latitude', np.double, (dim_emi_items[3][0],dim_emi_items[2][0]))
longitudes    = dataset.createVariable('longitude', np.double, (dim_emi_items[3][0],dim_emi_items[2][0]))
wetmap        = dataset.createVariable('WETMAP', np.double, ('time',dim_emi_items[3][0],dim_emi_items[2][0]))
# Attributes global
import time
dataset.description    = 'Wetland inundated fraction from %s'%(source)
dataset.history        = 'Created ' + time.ctime(time.time())

for i,j in enumerate(wrf_input.ncattrs()):
    if i == 0: continue
    dataset.setncattr(j,wrf_input.getncattr(j))

# Attributes variables
wetmap.grid_mapping    = projection
latitudes.units        = 'degrees_north'
longitudes.units       = 'degrees_east'
wetmap.units           = units

# data
latitudes[:,:]   = np.array(wrf_input.variables['XLAT_M'])
longitudes[:,:]  = np.array(wrf_input.variables['XLONG_M'])
wetmap[:,:]      = wet_re/100   ### -- range: 0-1 values

dataset.close()
print('DONE GENERATING THE WETLAND MAP')
