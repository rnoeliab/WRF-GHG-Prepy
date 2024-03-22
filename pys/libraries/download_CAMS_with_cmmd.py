# Autor Sbotia
# Script for downloading CO global data from CAMS forecasts
# Downloads monthly data and converts it to netcdf
# TO check status of jobs in browser
    ## https://apps.ecmwf.int/webmars/joblist/

# July 9/2019 ECMWF changed the vertical resolution of the CAMS forecasting system
# https://atmosphere.copernicus.eu/node/472 
# https://www.ecmwf.int/en/forecasts/documentation-and-support/137-model-levels

# Nov 4/2022 Using the cdsapi download here, see last cell
# Updated by Noelia Rojas B. 15/03/2023

import sys,os,glob
import subprocess
import cdsapi
import pandas as pd
import numpy as np
from zipfile import ZipFile

year        = '2022'
monthi      = '08'
monthe      = '08'
target_time = pd.date_range(year+'-'+monthi+'-'+'01',year+'-'+monthe+'-'+'16',freq='5D')
target_tmes = pd.date_range(year+'-'+monthi+'-'+'01',year+'-'+monthe+'-'+'16',freq='1D')
days        = target_tmes.strftime("%d")

ite = target_time.shape
sps = ['carbon_monoxide','methane']

nowpath = os.getcwd()
print("Current directory:", nowpath)
for sp in sps:
    for date in np.arange(1,target_time.shape[0]):
        print(target_time[date-1].date(),target_time[date].date())
        
        submit_date = '%s/%s'%(target_time[date-1].date(),target_time[date].date())
        filename    = 'CAMS_GACF_large_%s_%s_%s'%(sp,target_time[date-1].date(),target_time[date].date())
        
        print("sh","submit_cds_ads_download.sh","%s"%(submit_date),"%s"%(filename),"%s"%(sp))
    #    subprocess.call(["sh","submit_cds_ads_download.sh","%s"%(submit_date),"%s"%(filename),"%s"%(sp)])    
        print(" ")
        
nowpath = os.getcwd()
print("Current directory:", nowpath)
os.chdir('../..')
zip = os.getcwd() + '/input/bck_ghg/zips/'
newpath = os.getcwd() + '/input/bck_ghg/unzips/'
print("New directory:", newpath)
os.chdir(newpath)

for sp in sps:
    for date in np.arange(1,target_time.shape[0]):
        filename    = 'CAMS_GACF_large_%s_%s_%s'%(sp,target_time[date-1].date(),target_time[date].date())
        zipdata = ZipFile(zip+filename)
        zipinfos = zipdata.infolist()

        # iterate through each file
        for zipinfo in zipinfos:
            # This will do the renaming
            zipinfo.filename = filename +'.nc'
            zipdata.extract(zipinfo)
        print("unzip ", filename)

#For CH4 and CO separately:
outputfilec = 'CAMS_GACF_large_carbon_monoxide_'+year+monthi
cmmd = 'cdo -b F64 mergetime CAMS_GACF_large_carbon_monoxide_*.nc ' + outputfilec+'.nc'
subprocess.call(cmmd,shell=True)
print('Processing finished,', outputfilec,'was created')

outputfilem = 'CAMS_GACF_large_methane_'+year+monthi
cmmd  = 'cdo -b F64 mergetime CAMS_GACF_large_methane_*.nc '+ outputfilem+'.nc'
subprocess.call(cmmd,shell=True)
print('Processing finished,', outputfilem,'was created')

#Join this files
filenameout = 'CAMS_GACF_large_co_ch4_'+year+monthi
cmmd  = 'cdo merged '+ outputfilec +'.nc '+outputfilem + '.nc '+filenameout+'.nc'
subprocess.call(cmmd,shell=True)
print('Processing finished,', filenameout,'was created')

# Separate by day
for i,d in enumerate(days):
    cmmd = 'cdo -merge -selday,'+str(i+1)+' ' + outputfilec +'.nc -selday,'+str(i+1)+' '+outputfilem + '.nc ' + 'CAMS_GACF_large_co_ch4_'+year+monthi+str(d)+'.nc'
    subprocess.call(cmmd,shell=True)
    print('CAMS_GACF_large_co_ch4_'+year+monthi+str(d)+'.nc','was created')

print('Processing finished')

