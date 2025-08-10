from pathlib import Path

import numpy as np
import pendulum
from netCDF4 import Dataset


def wrf_to_fsl(wrf_file_path: Path, out_file: Path):
    tm_str = " ".join(wrf_file_path.stem.split("_")[-2:])
    file_date = pendulum.parse(tm_str)
    # Open the WRF file
    wrf_file = Dataset(wrf_file_path, "r")
    # out_file = Path('/home/wrf_model/aermod/aermet/ua', wrf_file_path.stem).with_suffix('.fsl')

    # Determine the centroid indices for the WRF grid
    nx = wrf_file.dimensions["west_east"].size
    ny = wrf_file.dimensions["south_north"].size

    centroid_x = nx // 2
    centroid_y = ny // 2

    # Extract the variables needed for FSL from the centroid
    pressure = (
        wrf_file.variables["P"][:, :, centroid_y, centroid_x]
        + wrf_file.variables["PB"][:, :, centroid_y, centroid_x]
    )  # Total pressure in Pa
    temperature = (
        -wrf_file.variables["T"][:, :, centroid_y, centroid_x] + 300
    )  # Potential temperature in K
    u_wind = wrf_file.variables["U"][:, :, centroid_y, centroid_x]
    v_wind = wrf_file.variables["V"][:, :, centroid_y, centroid_x]
    height = (
        wrf_file.variables["PH"][:, :, centroid_y, centroid_x]
        + wrf_file.variables["PHB"][:, :, centroid_y, centroid_x]
    )  # Geopotential height in m^2/s^2
    qvapor = wrf_file.variables["QVAPOR"][:, :, centroid_y, centroid_x]  # Specific humidity (kg/kg)

    # Convert geopotential height to meters
    height_m = height / 9.81  # Height in meters above sea level

    # Calculate wind speed and direction
    wind_speed = np.sqrt(u_wind**2 + v_wind**2)  # Wind speed in m/s
    wind_direction = np.arctan2(v_wind, u_wind) * (180 / np.pi)
    wind_direction = (wind_direction + 360) % 360  # Ensure wind direction is between 0-360 degrees

    # Calculate temperature in Celsius
    temp_celsius = temperature - 273.15  # Convert temperature from K to C

    # Calculate dew point temperature in Celsius
    dew_point_celsius = temp_celsius - ((100 - (qvapor * 1000)) / 5)

    # Example date and location

    latitude = wrf_file.variables["XLAT"][0, centroid_y, centroid_x]  # Latitude of the centroid
    longitude = wrf_file.variables["XLONG"][0, centroid_y, centroid_x]  # Longitude of the centroid

    # Prepare the FSL file content
    fsl_content = ""

    # Loop through 24 hours to create separate FSL records for each hour
    for hour in range(6):
        dt = file_date.add(hours=hour)

        # Generate FSL formatted data for the remaining levels
        data_rows = []
        for i in range(len(pressure[hour])):
            pres_hpa = pressure[hour][i] / 100 * 10  # Convert Pa to hPa
            hgt_m = height_m[hour][i] - height_m[hour][0]  # Height in meters above ground level
            temp_c = temp_celsius[hour][i]
            dew_c = dew_point_celsius[hour][i]
            wspd_knots = int(wind_speed[hour][i] * 10)  # Convert m/s to knots
            wdir_deg = int(wind_direction[hour][i])

            data_rows.append((pres_hpa, hgt_m, temp_c, dew_c, wdir_deg, wspd_knots))

        # Sort by pressure descending to ensure correct order
        data_rows.sort(reverse=True, key=lambda x: x[0])

        # Create the header for each hour
        header = f"    254 {dt.hour:6d} {dt.day:6d} {dt.strftime('%b').upper():>8} {dt.year:7d}\n"
        fsl_content += header

        # Metadata lines
        metadata_1 = f"      1  54823  54823  {latitude:5.2f}N{abs(longitude):6.2f}W     0  99999\n"
        metadata_2 = f"      2  99999  99999  99999     {len(data_rows) + 4}  99999  99999\n"
        metadata_3 = f"      3         JINAN                99999     ms\n"

        fsl_content += metadata_1 + metadata_2 + metadata_3

        # Add the sorted data rows with the correct level types
        for idx, (pres_hpa, hgt_m, temp_c, dew_c, wdir_deg, wspd_knots) in enumerate(data_rows):
            if idx == 0:
                level_type = 9  # Surface level
            elif pres_hpa in [1000, 850, 700, 500, 400, 300, 250, 200, 150, 100]:
                level_type = 4  # Mandatory level
            else:
                level_type = 5  # Significant level

            # Align the output according to the example
            wspd_knots = 1 if wspd_knots < 1 else wspd_knots

            fsl_content += (
                f"{level_type:7} {int(pres_hpa):6} {int(hgt_m):6} {int(temp_c):6} {int(dew_c):6} {int(wdir_deg):6} {int(wspd_knots):6}\n"
            )

    # Save the complete FSL data to a file
    with open(out_file, "a") as f:
        f.write(fsl_content)

    # Close the WRF file
    wrf_file.close()

    print("FSL file generated successfully!")
    return ""


def run():
    print("run")
    st = pendulum.parse("2024-10-01")
    et = pendulum.parse("2024-10-31")
    out_file = Path("/home/wrf_model/aermod/aermet/ua", "wrf.fsl")
    while st < et:
        tm = st
        file_path = Path(
            "/home/wrf_model/data/wrf_data",
            f"wrfout_d03_{tm.to_date_string()}_{tm.to_time_string()}",
        )
        print(file_path)
        if file_path.is_file():
            wrf_to_fsl(wrf_file_path=file_path, out_file=out_file)
        st = st.add(hours=6)


if __name__ == "__main__":
    # pf = Path('/home/wrf_model/data/wrf_data/wrfout_d03_2024-10-04_00:00:00')
    # print(pf.stem)
    # wrf_to_fsl(wrf_file_path=Path('/home/wrf_model/data/wrf_data/wrfout_d03_2024-10-05_00:00:00'))
    # wrf_to_fsl(wrf_file_path=Path('/home/wrf_model/data/wrf_data/wrfout_d03_2024-10-05_06:00:00'))
    # wrf_to_fsl(wrf_file_path=Path('/home/wrf_model/data/wrf_data/wrfout_d03_2024-10-05_12:00:00'))
    # wrf_to_fsl(wrf_file_path=Path('/home/wrf_model/data/wrf_data/wrfout_d03_2024-10-05_18:00:00'))
    run()
