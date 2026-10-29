
from pathlib import Path
from eccodes import (
    codes_bufr_new_from_file,
    codes_set,
    codes_get,
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
            "numberOfSubsets",
            "stormIdentifier",
            "ensembleMemberNumber",
            "ensembleForecastType",
            "latitude",
            "longitude",
            "timePeriod",
        ):
            try:
                values = codes_get_array(message, key)
                print(f"\n{key}:")
                print(f"Count: {len(values)}")
                print(f"First 10: {values[:10]}")
            except Exception as error:
                print(f"\n{key}: unavailable ({error})")

    finally:
        codes_release(message)


