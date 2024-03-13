# WRF-VPRM-PrepPy

The Weather Research and Forecasting (WRF) Model is a state of the art mesoscale numerical weather prediction system designed for both atmospheric research and operational forecasting applications. The model serves a wide range of meteorological applications across scales from tens of meters to thousands of kilometers. Coupled with the Vegetation Photosynthesis and Respiration Model (VPRM) (referred to as WRF-VPRM), has used to better understand the effects that mesoscale transport has on atmospheric CO2 distributions.

![all text](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/flowchart_vprm.png)

To run the WRF-VPRM model is necessary to have some data ready.  Therefore, a technique was created to prepare all CO2 and CH4 emissions from different sources (see figure above). The model needs external data (Biogenic, Anthropogenic and Fires Emissions), input and boundary conditions data (background data). 


## 1. Preparing external data !!!

Here, we are using the WRF-VPRM v4.2.1 model:

Firstly,

- Save the **"wrfinput"**, **"wrfbdy"** and **geo_em.d0#.nc** files in  the [wrf_inputs directory](https://github.com/rnoeliab/WRF-VPRM-Prepy/blob/main/input/wrf_inputs/)

Secondly,

- Clone this repository in a linux/windows terminal:
```
- git clone "[https://github.com/rnoeliab/Inputs-WRF-VPRM.git](https://github.com/rnoeliab/Inputs-WRF-VPRM.git)"
```

Thirdly,

- Run the scripts from the "[libraries](https://github.com/rnoeliab/Inputs-WRF-VPRM/tree/main/pys/libraries/)" directory, following the following sequence:

**NOTE**
Every time we execute a python script we must be in the **"vprm"** environment, therefore, we have to perform this step BEFORE starting to run the WRF-VPRM preprocessing.

```
a. Have Anaconda installed (https://github.com/rnoeliab/Installing_anaconda)
b. conda env create -f environment.yml
c. conda activate vprm 
```

### A. Biogenic Emissions

This processing is divided into two parts: For the Kaplan model and for the VPRM code:

#### A1. Kaplan model - Biogenic Methane

- For CH4 fields, we need to have the CPOOL ([lpj_cpool_2000.nc](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/input/bio_ghg/ch4_bio/lpj_cpool_2000.nc)) and wetland ([global_wetland_kaplan.nc](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/input/bio_ghg/ch4_bio/global_wetland_kaplan.nc)) maps ready, these are provided by this repository.

- Download the soil temperature data provided by ERA5 model, this is using the following step:

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
Don't forget that it must be run within the vprm environment

- The files, in [ch4_bio](https://github.com/rnoeliab/Inputs-WRF-VPRM/tree/main/input/bio_ghg/ch4_bio/), have to be ready to run the following scripts, which are located in the main script:

	- [prep_wetland_kaplan.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_wetland_kaplan.py), 
	- [prep_cpool_lpj.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_cpool_lpj.py),
	- [prep_T_ann.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_T_ann.py)


#### A2. VPRM code

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

### B. Anthropogenic Emissions
Preparing the Anthropogenic emissions (EDGAR + Wetchart): 

Firstly, 
- Check if the "download_edgar_ghg.sh" script is ready to be executed:
```
$ chmod +x download_edgar_ghg.sh
$ ./download_edgar_ghg.sh
```
This code will download CO, CO2 and CH4 emissions data from different sources, except for fire emissions. 

Secondly,
- Run the "EDGARtoAE.py" script.

```
python EDGARtoAE.py
```

Now, for wetchart:

- To download Wetland Methane Emissions data (WetCHARTs v1.3.1) it is necessary to enter the "[CMS: Global 0.5-deg Wetland Methane Emissions and Uncertainty](https://daac.ornl.gov/cgi-bin/dsviewer.pl?ds_id=1915)" website, sign-in and download monthly data from 2001 to 2019. For this case, we have chosen the model = 2913. For more information click on "[User Guide](https://daac.ornl.gov/CMS/guides/MonthlyWetland_CH4_WetCHARTs.html)"

```
Here is an example of the name structure of wetchars files:

wchts_v1-3-1_model_2913_global_wet_ch4_monthly-2009.nc
```


This information will be necessary to run the "[prep_edgar.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_edgar.py)" script.

### C. Fire Emissions
Preparing the Fire emissions: 

Firstly,
- To obtain fire emissions data from [GFAS website](https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-global-fire-emissions-gfas?tab=form), it is necessary to perform some previous steps:

```
1. Create ".cdsapirc" in the $HOME/ directory 
   gedit .cdsapirc &
2. to type:
   # To GFAS
   url: https://ads.atmosphere.copernicus.eu/api/v2
   key: <UID>:<APIKEY>
3. And, save.
```

Secondly,
- Modify the DATE and NAME from "[download_gfas_fire.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/libraries/download_gfas_fire.py)" script:

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
Finally,

- Run the script in the environment "vprm" :

```
$ python download_gfas_fire.py
```

This information will be necessary to run the "[prep_gfas.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_gfas.py)" script.


### D. Background Fields
- To obtain CO2 and CH4 data from background source, let's go to install MATLAB to run the script.
- To run the script is necessary to have wrfinput and wrfbdy ready to modify it.

```
$ python download_gfas_fire.py
```

## 2. Run main script

```
$ python .py
```

