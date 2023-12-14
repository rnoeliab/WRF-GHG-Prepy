import numpy as np
import netCDF4 as cdf
import pandas as pd
import xesmf as xe
import xarray as xr
import warnings

print('STARTING WITH GHG fire emissions REGRID-PREPROCESSING')
wrf_i          = cdf.Dataset(wrf_inp_p)
wrf_geo        = cdf.Dataset(wrf_geo_p)
wrf_lat        = np.array(wrf_geo.variables['XLAT_M'])
wrf_lon        = np.array(wrf_geo.variables['XLONG_M'])
wrf_lmask      = np.array(wrf_geo.variables['LANDMASK'])
wrf_lat_c      = np.array(wrf_geo.variables['XLAT_C'])
wrf_lon_c      = np.array(wrf_geo.variables['XLONG_C'])

gfas_open      = cdf.Dataset(gfas_path)

gfas_data = {}; gfas_name = {}
for v,pol in enumerate(var):  
    gfas_data[str(pol)]  =  np.array(gfas_open.variables[var[0]])*36*(10**11)/float(mvar[v]) 
    gfas_name[str(pol)]  =  gfas_open.variables[var[0]].long_name
    
    gfas_data[str(pol)][gfas_data[str(pol)]<=0] = 0

lons_ecmwf     = np.array(gfas_open.variables[lon])
lats_ecmwf     = np.array(gfas_open.variables[lat]) 

### aqui las longitudes ya son un vector.
#soil_temp      = np.roll(soil_temp_avg,int(soil_temp_avg.shape[2]/2),axis=2)   
lon_res        = abs(lons_ecmwf[1]-lons_ecmwf[0])
lat_res        = abs(lats_ecmwf[1]-lats_ecmwf[0])

lons_ecmwf     = np.arange(-180+lon_res/2,180,lon_res)

srclon_cen     = lons_ecmwf
srclat_cen     = lats_ecmwf

#### estas lineas fueron actualizadas.
srclat_cor  = np.linspace(lats_ecmwf[0]+lat_res/2,lats_ecmwf[-1]-lat_res/2,lats_ecmwf.shape[0]+1)
srclon_cor  = np.arange(lons_ecmwf[0]-lon_res/2,lons_ecmwf[-1]+lon_res,lon_res)

grid_in   = {'lon':srclon_cen,'lat':srclat_cen, 'lon_b':srclon_cor,'lat_b':srclat_cor}
grid_out  = {'lon':wrf_lon[0],'lat':wrf_lat[0], 'lon_b':wrf_lon_c[0],'lat_b':wrf_lat_c[0]}

regridder = xe.Regridder(grid_in,grid_out,regrid_method,reuse_weights=False)

gfas_data_re = {};
for v,pol in enumerate(var):
    gfas_data_re[str(pol)]  = regridder(gfas_data[str(pol)])  


print('generating netcdf file..')
wrf_input     = wrf_geo
dim_emi_items = list(wrf_input.dimensions.items())
domain        = dom
projection    = projection_wrf

bytime        = pd.date_range("2022-08-01", freq="D", periods=31)
nhoras        = ["{:02d}".format(n) for n in np.arange(0,24,1)]
for q,m in enumerate(bytime):
    for d in nhoras:
        date          = pd.to_datetime(m).strftime('%Y-%m-%d')+ '_'+d+':00:00'
        filename      = gfas_out + 'wrffirechemi_d0%s_%s'%(dom,str(date).replace(":","_"))
        dataset       = cdf.Dataset(filename,'w',format='NETCDF3_CLASSIC')

        # Dimensions
        len           = dataset.createDimension('DateStrLen',19)
        time          = dataset.createDimension('Time', 1)
        lon           = dataset.createDimension(dim_emi_items[2][0], wrf_input.getncattr('WEST-EAST_PATCH_END_UNSTAG'))
        lat           = dataset.createDimension(dim_emi_items[3][0], wrf_input.getncattr('SOUTH-NORTH_PATCH_END_UNSTAG'))
        levels        = dataset.createDimension('emissions_zdim_stag',1)

        # Variables
        time          = dataset.createVariable('Times', 'S1',('Time','DateStrLen'))
        #lat           = dataset.createVariable('south_north', np.double, (dim_emi_items[3][0],dim_emi_items[2][0]))
        #lon           = dataset.createVariable('west_east', np.double, (dim_emi_items[3][0],dim_emi_items[2][0]))
        cof           = dataset.createVariable('ebu_in_co', np.double, ('Time','emissions_zdim_stag',dim_emi_items[3][0],dim_emi_items[2][0]))
        co2f          = dataset.createVariable('ebu_in_co2', np.double, ('Time','emissions_zdim_stag',dim_emi_items[3][0],dim_emi_items[2][0]))
        ch4f          = dataset.createVariable('ebu_in_ch4', np.double, ('Time','emissions_zdim_stag',dim_emi_items[3][0],dim_emi_items[2][0]))
        
        # data
        time[:,:]     = np.array([" ".join(date).split()], dtype = 'S19')
        co2f[:,:]     = gfas_data_re['co2fire'][q]
        cof[:,:]      = gfas_data_re['cofire'][q]
        ch4f[:,:]     = gfas_data_re['ch4fire'][q]
        #lat[:,:]      = np.array(wrf_input.variables['XLAT_M'])
        #lon[:,:]      = np.array(wrf_input.variables['XLONG_M'])

        # Attributes global
        for i,j in enumerate(wrf_i.ncattrs()):
            if i == 0: continue
            dataset.setncattr(j,wrf_i.getncattr(j))

        # Attributes variables
        co2f.long_name    = gfas_name['co2fire']
        co2f.FieldType    = 104
        co2f.MemoryOrder  = 'XYZ'
        co2f.units        = 'mol km^-2 hr^⁻1'
        co2f.description  = 'GFAS Biomass burning Emissions'
        co2f.stagger      = 'Z'
        co2f.coordinates  = 'XLONG XLAT'

        cof.long_name     = gfas_name['cofire']
        cof.FieldType     = 104
        cof.MemoryOrder   = 'XYZ'
        cof.units         = 'mol km^-2 hr^⁻1'
        cof.description   = 'GFAS Biomass burning Emissions'
        cof.stagger       = 'Z'
        cof.coordinates   = 'XLONG XLAT'

        ch4f.long_name    = gfas_name['ch4fire']
        ch4f.FieldType    = 104
        ch4f.MemoryOrder  = 'XYZ'
        ch4f.units        = 'mol km^-2 hr^⁻1'
        ch4f.description  = 'GFAS Biomass burning Emissions'
        ch4f.stagger      = 'Z'
        ch4f.coordinates  = 'XLONG XLAT'
        
        dataset.close()

print('DONE WITH GHG fire emissions REGRID-PREPROCESSING')

# aqui se adiciono para evitar valores negativos
