
from pathlib import Path
from eccodes import (
    codes_bufr_new_from_file,
    codes_get,
    codes_release,
    codes_set,
)

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

        try:
            codes_set(message, "unpack", 1)

            print(f"\nBUFR message {count}")

            for key in (
                "edition",
                "dataCategory",
                "numberOfSubsets",
                "typicalYear",
                "typicalMonth",
                "typicalDay",
                "typicalHour",
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
                    print(f"  {key}: {codes_get(message, key)}")
                except Exception:
                    pass

        finally:
            codes_release(message)

print(f"\nTotal BUFR messages: {count}")

if count == 0:
    raise RuntimeError("No readable BUFR messages found.")
