
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from eccodes import (
    codes_bufr_new_from_file,
    codes_get,
    codes_release,
    codes_set,
    codes_keys_iterator_new,
    codes_keys_iterator_next,
    codes_keys_iterator_get_name,
    codes_keys_iterator_delete,
)

INPUT = Path("ecmwf-track.bufr")
OUTPUT = Path("storms.json")

MISSING = -1e90
MS_TO_KNOTS = 1.94384449


def get_value(message, key):
    """Read a valid numeric BUFR value."""
    try:
        value = float(codes_get(message, key))
        if not math.isfinite(value) or value <= MISSING:
            return None
        return value
    except Exception:
        return None


def get_text(message, key):
    """Read a text BUFR value."""
    try:
        value = str(codes_get(message, key)).strip()
        return value or None
    except Exception:
        return None


def iso_utc(value):
    return value.astimezone(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


def inspect_keys(message):
    """Print relevant available keys from the first BUFR message."""
    print("\n--- BUFR key diagnostic ---")

    iterator = codes_keys_iterator_new(message)

    try:
        while codes_keys_iterator_next(iterator):
            key = codes_keys_iterator_get_name(iterator)

            if any(term in key.lower() for term in (
                "storm",
                "track",
                "latitude",
                "longitude",
                "timeperiod",
                "timestep",
                "step",
                "wind",
                "pressure",
                "subset",
                "descriptor",
            )):
                try:
                    value = codes_get(message, key)
                except Exception:
                    value = "<unavailable>"

                print(f"{key}: {value}")
    finally:
        codes_keys_iterator_delete(iterator)


if not INPUT.exists():
    raise FileNotFoundError(f"Missing input file: {INPUT}")

records = []
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

            if messages_read == 1:
                inspect_keys(message)

            year = int(codes_get(message, "typicalYear"))
            month = int(codes_get(message, "typicalMonth"))
            day = int(codes_get(message, "typicalDay"))
            hour = int(codes_get(message, "typicalHour"))

            run_time = datetime(
                year, month, day, hour, tzinfo=timezone.utc
            )

            if reference_time is None:
                reference_time = run_time

            storm_id = get_text(message, "stormIdentifier")
            lat = get_value(message, "latitude")
            lon = get_value(message, "longitude")
            wind_ms = get_value(message, "windSpeedAt10M")
            lead = get_value(message, "timePeriod")

            if lat is None or lon is None:
                records_skipped += 1
                print(f"Skipping {storm_id}: missing coordinates")
                continue

            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                records_skipped += 1
                print(f"Skipping {storm_id}: invalid coordinates")
                continue

            lead_hours = int(lead) if lead is not None else None

            record = {
                "id": storm_id or "unknown",
                "latitude": lat,
                "longitude": lon,
                "wind_speed_ms": wind_ms,
                "wind_speed_knots": (
                    round(wind_ms * MS_TO_KNOTS, 2)
                    if wind_ms is not None else None
                ),
                "forecast_lead_hours": lead_hours,
            }

            if lead_hours is not None:
                record["valid_time_utc"] = iso_utc(
                    run_time + timedelta(hours=lead_hours)
                )

            records.append(record)

            print(
                f"Added {record['id']}: "
                f"lat={lat}, lon={lon}, lead={lead_hours}"
            )

        except Exception as error:
            records_skipped += 1
            print(f"Skipping message {messages_read}: {error}")

        finally:
            codes_release(message)

if reference_time is None:
    raise RuntimeError("No readable BUFR messages found.")

# Sort forecast points by storm ID and forecast lead time.
records.sort(
    key=lambda item: (
        item["id"],
        item["forecast_lead_hours"]
        if item["forecast_lead_hours"] is not None
        else -1,
    )
)

# Group points only when multiple positions for the same storm exist.
grouped = {}

for record in records:
    grouped.setdefault(record["id"], []).append(record)

tracks = []

for storm_id, points in grouped.items():
    # A single point is not a forecast track.
    if len(points) < 2:
        continue

    tracks.append({
        "id": storm_id,
        "points": points,
    })

result = {
    "source": "ECMWF IFS tropical cyclone tracks",
    "attribution": "Data from ECMWF, licensed under CC BY 4.0",
    "forecast_run_utc": iso_utc(reference_time),
    "messages_read": messages_read,
    "records_skipped": records_skipped,
    "storm_count": len(records),
    "storms": records,
    "tracks": tracks,
}

OUTPUT.write_text(
    json.dumps(result, indent=2),
    encoding="utf-8",
)

print("\n--- Summary ---")
print(f"Messages read: {messages_read}")
print(f"Records skipped: {records_skipped}")
print(f"Valid forecast points: {len(records)}")
print(f"Storm groups with 2+ points: {len(tracks)}")
print(f"JSON saved to: {OUTPUT}")
