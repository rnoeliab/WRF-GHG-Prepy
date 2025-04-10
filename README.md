# WRF-GHG-PrepPy

<dt>Contributors: sbotia@bgc-jena.mpg.de  and Theo.Glauch@dlr.de  <dt><br />

The Weather Research and Forecasting (WRF) Model is a state of the art mesoscale numerical weather prediction system designed for both atmospheric research and operational forecasting applications. The model serves a wide range of meteorological applications across scales from tens of meters to thousands of kilometers. Furthermore, a coupled with the Vegetation Photosynthesis and Respiration Model (VPRM) (referred to as WRF-VPRM), has used to better understand the effects that mesoscale transport has on atmospheric CO2 distributions.

![all text](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/flowchart_vprm.png)

This module provides different preprocessing to prepare the different emissions inventories (from CO, CO2 and CH4) that will be necessary to run the WRF-GHG (or WRF-VPRM) model (chem_opt = 17). 

**Take into account:**

<dt>I. Firstly, run the scripts found in the "pys/libraries" directory.<dt>

<dt>II. Secondly, run the "WRF_GHG_PrepPy.py" script.<dt>

<dt>III. Finally run the "prep_initial" and "prep_boundary" script.<dt>


## 1. Preparing external data !!!

Here, we are using the WRF-VPRM v4.2.1 model:

* Firstly - clone this repository in a linux/windows terminal and create an environment to work this module (there is an example in the [input](https://github.com/rnoeliab/WRF-VPRM-Prepy/blob/main/input/) directory):

```
>> git clone https://github.com/rnoeliab/WRF-GHG-Prepy.git
```

* Secondly - save the **"wrfinput"**, **"wrfbdy"** and **geo_em.d0#.nc** files in  the [wrf_inputs directory](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/input/wrf_inputs/)


* Thirdly - run the scripts found inside the [libraries](https://github.com/rnoeliab/WRF-GHG-Prepy/tree/main/pys/libraries/) directory, depending on the following sequence:

**NOTE**

<dt>Every time we execute a python script we must be within our created environment .<dt>

(see [WRF-GHG-PrepPy Code](https://github.com/rnoeliab/WRF-GHG-Prepy/tree/main/input))

### A. Biogenic Emissions

This processing is divided into two parts: The Kaplan model and VPRM code:

#### A1. Kaplan model - Biogenic Methane (CH4)

Three data are necessary here: CPOOL and wetland maps, and soil temperature data). The first two are provided by this repository and the latest data is downloaded from the Copernicus platform.

1. CPOOL - [lpj_cpool_2000.nc](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/input/bio_ghg/ch4_bio/lpj_cpool_2000.nc)
2. wetland - [global_wetland_kaplan.nc](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/input/bio_ghg/ch4_bio/global_wetland_kaplan.nc)
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

These files, saved in the [ch4_bio](https://github.com/rnoeliab/WRF-GHG-Prepy/tree/main/input/bio_ghg/ch4_bio/) directory, are necessary to run the following scripts:

- [prep_wetland_kaplan.py](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/prep_wetland_kaplan.py), 
- [prep_cpool_lpj.py](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/prep_cpool_lpj.py),
- [prep_T_ann.py](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/prep_T_ann.py)

These scripts will be run at the end of processing, since they are incorporated within the main code.

#### A2. VPRM input 

To get the VPRM input, we'll need to go to Theo's processing: [pyVPRM](https://github.com/tglauch/pyVPRM/tree/main) and [pyVPRM_examples](https://github.com/tglauch/pyVPRM_examples). 

<dt> The pyVPRM repository has the scripts that will be used to preprocess the inputs VPRM. The pyVPRM_examples repository is an example of how it should be preprocessed. <dt>
<dt> <dt>

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

![all text](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/imags/copernicus_tiles.png)


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

These files must be saved in: [co2_bio](https://github.com/rnoeliab/WRF-GHG-Prepy/tree/main/input/bio_ghg/co2_bio)

**NOTE**  
Here I leave some files to run "vprm_preprocessor_new.py" as an example for large domains [vprm_input](https://github.com/rnoeliab/WRF-GHG-Prepy/tree/main/vprm_input).


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

This information will be necessary to run the [prep_edgar.py](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/prep_edgar.py) script.

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

* Secondly - modify the DATE and NAME from "[download_gfas_fire.py](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/libraries/download_gfas_fire.py)" script:

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

This information will be necessary to run the [prep_gfas.py](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/prep_gfas.py) script.


## D. Run main script

After preparing all the external information and obtaining the CO, CO2 and CH4 emissions from anthropogenic, biogenic and burned sources; the [WRF_GHG_PrepPy.py](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/pys/WRF_GHG_PrepPy.py) script will be executed.

```
$ python WRF_GHG_PrepPy.py
```

This script will generate the input files for the WRF-GHG model (for all domains), the file will be saved in [output](https://github.com/rnoeliab/WRF-GHG-Prepy/blob/main/output/):

```
wrfchemi_d0<domain>_<date>*
wrffire_d0<domain>_<date>*
vprm_input_d0<domain>_<date>*
```

Before running the WRF-GHG model, once all the emissions files are prepared, the next step is to determine the source of initial and boundary conditions. For this, we consider two CAMS products: the inversion-based dataset and the GACF dataset.


## 1. Run the Background Fields

To prepare the initial and boundary chemical conditions for the WRF-GHG model, specifically for CO, CO₂, and CH₄, a preprocessing step is carried out using datasets provided by CAMS.

Although CAMS offers multiple products (such as CAMS-Inversion and CAMS-GACF), only one product is selected per gas for use in the model. For CH₄, the CAMS-Inversion product was chosen; for CO, CAMS-GACF was used; and for CO₂, only the CAMS-Inversion product was selected.

These datasets were processed and incorporated into the "wrfinput" and "wrfbdy" files, which are initially generated by the WRF-GHG system using the ./real.exe utility.

The preprocessing involved downloading global concentration fields from the CAMS website and adjusting their horizontal and vertical dimensions to match the domain configuration used by the model.











## Extra: Errors with MODIS data

<dt> Some problems occurred when running "vprm". Therefore I share some files, in "Extra_files",that could solve these problems: <dt>
An exercise to do before running the vprm_preprocessor_new.py script:
Within the environment, open a terminal:


```
>> python
>> import rioxarray
>> ds = rioxarray.open_rasterio("MOD09A1.A2020049.h08v11.061.hdf")
```

#### NOAA data  -- (CO2)







```

```










