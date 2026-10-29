
from pathlib import Path
from ecmwf.opendata import Client
from eccodes import (
    codes_bufr_new_from_file,
    codes_set,
    codes_release,
    codes_bufr_keys_iterator_new,
    codes_bufr_keys_iterator_next,
    codes_bufr_keys_iterator_get_name,
    codes_bufr_keys_iterator_delete,
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
                print("\n--- Available BUFR keys ---")

                iterator = None

                try:
                    iterator = codes_bufr_keys_iterator_new(message)

                    while codes_bufr_keys_iterator_next(iterator):
                        key = codes_bufr_keys_iterator_get_name(iterator)
                        print(key)

                except Exception as error:
                    print(f"Key inspection failed: {error}")

                finally:
                    if iterator is not None:
                        codes_bufr_keys_iterator_delete(iterator)

        finally:
            codes_release(message)

print(f"\nTotal BUFR messages: {messages}")

if messages == 0:
    raise RuntimeError("Downloaded file contains no readable BUFR messages.")
