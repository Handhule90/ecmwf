
from pathlib import Path
from ecmwf.opendata import Client
from eccodes import (
    codes_bufr_new_from_file,
    codes_get,
    codes_release,
    codes_set,
)

client = Client(source="ecmwf")
output = Path("ensemble-track.bufr")

for step in (144, 360):
    try:
        result = client.latest(
    stream="enfo",
    type="tf",
    step=step,
    target=str(output),
)

if output.exists() and output.stat().st_size > 0:
    print(f"Downloaded: {result}")
    break

print("No file downloaded; trying the next step.")
    except Exception as error:
        print(f"Step {step}: {error}")
else:
    raise RuntimeError("No ensemble track file available.")

with output.open("rb") as file:
    message = codes_bufr_new_from_file(file)

    if message is None:
        raise RuntimeError("No BUFR message found.")

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
