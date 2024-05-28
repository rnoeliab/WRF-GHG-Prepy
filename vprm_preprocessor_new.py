import os,sys
import pyVPRM
from pyVPRM.sat_managers.modis import modis
from pyVPRM.sat_managers.copernicus import copernicus_land_cover_map
from pyVPRM.lib.functions import lat_lon_to_modis, add_corners_to_1d_grid, parse_wrf_grid_file
from pyVPRM.VPRM import vprm
import yaml
import glob
import time
import numpy as np
import pandas as pd
import xarray as xr
import argparse
from shapely.geometry import box, Polygon
import geopandas as gpd
from datetime import datetime, timedelta
from pyproj import Transformer

def all_files_exist(item):
    for key in item.assets.keys():
        path = str(item.assets[key].href[7:])
        if not os.path.exists(path):
            print('{} does not exist. Skip'.format(path))
            return False
    return True


# Read command line arguments
p = argparse.ArgumentParser(
        description = "Commend Line Arguments",
        formatter_class = argparse.RawTextHelpFormatter)
p.add_argument("--config", type=str)
p.add_argument("--year", type=int)
p.add_argument("--n_cpus", type=int, default=1)
p.add_argument("--chunk_x", type=int, default=1)
p.add_argument("--chunk_y", type=int, default=1)

args = p.parse_args()
print(args)

this_year = int(args.year)
with open(args.config, "r") as stream:
    try:
        cfg  = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

out_grid = parse_wrf_grid_file(cfg['geo_em_file'], n_chunks=cfg['n_chunks'],
                              chunk_x=args.chunk_x, chunk_y=args.chunk_y)

days = pd.date_range(start="{}-01-01".format(this_year),
                     end="{}-12-31".format(this_year))
days = list(days)
hvs = np.unique([lat_lon_to_modis(out_grid['lat_b'].values.flatten()[i], 
                                  out_grid['lon_b'].values.flatten()[i]) 
                for i in range(len(out_grid['lat_b'].values.flatten()))],
                  axis=0)
print(hvs)
#Load the data
insts = []
for c, i in enumerate(hvs):
    file_collections = sorted([f for f in glob.glob(os.path.join(cfg['sat_image_path'], str(this_year),'*h{:02d}v{:02d}*.hdf'.format(i[0], i[1]))) if '.xml' not in f])
    
    if len(file_collections) == 0:
        continue

    new_inst = vprm(vprm_config_path = os.path.join(pyVPRM.__path__[0], 
                                                    'vprm_configs/copernicus_land_cover.yaml') ,
                    n_cpus=args.n_cpus)
                                 
    for c0, fpath in enumerate(file_collections):
        if cfg['satellite'] == 'modis':
            print(fpath)
            handler = modis(sat_image_path=fpath)
            handler.load() 
        elif cfg['satellite'] == 'viirs':
            print(fpath)
            handler = VIIRS(sat_image_path=fpath)
            handler.load()
        else:
            print('Set the satellite in the cfg either to modis or viirs.')

        if c0 == 0:
            trans = Transformer.from_crs('+proj=longlat +datum=WGS84',
                                           handler.sat_img.rio.crs)

            # To save memory crop satellite images to WRF grid
            x_a, y_a = trans.transform(out_grid['lon_b'], out_grid['lat_b'])
            b = box(float(np.min(x_a)), float(np.min(y_a)),
                    float(np.max(x_a)), float(np.max(y_a)))
            b = gpd.GeoSeries(Polygon(b), crs=handler.sat_img.rio.crs)
            b = b.scale(1.2, 1.2)
        handler.crop_box(b)

        if cfg['satellite'] == 'modis':
            new_inst.add_sat_img(handler, b_nir='sur_refl_b02', b_red='sur_refl_b01',
                                  b_blue='sur_refl_b03', b_swir='sur_refl_b06',
                                  which_evi='evi',
                                  drop_bands=True,
                                  timestamp_key='sur_refl_day_of_year',
                                  mask_bad_pixels=True,
                                  mask_clouds=True) 
        elif cfg['satellite'] == 'viirs':
            new_inst.add_sat_img(handler, b_nir='SurfReflect_I2', b_red='SurfReflect_I1',
                                  b_blue='no_blue_sensor', b_swir='SurfReflect_I3',
                                  which_evi='evi2',
                                  drop_bands=True)
                                  
    # Sort and merge satellite images
    new_inst.sort_and_merge_by_timestamp()
    
    # Apply lowess smoothing
    new_inst.lowess(keys=['evi', 'lswi'],
                   times=days,
                   frac=0.25, it=3) #0.2

    new_inst.clip_values('evi', 0, 1)
    new_inst.clip_values('lswi',-1, 1)
    new_inst.sat_imgs.sat_img = new_inst.sat_imgs.sat_img[['evi', 'lswi']]

    insts.append(new_inst)                                       
                                       
insts = np.array(insts)

