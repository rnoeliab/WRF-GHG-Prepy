#/pf/b/b301034/anaconda3/bin python

import numpy as np
import netCDF4 as cdf
import pandas as pd
import xarray as xr
import xesmf as xe
import warnings

def prep_cpool(wrf_geo_p,path_cpool,cpool_var,regrid_method,sim_time,dom,projection_wrf,cpool_out):
    print('STARTING WITH WETLAND REGRID-PREPROCESSING OF THE CARBON POOL BASED ON LPJ MODEL')
    cpool_data  = cdf.Dataset(path_cpool)                           # 0.5 degrees entire world
    cpool    = np.array(cpool_data.variables[cpool_var]) 
    cpool_lat     = np.array(cpool_data.variables['lat']) 
    cpool_lon     = np.array(cpool_data.variables['lon']) 

    #wrf_i       = cdf.Dataset(wrf_inp)
    wrf_geo     = cdf.Dataset(wrf_geo_p)

    wrf_lat     = np.array(wrf_geo.variables['XLAT_M'])
    wrf_lon     = np.array(wrf_geo.variables['XLONG_M'])
    wrf_lmask   = np.array(wrf_geo.variables['LANDMASK'])
    wrf_lat_c   = np.array(wrf_geo.variables['XLAT_C'])
    wrf_lon_c   = np.array(wrf_geo.variables['XLONG_C'])

    fill_value     = -9999.0 
    cpool[cpool==fill_value] = 0

    lon_res     = abs(cpool_lon[1]-cpool_lon[0])
    lat_res     = abs(cpool_lat[1]-cpool_lat[0])
    srclon_cen  = cpool_lon
    srclat_cen  = cpool_lat

    # I use different methods here, this depends on how the lat and lon comes from input.
    # Here the latitudes were going from north to south and the np.arange can not start from + to -
    # linspace can

    srclat_cor  = np.linspace(cpool_lat[0]+lat_res/2,cpool_lat[-1]-lat_res/2,cpool_lat.shape[0]+1)
    srclon_cor  = np.arange(cpool_lon[0]-lon_res/2,cpool_lon[-1]+lon_res,lon_res)

    grid_in     = {'lon':srclon_cen,'lat':srclat_cen, 'lon_b':srclon_cor,'lat_b':srclat_cor}
    grid_out    = {'lon':wrf_lon[0],'lat':wrf_lat[0], 'lon_b':wrf_lon_c[0],'lat_b':wrf_lat_c[0]}
    regridder   = xe.Regridder(grid_in,grid_out,regrid_method,reuse_weights=False)
    cpool_re      = regridder(cpool)   

    print('generating netcdf file for cpool based on wrf landmask..')

    wrf_input     = wrf_geo
    dim_emi_items = list(wrf_input.dimensions.items())

    date          = sim_time[0][0:10]
    domain        = dom #wrf_input.getncattr('GRID_ID')
    projection    = projection_wrf
    units         = 'g m-2 month-1'
    #filename      = cpool_out + 'cpool_fast_LPJ_cdo_d0%s_%s.nc'%(domain,date)
    filename      = cpool_out + 'CPOOL_d0%s_%s.nc'%(domain,pd.to_datetime(date).year)

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
    cpool[:,:]       = (cpool_re[0] * wrf_lmask[0]) 

    dataset.close()

    print('DONE WITH THE REGRID OF THE CARBON POOL')
