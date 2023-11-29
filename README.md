# WRF-VPRM-PrepPy

The Weather Research and Forecasting (WRF) Model is a state of the art mesoscale numerical weather prediction system designed for both atmospheric research and operational forecasting applications. The model serves a wide range of meteorological applications across scales from tens of meters to thousands of kilometers. Coupled with the Vegetation Photosynthesis and Respiration Model (VPRM) (referred to as WRF-VPRM), has used to better understand the effects that mesoscale transport has on atmospheric CO2 distributions.

To run WRF-VPRM is necessary to prepare some data such as input (Anthropogenic, Fires and Biogenic Emissions) and Boundary conditions.

Therefore, a pre-processing tô obtain the input fields tô run WRF-VPRM v4.2.1 model is executed here.

First, clone this repository in a linux/windows terminal:
- git clone "[https://github.com/rnoeliab/Inputs-WRF-VPRM.git](https://github.com/rnoeliab/Inputs-WRF-VPRM.git)"

Second, go to [pys](https://github.com/rnoeliab/Inputs-WRF-VPRM/tree/main/pys) directory:
- cd  Inputs-WRF-VPRM/pys/ 

## 1. Anthropogenic Emissions
Preparing the Anthropogenic emissions: 

Check if the "download_edgar_ghg.sh" script is ready to be executed:
```
$ chmod +x download_edgar_ghg.sh
$ ./download_edgar_ghg.sh
```
This code will download CO, CO2 and CH4 emissions data from different sources, except for fire emissions. The next step is to run the python script "EDGARtoAE.py". To do this step, we must take into account some points:

```
a. Have Anaconda installed ([Installing Anaconda](https://github.com/rnoeliab/Installing_anaconda))
b. conda create -n vprm python==3.8 
c. conda activate vprm
d. conda install -c conda-forge xarray dask netCDF4 bottleneck
e. python EDGARtoAE.py
```

This information will be necessary to run the "[prep_edgar.py](https://github.com/rnoeliab/Inputs-WRF-VPRM/blob/main/pys/prep_edgar.py)" script.

## 2. Fire Emissions
Preparing the Fire emissions: 

To obtain fire emissions data from GFAS (), it is necessary to perform some previous steps:

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
Then run the script:

```
$ create activate vprm
$ conda install -c conda-forge cdsapi
$ python download_gfas_fire.py
```

## 3. Biogenic Emissions
Preparing the Biogenic emissions: 

Here, we go to 


```
1. Create ".cdsapirc" in the $HOME/ directory 
   gedit .cdsapirc &
2. to type:
   # To Meteo
   url: https://cds.climate.copernicus.eu/api/v2
   key: YOUR KEY
3. And, save.
```


## 4. Background Fields
