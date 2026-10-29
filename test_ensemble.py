
from pathlib import Path
from ecmwf.opendata import Client
from eccodes import (
    codes_bufr_new_from_file,
    codes_get,
    codes_set,
    codes_release,
)

client = Client(source="ecmwf")
output = Path("ensemble-track.bufr")
downloaded = False

for step in (144, 360):
    try:
        output.unlink(missing_ok=True)

        latest = client.latest(
            stream="enfo",
            type="tf",
            step=step,
        )

        print(f"Selected ensemble run: {latest}")

        client.retrieve(
            stream="enfo",
            type="tf",
            date=latest.date(),
            time=latest.hour,
            step=step,
            target=str(output),
        )

        if output.exists() and output.stat().st_size > 0:
            print(f"Download successful: {output.stat().st_size:,} bytes")
            downloaded = True
            break

    except Exception as error:
        print(f"Step {step} failed: {error}")

if not downloaded:
    raise RuntimeError("Could not download ensemble track data.")

messages = 0

with output.open("rb") as file:
    while True:
        message = codes_bufr_new_from_file(file)
        if message is None:
            break

        messages += 1

        try:
            codes_set(message, "unpack", 1)

            if messages == 1:
                for key in (
                    "typicalYear",
                    "typicalMonth",
                    "typicalDay",
                    "typicalHour",
                    "stormIdentifier",
                    "number",
                    "perturbationNumber",
                    "latitude",
                    "longitude",
                    "timePeriod",
                ):
                    try:
                        print(f"{key}: {codes_get(message, key)}")
                    except Exception:
                        print(f"{key}: unavailable")
        finally:
            codes_release(message)

print(f"Total BUFR messages: {messages}")

if messages == 0:
    raise RuntimeError("Downloaded file contains no readable BUFR messages.")
