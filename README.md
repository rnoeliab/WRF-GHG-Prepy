# WRF-VPRM-PrepPy

The Weather Research and Forecasting (WRF) Model is a state of the art mesoscale numerical weather prediction system designed for both atmospheric research and operational forecasting applications. The model serves a wide range of meteorological applications across scales from tens of meters to thousands of kilometers. Coupled with the Vegetation Photosynthesis and Respiration Model (VPRM) (referred to as WRF-VPRM), has used to better understand the effects that mesoscale transport has on atmospheric CO2 distributions.

![all text](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/flowchart_vprm.png)

To run the WRF-VPRM model is necessary to have some data ready.  Therefore, a technique was created to prepare all CO2 and CH4 emissions from different sources (see figure above). The model needs external data (Biogenic, Anthropogenic and Fires Emissions), input and boundary conditions data (background data). 


### Preparing external data !!!

Here, we are using the WRF-VPRM v4.2.1 model:

- First of all, the model is run to have the **"wrfinput"** and **"wrfbdy"** files ready (only using **./real.exe**). Also, we need to have the **geo_em.d0#.nc** files saved.

Now, let's clone this repository in a linux/windows terminal:
- git clone "[https://github.com/rnoeliab/Inputs-WRF-VPRM.git](https://github.com/rnoeliab/Inputs-WRF-VPRM.git)"

Next, let's go to [pys](https://github.com/rnoeliab/Inputs-WRF-VPRM/tree/main/pys) directory:
- cd  Inputs-WRF-VPRM/pys/ 

Every time we execute a python script we must be in the **"vprm-envs"** environment, therefore, we have to perform this step before starting to run the WRF-VPRM preprocessing.

```
a. Have Anaconda installed ([Installing Anaconda](https://github.com/rnoeliab/Installing_anaconda))
b. conda env create -f environment.yml
c. conda activate vprm-envs 
```

## 1. Biogenic Emissions

This processing is divided into two parts: For the Kaplan model and for the VPRM code:

### 1.1. Kaplan model - Biogenic Methane

For CH4 fields, we need to have the CPOOL ([lpj_cpool_2000.nc](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/input/bio_ghg/ch4_bio/lpj_cpool_2000.nc)) and wetland ([global_wetland_kaplan.nc](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/input/bio_ghg/ch4_bio/global_wetland_kaplan.nc)) maps ready and also download the soil temperature data provided by ERA5 model, using the following step:

```
1. Create a user, log in and read How to use the CDS API:
   > https://cds.climate.copernicus.eu/api-how-to

2. Create ".cdsapirc" in the $HOME/ directory 
   > gedit .cdsapirc &
3. write the following:
   # To Meteo
   url: https://cds.climate.copernicus.eu/api/v2
   key: YOUR KEY
4. And, save.
```

Run the [download_era5_soiltemperature.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/download_era5_soiltemperature.py) script to obtain soil temperature data for the appropriate **year** and over our **study area**.

```
$ python download_era5_soiltemperature.py
```

**NOTE**  
Don't forget that it must be run within the vprm-envs environment

**READ HERE**
After carrying out these procedures, we are going to generate three files (see the [ch4_bio](https://github.com/rnoeliab/Inputs-WRF-VPRM/tree/main/input/bio_ghg/ch4_bio) directory), these files will be read by these three scripts:

- [prep_wetland_kaplan.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_wetland_kaplan.py), 
- [prep_cpool_lpj.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_cpool_lpj.py),
- [prep_T_ann.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_T_ann.py)

And, these scripts are within the WRF-VPRM-Prepy code

### 1.2. VPRM code

Here, we first need to get some files ready:

For CO2 fields, it is necessary to obtain EVI (daily, maximum and minimum), LSWI (daily, maximum and minimum) and vegetation fraction data. This data was obtained through preprocessing, by Theo.

```
VPRM_input_EVI_2022.nc
VPRM_input_EVI_MAX_2022.nc
VPRM_input_EVI_MIN_2022.nc
VPRM_input_LSWI_2022.nc
VPRM_input_LSWI_MAX_2022.nc
VPRM_input_LSWI_MIN_2022.nc
VPRM_input_VEG_FRA_2022.nc
```

## 2. Anthropogenic Emissions
Preparing the Anthropogenic emissions: 

Check if the "download_edgar_ghg.sh" script is ready to be executed:
```
$ chmod +x download_edgar_ghg.sh
$ ./download_edgar_ghg.sh
```
This code will download CO, CO2 and CH4 emissions data from different sources, except for fire emissions. The next step is to run the python script "EDGARtoAE.py". To do this step, we must take into account some points:

```
a. Have Anaconda installed ([Installing Anaconda](https://github.com/rnoeliab/Installing_anaconda))
b. conda env create -f environment.yml
c. conda activate vprm-envs 
d. python EDGARtoAE.py
```

This information will be necessary to run the "[prep_edgar.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_edgar.py)" script.

## 2. Fire Emissions
Preparing the Fire emissions: 

To obtain fire emissions data from [GFAS website](https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-global-fire-emissions-gfas?tab=form), it is necessary to perform some previous steps:

```
1. Create ".cdsapirc" in the $HOME/ directory 
   gedit .cdsapirc &
2. to type:
   # To GFAS
   url: https://ads.atmosphere.copernicus.eu/api/v2
   key: YOUR KEY
3. And, save.
```

The next step is modify the DATE and NAME from "[download_gfas_fire.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/download_gfas_fire.py)" script:
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
Then run the script in the environment "vprm-envs" :

```
$ python download_gfas_fire.py
```
This information will be necessary to run the "[prep_gfas.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_gfas.py)" script.


## 4. Background Fields
