# Some Problems

There are probably some problems running Theo's program together with WRF-GHG-Preppy. In my case it was not necessary to create two environments to perform each job, but rather a "pyvprm" environment.

However, some problems arose when reading the "hdf" files, resulting in this message:

```
 "RasterioIOError: '...20324091904.hdf' not recognized as being in a supported file format. It could have been recognized by driver HDF4, but plugin gdal_HDF4.so is not available in your installation. You may install it with 'conda install -c conda-forge libgdal-hdf4
```




To do this, I followed some steps where I managed to solve this problem.




conda create -n pyvprm python==3.9.13
conda activate pyvprm
pip install cdsapi
conda install pandas
conda install -c conda-forge xesmf
conda install -c conda-forge dask netCDF4
conda install -c conda-forge matplotlib cartopy jupyterlab
conda install -c conda-forge xarray dask netCDF4 bottleneck


<dt> Now to edit the main code, you must take into account the following: <dt>

<dt> 1. The period in which the WRF-GHG model will be run, that is, start and end date (including hours).<dt>
<dt> 2. The domains <dt>
<dt> 3. and that the input and output paths are correct. <dt>

## Edit WRF_Chem_PrepPy.py

Ejm: 

```
domains        = 4                                                 # check this always
wrf_inp        = '../input/wrf_inputs/wrfinput_d0'                   # check this always
wrf_geos       = '../input/wrf_inputs/geo_em.d0'                     # check this always
sim_time       = '2022-08-01 00:00:00','2022-08-15 23:00:00'       # check this!!
dates          = pd.to_datetime(sim_time[0]).strftime('%Y-%m-%d')
pos            = '.nc'  
projection_wrf = 'Lambert Conformal'

ch4_bio_p      = '../input/bio_ghg/ch4_bio/'
co2_bio_p      = '../input/bio_ghg/co2_bio/'
fire_p         = '../input/fire_ghg/'
anthr_p        = '../input/anthr_ghg/'

output_reg     = '../output/'

```

### Run!!!

```
python WRF_GHG_PrepPy.py
```


