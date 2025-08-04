import cdsapi
import os

print("current directory:", os.getcwd())
newpath = os.getcwd() + "/data/"
print("New directory:",newpath)
os.chdir(newpath)

#print('Sending request for %s to CDS via the cdsapi'%(submitdate))
#print(submitdate,filename)

import cdsapi

c = cdsapi.Client()

c.retrieve(
    'cams-global-greenhouse-gas-inversion',
    {
        'version':'latest',
        'format':'zip',
        'variable':'methane',
        'quantity': 'concentration',
        'input_observations':'surface_satellite',
        'time_aggregation': 'instantaneous',
        'year': '2023',
        'month': [
            '01',
        ],
    },
    'CAMS-GIO-CH4-FC202301.zip')

