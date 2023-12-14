''''
WRF-VPRM-Preppy 

1. Create by Santiago Botia ()
2. Modified and updated by Noelia Rojas B. (rnoeliab@gmail.com)
3. Last updated in Dec 2023.

Preprocessor to obtain (CH4, CO2 and CO):
- Biogenic emissions
- Anthropogenic emissions
- Burning emissions 

This preppy needs the wrfinput_d0#.nc and geo_em.d0#.nc files.
'''

import datetime
import subprocess
import pandas as pd
import os
import warnings

def path(out_diretory):
    if not os.path.exists(out_diretory):
        os.makedirs(out_diretory)
    return out_diretory  

'''''
IMPORTANT DATA:

- domains --> Number of domains.
- wrf_inp --> Path where are the "wrfinputs" files.
- wrf_geo --> Path where are the "geo_em" files.
- sim_time --> It is necessary to set the start and end of the processing.

'''''

domains        = 4                                                 # check this always
wrf_inps        = '../input/wrf_inputs/'                            # check this always

sim_time       = '2022-08-01 00:00:00','2022-08-31 23:00:00'       # check this!!
dates          = pd.to_datetime(sim_time[0]).strftime('%Y-%m-%d')

pos            = '.nc'  
projection_wrf = 'Lambert Conformal'

''''
1. Preparing the data for the Kaplan model (biogenic emissions) -> CH4

  There are three python scripts to obtain the necessary inputs for the Kaplan model and calculate biogenic methane emissions.
  - prep_wetland_kaplan.py
  - prep_cpool_lpj.py
  - prep_T_ann.py
''''

#These ones are updated 2023-12 ---> Noelia Rojas B.

ch4_bio_p  = '../input/bio_ghg/ch4_bio/'
output_reg = path('../output/kaplan_model/')

for i,j in enumerate(range(domains),start=1):
    dom              = i
    wrf_inp_p        = wrf_inps + 'wrfinput_d0'  + str(i)
    wrf_geo_p        = wrf_inps + 'geo_em.d0' + str(i) + pos
    
    # ================= Kaplan inventory
    wet_var          = 'wetland'
    path_wet         = 'global_wetland_kaplan.nc'
    lat              = 'lat'
    lon              = 'lon'
    regrid_method    = 'conservative'
    source           = 'Kaplan'
    
    print(datetime.datetime.now())
    %run -i prep_wetland_kaplan.py
    print(datetime.datetime.now())

    cpool_var        = 'cpool_fast'
    cpool_path       = ch4_bio_p +'lpj_cpool_2000.nc'
    cmmd             = 'cdo remapbil,'+ wrf_inp_p + ' -fillmiss2 ' + cpool_path + ' intermediate_cpool_regrid.nc'
    
    print(datetime.datetime.now())
    subprocess.call(cmmd,shell=True)
    %run -i prep_cpool_lpj.py
    !rm intermediate_cpool_regrid.nc
    print(datetime.datetime.now()) 

    # Remember to check the year. The netcdf files for temp should be a Monthly mean. shape = (12).
    ### If changing year, remeber to change T_ANN year down below
    t_ann_path       = 'ERA_monthly_soiltemperature_2022.nc'
    t_var            = 'stl1' # remember to include the other options
    lat              = 'latitude'
    lon              = 'longitude'
    regrid_method    = 'conservative'
    
    print(datetime.datetime.now())
    %run -i prep_T_ann.py
    print(datetime.datetime.now())
    
    print('===================================')
    print('FINISHED WITH DOMAIN %s'%(str(dom)))
    print('===================================')   

'''
Join CH4 and CO2 biogenic dataset
'''