if len(insts) == 0:
    print('No data found')
    
    out_grid = out_grid.rename({'x': 'west_east', 'y': 'south_north'})
    
    # Save to NetCDF files
    file_base = 'VPRM_input_'
    filename_dict = {'lswi': 'LSWI', 'evi': 'EVI', 'veg_fraction': 'VEG_FRA',
                 'lswi_max': 'LSWI_MAX', 'lswi_min': 'LSWI_MIN',
                 'evi_max': 'EVI_MAX', 'evi_min': 'EVI_MIN'}

    if not os.path.exists(cfg['out_path']):
       os.makedirs(cfg['out_path'])

    xr_dict = dict()

    #veg_type
    shp = list(out_grid['lon'].shape)
    ones = list(np.ones(shp))
    shp.insert(0,7)
    zeros = list(np.zeros(shp))
    zeros.append(ones)
    out_grid_vmap = out_grid.assign({'vegetation_fraction_map': (('vprm_classes', 'south_north', 'west_east'), zeros)})
    out_grid_vmap = out_grid_vmap.assign_coords({"vprm_classes": np.arange(1,9)})
    out_grid_vmap = out_grid_vmap.drop_dims(['x_b', 'y_b'])
    xr_dict['veg_fraction'] = out_grid_vmap
    print(out_grid_vmap)

    # min/max files
    for k in ['evi_min', 'evi_max', 'lswi_min', 'lswi_max']:
        shp = list(out_grid['lon'].shape)
        shp.insert(0,8)
        out_grid_t = out_grid.assign({k: (('vprm_classes', 'south_north', 'west_east'), np.zeros(shp))})
        out_grid_t = out_grid_t.assign_coords({'vprm_classes': np.arange(1,9)})
        xr_dict[k] = out_grid_t

    # evi / lswi files
    for k in ['evi', 'lswi']:
        shp = list(np.shape(list(np.zeros(out_grid['lon'].shape))))
        shp.insert(0, len(days))
        shp.insert(0,8)
        out_grid_t = out_grid.assign({k: (('vprm_classes', 'time', 'south_north', 'west_east'), np.zeros(shp))})
        out_grid_t = out_grid_t.assign_coords({'vprm_classes': np.arange(1,9)})
        out_grid_t = out_grid_t.assign_coords({'time': np.arange(1,len(days)+1)})
        xr_dict[k] = out_grid_t

    for key in xr_dict.keys():
        ofile = os.path.join(cfg['out_path'],file_base + filename_dict[key] +'_{}_part_{}_{}.nc'.format(this_year,
                                                                                                   args.chunk_x,
                                                                                                   args.chunk_y))
        if os.path.exists(ofile):
            os.remove(ofile)
        xr_dict[key].to_netcdf(ofile)
    exit()


vprm_inst = insts[0]
if len(insts) > 1:
    vprm_inst.add_vprm_insts(insts[1:])
    
print(vprm_inst.sat_imgs.sat_img)    
    
# Add the land cover map
if not os.path.exists(cfg['out_path']):
    os.makedirs(cfg['out_path'])
veg_file = os.path.join(cfg['out_path'], 'veg_map_on_modis_grid_{}_{}.nc'.format(args.chunk_x,
                                                                                 args.chunk_y))
print('Generate land cover map')

if os.path.exists(veg_file):
    vprm_inst.add_land_cover_map(veg_file)
    print("aqui")
else:
    regridder_path = os.path.join(cfg['out_path'], 'regridder_{}_{}_lcm.nc'.format(args.chunk_x,
                                                                                   args.chunk_y))
    handler_lt = None
    copernicus_data_path = cfg['copernicus_path']
    if os.path.isfile(copernicus_data_path):
        handler_lt = city_land_cover_map(copernicus_data_path)
        handler_lt.load()
    else:
        tiles_to_add = []
        for i, c in enumerate(glob.glob(os.path.join(copernicus_data_path, '*'))):
            print(c)
            temp_map = copernicus_land_cover_map(c)
            temp_map.load()
            dj = vprm_inst.is_disjoint(temp_map)
            if dj:
                continue
            print('Add {}'.format(c))
            if handler_lt is None:
                handler_lt = temp_map
            else:
                tiles_to_add.append(temp_map)

        handler_lt.add_tile(tiles_to_add, reproject=False)
    geom = box(*vprm_inst.sat_imgs.sat_img.rio.bounds())
    df = gpd.GeoDataFrame({"id":1,"geometry":[geom]})
    df = df.set_crs(vprm_inst.sat_imgs.sat_img.rio.crs)
    df = df.scale(1.1, 1.1)
    handler_lt.crop_to_polygon(df) 
    vprm_inst.add_land_cover_map(handler_lt, save_path=veg_file,
                                 regridder_save_path=regridder_path,
                                 mpi=True, logs=False)

regridder_path = os.path.join(cfg['out_path'], 'regridder_{}_{}.nc'.format(args.chunk_x,
                                                                            args.chunk_y))
print('Create regridder')
wrf_op = vprm_inst.to_wrf_output(out_grid, driver = 'xEMSF', # currently only xESMF works here when the WRF grid is 2D 
                                 regridder_save_path=regridder_path,
                                 mpi=True)

print(wrf_op)
# Save to NetCDF files
file_base = 'VPRM_input_'
filename_dict = {'lswi': 'LSWI', 'evi': 'EVI', 'veg_fraction': 'VEG_FRA',
                 'lswi_max': 'LSWI_MAX', 'lswi_min': 'LSWI_MIN', 
                 'evi_max': 'EVI_MAX', 'evi_min': 'EVI_MIN'} 
for key in wrf_op.keys():
    ofile = os.path.join(cfg['out_path'],file_base + filename_dict[key] +'_{}_part_{}_{}.nc'.format(this_year, args.chunk_x, args.chunk_y))
    if os.path.exists(ofile):
        os.remove(ofile)
    if ('lswi' in key) | ('evi' in key):
        t = wrf_op[key][key].loc[{'vprm_classes': 8}].values
        t[~np.isfinite(t)] = 0
        wrf_op[key][key].loc[{'vprm_classes': 8}] = t
    wrf_op[key].to_netcdf(ofile)                                                    
                                 
## python vprm_preprocessor_new.py --year 2023 --config ./config/preprocessor_config.yaml --chunk_x=1 --chunk_y=1
