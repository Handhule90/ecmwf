
from pathlib import Path
from eccodes import (
    codes_bufr_new_from_file,
    codes_get,
    codes_set,
    codes_release,
)

path = Path("ensemble-track.bufr")

with path.open("rb") as file:
    message_number = 0

    while True:
        message = codes_bufr_new_from_file(file)

        if message is None:
            break

        message_number += 1

        try:
            codes_set(message, "unpack", 1)

            print(f"\n--- Message {message_number} ---")

            for key in (
                "#1#stormIdentifier",
                "#1#ensembleMemberNumber",
                "#1#ensembleForecastType",
                "#1#year",
                "#1#month",
                "#1#day",
                "#1#hour",
                "#1#latitude",
                "#1#longitude",
                "#1#timePeriod",
            ):
                try:
                    print(f"{key}: {codes_get(message, key)}")
                except Exception:
                    print(f"{key}: unavailable")

        finally:
            codes_release(message)

print(f"\nMessages inspected: {message_number}")
