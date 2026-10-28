
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from eccodes import (
    codes_bufr_new_from_file,
    codes_get,
    codes_get_array,
    codes_release,
    codes_set,
)

INPUT = Path("ecmwf-track.bufr")
OUTPUT = Path("storms.json")
MS_TO_KNOTS = 1.94384449
MISSING = -1e90


def get_text(message, key):
    try:
        value = str(codes_get(message, key)).strip()
        return value or None
    except Exception:
        return None


def get_number(message, key):
    """Get the first valid numeric value from a scalar or repeated key."""
    try:
        values = codes_get_array(message, key)
        for item in values:
            value = float(item)
            if math.isfinite(value) and value > MISSING:
                return value
    except Exception:
        try:
            value = float(codes_get(message, key))
            if math.isfinite(value) and value > MISSING:
                return value
        except Exception:
            pass
    return None


def iso_utc(value):
    return value.astimezone(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


def valid_position(lat, lon):
    return (
        lat is not None
        and lon is not None
        and -90 <= lat <= 90
        and -180 <= lon <= 180
    )


def make_point(storm_id, lat, lon, lead, run_time, wind_ms=None):
    point = {
        "id": storm_id,
        "latitude": lat,
        "longitude": lon,
        "wind_speed_ms": wind_ms,
        "wind_speed_knots": (
            round(wind_ms * MS_TO_KNOTS, 2)
            if wind_ms is not None else None
        ),
        "forecast_lead_hours": int(lead),
        "valid_time_utc": iso_utc(
            run_time + timedelta(hours=lead)
        ),
    }
    return point


if not INPUT.exists():
    raise FileNotFoundError(f"Missing input file: {INPUT}")

records = []
tracks = []
messages_read = 0
records_skipped = 0
reference_time = None

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

            if reference_time is None:
                reference_time = run_time

            storm_id = get_text(message, "stormIdentifier") or "unknown"
            points = []

            # Initial analyzed position: significance rank #2.
            lat = get_number(message, "#2#latitude")
            lon = get_number(message, "#2#longitude")
            wind = get_number(message, "#1#windSpeedAt10M")

            if valid_position(lat, lon):
                points.append(
                    make_point(storm_id, lat, lon, 0, run_time, wind)
                )

            # Forecast periods use numbered timePeriod keys.
            # For period rank N, the storm-centre position is rank 2*N+2.
            period_rank = 1

            while period_rank <= 100:
                lead = get_number(
                    message, f"#{period_rank}#timePeriod"
                )

                if lead is None:
                    break

                position_rank = 2 * period_rank + 2
                wind_rank = period_rank + 1

                lat = get_number(
                    message, f"#{position_rank}#latitude"
                )
                lon = get_number(
                    message, f"#{position_rank}#longitude"
                )
                wind = get_number(
                    message, f"#{wind_rank}#windSpeedAt10M"
                )

                if valid_position(lat, lon):
                    points.append(
                        make_point(
                            storm_id, lat, lon, lead, run_time, wind
                        )
                    )
                else:
                    records_skipped += 1

                period_rank += 1

            # Sort positions chronologically and remove duplicate leads.
            points.sort(key=lambda p: p["forecast_lead_hours"])

            unique_points = []
            seen_leads = set()

            for point in points:
                lead = point["forecast_lead_hours"]
                if lead not in seen_leads:
                    unique_points.append(point)
                    seen_leads.add(lead)

            records.extend(unique_points)

            if len(unique_points) >= 2:
                tracks.append({
                    "id": storm_id,
                    "points": unique_points,
                })

            print(
                f"{storm_id}: extracted "
                f"{len(unique_points)} positions"
            )

        except Exception as error:
            records_skipped += 1
            print(f"Skipping message {messages_read}: {error}")

        finally:
            codes_release(message)

if reference_time is None:
    raise RuntimeError("No readable BUFR messages found.")

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
print(f"Valid positions: {len(records)}")
print(f"Tracks with 2+ positions: {len(tracks)}")
print(f"JSON saved to: {OUTPUT}")
