# WRF-VPRM-PrepPy

The Weather Research and Forecasting (WRF) Model is a state of the art mesoscale numerical weather prediction system designed for both atmospheric research and operational forecasting applications. The model serves a wide range of meteorological applications across scales from tens of meters to thousands of kilometers. Furthermore, a coupled with the Vegetation Photosynthesis and Respiration Model (VPRM) (referred to as WRF-VPRM), has used to better understand the effects that mesoscale transport has on atmospheric CO2 distributions.

![all text](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/flowchart_vprm.png)

This module provides different preprocessing to prepare the different emissions inventories (from CO, CO2 and CH4) that will be necessary to run the WRF-GHG (or WRF-VPRM) model (chem_opt = 17). 

**Take into account:**

<dt>I. Firstly, run the scripts found in the "pys/libraries" directory.<dt>

<dt>II. Secondly, run the scripts found in the "pys/prep" directory.<dt>

<dt>III. Finally run the "WRF_Chem_PrepPy.py" script.<dt>


## 1. Preparing external data !!!

Here, we are using the WRF-VPRM v4.2.1 model:

* Firstly - clone this repository in a linux/windows terminal and create an environment to work this module (there is an example in the [input](https://github.com/rnoeliab/WRF-VPRM-Prepy/blob/main/input/) directory):

```
>> git clone https://github.com/rnoeliab/WRF-VPRM-Prepy.git
```

* Secondly - save the **"wrfinput"**, **"wrfbdy"** and **geo_em.d0#.nc** files in  the [wrf_inputs directory](https://github.com/rnoeliab/WRF-VPRM-Prepy/blob/main/input/wrf_inputs/)


* Thirdly - run the scripts found inside the [libraries](https://github.com/rnoeliab/Inputs-WRF-VPRM/tree/main/pys/libraries/) directory, depending on the following sequence:

**NOTE**

<dt>Every time we execute a python script we must be within our created environment .<dt>

(see [WRF-VPRM-PrepPy Code](https://github.com/rnoeliab/WRF-VPRM-Prepy/tree/main/input))

### A. Biogenic Emissions

This processing is divided into two parts: The Kaplan model and VPRM code:

#### A1. Kaplan model - Biogenic Methane (CH4)

Three data are necessary here: CPOOL and wetland maps, and soil temperature data). The first two are provided by this repository and the latest data is downloaded from the Copernicus platform.

1. CPOOL - [lpj_cpool_2000.nc](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/input/bio_ghg/ch4_bio/lpj_cpool_2000.nc)
2. wetland - [global_wetland_kaplan.nc](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/input/bio_ghg/ch4_bio/global_wetland_kaplan.nc)
3. Download the soil temperature data provided by ERA5 model, this is using the following step:

```
1. Create a user, log in and read How to use the CDS API:
   > https://cds.climate.copernicus.eu/api-how-to

2. Create ".cdsapirc" in the $HOME/ directory 
   > gedit .cdsapirc &
3. write the following:
   # To Meteo
   url: https://cds.climate.copernicus.eu/api/v2
   key: <UID>:<APIKEY>
4. And, save.

5. Run the download_era5_soiltemperature.py script (../pys/libraries/download_era5_soiltemperature.py) to obtain soil temperature data for the appropriate **year** and over our **study area**.

$ python download_era5_soiltemperature.py
```

**NOTE**  
Don't forget that it must be run within our created environment

These files, saved in the [ch4_bio](https://github.com/rnoeliab/Inputs-WRF-VPRM/tree/main/input/bio_ghg/ch4_bio/) directory, are necessary to run the following scripts (located in the main script) :

- [prep_wetland_kaplan.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_wetland_kaplan.py), 
- [prep_cpool_lpj.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_cpool_lpj.py),
- [prep_T_ann.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_T_ann.py)

These scripts will be run at the end of processing...

#### A2. VPRM input 

To get the VPRM input, we'll need to go to Theo's processing: [pyVPRM](https://github.com/tglauch/pyVPRM/tree/main) and [pyVPRM_examples](https://github.com/tglauch/pyVPRM_examples).

<dt>Perform the following steps:<dt>

##### A.2.1 pyVPRM_examples install

<dt> Clone the repository <dt>

```
git clone https://github.com/tglauch/pyVPRM_examples.git
```

##### A.2.2 Create a environment

Within the [pyVPRM](https://github.com/tglauch/pyVPRM/tree/main) repository, consider the steps to follow from (How to Use)[https://github.com/tglauch/pyVPRM?tab=readme-ov-file#how-to-use] to install the necessary libraries to run the [vprm_preprocessor_new.py](https://github.com/tglauch/pyVPRM_examples/blob/main/wrf_preprocessor/vprm_preprocessor_new.py)

```
conda config --add channels conda-forge
conda config --set channel_priority strict
conda install -c conda-forge dask netCDF4
conda install esmf
conda install esmpy

pip install git+https://github.com/tglauch/pyVPRM.git
```

##### A.2.3 Land Cover map download

On the [Global Land Cover - Copernicus](https://lcviewer.vito.be/2019) website, in the menu bar, click on download. Several tiles will appear, click on the necessary tiles. Save in [copernicus](https://github.com/tglauch/pyVPRM_examples/tree/main/wrf_preprocessor/data/copernicus) folder.

![all text](https://github.com/rnoeliab/WRF-VPRM-Prepy/blob/main/imags/copernicus_tiles.png)


##### A.2.4 MODIS download

To download the necessary MODIS images, take into account the following:

<dt> Create a config.yaml and add <dt>

```
years: 
 - 2022
satellite: modis
sat_image_path: ./data/modis/
hvs:
 - [9,7]
 - [9,8]
 - [9,9]
 - [9,10]
 - [10,7]
```

<dt> Edit logins_draft.yaml <dt>

```
modis:
    - 'username'
    - 'pwd'
```

Both save in [sat_data_download](https://github.com/tglauch/pyVPRM_examples/tree/main/sat_data_download) and run:


```
python download_satellite_images.py --year 2022 --login_data logins_draft.yaml --config config.yaml 
```

##### A.2.4 Run vprm_preprocessor_new.py

Before running the vprm_preprocessor_new.py, it is necessary to be in the created environment. Don't forget to edit the [preprocessor_config.yaml](https://github.com/tglauch/pyVPRM_examples/blob/main/wrf_preprocessor/config/preprocessor_config.yaml), verify the data to be used (MODIS and copernicus). Finally, run:

```
python vprm_preprocessor_new.py --year 2022 --config ./config/preprocessor_config.yaml
```

**Note:**

<dt>If the domains to be run are large, it is recommended to use chunks (Ex: n_chunks = 4),<dt>

```
python vprm_preprocessor_new.py --year 2023 --config ./config/preprocessor_config.yaml --n_cpus=32 --chunk_x=4 --chunk_y=4
```

Finally,
<dt>This processing will generate the following files:<dt>

```
VPRM_input_EVI_2022.nc
VPRM_input_EVI_MAX_2022.nc
VPRM_input_EVI_MIN_2022.nc
VPRM_input_LSWI_2022.nc
VPRM_input_LSWI_MAX_2022.nc
VPRM_input_LSWI_MIN_2022.nc
VPRM_input_VEG_FRA_2022.nc
```

These files must be saved in: [bio_ghg](https://github.com/rnoeliab/WRF-VPRM-Prepy/tree/main/input/bio_ghg)

### B. Anthropogenic Emissions
Preparing the Anthropogenic emissions (EDGAR + Wetchart): 

#### EDGAR -- GHG emissions 

* Firstly - check if the "download_edgar_ghg.sh" script is ready to be executed:
```
$ chmod +x download_edgar_ghg.sh
$ ./download_edgar_ghg.sh
```
This code will download CO, CO2 and CH4 emissions data from different sources, except for fire emissions. 

* Secondly - run the "EDGARtoAE.py" script.
```
python EDGARtoAE.py
```

#### Wetchart -- Global 0.5-deg Wetland Methane Emissions

* Firstly - to download Wetland Methane Emissions data (WetCHARTs v1.3.1) it is necessary to enter the "[CMS: Global 0.5-deg Wetland Methane Emissions and Uncertainty](https://daac.ornl.gov/cgi-bin/dsviewer.pl?ds_id=1915)" website,

* Secondly - sign-in

* Thirdly - download monthly data from 2001 to 2019. 

For this case, we have chosen the model = 2913. For more information click on "[User Guide](https://daac.ornl.gov/CMS/guides/MonthlyWetland_CH4_WetCHARTs.html)"

```
Here is an example of how file names should be saved in the wetchart directory:

"../../input/anthr_ghg/wetchart/"
wchts_v1-3-1_model_2913_global_wet_ch4_monthly-2009.nc
```

This information will be necessary to run the [prep_edgar.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_edgar.py) script.

### C. Fire Emissions
Preparing the Fire emissions: 

* Firstly - to obtain fire emissions data from [GFAS website](https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-global-fire-emissions-gfas?tab=form), it is necessary to perform some previous steps:

```
1. Create ".cdsapirc" in the $HOME/ directory 
   gedit .cdsapirc &
2. to type:
   # To GFAS
   url: https://ads.atmosphere.copernicus.eu/api/v2
   key: <UID>:<APIKEY>
3. And, save.
```

* Secondly - modify the DATE and NAME from "[download_gfas_fire.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/libraries/download_gfas_fire.py)" script:

```
c.retrieve(
    'cams-global-fire-emissions-gfas',
    {
    'format':'netcdf',
    'variable':['altitude_of_plume_bottom', 
                'altitude_of_plume_top', 'injection_height', 
                'mean_altitude_of_maximum_injection', 
                'wildfire_flux_of_carbon_dioxide', 
                'wildfire_flux_of_methane',
                'wildfire_flux_of_carbon_monoxide'],
    'date':'2022-08-01/2022-08-31',      ### Change here
    },
    'gdas_fires.nc'                      #### change here 
    )
    
```

* Thirdly - run the script in our created environment :

```
$ python download_gfas_fire.py
```

This information will be necessary to run the [prep_gfas.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_gfas.py) script.


## D. Run main script

After preparing all the external information and obtaining the CO, CO2 and CH4 emissions from anthropogenic, biogenic and burned sources; the [WRF_Chem_PrepPy.py](https://github.com/rnoeliab/WRF-VPRM-Prepy/blob/main/pys/WRF_Chem_PrepPy.py) script will be executed.

```
$ python WRF_Chem_PrepPy.py
```

This script will generate the input files for the WRF-GHG model (for all domains):

```
wrfchemi_d0<domain>_<date>*
wrffire_d0<domain>_<date>*
vprm_input_d0<domain>_<date>*
```

## 1. Run the Background Fields

To prepare the chemical initial and boundary conditions to feed the WRF-GHG model, specifically for CO, CO2 and CH4, some steps must be carried out.

Due to the lack of CO2 information in different global platforms, only methane and carbon monoxide went through this pre-processing to modify the "wrfinput" and "wrfbdy" files. Remembering that these files are already generated by the WRF-GHG model.

This preprocessing is based on downloading information on the global concentration of CO and CH4 from the CAMS website, and adjusting both the horizontal and vertical dimensions appropriate for **wrfinput** and **wrfbdy**.

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

This script is linked with the files [submit_cds_ads_download.sh](https://github.com/rnoeliab/WRF-VPRM-Prepy/blob/main/pys/libraries/submit_cds_ads_download.sh) and [download_ghg_egg4.py](https://github.com/rnoeliab/WRF-VPRM-Prepy/blob/main/pys/libraries/download_ghg_egg4.py).


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

To start running scripts: A and B, it is recommended to have some files ready:

```
- wrfinput/wrfbdy
- CAMS data
- interp_indices.txt.npz
- ecmwf_coeffs_L137.csv
```

In [prep_initial_cond.py](https://github.com/rnoeliab/WRF-VPRM-Prepy/blob/main/pys/prep_initial_cond.py) and [prep_boundary_cond.py](https://github.com/rnoeliab/WRF-VPRM-Prepy/blob/main/pys/prep_boundary_cond.py) scripts: modify the number of domains and simulation time.


```
requested_domains = [ "d01", "d02","d03","d04"]
sim_time          = '2022-08-01 00:00:00','2022-08-15 23:00:00'       # check this!!
```

<dt> The start and end data in the sim_time should be similar to "namelist.input". CAMS data will be stored in both the wrfinput and wrfbdy files <dt>

After taking into account these modifications and running the scripts, the wrfinput and wrfbdy files will be modified, storing the CAMS information. Ready to run the WRF-GHG model.


#### NOAA data  -- (CO2)


```

```



