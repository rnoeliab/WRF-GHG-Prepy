# WRF-VPRM-PrepPy

The Weather Research and Forecasting (WRF) Model is a state of the art mesoscale numerical weather prediction system designed for both atmospheric research and operational forecasting applications. The model serves a wide range of meteorological applications across scales from tens of meters to thousands of kilometers. Coupled with the Vegetation Photosynthesis and Respiration Model (VPRM) (referred to as WRF-VPRM), has used to better understand the effects that mesoscale transport has on atmospheric CO2 distributions.

To run WRF-VPRM is necessary to prepare some data such as input (Anthropogenic, Fires and Biogenic Emissions) and Boundary conditions.

Therefore, a pre-processing tô obtain the input fields tô run WRF-VPRM v4.2.1 model is executed here.

First, clone this repository in a linux/windows terminal:
- git clone "[https://github.com/rnoeliab/Inputs-WRF-VPRM.git](https://github.com/rnoeliab/Inputs-WRF-VPRM.git)"

Second, go to [pys](https://github.com/rnoeliab/Inputs-WRF-VPRM/tree/main/pys) directory:
- cd  Inputs-WRF-VPRM/pys/ 

## 1. Anthropogenic Emissions
Preparing Anthropogenic emissions: 

Check if the "download_edgar_ghg.sh" script is ready to be executed, if not, write:

- chmod +x download_edgar_ghg.sh

then, run:

- ./download_edgar_ghg.sh

This code will download CO, CO2 and CH4 emissions data from different sources. This information will be necessary to 

The next step is to run the python script "EDGARtoAE.py". To do this step, we must take into account some points:

>> Have Anaconda installed ([Installing Anaconda](https://github.com/rnoeliab/Installing_anaconda))
>> conda create -n vprm python==3.8 
>> conda activate vprm
>> conda install -c conda-forge xarray dask netCDF4 bottleneck

-  


run the download.sh code

## 2. Fires Emissions

## 3. Biogenic Emissions

## 4. Background Fields
