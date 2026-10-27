
from eccodes import (
    codes_bufr_new_from_file,
    codes_get,
    codes_release,
)

from pathlib import Path

path = Path("ecmwf-track.bufr")

if not path.exists():
    raise FileNotFoundError(f"Missing file: {path}")

count = 0

with path.open("rb") as file:
    while True:
        message = codes_bufr_new_from_file(file)

        if message is None:
            break

        count += 1

        
            from eccodes import codes_set, codes_get, codes_get_array

            codes_set(message, "unpack", 1)

            print("  Available keys:")
            for key in (
                "latitude",
                "longitude",
                "year",
                "month",
                "day",
                "hour",
                "minute",
                "timePeriod",
                "windSpeedAt10M",
                "stormIdentifier",
            ):
                try:
                    print(f"    {key}: {codes_get(message, key)}")
                except Exception:
                    pass


        try:
            print(f"BUFR message {count}")
            for key in (
                "edition",
                "dataCategory",
                "numberOfSubsets",
                "typicalYear",
                "typicalMonth",
                "typicalDay",
                "typicalHour",
            ):
                try:
                    print(f"  {key}: {codes_get(message, key)}")
                except Exception:
                    pass
        finally:
            codes_release(message)

print(f"\nTotal BUFR messages: {count}")

if count == 0:
    raise RuntimeError("No readable BUFR messages found.")
