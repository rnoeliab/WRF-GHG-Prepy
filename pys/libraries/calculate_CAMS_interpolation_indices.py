print('========================================================================')
print('Calculates inteprolation indices based on a currently used WRF domain and')
print('a selected CAMS forecast netcdf file. A major overhaul of matlab script from Julia Marshall')
print('Developed for in CoMet Reanalysis v3 and beyond')
print('Michal Galkowski, MPI-BGC Jena, 2020')
print('Translated for python by Noelia Rojas, IFUSP Brazil')
print('over the Amazon domain.')
print('========================================================================')

import os
import xarray as xr
import numpy as np

def short_dist(latlon1,latlon2):
    #And adaptation of lldistkm, to only use the faster Pythagoran method
    #which is wholly sufficent for distances <100 km.
    #Distance:
    # d1km: distance in km based on Haversine formula
    # (Haversine: http://en.wikipedia.org/wiki/Haversine_formula)
    # d2km: distance in km based on Pythagoras theorem
    # (see: http://en.wikipedia.org/wiki/Pythagorean_theorem)
    # After:
    # http://www.movable-type.co.uk/scripts/latlong.html
    #
    # --Inputs:
    #   latlon1: latlon of origin point [lat lon]
    #   latlon2: latlon of destination point [lat lon]
    #
    # --Outputs:
    #   d1km: distance calculated by Haversine formula
    #   d2km: distance calculated based on Pythagoran theorem
    #
    # --Example 1, short distance:
    #   latlon1=[-43 172];
    #   latlon2=[-44  171];
    #   [d1km d2km]=distance(latlon1,latlon2)
    #   d1km =
    #           137.365669065197 (km)
    #   d2km =
    #           137.368179013869 (km)
    #   %d1km approximately equal to d2km
    #
    # --Example 2, longer distance:
    #   latlon1=[-43 172];
    #   latlon2=[20  -108];
    #   [d1km d2km]=distance(latlon1,latlon2)
    #   d1km =
    #           10734.8931427602 (km)
    #   d2km =
    #           31303.4535270825 (km)
    #   d1km is significantly different from d2km (d2km is not able to work
    #   for longer distances).
    #
    # First version: 15 Jan 2012
    # Updated: 17 June 2012
    #--------------------------------------------------------------------------
    R=6371  ## Radius of the earth in kmeters 
    lat1=np.radians(latlon1[0])
    lat2=np.radians(latlon2[:,0])
    lon1=np.radians(latlon1[1])
    lon2=np.radians(latlon2[:,1])
    deltaLat=lat2-lat1;
    deltaLon=lon2-lon1;
    # a=(np.sin(delta_lat/2))*(np.sin(delta_lat/2))+(np.cos(lat1))*(np.cos(lat2))*(np.sin(delta_lon/2))*(np.sin(delta_lon/2))
    # c=2*np.arctan2(np.sqrt(a),np.sqrt(1-a))
    # d=R*c       ## Haversine distance

    x=deltaLon*np.cos((lat1+lat2)/2);
    y=deltaLat;
    d2km=R*np.sqrt(x*x + y*y);      #Pythagoran distance
    d2km
    return d2km

# Set directory and file paths
cams_path   = '../../input/bck_ghg/CAMS/unzips/';
geo_em_path = '../../input/wrf_inputs/';

# Specify output file
#output_file = '../../bck_ghg/';

filein = os.path.join(cams_path, 'CAMS_GACF_large_co_ch4_20220801.nc')

print('Lat Lon coordinates for CAMS read from file:\n %s'%filein);

requested_domains = [ "d01", "d02","d03","d04"];

for current_domain_idx in requested_domains:
  geo_em_file_path = os.path.join(geo_em_path, 'geo_em.'+current_domain_idx+'.nc');

  print('Reading geo_em file:\n  %s'%geo_em_file_path );
  xlat  = xr.open_dataset(geo_em_file_path)['XLAT_M'].values[0];
  xlong = xr.open_dataset(geo_em_file_path)['XLONG_M'].values[0];
  indices = np.zeros([xlat.shape[0],xlat.shape[1],2]);

  cams_lat = xr.open_dataset(filein)['latitude'];
  cams_lon = xr.open_dataset(filein)['longitude']; 
  mesh_lon, mesh_lat = np.meshgrid(cams_lon, cams_lat);

  print( 'Calculating distances between CAMS and WRF nodes using short_dist function'  ); 

  for x1 in range(xlat.shape[1]):
    print(f'Domain {current_domain_idx}, longitude band #{x1+1}/{xlat.shape[1]}')
    for x2 in range(xlat.shape[0]):
      testdist = short_dist([xlat[x2, x1],xlong[x2, x1]],np.concatenate((mesh_lat.reshape(-1, 1), mesh_lon.reshape(-1, 1)), axis=1))
      mindist=np.min(testdist);
      dist2d = testdist.reshape(mesh_lat.shape)
      j, i = np.where(dist2d == mindist)
#      print('The minimum distance found here is %f.'%mindist);
      indices[x2, x1, 0] = i[0]
      indices[x2, x1, 1] = j[0]

      variable_name = 'cams_indices_' + current_domain_idx
      globals()[variable_name] = indices

  variable_name = 'cams_indices_' + current_domain_idx
  globals()[variable_name] = indices

nowpath = os.getcwd()
print("Current directory:", nowpath)
os.chdir('../..')

output_file = os.getcwd() + '/input/bck_ghg/'

print(f'Saving output index matrices in into: {output_file}')
variables = [name for name in globals().keys() if name.startswith('cams_indices_')]
#print([**{var: globals()[var] for var in variables}])
np.savez(output_file+'interp_indices.txt', **{var: globals()[var] for var in variables})


