#!/usr/bin/python

from pathlib import Path
import pandas as pd
from nptdms import TdmsFile

COLUMNS = {
    "/'Azimuth'/'psp://139.229.171.3/PXIComm_NSV/Azimuth Angle Actual'": "azimuth_actual_angle",
    "/'Azimuth'/'psp://139.229.171.3/PXIComm_NSV/Azimuth Velocity Actual'": "azimuth_actual_velocity",
    "/'Azimuth'/'psp://139.229.171.3/PXIComm_NSV/Azimuth Torque Actual'" : "azimuth_actual_torque",
    "/'Elevation'/'psp://139.229.171.3/PXIComm_NSV/Elevation Angle Actual'" : "elevation_actual_angle",
    "/'Elevation'/'psp://139.229.171.3/PXIComm_NSV/Elevation Velocity Actual'" : "elevation_actual_velocity",
    "/'Elevation'/'psp://139.229.171.3/PXIComm_NSV/Elevation Torque Actual'" : "elevation_actual_torque",
}


def read_tdms(filename):
    tdms_file = TdmsFile(filename)
    df = tdms_file.
    for column in COLUMNS.keys():
        df[column] = tdms_file.object(column).data
    df.rename(columns=COLUMNS, inplace=True)
    return df


def main(filename):
    df = read_tdms(filename)
    df.to_csv(filename.replace(".tdms", ".csv"), index=False)


if __name__:
    filename = Path.home() / "TelemetryData_2023_11_21_23_10.tdms"
    main(str(filename))
