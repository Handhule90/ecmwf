
from pathlib import Path
from ecmwf.opendata import Client

client = Client(source="ecmwf")
output = Path("ensemble-track.bufr")

for step in (144, 360):
    try:
        print(f"Testing ensemble tracks at step={step}...")

        result = client.latest(
            stream="enfo",
            type="tf",
            step=step,
            target=str(output),
        )

        print(f"Found ensemble run: {result}")

        if output.exists() and output.stat().st_size > 0:
            print(f"SUCCESS! Downloaded {output.stat().st_size:,} bytes.")
            break

    except Exception as error:
        print(f"Step {step} unavailable: {error}")
else:
    raise RuntimeError("No usable ensemble track file was downloaded.")

