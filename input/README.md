# WRF-VPRM-PrepPy Code

To run the main script "WRF_Chem_PrepPy.py" it is necessary to have the libraries ready. There are two paths:

### 1. Running the file "environment.yml"

```
conda env create -f environment.yml
```

### 2. Manually

```
conda create -n vprm python==3.8
conda activate vprm
pip install cdsapi
conda install pandas
conda install -c conda-forge xesmf
conda install -c conda-forge dask netCDF4
conda install -c conda-forge matplotlib cartopy jupyterlab
conda install -c conda-forge xarray dask netCDF4 bottleneck
```

## ddd

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
