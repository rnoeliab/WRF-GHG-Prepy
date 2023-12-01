import numpy as np
import math, os, glob
import netCDF4 as cdf
import xarray as xr
from datetime import datetime, timedelta
import datetime as dt
import pandas as pd
from scipy.interpolate import interp1d

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

#wrf_i       = cdf.Dataset(wrf_inp)
wrf_geo     = cdf.Dataset(wrf_inp_p)

### Calculating the time of each EVI and LSWI data for interpolate
#times_evi = pd.DataFrame({})
#for n,t in enumerate(evi.time.values):
#    cal = datetime(2022, 1, 1, tzinfo=timezone.utc) + timedelta(t.astype(float)-1)
#    times_evi.loc[n,"date"] = pd.to_datetime(cal).strftime('%Y-%m-%d')
#    times_evi.loc[n,'julian'] = t.astype(float)
    
## Prepare the output dates
all_time = pd.date_range(sim_time[0][0:4]+'-01-01', sim_time[1][0:4]+'-12-31',freq="D").strftime('%Y-%m-%d')

############ storing the EVI and LSWI data for a year   ---using interpolating
#new_evi = np.zeros((evi.evi.shape[0],all_time.shape[0],evi.evi.shape[2],evi.evi.shape[3]))
#new_lswi = np.zeros((lswi.lswi.shape[0],all_time.shape[0],lswi.lswi.shape[2],lswi.lswi.shape[3]))

#for v in range(evi.vprm_classes.shape[0]):
#    len_time = np.arange(0,2,1)
#    new_time = np.linspace(0,1,9)
#    for t in range(evi.time.shape[0]-2):
#        count = 0
#        mask = np.isnan(evi.evi.values[v,t:t+2,:,:])
#        evi.evi.values[v,t:t+2,:,:][mask] = np.interp(np.flatnonzero(mask), 
#                                                      np.flatnonzero(~mask), 
#                                                      evi.evi.values[v,t:t+2,:,:][~mask])
#        f = interp1d(len_time,evi.evi.values[v,t:t+2,:,:], axis=0)
#        f1 = interp1d(len_time,lswi.lswi.values[v,t:t+2,:,:], axis=0)
#        for n in range(new_time.shape[0]-1):
#            new_evi[v,evi.time.values[t]+count,:,:] = f(new_time[n])
#            new_lswi[v,lswi.time.values[t]+count,:,:] = f1(new_time[n])
#            count=count+1
#    new_evi[v,evi.time.values[t]+count,:,:] =  new_evi[v,evi.time.values[t]+count-1,:,:]
#    new_lswi[v,lswi.time.values[t]+count,:,:] =  new_lswi[v,lswi.time.values[t]+count-1,:,:]
#    for t in range(4):   #### --- for 01/01 - 03/01 we use the same data in 04/01
#        new_evi[v,t,:,:] = evi.evi.values[v,0,:,:]
#        new_lswi[v,t,:,:] = lswi.lswi.values[v,0,:,:]


#### drop the EVI and LSWI data for us time:
#evi_month = new_evi[:,star:end+1,:,:]
#lswi_month = new_lswi[:,star:end+1,:,:]

star = list(all_time).index(sim_time[0][0:10])
end = list(all_time).index(sim_time[1][0:10])
evi_month = evi.sel(time=slice(star,end))
lswi_month = lswi.sel(time=slice(star,end))

print('generating netcdf file..')
wrf_input     = wrf_geo
dim_emi_items = list(wrf_input.dimensions.items())
domain        = dom
projection    = projection_wrf

bytime        = pd.date_range(sim_time[0][0:10], sim_time[1][0:10], freq="D")
for q,m in enumerate(bytime):
    date          = pd.to_datetime(m).strftime('%Y-%m-%d')+'_00:00:00'
    filename      = file_out + 'vprm_input_d0%s_%s'%(dom,str(date).replace(":","_"))
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
    evi_min_in[:,:,:]   = evi_min.variables['evi_min'].values
    evi_max_in[:,:,:]   = evi_max.variables['evi_max'].values
    evi_in[:,:,:]       = evi_month.variables['evi'].values[:,q,:,:]  #evi_month[:,q,:,:]
    lswi_min_in[:,:,:]  = lswi_min.variables['lswi_min'].values
    lswi_max_in[:,:,:]  = lswi_max.variables['lswi_max'].values
    lswi_in[:,:,:]      = lswi_month.variables['lswi'].values[:,q,:,:] #lswi_month[:,q,:,:]
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


