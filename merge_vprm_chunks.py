import warnings
warnings.filterwarnings("ignore")
from pyVPRM.lib.fancy_plot import *
from rioxarray import merge
import numpy as np
import os
import glob
import xarray as xr
import shutil

base_theo =  '/home/rnoeliab/pyVPRM_examples/wrf_preprocessor/out/dominio_1/'
output = '/home/rnoeliab/WRF-VPRM-Prepy/input/bio_ghg/co2_bio/'

for fbase in np.unique([i.split('_part')[0] for i in glob.glob(os.path.join(base_theo, 'VPRM_input*part_*'))]):
    print(fbase)  
    if os.path.exists(fbase+'.nc'):
       continue
    lon_stripes = []
    for n in np.arange(1,33,1):
        list = sorted(glob.glob(fbase+'*_{}.nc'.format(n)))
        spslits = [n.split('_part_')[1] for n in list]
        names = [n.split('_part_')[0] for n in list][0]
        file_s = sorted(spslits, key=lambda x: int(x.split('_')[0]))
        files = [names + '_part_'+ i for i in file_s]     
        try: 
            lon_stripes.append(xr.concat([xr.open_dataset(i).drop_dims(['x_b', 'y_b']) for i in files],
                                   dim ='west_east', compat='no_conflicts'))
        except:
            lon_stripes.append(xr.concat([xr.open_dataset(i) for i in files],
                                   dim ='west_east', compat='no_conflicts'))
        if not os.path.exists(os.path.join(base_theo,'splits')):
            os.makedirs(os.path.join(base_theo, 'splits'))
        for file in files:
            shutil.move(file, os.path.join(base_theo, 'splits', os.path.basename(file)))
    full = xr.concat(lon_stripes,dim ='south_north')
 #   print(fbase+'.nc')

    full.to_netcdf(fbase+'.nc')
