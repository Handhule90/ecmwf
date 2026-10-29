
from pathlib import Path
from eccodes import (
    codes_bufr_new_from_file,
    codes_set,
    codes_get,
    codes_release,
)

with open("ensemble-track.bufr", "rb") as file:
    message_number = 0

    while True:
        message = codes_bufr_new_from_file(file)
        if message is None:
            break

        message_number += 1

        try:
            codes_set(message, "unpack", 1)

            if message_number > 5:
                break

            print(f"\n--- Message {message_number} ---")

            for key in (
                "numberOfSubsets",
                "compressedData",
                "#1#stormIdentifier",
                "#1#ensembleMemberNumber",
                "#1#ensembleForecastType",
                "#1#latitude",
                "#1#longitude",
                "#2#latitude",
                "#2#longitude",
                "#3#latitude",
                "#3#longitude",
                "#4#latitude",
                "#4#longitude",
                "#1#timePeriod",
                "#2#timePeriod",
            ):
                try:
                    print(f"{key}: {codes_get(message, key)}")
                except Exception:
                    print(f"{key}: unavailable")

        finally:
            codes_release(message)

print(f"\nMessages inspected: {min(message_number, 5)}")

