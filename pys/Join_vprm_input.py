import numpy as np
import math, os, glob
import netCDF4 as cdf
import xarray as xr
from datetime import timedelta
import pandas as pd
from scipy.interpolate import interp1d

def biogenic(wrf_inp_p,wrf_geo_p,ch4_bio_p,co2_bio_p,dates,sim_time,dom,projection_wrf,output_reg):
    print('JOIN CH4 AND CO2 BIOGENIC DATASET')
    
    ######### READ CH4 BIO -- Kaplan inventory
    cpoolp  = ch4_bio_p +'CPOOL_d0%s_%s.nc'%(dom,pd.to_datetime(dates).year)
    tannp   = ch4_bio_p + 'T_ANN_d0%s_%s.nc'%(dom,pd.to_datetime(dates).year)
    wetmapp = ch4_bio_p + 'WETMAP_d0%s_%s.nc'%(dom,pd.to_datetime(dates).year)

    ######### READ CO2 BIO ---- prec vprm    
    vprm_inp  = co2_bio_p
    evi_minp  = vprm_inp + 'd0%s/VPRM_input_EVI_MIN_%s.nc'%(dom,pd.to_datetime(dates).year)
    evi_maxp  = vprm_inp + 'd0%s/VPRM_input_EVI_MAX_%s.nc'%(dom,pd.to_datetime(dates).year)
    evip      = vprm_inp + 'd0%s/VPRM_input_EVI_%s.nc'%(dom,pd.to_datetime(dates).year)
    lswi_minp = vprm_inp + 'd0%s/VPRM_input_LSWI_MIN_%s.nc'%(dom,pd.to_datetime(dates).year)
    lswi_maxp = vprm_inp + 'd0%s/VPRM_input_LSWI_MAX_%s.nc'%(dom,pd.to_datetime(dates).year)
    lswip     = vprm_inp + 'd0%s/VPRM_input_LSWI_%s.nc'%(dom,pd.to_datetime(dates).year)
    vegfrap   = vprm_inp + 'd0%s/VPRM_input_VEG_FRA_%s.nc'%(dom,pd.to_datetime(dates).year)


    ######### READ CH4 BIO -- Kaplan inventory
    cpool  = xr.open_dataset(cpoolp)
    tann   = xr.open_dataset(tannp)
    wetmap = xr.open_dataset(wetmapp)

    ######### READ CO2 BIO ---- prec vprm
    evi_min = xr.open_dataset(evi_minp)
    evi_max = xr.open_dataset(evi_maxp)
    evi = xr.open_dataset(evip)
    lswi_min = xr.open_dataset(lswi_minp)
    lswi_max = xr.open_dataset(lswi_maxp)
    lswi = xr.open_dataset(lswip)
    vegfra = xr.open_dataset(vegfrap)  

    wrf_i     = cdf.Dataset(wrf_inp_p)    
    ## Prepare the output dates
    all_time = pd.date_range(sim_time[0][0:4]+'-01-01', sim_time[1][0:4]+'-12-31',freq="D").strftime('%Y-%m-%d')

    #### drop the EVI and LSWI data for us time:
    star = list(all_time).index(sim_time[0][0:10])
    end = list(all_time).index(sim_time[1][0:10])
    
    evi_m = evi.sel(time=slice(star,end))
    lswi_m = lswi.sel(time=slice(star,end))
    
    ########### to limit values outside the range ########
    evi_mins = evi_min.evi_min.values
    evi_maxs = evi_max.evi_max.values
    evi_month = evi_m.evi.values
    lswi_mins = lswi_min.lswi_min.values
    lswi_maxs = lswi_max.lswi_max.values
    lswi_month = lswi_m.lswi.values
    vegfra_s = vegfra['vegetation_fraction_map'].values
    
    evi_mins[np.isnan(evi_mins)] = 0
    evi_mins[evi_mins > 2.1] = 0
    evi_maxs[np.isnan(evi_maxs)] = 0
    evi_maxs[evi_maxs > 2.1] = 0
    
    evi_month[np.isnan(evi_month)] = 0
    evi_month[evi_month > 2.1] = 0
    lswi_month[np.isnan(lswi_month)] = 0
    lswi_month[lswi_month > 2.1] = 0
    
    lswi_mins[np.isnan(lswi_mins)] = 0
    lswi_mins[lswi_mins > 2.1] = 0
    lswi_maxs[np.isnan(lswi_maxs)] = 0
    lswi_maxs[lswi_maxs > 2.1] = 0
    
    print('generating netcdf file..')
    wrf_input     = wrf_i
    dim_emi_items = list(wrf_input.dimensions.items())
    domain        = dom
    projection    = projection_wrf

    bytime        = pd.date_range(sim_time[0][0:10], sim_time[1][0:10], freq="D")
    for q,m in enumerate(bytime):
        date          = pd.to_datetime(m).strftime('%Y-%m-%d')+'_00:00:00'
        filename      = output_reg + 'vprm_input_d0%s_%s'%(dom,str(date).replace(":","_"))
        dataset       = cdf.Dataset(filename,'w',format='NETCDF3_CLASSIC')

        # Dimensions
        len           = dataset.createDimension('DateStrLen',19)
        time          = dataset.createDimension('Time', 1)
        lon           = dataset.createDimension(dim_emi_items[2][0], wrf_input.getncattr('WEST-EAST_PATCH_END_UNSTAG'))
        lat           = dataset.createDimension(dim_emi_items[3][0], wrf_input.getncattr('SOUTH-NORTH_PATCH_END_UNSTAG'))
        vegfran       = dataset.createDimension('vprm_vgcls',8)
        levels        = dataset.createDimension('zdim',1)

        # Variables
        time          = dataset.createVariable('Times', 'S1',('Time','DateStrLen'))
        lat           = dataset.createVariable('XLAT', 'f4', (dim_emi_items[3][0],dim_emi_items[2][0]))
        lon           = dataset.createVariable('XLONG', 'f4', (dim_emi_items[3][0],dim_emi_items[2][0]))

        evi_min_in    = dataset.createVariable('EVI_MIN', 'f4', ('Time','vprm_vgcls',dim_emi_items[3][0],dim_emi_items[2][0]))
        evi_max_in    = dataset.createVariable('EVI_MAX', 'f4', ('Time','vprm_vgcls',dim_emi_items[3][0],dim_emi_items[2][0]))
        evi_in        = dataset.createVariable('EVI', 'f4', ('Time','vprm_vgcls',dim_emi_items[3][0],dim_emi_items[2][0]))
        lswi_min_in   = dataset.createVariable('LSWI_MIN', 'f4', ('Time','vprm_vgcls',dim_emi_items[3][0],dim_emi_items[2][0]))
        lswi_max_in   = dataset.createVariable('LSWI_MAX', 'f4', ('Time','vprm_vgcls',dim_emi_items[3][0],dim_emi_items[2][0]))
        lswi_in       = dataset.createVariable('LSWI', 'f4', ('Time','vprm_vgcls',dim_emi_items[3][0],dim_emi_items[2][0]))
        vegfra_in     = dataset.createVariable('VEGFRA_VPRM', 'f4', ('Time','vprm_vgcls',dim_emi_items[3][0],dim_emi_items[2][0]))
        cpool_in      = dataset.createVariable('CPOOL', 'f4', ('Time','zdim',dim_emi_items[3][0],dim_emi_items[2][0]))
        wetmap_in     = dataset.createVariable('WETMAP', 'f4', ('Time','zdim',dim_emi_items[3][0],dim_emi_items[2][0]))
        tann_in       = dataset.createVariable('T_ANN', 'f4', ('Time','zdim',dim_emi_items[3][0],dim_emi_items[2][0]))

        # data
        time[:,:]           = np.array([" ".join(date).split()], dtype = 'S19')
	
        evi_min_in[:,:,:]   = evi_mins[:,:,:]
        evi_max_in[:,:,:]   = evi_maxs[:,:,:]
        evi_in[:,:,:]       = evi_month[:,q,:,:]
        lswi_min_in[:,:,:]  = lswi_mins[:,:,:]
        lswi_max_in[:,:,:]  = lswi_maxs[:,:,:]
        lswi_in[:,:,:]      = lswi_month[:,q,:,:]
        vegfra_in[:,:,:]    = vegfra.variables['vegetation_fraction_map'].values
        cpool_in[:,:]       = cpool.variables['CPOOL'].values
        wetmap_in[:,:]      = wetmap.variables['WETMAP'].values
        tann_in[:,:]        = tann.variables['T_ANN'].values

        lat[:,:]            = np.array(wrf_input.variables['XLAT'])
        lon[:,:]            = np.array(wrf_input.variables['XLONG'])


        # Attributes global
        lista = ['CEN_LAT','CEN_LON','TRUELAT1','TRUELAT2','MOAD_CEN_LAT','STAND_LON','POLE_LAT','POLE_LON','MAP_PROJ',
                'NUM_LAND_CAT','ISWATER','ISLAKE','ISICE','ISURBAN','ISOILWATER','MMINLU','GMT','JULYR','JULDAY']
        import time
        dataset.Source    = 'WRF input file created by Benavente R.N., (2023). Reference: vprm_shapeshifter, v1.5 (MPI-BGC Jena 2019)'
        dataset.History   = 'Created ' + time.ctime(time.time())

        for i,j in enumerate(lista):
            dataset.setncattr(j,wrf_input.getncattr(j))

        # Attributes variables
        evi_min_in.long_name    = 'minimum annual EVI index value'
        evi_min_in.FieldType    = 104
        evi_min_in.MemoryOrder  = 'XYZ'
        evi_min_in.units        = ''
        evi_min_in.description  = 'Minimal value of EVI index'
        evi_min_in.stagger      = 'M'
        evi_min_in.coordinates  = 'XLONG XLAT'

        evi_max_in.long_name    = 'maximum annual EVI index value'
        evi_max_in.FieldType    = 104
        evi_max_in.MemoryOrder  = 'XYZ'
        evi_max_in.units        = ''
        evi_max_in.description  = 'Maximal value of EVI index'
        evi_max_in.stagger      = 'M'
        evi_max_in.coordinates  = 'XLONG XLAT'

        evi_in.long_name        = 'EVI index value'
        evi_in.FieldType        = 104
        evi_in.MemoryOrder      = 'XYZ'
        evi_in.units            = ''
        evi_in.description      = 'Value of EVI index'
        evi_in.stagger          = 'M'
        evi_in.coordinates      = 'XLONG XLAT'

        lswi_min_in.long_name   = 'minimum annual LSWI index value'
        lswi_min_in.FieldType   = 104
        lswi_min_in.MemoryOrder = 'XYZ'
        lswi_min_in.units       = ''
        lswi_min_in.description = 'Minimal value of lswi index'
        lswi_min_in.stagger     = 'M'
        lswi_min_in.coordinates = 'XLONG XLAT'

        lswi_max_in.long_name   = 'maximum annual LSWI index value'
        lswi_max_in.FieldType   = 104
        lswi_max_in.MemoryOrder = 'XYZ'
        lswi_max_in.units       = ''
        lswi_max_in.description = 'Maximal value of lswi index'
        lswi_max_in.stagger     = 'M'
        lswi_max_in.coordinates = 'XLONG XLAT'

        lswi_in.long_name       = 'LSWI index value'
        lswi_in.FieldType       = 104
        lswi_in.MemoryOrder     = 'XYZ'
        lswi_in.units           = ''
        lswi_in.description     = 'Value of lswi index'
        lswi_in.stagger         = 'M'
        lswi_in.coordinates     = 'XLONG XLAT'

        vegfra_in.long_name    = 'VPRM vegetation fraction'
        vegfra_in.FieldType    = 104
        vegfra_in.MemoryOrder  = 'XYZ'
        vegfra_in.units        = ''
        vegfra_in.description  = 'Vegetation fraction for VPRM'
        vegfra_in.stagger      = 'M'
        vegfra_in.coordinates  = 'XLONG XLAT'

        cpool_in.long_name    = 'LPJ Carbon pool'
        cpool_in.FieldType    = 104
        cpool_in.MemoryOrder  = 'XYZ'
        cpool_in.units        = '$kgC/m^{2}$'
        cpool_in.description  = 'Carbon pool value for Kaplan model'
        cpool_in.stagger      = 'M'
        cpool_in.coordinates  = 'XLONG XLAT'

        wetmap_in.long_name   = 'Kaplan potential wetland map'
        wetmap_in.FieldType   = 104
        wetmap_in.MemoryOrder = 'XYZ'
        wetmap_in.units       = '1 Woolong'
        wetmap_in.description = 'Wetland map for Kaplan model'
        wetmap_in.stagger     = 'M'
        wetmap_in.coordinates = 'XLONG XLAT'

        tann_in.long_name     = 'mean annual temperature'
        tann_in.FieldType     = 104
        tann_in.MemoryOrder   = 'XYZ'
        tann_in.units         = 'K'
        tann_in.description   = 'Annual mean temperature for vegetation classes'
        tann_in.stagger       = 'M'
        tann_in.coordinates   = 'XLONG XLAT'

        dataset.close()

    print('DONE GENERATING THE VPRM INPUT')        

