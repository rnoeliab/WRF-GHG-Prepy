import numpy as np
import pandas as pd
import netCDF4 as cdf
import xarray as xr
from datetime import datetime, timedelta
import os, time

# -----------------------------------------------------------------------------------
def process_co_gacf(wrfbdy_path, wrfinput_path, cams_dir, interp_index_file, ifs_ab_file):
    """Process CO boundary and tendencies using CAMS‑GACF (Script B logic)."""
    wrfbdy = xr.open_dataset(wrfbdy_path)
    wrfinput = xr.open_dataset(wrfinput_path)
    boundary_dates = [
        datetime.strptime(t.decode("utf-8"), '%Y-%m-%d_%H:%M:%S')
        for t in wrfbdy['Times'].values]
    
    dt = (boundary_dates[1] - boundary_dates[0])
    boundary_dates.append(boundary_dates[-1] + dt)

    bdy_secs = dt.total_seconds()
    bdy_date_strs = [d.strftime('%Y%m%d') for d in boundary_dates]
    cams_files = [os.path.join(cams_dir, f'CAMS_GACF_large_co_ch4_{d}.nc')
                  for d in bdy_date_strs]

    interp = np.load(interp_index_file)['cams_indices_d01']
    rawab = np.genfromtxt(ifs_ab_file, delimiter=",", skip_header=1)
    a, b = rawab[:,1].astype(float), rawab[:,2].astype(float)

    wrf_pressure = wrfinput['PB'].values[0] + wrfinput['P'].values[0]
    dummyX = np.zeros(wrfbdy['CO2_BIO_BXS'].shape)  ### (bdy_width: 5,bottom_top: 50,south_north: 160)
    dummyY = np.zeros(wrfbdy['CO2_BIO_BYS'].shape) ### (bdy_width: 5,bottom_top: 50,west_east: 347)
    nlev, n_sn, n_ew = dummyX.shape[2], dummyX.shape[3], dummyY.shape[3]

    # Set CO_BIO offsets (following B script)
    co_bxs = np.zeros((len(boundary_dates),) + dummyX.shape)
    co_bxe = np.zeros_like(co_bxs)
    co_bys = np.zeros((len(boundary_dates),) + dummyY.shape)
    co_bye = np.zeros_like(co_bys)

    for t, dt_now in enumerate(boundary_dates):
        ds = xr.open_dataset(cams_files[t])
        nc = cdf.Dataset(cams_files[t], 'r')
        posw = int(time.mktime(dt_now.timetuple()))
        camst = ds['time'].values
        posc = [int(time.mktime(pd.to_datetime(str(x)).timetuple())) for x in camst]
        if posw not in posc:
            print(f"Warning: CO time {dt_now} not in CAMS")
            continue
        idx = posc.index(posw)

        cams_co = nc.variables['co'][idx] * (28.97/28.01) * 1e6
        cams_lnsp = nc.variables['lnsp'][idx]
        cams_ps = np.exp(cams_lnsp)

        co_init = np.full((nlev, n_sn, n_ew), -999.)
        for lev in range(nlev):
            for j in  [i for i in range(5)] + [i for i in range(n_sn-5, n_sn)]:
                for i in range(n_ew):
                    lat_i = int(interp[j,i,1])
                    lon_i = int(interp[j,i,0])
                    ps = cams_ps[0,lat_i, lon_i]
                    cams_p = ps * b + a
                    wp = wrf_pressure[lev,j,i]
                    lev_i = np.abs(cams_p - wp).argmin()
                    co_init[lev,j,i] = cams_co[lev_i, lat_i, lon_i]

        for lev in range(nlev):
            for i in [i for i in range(5)] + [i for i in range(n_ew-5, n_ew)]:
                for j in range(n_sn):
                    lat_i = int(interp[j,i,1])
                    lon_i = int(interp[j,i,0])
                    ps = cams_ps[0,lat_i, lon_i]
                    cams_p = ps * b + a
                    wp = wrf_pressure[lev,j,i]
                    lev_i = np.abs(cams_p - wp).argmin()
                    co_init[lev,j,i] = cams_co[lev_i, lat_i, lon_i]
        
        if t < len(boundary_dates)-1:
            co_bxs[t] = np.transpose(co_init[:,:,0:5], (2,0,1))
            co_bxe[t] = np.transpose(co_init[:,:,-5:], (2,0,1))
            co_bys[t] = np.transpose(co_init[:,0:5,:], (1,0,2))
            co_bye[t] = np.transpose(co_init[:,-5:,:], (1,0,2))
        else:
            co_bxs = np.insert(co_bxs, co_bxs.shape[0], np.transpose(co_init[:,:,0:5], axes=(2, 0, 1)), 0)
            co_bxe = np.insert(co_bxe, co_bxe.shape[0], np.transpose(co_init[:,:,-5:], axes=(2, 0, 1)), 0)
            co_bys = np.insert(co_bys, co_bys.shape[0], np.transpose(co_init[:,0:5,:], axes=(1, 0, 2)), 0)
            co_bye = np.insert(co_bye, co_bye.shape[0], np.transpose(co_init[:,-5:,:], axes=(1, 0, 2)), 0)            

    # Interpolate odd timesteps
    for t in range(1, len(boundary_dates)-1, 2):
        for arr in (co_bxs,co_bxe,co_bys,co_bye):
            arr[t] = 0.5*(arr[t-1] + arr[t+1])

    # Compute tendencies
    co_btxs = (co_bxs[1:] - co_bxs[:-1]) / bdy_secs
    co_btxe = (co_bxe[1:] - co_bxe[:-1]) / bdy_secs
    co_btys = (co_bys[1:] - co_bys[:-1]) / bdy_secs
    co_btye = (co_bye[1:] - co_bye[:-1]) / bdy_secs

    # Write to WRF boundary file
    with cdf.Dataset(wrfbdy_path, 'r+') as nc:
        nc.variables['CO_BCK_BXS'][:] = co_bxs[:-1]
        nc.variables['CO_BCK_BXE'][:] = co_bxe[:-1]
        nc.variables['CO_BCK_BYS'][:] = co_bys[:-1]
        nc.variables['CO_BCK_BYE'][:] = co_bye[:-1]
        nc.variables['CO_BCK_BTXS'][:] = co_btxs
        nc.variables['CO_BCK_BTXE'][:] = co_btxe
        nc.variables['CO_BCK_BTYS'][:] = co_btys
        nc.variables['CO_BCK_BTYE'][:] = co_btye

    print("✅ CO processing complete.\n")

