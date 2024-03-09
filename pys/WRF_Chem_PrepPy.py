import datetime
import subprocess
import pandas as pd
import prep_T_ann, prep_wetland_kaplan,prep_cpool_lpj
#from cdo import *
import warnings

'''
IMPORTANT DATA:

- domains --> Number of domains.
- wrf_inp --> Path where are the "wrfinputs" files.
- wrf_geo --> Path where are the "geo_em" files.
- sim_time --> It is necessary to set the start and end of the processing.
'''
domains        = 3                                                 # check this always
wrf_inp        = '../input/wrf_inputs/wrfinput_d0'                   # check this always
wrf_geos        = '../input/wrf_inputs/geo_em.d0'                     # check this always
sim_time       = '2023-08-01 00:00:00','2022-01-31 23:00:00'       # check this!!
dates          = pd.to_datetime(sim_time[0]).strftime('%Y-%m-%d')
pos            = '.nc'  
projection_wrf = 'Lambert Conformal'

ch4_bio_p      = '../input/bio_ghg/ch4_bio/'
ch4_bio_reg    = ch4_bio_p+'regrid/'
fire_p         = '../input/fire_ghg/'
fire_reg       = fire_p+'regrid/'
anthr_p      = '../input/anthr_ghg/'
anthr_reg    = anthr_p+'regrid/'

'''
1. Preparing the data for the Kaplan model (biogenic emissions) -> CH4

  There are three python scripts to obtain the necessary inputs for the Kaplan model and calculate biogenic methane emissions.
  - prep_wetland_kaplan.py
  - prep_cpool_lpj.py
  - prep_T_ann.py
'''

for i,j in enumerate(range(domains),start=1):
    dom              = i
    wrf_inp_p        = wrf_inp  + str(i)
    wrf_geo_p        = wrf_geos  + str(i) + pos

    # ================= Kaplan inventory
    wet_var          = 'wetland'
    path_wet         = ch4_bio_p + 'global/global_wetland_kaplan.nc'
    regrid_method    = 'conservative'
    
    print(datetime.datetime.now())
    prep_wetland_kaplan.prep_wetland(wrf_geo_p,path_wet,wet_var,regrid_method,sim_time,dom,projection_wrf,ch4_bio_reg)
    print(datetime.datetime.now())
    
    cpool_var        = 'cpool_fast'
    path_cpool       = ch4_bio_p + 'global/lpj_cpool_2000.nc'
  #  cmmd             = 'cdo remapbil,'+ wrf_inp_p + ' -fillmiss2 ' + cpool_path + ' intermediate_cpool_regrid.nc'
    
    print(datetime.datetime.now())
  #  subprocess.call(cmmd,shell=True)
    prep_cpool_lpj.prep_cpool(wrf_geo_p,path_cpool,cpool_var,regrid_method,sim_time,dom,projection_wrf,ch4_bio_reg)
    print(datetime.datetime.now()) 
       
    # Remember to check the year. The netcdf files for temp should be a Monthly mean. shape = (12).
    ### If changing year, remeber to change T_ANN year down below
    path_t_ann       = ch4_bio_p + 'global/ERA_monthly_soiltemperature_2023.nc'
    t_var            = 'stl1' # remember to include the other options
    regrid_method    = 'conservative'
    
    print(datetime.datetime.now())
    prep_T_ann.prep_T(wrf_geo_p,path_t_ann,t_var,regrid_method,sim_time,dom,projection_wrf,ch4_bio_reg)
    print(datetime.datetime.now())
    
    #!rm intermediate_cpool_regrid.nc
    
    print('===================================')
    print('FINISHED WITH DOMAIN %s'%(str(dom)))
    print('===================================')  

'''
2. Preparing the data for the Kaplan model (biogenic emissions) -> CH4

  There are three python scripts to obtain the necessary inputs for the Kaplan model and calculate biogenic methane emissions.
  - prep_wetland_kaplan.py
  - prep_cpool_lpj.py
  - prep_T_ann.py
'''
for i,j in enumerate(range(domains),start=1):
    
    dom              = i
    wrf_inp_p        = wrf_inp  + str(i)
    wrf_geo_p        = wrf_geos  + str(i) + pos

    # Remember to check the year. 
    ### If changing year, remeber to change GFAS for each time 
    path_gfas        = fire_p+'global/2208_ghg.nc'
    var              = ['co2fire','ch4fire','cofire'] # remember to include the other options
    mvar             = [28.01,44.01,16.043]
    regrid_method    = 'conservative'
    
    print(datetime.datetime.now())
    prep_T_ann.prep_T(wrf_geo_p,path_t_ann,t_var,regrid_method,sim_time,dom,projection_wrf,ch4_bio_reg)
    %run -i pre_gfas.py
    print(datetime.datetime.now())
    
    #!rm intermediate_cpool_regrid.nc
    
    print('===================================')
    print('FINISHED WITH DOMAIN %s'%(str(dom)))
    print('===================================')    
    