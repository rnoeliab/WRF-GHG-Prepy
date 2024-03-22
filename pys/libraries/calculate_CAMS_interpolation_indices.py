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
    R=6371000  ## Radius of the earth in meters 
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
cams_path   = '/home/noelia/git-nonna/WRF-VPRM-Prepy-example/input/bck_ghg/unzips/';
geo_em_path = '/home/noelia/git-nonna/WRF-VPRM-Prepy-example/input/wrf_inputs/4d/';

# Specify output file
output_file = '/home/noelia/git-nonna/WRF-VPRM-Prepy-example/input/bck_ghg/matlab_original/cal_indices/results/interp_indices_4d.txt';

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

  for x1 in range(xlat.shape[0]):
    print(f'Domain {current_domain_idx}, longitude band #{x1+1}/{xlat.shape[0]}')
    for x2 in range(xlat.shape[1]):
      testdist = short_dist([xlat[x1, x2],xlong[x1, x2]],np.concatenate((mesh_lat.reshape(-1, 1), mesh_lon.reshape(-1, 1)), axis=1))
      mindist=np.min(testdist);
  #    print('The minimum distance found here is %f.'%mindist);
      dist2d = testdist.reshape(mesh_lat.shape)
      i, j = np.where(dist2d == mindist)
      indices[x1, x2, 0] = j[0]
      indices[x1, x2, 1] = i[0]

      variable_name = 'cams_indices_' + current_domain_idx
      globals()[variable_name] = indices

  variable_name = 'cams_indices_' + current_domain_idx
  globals()[variable_name] = indices

print(f'Saving output index matrices in into: {output_file}')
variables = [name for name in globals().keys() if name.startswith('cams_indices_')]
np.savez(output_file, **{var: globals()[var] for var in variables})

