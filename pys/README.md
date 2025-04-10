# codes to use the initial and boundary conditions script

## 1. Processing for the CAMS-GACF product 

For CO and CH₄:

#### Steps:
<dt> Here I am leaving an example: <dt>

<dt> Run date, 01-15 - August - 2022, for 4 domains.<dt>

**1A: Download CAMS data for our period**

<dt>In "download_CAMS_with_cmmd.py" : modify your period <dt>

```
year        = '2022'
monthi      = '08'
monthe      = '08'
```

This script is linked with the files [submit_cds_ads_download.sh](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/libraries/submit_cds_ads_download.sh) and [download_ghg_egg4.py](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/libraries/download_ghg_egg4.py).


```
Finally, run: python download_CAMS_with_cmmd.py
```

**1B: Calculate CAMS Interpolation Indices**

<dt>In "calculate_CAMS_interpolation_indices.py" : modify the number of domains and the file name ("filein"). <dt>

```
See lines: 81 and 85

filein = os.path.join(cams_path, 'CAMS_GACF_large_co_ch4_20220801.nc')
requested_domains = [ "d01", "d02","d03","d04"];
```

It is recommended to place the name of the file using the year, month and initial day ("20220801"), since that name is generated when the download_CAMS_with_cmmd.py script is run.


**1C: Run Inicial and Boundary conditions**

To start running scripts: "prep_initial_cond.py" and "prep_boundary_cond.py", it is recommended to have some files ready:

```
- wrfinput/wrfbdy
- CAMS data
- interp_indices.txt.npz
- ecmwf_coeffs_L137.csv
```

In [prep_initial_cond.py](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/prep_initial_cond.py) and [prep_boundary_cond.py](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/prep_boundary_cond.py) scripts: modify the number of domains and simulation time.


```
requested_domains = [ "d01", "d02","d03","d04"]
sim_time          = '2022-08-01 00:00:00','2022-08-15 23:00:00'       # check this!!
```

<dt> The start and end data in the sim_time should be similar to "namelist.input". CAMS data will be stored in both the wrfinput and wrfbdy files <dt>

After taking into account these modifications and running the scripts, the wrfinput and wrfbdy files will be modified, storing the CAMS information. 



## 2. CAMS-Inversion product





