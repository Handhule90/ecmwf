
from pathlib import Path
from eccodes import (
    codes_bufr_new_from_file,
    codes_set,
    codes_get_array,
    codes_release,
)
import numpy as np

MISSING = -1e90

with open("ensemble-track.bufr", "rb") as file:
    message = codes_bufr_new_from_file(file)

    if message is None:
        raise RuntimeError("No BUFR message found.")

    try:
        codes_set(message, "unpack", 1)

        for period in range(1, 11):
            try:
                lats = codes_get_array(message, f"#{period}#latitude")
                lons = codes_get_array(message, f"#{period}#longitude")
            except Exception:
                break

            valid = (
                np.isfinite(lats)
                & np.isfinite(lons)
                & (lats > -90)
                & (lats < 90)
                & (lons >= -180)
                & (lons <= 180)
            )

            print(
                f"Period {period}: "
                f"valid={np.count_nonzero(valid)}, "
                f"latitude_count={len(lats)}, "
                f"longitude_count={len(lons)}"
            )

    finally:
        codes_release(message)





