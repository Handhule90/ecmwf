
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from eccodes import (
    codes_bufr_new_from_file,
    codes_get,
    codes_release,
    codes_set,
)

INPUT = Path("ecmwf-track.bufr")
OUTPUT = Path("storms.json")

MISSING = -1e90
MS_TO_KNOTS = 1.94384449


def get_value(message, key):
    """Return a decoded numeric value, or None if missing."""
    try:
        value = float(codes_get(message, key))
        if not math.isfinite(value) or value <= MISSING:
            return None
        return value
    except (ValueError, TypeError, RuntimeError):
        return None


def get_text(message, key):
    """Return a decoded text value, or None if unavailable."""
    try:
        value = str(codes_get(message, key)).strip()
        return value if value else None
    except Exception:
        return None


if not INPUT.exists():
    raise FileNotFoundError(f"Missing input file: {INPUT}")

storms = []
reference_time = None
messages_read = 0
records_skipped = 0

with INPUT.open("rb") as file:
    while True:
        message = codes_bufr_new_from_file(file)
        if message is None:
            break

        messages_read += 1

        try:
            codes_set(message, "unpack", 1)

            year = int(codes_get(message, "typicalYear"))
            month = int(codes_get(message, "typicalMonth"))
            day = int(codes_get(message, "typicalDay"))
            hour = int(codes_get(message, "typicalHour"))

            run_time = datetime(
                year, month, day, hour, tzinfo=timezone.utc
            )
            reference_time = run_time

            lat = get_value(message, "latitude")
            lon = get_value(message, "longitude")
            wind_ms = get_value(message, "windSpeedAt10M")
            lead = get_value(message, "timePeriod")
            storm_id = get_text(message, "stormIdentifier")

            # Coordinates are essential for displaying a map marker.
            if lat is None or lon is None:
                records_skipped += 1
                print(f"Skipping {storm_id}: missing coordinates")
                continue

            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                records_skipped += 1
                print(f"Skipping {storm_id}: invalid coordinates")
                continue

            record = {
                "id": storm_id,
                "latitude": lat,
                "longitude": lon,
                "wind_speed_ms": wind_ms,
                "wind_speed_knots": (
                    round(wind_ms * MS_TO_KNOTS, 2)
                    if wind_ms is not None else None
                ),
                "forecast_lead_hours": (
                    int(lead) if lead is not None else None
                ),
            }

            # Calculate a forecast valid time when a lead time is present.
            if lead is not None:
                valid_time = run_time + timedelta(hours=lead)
                record["valid_time_utc"] = (
                    valid_time.isoformat().replace("+00:00", "Z")
                )

            storms.append(record)
            print(
                f"Added {storm_id}: "
                f"({lat}, {lon}), lead={lead}"
            )

        finally:
            codes_release(message)

if reference_time is None:
    raise RuntimeError("No readable BUFR messages found.")

result = {
    "source": "ECMWF IFS tropical cyclone tracks",
    "attribution": (
        "Data from ECMWF, licensed under CC BY 4.0"
    ),
    "forecast_run_utc": (
        reference_time.isoformat().replace("+00:00", "Z")
    ),
    "messages_read": messages_read,
    "records_skipped": records_skipped,
    "storm_count": len(storms),
    "storms": storms,
}

OUTPUT.write_text(
    json.dumps(result, indent=2),
    encoding="utf-8",
)

print(f"\nMessages read: {messages_read}")
print(f"Records skipped: {records_skipped}")
print(f"Valid records: {len(storms)}")
print(f"JSON saved to: {OUTPUT}")
