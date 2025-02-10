# Some Problems

There are probably some problems running Theo's program together with WRF-GHG-Preppy. In my case it was not necessary to create two environments to perform each job, but rather a "pyvprm" environment.

However, some problems arose when reading the "hdf" files, resulting in this message:

```
 "RasterioIOError: '...20324091904.hdf' not recognized as being in a supported file format. It could have been recognized by driver HDF4, but plugin gdal_HDF4.so is not available in your installation. You may install it with 'conda install -c conda-forge libgdal-hdf4
```

For this, I followed some steps where I managed to solve this problem:

```
conda create -n pyvprm
conda activate pyvprm
onda install -c conda-forge rioxarray==0.13.3
conda config --add channels conda-forge
conda config --set channel_priority strict
conda install -c conda-forge dask netCDF4
conda install esmf
conda install esmpy
conda install -c conda-forge libgdal-hdf4

```





