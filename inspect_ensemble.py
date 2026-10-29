
from pathlib import Path
from eccodes import (
    codes_bufr_new_from_file,
    codes_set,
    codes_get_array,
    codes_release,
)

with open("ensemble-track.bufr", "rb") as file:
    message = codes_bufr_new_from_file(file)

    if message is None:
        raise RuntimeError("No BUFR message found.")

    try:
        codes_set(message, "unpack", 1)

        for key in (
            "ensembleMemberNumber",
            "latitude",
            "longitude",
            "timePeriod",
        ):
            values = codes_get_array(message, key)
            print(f"\n{key}: count={len(values)}")
            print(values[:30])

    finally:
        codes_release(message)



