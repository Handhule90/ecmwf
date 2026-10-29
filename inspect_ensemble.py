
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

        print("Subsets:", codes_get(message, "numberOfSubsets"))
        print("Compressed:", codes_get(message, "compressedData"))

        for key in (
            "#1#latitude",
            "#2#latitude",
            "#3#latitude",
            "#1#longitude",
            "#2#longitude",
            "#3#longitude",
            "#1#timePeriod",
            "#2#timePeriod",
            "#3#timePeriod",
        ):
            try:
                values = codes_get_array(message, key)
                print(f"\n{key}: count={len(values)}")
                print(values[:10])
            except Exception as error:
                print(f"\n{key}: unavailable ({error})")

    finally:
        codes_release(message)




