
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

        print(f"Testing ensemble tracks at step={step}...")

        result = client.latest(
            stream="enfo",
            type="tf",
            step=step,
            target=str(output),
        )

        print(f"Selected run: {result}")

        if output.exists() and output.stat().st_size > 0:
            print(f"Downloaded {output.stat().st_size:,} bytes.")
            downloaded = True
            break

        print("No file was downloaded for this step.")

    except Exception as error:
        print(f"Step {step} failed: {error}")

if not downloaded:
    raise RuntimeError("No ensemble track file was downloaded.")

with output.open("rb") as file:
    message = codes_bufr_new_from_file(file)

    if message is None:
        raise RuntimeError("The downloaded file contains no readable BUFR message.")

    try:
        codes_set(message, "unpack", 1)

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