def process_gas_inversion(gases, wrfbdy_path, wrfinput_path, gas_configs):
    # Function to read WRF pressure field
    def read_wrf_pressure(path):
        with cdf.Dataset(path, 'r') as wrf_ds:
            wrf_pressure = wrf_ds.variables['PB'][0] + wrf_ds.variables['P'][0]
        return  wrf_pressure
    
    def get_boundary_dates(path):
        with cdf.Dataset(path) as wrfbdy_ds:
            times_raw = wrfbdy_ds.variables['Times'][:]
            times_str = ["".join([char.decode('utf-8') for char in row]) for row in times_raw]
            simstart_time_dt = datetime.strptime(times_str[0], "%Y-%m-%d_%H:%M:%S")
            simstart_time = simstart_time_dt.strftime("%Y%m%d")
            boundary_dates = [datetime.strptime(s, '%Y-%m-%d_%H:%M:%S') for s in times_str if s.strip()]
            bdy_interval_seconds = (boundary_dates[1] - boundary_dates[0]).total_seconds()
            bdy_interval_hours = bdy_interval_seconds / 3600
        return boundary_dates, bdy_interval_seconds

    def initialize_dummy_fields(wrfinput_path, wrfbdy_path):
        with cdf.Dataset(wrfinput_path) as input_ds:
            dummy_3d = np.full(input_ds.variables['CO2_BIO'][0].shape, -999.)

        with cdf.Dataset(wrfbdy_path) as bdy_ds:
            dummy_4d_X = np.full(bdy_ds.variables['CO2_BIO_BXS'].shape, -999.)
            dummy_4d_Y = np.full(bdy_ds.variables['CO2_BIO_BYS'].shape, -999.)
        return dummy_3d, dummy_4d_X, dummy_4d_Y

    def vertical_interp(wrf_pressure, cams_pressure, cams_field, a, b, interp_idx, nlev, n_sn, n_ew):
        result = np.full((nlev, n_sn, n_ew), -999.)
        for k in range(nlev):
            for j in list(range(5)) + list(range(n_sn - 5, n_sn)):
                for i in range(n_ew):
                    lat_i = int(interp_idx[j, i, 1])
                    lon_i = int(interp_idx[j, i, 0])
                    ps = cams_pressure[lat_i, lon_i]
                    cams_p = ps * b.astype(float) + a.astype(float)
                    wp = wrf_pressure[k, j, i]
                    lev_i = np.abs(cams_p - wp).argmin()
                    result[k, j, i] = cams_field[lev_i, lat_i, lon_i]
        for k in range(nlev):
            for i in list(range(5)) + list(range(n_ew - 5, n_ew)):
                for j in range(n_sn):
                    lat_i = int(interp_idx[j, i, 1])
                    lon_i = int(interp_idx[j, i, 0])
                    ps = cams_pressure[lat_i, lon_i]
                    cams_p = ps * b.astype(float) + a.astype(float)
                    wp = wrf_pressure[k, j, i]
                    lev_i = np.abs(cams_p - wp).argmin()
                    result[k, j, i] = cams_field[lev_i, lat_i, lon_i]
        return result

    # --- Preparaciones generales ---
    wrf_pressure = read_wrf_pressure(wrfinput_path)
    boundary_dates, bdy_secs = get_boundary_dates(wrfbdy_path)
    dummy_3d, dummy_4d_X, dummy_4d_Y = initialize_dummy_fields(wrfinput_path, wrfbdy_path)
    nlev, n_sn, n_ew = dummy_3d.shape

    for gas in gases:
        print(f"🔁 Processing gas: {gas}")
        config = gas_configs[gas]
        cams_ds = xr.open_dataset(config['cams_file']).load()
        interp_idx = np.load(config['interp_file'])['cams_indices_d01']
        if gas == 'CO2':
            a = cams_ds['ap'].values
            b = cams_ds['bp'].values
            conversion = 1e6
            gas_field = 'CO2'
            default_value = 400

            with cdf.Dataset(wrfbdy_path, 'r+') as ncid_bdy:
                value_array = default_value * np.ones((1, 5, nlev, n_sn))
                expanded_array = np.repeat(value_array, len(boundary_dates), axis=0)
                ncid_bdy.variables['CO2_BIO_BXS'][:] = expanded_array.astype('float32')
                ncid_bdy.variables['CO2_BIO_BXE'][:] = expanded_array.astype('float32')

                value_array = default_value * np.ones((1, 5, nlev, n_ew))
                expanded_array = np.repeat(value_array, len(boundary_dates), axis=0)
                ncid_bdy.variables['CO2_BIO_BYS'][:] = expanded_array.astype('float32')
                ncid_bdy.variables['CO2_BIO_BYE'][:] = expanded_array.astype('float32')

        else:  # CH4
            a = cams_ds['hyai'].values
            b = cams_ds['hybi'].values
            conversion = 1e-3
            gas_field = 'CH4'
            default_value = 1.8

            with cdf.Dataset(wrfbdy_path, 'r+') as ncid_bdy:
                value_array = default_value * np.ones((1, 5, nlev, n_sn))
                expanded_array = np.repeat(value_array, len(boundary_dates), axis=0)
                for v in ['CH4_BIO_BXS', 'CH4_BIO_BXE', 'CH4_BIO_Soils_BXS', 'CH4_BIO_Soils_BXE']:
                    ncid_bdy.variables[v][:] = expanded_array

                value_array = default_value * np.ones((1, 5, nlev, n_ew))
                expanded_array = np.repeat(value_array, len(boundary_dates), axis=0)
                for v in ['CH4_BIO_BYS', 'CH4_BIO_BYE', 'CH4_BIO_Soils_BYS', 'CH4_BIO_Soils_BYE']:
                    ncid_bdy.variables[v][:] = expanded_array

        # Output arrays
        gas_bxs = np.full((len(boundary_dates),) + dummy_4d_X[0].shape, -999.)
        gas_bxe = np.full_like(gas_bxs, -999.)
        gas_bys = np.full((len(boundary_dates),) + dummy_4d_Y[0].shape, -999.)
        gas_bye = np.full_like(gas_bys, -999.)

        gas_btxs = np.zeros_like(gas_bxs)
        gas_btxe = np.zeros_like(gas_bxe)
        gas_btys = np.zeros_like(gas_bys)
        gas_btye = np.zeros_like(gas_bye)

        for t_idx, t in enumerate(boundary_dates):
            t64 = np.datetime64(t).astype('datetime64[ns]')
            time_i = np.where(cams_ds['time'].values == t64)[0]
            if len(time_i) == 0:
                print(f"⏳ Skipping CAMS time {t}")
                continue

            time_i = int(time_i[0])
            gas_cams = cams_ds[gas_field].isel(time=time_i).values * conversion
            cams_ps = cams_ds['Psurf' if gas == 'CO2' else 'ps'].isel(time=time_i).values

            interpolated_field = vertical_interp(wrf_pressure, cams_ps, gas_cams, a, b, interp_idx, nlev, n_sn, n_ew)

            tx = np.transpose(interpolated_field[:, :, 0:5], (2, 0, 1))
            te = np.transpose(interpolated_field[:, :, -5:], (2, 0, 1))
            ts = np.transpose(interpolated_field[:, 0:5, :], (1, 0, 2))
            tn = np.transpose(interpolated_field[:, -5:, :], (1, 0, 2))

            gas_bxs[t_idx] = tx
            gas_bxe[t_idx] = te
            gas_bys[t_idx] = ts
            gas_bye[t_idx] = tn

        gas_btxs[-1] = gas_btxs[-2]
        gas_btxe[-1] = gas_btxe[-2]
        gas_btys[-1] = gas_btys[-2]
        gas_btye[-1] = gas_btye[-2]

        # Tendencies
        print(f'📈 Computing tendencies for {gas}')
        for time_idx in range(len(boundary_dates)-1):
            for x in range(n_sn):
                for lvl_idx in range(nlev):
                    for y in range(gas_bxs.shape[1]):
                        gas_btxs[time_idx,y,lvl_idx,x] = (gas_bxs[time_idx+1,y,lvl_idx,x] - gas_bxs[time_idx,y,lvl_idx,x]) / bdy_secs
                        gas_btxe[time_idx,y,lvl_idx,x] = (gas_bxe[time_idx+1,y,lvl_idx,x] - gas_bxe[time_idx,y,lvl_idx,x]) / bdy_secs
            for x in range(n_ew):
                for lvl_idx in range(nlev):
                    for y in range(gas_bys.shape[1]):
                        gas_btys[time_idx,y,lvl_idx,x] = (gas_bys[time_idx+1,y,lvl_idx,x] - gas_bys[time_idx,y,lvl_idx,x]) / bdy_secs
                        gas_btye[time_idx,y,lvl_idx,x] = (gas_bye[time_idx+1,y,lvl_idx,x] - gas_bye[time_idx,y,lvl_idx,x]) / bdy_secs

        # Write to file
        bname = gas.upper()
        var_names = [f'{bname}_BCK_BXS', f'{bname}_BCK_BXE', f'{bname}_BCK_BYS', f'{bname}_BCK_BYE',
                     f'{bname}_BCK_BTXS', f'{bname}_BCK_BTXE', f'{bname}_BCK_BTYS', f'{bname}_BCK_BTYE']

        with cdf.Dataset(wrfbdy_path, 'r+') as nc:
            nc.variables[var_names[0]][:] = gas_bxs
            nc.variables[var_names[1]][:] = gas_bxe
            nc.variables[var_names[2]][:] = gas_bys
            nc.variables[var_names[3]][:] = gas_bye
            nc.variables[var_names[4]][:] = gas_btxs
            nc.variables[var_names[5]][:] = gas_btxe
            nc.variables[var_names[6]][:] = gas_btys
            nc.variables[var_names[7]][:] = gas_btye

        print(f"✅ Finished {gas}")