for i,j in enumerate(range(domains),start=1):
    dom              = i
    wrf_inp_p        = wrf_inps + 'wrfinput_d0'  + str(i)
    
    ######### Paths of the CH4 BIO files -- Kaplan inventory
    cpoolp  = output_reg +'CPOOL_d0%s_%s.nc'%(dom,pd.to_datetime(dates).year)
    tannp   = output_reg + 'T_ANN_d0%s_%s.nc'%(dom,pd.to_datetime(dates).year)
    wetmapp = output_reg + 'WETMAP_d0%s_%s.nc'%(dom,pd.to_datetime(dates).year)

    ######### Paths of the CO2 BIO files ---- prec vprm    
    vprm_inp  = '../input/bio_ghg/co2_bio/regrid/'
    evi_minp  = vprm_inp + 'd0%s/VPRM_input_EVI_MIN_%s.nc'%(dom,pd.to_datetime(dates).year)
    evi_maxp  = vprm_inp + 'd0%s/VPRM_input_EVI_MAX_%s.nc'%(dom,pd.to_datetime(dates).year)
    evip      = vprm_inp + 'd0%s/VPRM_input_EVI_%s.nc'%(dom,pd.to_datetime(dates).year)
    lswi_minp = vprm_inp + 'd0%s/VPRM_input_LSWI_MIN_%s.nc'%(dom,pd.to_datetime(dates).year)
    lswi_maxp = vprm_inp + 'd0%s/VPRM_input_LSWI_MAX_%s.nc'%(dom,pd.to_datetime(dates).year)
    lswip     = vprm_inp + 'd0%s/VPRM_input_LSWI_%s.nc'%(dom,pd.to_datetime(dates).year)
    vegfrap   = vprm_inp + 'd0%s/VPRM_input_VEG_FRA_%s.nc'%(dom,pd.to_datetime(dates).year)
    
    file_out = path('../output/vprm_input/')
    print(datetime.datetime.now())
    %run -i Join_vprm_input.py
    print(datetime.datetime.now())  
    
    print('===================================')
    print('FINISHED WITH DOMAIN %s'%(str(dom)))
    print('===================================')    



'''
2. Preparing the data for the Anthropogenic emissions -> CH4, CO2 and CO
'''

edgar_path = '../input/anthr_ghg/data_total/'
wchts_path = '../input/anthr_ghg/wetchart/'
output_reg = path('../output/wrfchemis/')

for i,j in enumerate(range(domains),start=1):
    dom              = i
    wrf_inp_p        = wrf_inps + 'wrfinput_d0'  + str(i)
    wrf_geo_p        = wrf_inps + 'geo_em.d0' + str(i) + pos

    var             = ['CO','CO2','CH4'] # remember to include the other options
    mvar            = [28.01,44.01,16.043]
    num_model       = ['2913','2923','2933','2914','2924','2934']    #### for wetcharts data
    month           = int(pd.to_datetime(sim_time[0]).strftime('%m'))
    lat             = 'lat'
    lon             = 'lon'
    regrid_method   = 'conservative'
    
    print(datetime.datetime.now())
    %run -i prep_edgar.py
    print(datetime.datetime.now())
    
    #!rm intermediate_cpool_regrid.nc
    
    print('===================================')
    print('FINISHED WITH DOMAIN %s'%(str(dom)))
    print('===================================')  


'''
3. Preparing the data for the Fires emissions -> CH4, CO2 and CO
'''

for i,j in enumerate(range(domains),start=1):
    
    dom              = i
    wrf_inp          = w + pre  + str(i)
    wrf_geo_p        = w_geo + pre2 + str(i) + pos

    # Remember to check the year. The netcdf files for temp should be a.....
    ### If changing year, remeber to change GFAS for each time 
    gfas_path       = '../../../DATA/sources/FIRES/global/2208_ghg.nc'
    var             = ['co2fire','ch4fire','cofire'] # remember to include the other options
    mvar             = [28.01,44.01,16.043]
    lat             = 'latitude'
    lon             = 'longitude'
    gfas_out        = '../../../DATA/sources/FIRES/regrid/'
    regrid_method   = 'conservative'
    
    print(datetime.datetime.now())
    %run -i pre_gfas.py
    print(datetime.datetime.now())
    
    #!rm intermediate_cpool_regrid.nc
    
    print('===================================')
    print('FINISHED WITH DOMAIN %s'%(str(dom)))
    print('===================================')    
