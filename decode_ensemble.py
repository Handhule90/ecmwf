
import json
from pathlib import Path

from eccodes import (
    codes_bufr_new_from_file,
    codes_set,
    codes_get,
    codes_get_array,
    codes_release,
)

INPUT = Path("ensemble-track.bufr")
OUTPUT = Path("ensemble.json")
MISSING = -1e90


def get_array(message, key):
    try:
        return codes_get_array(message, key)
    except Exception:
        return []


def get_scalar(message, key, default=None):
    try:
        return codes_get(message, key)
    except Exception:
        return default


storms = {}
messages_read = 0

with INPUT.open("rb") as file:
    while True:
        message = codes_bufr_new_from_file(file)
        if message is None:
            break

        messages_read += 1

        try:
            codes_set(message, "unpack", 1)

            storm_id = str(
                get_scalar(message, "#1#stormIdentifier", "UNKNOWN")
            ).strip()

            member_numbers = get_array(
                message, "#1#ensembleMemberNumber"
            )

            if len(member_numbers) == 0:
                member_numbers = get_array(message, "ensembleMemberNumber")

            if len(member_numbers) == 0:
                continue

            member_numbers = [int(x) for x in member_numbers]
            member_count = len(member_numbers)

            if storm_id not in storms:
                storms[storm_id] = {}

            # Each repeated key represents a forecast position group.
            for period_index in range(1, 30):
                latitudes = get_array(
                    message, f"#{period_index}#latitude"
                )
                longitudes = get_array(
                    message, f"#{period_index}#longitude"
                )
                periods = get_array(
                    message, f"#{period_index}#timePeriod"
                )

                if not latitudes or not longitudes or not periods:
                    continue

                forecast_hour = int(periods[0])

                if len(latitudes) == 1 and member_count > 1:
                    latitudes = list(latitudes) * member_count

                if len(longitudes) == 1 and member_count > 1:
                    longitudes = list(longitudes) * member_count

                count = min(
                    member_count, len(latitudes), len(longitudes)
                )

                for i in range(count):
                    lat = float(latitudes[i])
                    lon = float(longitudes[i])

                    if (
                        lat <= MISSING
                        or lon <= MISSING
                        or not -90 <= lat <= 90
                        or not -180 <= lon <= 180
                    ):
                        continue

                    member_id = str(member_numbers[i])

                    storms[storm_id].setdefault(member_id, [])

                    point = {
                        "forecast_hour": forecast_hour,
                        "latitude": lat,
                        "longitude": lon,
                    }

                    if point not in storms[storm_id][member_id]:
                        storms[storm_id][member_id].append(point)

        except Exception as error:
            print(f"Message {messages_read} skipped: {error}")

        finally:
            codes_release(message)

# Sort each member's positions by forecast time.
result = {}

for storm_id, members in storms.items():
    result[storm_id] = {}

    for member_id, points in members.items():
        points.sort(key=lambda point: point["forecast_hour"])

        if points:
            result[storm_id][member_id] = points

payload = {
    "source": "ECMWF ensemble forecast",
    "description": (
        "Ensemble member tracks; spread is not a calibrated probability."
    ),
    "messages_read": messages_read,
    "storm_count": len(result),
    "storms": result,
}

OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

print(f"Messages read: {messages_read}")
print(f"Storms decoded: {len(result)}")
for storm_id, members in result.items():
    print(f"{storm_id}: {len(members)} ensemble members")

print(f"Saved: {OUTPUT}")