def main():
    root = '/path/'
    wrfbdy = os.path.join(root, 'wrfbdy_d01')
    wrfinput = os.path.join(root, 'wrfinput_d01')

    gas_configs = {
        'CO2': {
            'cams_file': '/path-CAMS-inversion/data/cams73_latest_co2_conc_satellite_inst_202301_upgrade.nc',
            'interp_file': '/path-interp_indices.txt.npz'
        },
        'CH4': {
            'cams_file': '/path-CAMS-inversion/data/cams73_latest_ch4_conc_surface_satellite_inst_202301.nc',
            'interp_file': '/path-interp_indices.txt.npz'
        }
    }

    process_gas_inversion(['CO2', 'CH4'], wrfbdy, wrfinput, gas_configs)
    print("🎉 All gases processed successfully!")



    # CO: CAMS-GACF
#    process_co_gacf(
#        wrfbdy,
#        wrfinput,
#        cams_dir='../input/bck_ghg/CAMS/unzips/',
#        interp_index_file='../input/bck_ghg/interp_indices_GACF_d03.txt.npz',
#        ifs_ab_file='../input/bck_ghg/ecmwf_coeffs_L137.csv'
#    )

    # CO2 and CH4: CAMS-inversion
    # adjust file paths as needed

if __name__ == '__main__':
    main()
