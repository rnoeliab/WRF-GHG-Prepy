import numpy as np
import netCDF4 as cdf
import pandas as pd
import xesmf as xe
import xarray as xr
import warnings, glob
import time

def anthr(wrf_geo_p,wrf_inp_p,wchts_path,num_model,mvar,edgar_path,var,regrid_method,sim_time,dom,projection_wrf,output_reg):
    print('STARTING WITH WETCHARTS AND EDGAR GHG emissions REGRID-PREPROCESSING')
    wrf_i          = cdf.Dataset(wrf_inp_p)
    wrf_geo        = cdf.Dataset(wrf_geo_p)
    wrf_lat        = np.array(wrf_geo.variables['XLAT_M'])
    wrf_lon        = np.array(wrf_geo.variables['XLONG_M'])
    wrf_lmask      = np.array(wrf_geo.variables['LANDMASK'])
    wrf_lat_c      = np.array(wrf_geo.variables['XLAT_C'])
    wrf_lon_c      = np.array(wrf_geo.variables['XLONG_C'])

    month           = int(pd.to_datetime(sim_time[0]).strftime('%m'))
    ################### wetcharts  data --- convert umol/m2s to mol/km2h
    wchts_data = {}
    for nm in num_model:
        files = sorted(glob.glob(wchts_path+'wchts_v1-3-1_model_'+str(nm)+'_global*.nc'))
        means = []
        for f in files:
            wchts_open = cdf.Dataset(f)
            data = np.array(wchts_open.variables['emission'][month-1])
            data[data<=0] = 0
            data[np.isnan(data)] = 0
            means.append(data)
        wchts_data[nm] = np.mean(means, axis=0)
        wchts_data[nm] = wchts_data[nm]*36

    lons_wchts   = np.array(wchts_open.variables['lon'])
    lats_wchts   = np.array(wchts_open.variables['lat'])

    ### aqui las longitudes ya son un vector.
    lon_res        = abs(lons_wchts[1]-lons_wchts[0])
    lat_res        = abs(lats_wchts[1]-lats_wchts[0])

    srclon_cen     = lons_wchts
    srclat_cen     = lats_wchts

    #### estas lineas fueron actualizadas.
    srclat_cor  = np.linspace(lats_wchts[0]+lat_res/2,lats_wchts[-1]-lat_res/2,lats_wchts.shape[0]+1)
    srclon_cor  = np.arange(lons_wchts[0]-lon_res/2,lons_wchts[-1]+lon_res,lon_res)

    grid_in   = {'lon':srclon_cen,'lat':srclat_cen, 'lon_b':srclon_cor,'lat_b':srclat_cor}
    grid_out  = {'lon':wrf_lon[0],'lat':wrf_lat[0], 'lon_b':wrf_lon_c[0],'lat_b':wrf_lat_c[0]}

    regridder = xe.Regridder(grid_in,grid_out,regrid_method,reuse_weights=False)

    wchts_data_re = {};
    for nm in num_model:
        wchts_data_re[str(nm)]  = regridder(wchts_data[str(nm)])  

    ###################################################################################################
    ################# EDGAR data
    edgar_data = {}; edgar_units = {}
    for v,pol in enumerate(var):
        edgar_open            = xr.open_dataset(edgar_path+'v6.0_'+var[v]+'_TOTAL_NO_FIRES_2018.0.1x0.1.nc')
        edgar_open['lon_adj'] = xr.where(edgar_open['lon']> 180, edgar_open['lon'] - 360, edgar_open['lon'])
        edgar_open            = edgar_open.sortby(edgar_open["lon_adj"])
        
        edgar_data[str(pol)]  = np.array(edgar_open['emis_tot'][month-1,:,:])*36*(10**11)/float(mvar[v]) 
        edgar_units[str(pol)] = edgar_open['emis_tot'].units
        
        lons_edgar     = np.array(edgar_open['lon_adj'])
        lats_edgar     = np.array(edgar_open['lat'])

    ##### referencia PRE-CHEM
    temp_fact_utc = [0.052, 0.045, 0.035, 0.026, 0.018, 0.015, 0.020, 0.025, 
                    0.031, 0.036, 0.041, 0.045, 0.048, 0.050, 0.050, 0.049,
                    0.047, 0.047, 0.048, 0.050, 0.053, 0.056, 0.058, 0.056]

    ### aqui las longitudes ya son un vector.
    lon_res        = abs(lons_edgar[1]-lons_edgar[0])
    lat_res        = abs(lats_edgar[1]-lats_edgar[0])

    srclon_cen     = lons_edgar
    srclat_cen     = lats_edgar

    #### estas lineas fueron actualizadas.
    srclat_cor  = np.linspace(lats_edgar[0]+lat_res/2,lats_edgar[-1]-lat_res/2,lats_edgar.shape[0]+1)
    srclon_cor  = np.arange(lons_edgar[0]-lon_res/2,lons_edgar[-1]+lon_res,lon_res)

    grid_in   = {'lon':srclon_cen,'lat':srclat_cen, 'lon_b':srclon_cor,'lat_b':srclat_cor}
    grid_out  = {'lon':wrf_lon[0],'lat':wrf_lat[0], 'lon_b':wrf_lon_c[0],'lat_b':wrf_lat_c[0]}


    regridder = xe.Regridder(grid_in,grid_out,regrid_method,reuse_weights=False)

    edgar_data_re = {};
    for v,pol in enumerate(var):
        edgar_data_re[str(pol)]  = regridder(edgar_data[str(pol)])  
        
    print('generating netcdf file..')
    wrf_input     = wrf_geo
    dim_emi_items = list(wrf_input.dimensions.items())
    domain        = dom
    projection    = projection_wrf

    dates         = pd.to_datetime(sim_time[0]).strftime('%Y-%m-%d')
    bytime        = pd.date_range(dates, freq="D", periods=31)
    nhoras        = ["{:02d}".format(n) for n in np.arange(0,24,1)]
    for q,m in enumerate(bytime):
        for h,d in enumerate(nhoras):
            date          = pd.to_datetime(m).strftime('%Y-%m-%d')+ '_'+d+':00:00'
            filename      = output_reg + 'wrfchemi_d0%s_%s'%(dom,str(date).replace(":","_"))
            dataset       = cdf.Dataset(filename,'w',format='NETCDF3_CLASSIC')

            # Dimensions
            lon           = dataset.createDimension(dim_emi_items[2][0], wrf_input.getncattr('WEST-EAST_PATCH_END_UNSTAG'))
            lat           = dataset.createDimension(dim_emi_items[3][0], wrf_input.getncattr('SOUTH-NORTH_PATCH_END_UNSTAG'))
            levels        = dataset.createDimension('emissions_zdim_stag',10)
            len           = dataset.createDimension('DateStrLen',19)
            time          = dataset.createDimension('Time', 1)


            # Variables
            time          = dataset.createVariable('Times', 'S1',('Time','DateStrLen'))
            lat           = dataset.createVariable('XLAT',  'f4', (dim_emi_items[3][0],dim_emi_items[2][0]))
            lon           = dataset.createVariable('XLONG', 'f4', (dim_emi_items[3][0],dim_emi_items[2][0]))

            co2f          = dataset.createVariable('E_CO2', 'f4', ('Time','emissions_zdim_stag',dim_emi_items[3][0],dim_emi_items[2][0]))
            cof           = dataset.createVariable('E_CO',  'f4', ('Time','emissions_zdim_stag',dim_emi_items[3][0],dim_emi_items[2][0]))
            ch4f          = dataset.createVariable('E_CH4', 'f4', ('Time','emissions_zdim_stag',dim_emi_items[3][0],dim_emi_items[2][0]))
    
            co2tf         = dataset.createVariable('E_CO2TST1', 'f4', ('Time','emissions_zdim_stag',dim_emi_items[3][0],dim_emi_items[2][0]))
            
            ch4t1f        = dataset.createVariable('E_CH4TST1', 'f4', ('Time','emissions_zdim_stag',dim_emi_items[3][0],dim_emi_items[2][0]))
            ch4t2f        = dataset.createVariable('E_CH4TST2', 'f4', ('Time','emissions_zdim_stag',dim_emi_items[3][0],dim_emi_items[2][0]))
            ch4t3f        = dataset.createVariable('E_CH4TST3', 'f4', ('Time','emissions_zdim_stag',dim_emi_items[3][0],dim_emi_items[2][0]))
            ch4t4f        = dataset.createVariable('E_CH4TST4', 'f4', ('Time','emissions_zdim_stag',dim_emi_items[3][0],dim_emi_items[2][0]))
            ch4t5f        = dataset.createVariable('E_CH4TST5', 'f4', ('Time','emissions_zdim_stag',dim_emi_items[3][0],dim_emi_items[2][0]))
            ch4t6f        = dataset.createVariable('E_CH4TST6', 'f4', ('Time','emissions_zdim_stag',dim_emi_items[3][0],dim_emi_items[2][0]))
            
            # data
            time[:,:]     = np.array([" ".join(date).split()], dtype = 'S19')
            lat[:,:]      = np.array(wrf_input.variables['XLAT_M'][0])
            lon[:,:]      = np.array(wrf_input.variables['XLONG_M'][0])
            ch4f[0,0,:,:] = edgar_data_re["CH4"]*temp_fact_utc[h]
            co2f[0,0,:,:] = edgar_data_re["CO2"]*temp_fact_utc[h]
            cof[0,0,:,:]  = edgar_data_re["CO"]*temp_fact_utc[h]
        
            ch4t1f[0,0,:,:] = wchts_data_re["2913"]
            ch4t2f[0,0,:,:] = wchts_data_re["2923"]
            ch4t3f[0,0,:,:] = wchts_data_re["2933"]
            ch4t4f[0,0,:,:] = wchts_data_re["2914"]
            ch4t5f[0,0,:,:] = wchts_data_re["2924"]
            ch4t6f[0,0,:,:] = wchts_data_re["2934"]      
            
            for q in range(1,10):
                #print(q)
                co2f[0,q,:,:]  = np.zeros(edgar_data_re["CO2"].shape)
                cof[0,q,:,:]   = np.zeros(edgar_data_re["CO"].shape)
                ch4f[0,q,:,:]  = np.zeros(edgar_data_re["CH4"].shape)

                ch4t1f[0,q,:,:] = np.zeros(wchts_data_re["2913"].shape)
                ch4t2f[0,q,:,:] = np.zeros(wchts_data_re["2923"].shape)
                ch4t3f[0,q,:,:] = np.zeros(wchts_data_re["2933"].shape)
                ch4t4f[0,q,:,:] = np.zeros(wchts_data_re["2914"].shape)
                ch4t5f[0,q,:,:] = np.zeros(wchts_data_re["2924"].shape)
                ch4t6f[0,q,:,:] = np.zeros(wchts_data_re["2934"].shape)


            # Attributes global
            dataset.Source    = 'WRF input file created by Benavente R.N., (2023). Reference: (MPI-BGC Jena 2019)'
            dataset.History   = 'Created ' + time.ctime(time.time())
            for i,j in enumerate(wrf_i.ncattrs()):
                if i == 0: continue
                dataset.setncattr(j,wrf_i.getncattr(j))

            # Attributes variables
            lon.MemoryOrder  = 'XY'
            lon.description  = 'LONGITUDE, WEST IS NEGATIVE'
            lon.untis        = 'degree east'
            lon.long_name    = " "
            lon.FieldType    = 104

            lat.MemoryOrder  = 'XY'
            lat.description  = 'LATITUDE, SOUTH IS NEGATIVE'
            lat.units        = 'degree north'
            lat.stagger      = ""
            lat.FieldType    = 104

            co2f.MemoryOrder  = 'XYZ'
            co2f.description  = 'EMISSIONS'
            co2f.units        = 'mol km^-2 hr^-1'
            co2f.stagger      = "Z"
            co2f.FieldType    = 104


            ch4f.MemoryOrder  = 'XYZ'
            ch4f.description  = 'EMISSIONS'
            ch4f.units        = 'mol km^-2 hr^-1'
            ch4f.stagger      = "Z"
            ch4f.FieldType    = 104


            cof.MemoryOrder  = 'XYZ'
            cof.description  = 'EMISSIONS'
            cof.units        = 'mol km^-2 hr^-1'
            cof.stagger      = "Z"
            cof.FieldType    = 104

            co2tf.MemoryOrder  = 'XYZ'
            co2tf.description  = 'EMISSIONS'
            co2tf.units        = 'mol km^-2 hr^-1'
            co2tf.stagger      = "Z"
            co2tf.FieldType    = 104

            ch4t1f.MemoryOrder  = 'XYZ'
            ch4t1f.description  = 'EMISSIONS'
            ch4t1f.units        = 'mol km^-2 hr^-1'
            ch4t1f.stagger      = "Z"
            ch4t1f.FieldType    = 104


            ch4t2f.MemoryOrder  = 'XYZ'
            ch4t2f.description  = 'EMISSIONS'
            ch4t2f.units        = 'mol km^-2 hr^-1'
            ch4t2f.stagger      = "Z"
            ch4t2f.FieldType    = 104
            
            ch4t3f.MemoryOrder  = 'XYZ'
            ch4t3f.description  = 'EMISSIONS'
            ch4t3f.units        = 'mol km^-2 hr^-1'
            ch4t3f.stagger      = "Z"
            ch4t3f.FieldType    = 104
            
            ch4t4f.MemoryOrder  = 'XYZ'
            ch4t4f.description  = 'EMISSIONS'
            ch4t4f.units        = 'mol km^-2 hr^-1'
            ch4t4f.stagger      = "Z"
            ch4t4f.FieldType    = 104
            
            ch4t5f.MemoryOrder  = 'XYZ'
            ch4t5f.description  = 'EMISSIONS'
            ch4t5f.units        = 'mol km^-2 hr^-1'
            ch4t5f.stagger      = "Z"
            ch4t5f.FieldType    = 104
            
            ch4t6f.MemoryOrder  = 'XYZ'
            ch4t6f.description  = 'EMISSIONS'
            ch4t6f.units        = 'mol km^-2 hr^-1'
            ch4t6f.stagger      = "Z"
            ch4t6f.FieldType    = 104
            
            dataset.close()

    print('DONE WITH GHG fire emissions REGRID-PREPROCESSING')
