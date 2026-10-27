
from pathlib import Path
from ecmwf.opendata import Client

client = Client(source="ecmwf")

candidates = []

for step in (144, 360):
    try:
        latest = client.latest(
            stream="oper",
            type="tf",
            step=step,
            target="track.bufr",
        )
        candidates.append((latest, step))
        print(f"Found a {step}-hour track run: {latest}")
    except Exception as error:
        print(f"No usable {step}-hour run found: {error}")

if not candidates:
    raise RuntimeError("Could not locate an ECMWF track file.")

run_time, step = max(candidates, key=lambda item: item[0])

output = Path("ecmwf-track.bufr")

client.retrieve(
    stream="oper",
    type="tf",
    date=run_time.date(),
    time=run_time.hour,
    step=step,
    target=str(output),
)

if not output.exists() or output.stat().st_size == 0:
    raise RuntimeError("The downloaded track file is empty.")

print(f"Downloaded: {output}")
print(f"File size: {output.stat().st_size:,} bytes")
print(f"Forecast run: {run_time} UTC")
