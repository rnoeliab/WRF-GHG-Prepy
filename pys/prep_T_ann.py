#/pf/b/b301034/anaconda3/bin python

import numpy as np
import netCDF4 as cdf
import pandas as pd
import xesmf as xe
import xarray as xr
import warnings

def prep_T(wrf_geo_p,t_ann_path,t_var,regrid_method,sim_time,dom,projection_wrf,output_reg):
    print('STARTING WITH ANNUAL TEMPERATURE REGRID-PREPROCESSING')
    #wrf_i          = cdf.Dataset(wrf_inp)
    wrf_geo        = cdf.Dataset(wrf_geo_p)
    wrf_lat        = np.array(wrf_geo.variables['XLAT_M'])
    wrf_lon        = np.array(wrf_geo.variables['XLONG_M'])
    wrf_lmask      = np.array(wrf_geo.variables['LANDMASK'])
    wrf_lat_c      = np.array(wrf_geo.variables['XLAT_C'])
    wrf_lon_c      = np.array(wrf_geo.variables['XLONG_C'])

    temp_data      = cdf.Dataset(t_ann_path)
    soil_temp_avg  = np.array(temp_data.variables[t_var]).mean(axis=0)  ### AVG taken here.
    #fill_value     = -9.0000017e+33
    #soil_temp_avg[soil_temp_avg==fill_value] = 0    #
    lons_ecmwf     = np.array(temp_data.variables['longitude'])
    lats_ecmwf     = np.array(temp_data.variables['latitude']) 

    ### aqui las longitudes ya son un vector.
    #soil_temp      = np.roll(soil_temp_avg,int(soil_temp_avg.shape[2]/2),axis=2)   
    lon_res        = abs(lons_ecmwf[1]-lons_ecmwf[0])
    lat_res        = abs(lats_ecmwf[1]-lats_ecmwf[0])

    #lons_ecmwf     = np.arange(-180+lon_res/2,180,lon_res)

    srclon_cen     = lons_ecmwf
    srclat_cen     = lats_ecmwf

    #### estas lineas fueron actualizadas.
    srclat_cor  = np.linspace(lats_ecmwf[0]+lat_res/2,lats_ecmwf[-1]-lat_res/2,lats_ecmwf.shape[0]+1)
    srclon_cor  = np.arange(lons_ecmwf[0]-lon_res/2,lons_ecmwf[-1]+lon_res,lon_res)

    grid_in   = {'lon':srclon_cen,'lat':srclat_cen, 'lon_b':srclon_cor,'lat_b':srclat_cor}
    grid_out  = {'lon':wrf_lon[0],'lat':wrf_lat[0], 'lon_b':wrf_lon_c[0],'lat_b':wrf_lat_c[0]}

    regridder = xe.Regridder(grid_in,grid_out,regrid_method,reuse_weights=False)

    t_ann_re      = regridder(soil_temp_avg)  

    print('writing netcdf files')

    wrf_input     = wrf_geo
    dim_emi_items = list(wrf_input.dimensions.items())
    date          = pd.to_datetime(sim_time[0]).strftime('%Y-%m-%d')
    domain        = dom #wrf_input.getncattr('GRID_ID')
    projection    = projection_wrf #wrf_input.MAP_PROJ_CHAR
    units         = 'K'

    filename      = output_reg + 'T_ANN_d0%s_%s.nc'%(domain,pd.to_datetime(date).year)
    dataset       = cdf.Dataset(filename,'w',format='NETCDF4_CLASSIC')
    # Dimensions
    lat           = dataset.createDimension(dim_emi_items[3][0], wrf_input.getncattr('SOUTH-NORTH_PATCH_END_UNSTAG'))
    lon           = dataset.createDimension(dim_emi_items[2][0], wrf_input.getncattr('WEST-EAST_PATCH_END_UNSTAG'))
    time          = dataset.createDimension('time', 1)
    # Variables
    latitudes     = dataset.createVariable('latitude', np.double, (dim_emi_items[3][0],dim_emi_items[2][0]))
    longitudes    = dataset.createVariable('longitude', np.double, (dim_emi_items[3][0],dim_emi_items[2][0]))
    t_ann         = dataset.createVariable('T_ANN', np.double, ('time',dim_emi_items[3][0],dim_emi_items[2][0]))
    lambert       = dataset.createVariable('Lambert', 'c')
    # Attributes global
    import time
    dataset.history        = 'Created ' + time.ctime(time.time())

    # Attributes variables
    lambert.grid_mapping                  = projection 
    lambert.latitude_of_projection_origin = wrf_input.MOAD_CEN_LAT
    lambert.longitude_of_central_meridian = wrf_input.CEN_LON
    lambert.standard_parallel             = wrf_input.TRUELAT1
    t_ann.grid_mapping                    = projection
    latitudes.units                       = 'degrees_north'
    longitudes.units                      = 'degrees_east'
    t_ann.units                           = units
    # data
    latitudes[:,:]                        = np.array(wrf_input.variables['XLAT_M'])
    longitudes[:,:]                       = np.array(wrf_input.variables['XLONG_M'])
    t_ann[:,:]                            = t_ann_re

    dataset.close()

    print('DONE WITH ANNUAL TEMPERATURE REGRID-PREPROCESSING')

if __name__ == "__main__":
    # This will run if prep_T_ann.py is executed directly
    print("run if prep_T_ann.py is being run directly")
    prep_T()