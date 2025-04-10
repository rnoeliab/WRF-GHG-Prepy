# codes to use the initial and boundary conditions script

## 1. Processing for the CAMS-GACF product 

For CO and CH₄:

#### Steps:
<dt> Here I am leaving an example: <dt>

<dt> Run date, 01-15 - August - 2022, for 4 domains.<dt>

**1A: Download CAMS-GACF data for our period**

<dt>In "download_CAMS-GACF_with_cmmd.py" : modify your period <dt>

```
year        = '2022'
monthi      = '08'
monthe      = '08'
```

This script is linked with the files [submit_cds_ads_download.sh](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/libraries/submit_cds_ads_download.sh) and [download_ghg_CAMS-GACF.py](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/libraries/download_ghg_CAMS-GACF.py).


```
Finally, run: python download_CAMS-GACF_with_cmmd.py
```

**1B: Calculate CAMS-GACF Interpolation Indices**

<dt>In "calculate_CAMS-GACF_interpolation_indices.py" : modify the number of domains and the file name ("filein"). <dt>

```
See lines: 81 and 85

filein = os.path.join(cams_path, 'CAMS_GACF_large_co_ch4_20220801.nc')
requested_domains = [ "d01", "d02","d03","d04"];
```

It is recommended to place the name of the file using the year, month and initial day ("20220801"), since that name is generated when the download_CAMS-GACF_with_cmmd.py script is run.


**1C: Run Inicial and Boundary conditions**

To start running scripts: "prep_boundary_cond_CAMS-GACF.py" and "prep_boundary_cond_CAMS-GACF.py", it is recommended to have some files ready:

```
- wrfinput/wrfbdy
- CAMS-GACF data
- interp_CAMS-GACF_indices.txt.npz
- ecmwf_coeffs_L137.csv
```

In [prep_initial_cond_CAMS-GACF.py](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/ic--cc/prep_initial_cond_CAMS-GACF.py) and [prep_boundary_cond_CAMS-GACF.py](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/ic--cc/prep_boundary_cond_CAMS-GACF.py) scripts: modify the number of domains and simulation time.


```
requested_domains = [ "d01", "d02","d03","d04"]
sim_time          = '2022-08-01 00:00:00','2022-08-15 23:00:00'       # check this!!
```

## 2. Processing for the CAMS-Inversion product

For CO₂ and CH₄

#### Steps:

**1A: Download CAMS-Inversion data for our period**

<dt>In "download_CAMS-Inversion-concentrations.py" : modify your period <dt>

```
import cdsapi

c = cdsapi.Client()

c.retrieve(
    'cams-global-greenhouse-gas-inversion',
    {
        'version':'latest',
        'format':'zip',
        'variable':'carbon_dioxide',
        'quantity': 'concentration',
        'input_observations': 'satellite', #'surface_satellite',
        'time_aggregation': 'instantaneous',
        'year': '2022',
        'month': [
            '08',
        ],
    },
    'CAMS-GIO-CO2-FC202208.zip')
```

I recommend downloading data for a maximum of one month.

```
$ python download_CAMS-Inversion-concentrations.py
```




<dt> The start and end data in the sim_time should be similar to "namelist.input". CAMS data will be stored in both the wrfinput and wrfbdy files <dt>

After taking into account these modifications and running the scripts, the wrfinput and wrfbdy files will be modified, storing the CAMS information. 








