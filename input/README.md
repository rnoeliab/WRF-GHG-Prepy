# WRF-VPRM-PrepPy Code

To run this script you need to install some libraries

```
conda create -n vprm python==3.8
conda activate vprm
conda install pandas

```


```
import datetime
import subprocess
import pandas as pd
#from cdo import *
import warnings

domains        = 4                                         # check this always
wrf_inp        = '../input/wrfinput/wrfinput_d0'           # check this always
wrf_geos       = '../input/domains/geo_em.d0'              # check this always

sim_time       = '2022-08-01 00:00:00','2022-08-31 23:00:00'       # check this!!
dates          = pd.to_datetime(sim_time[0]).strftime('%Y-%m-%d')

pos            = '.nc'  
projection_wrf = 'Lambert Conformal'

```
