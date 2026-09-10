"""21_fetch_mympg.py -- pull fueleconomy.gov My MPG (user-shared) summaries
for every vehicle flagged mpgData == 'Y' in vehicles.csv.

Endpoint: /ws/rest/ympg/shared/ympgVehicle/{id} (public federal API, JSON).
Resumable: results append to external/mympg_cache.jsonl; already-cached ids
are skipped, so rerunning continues instead of restarting. 4 worker threads
with a small stagger out of politeness.
"""

import json
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "external", "mympg_cache.jsonl")
URL = "https://www.fueleconomy.gov/ws/rest/ympg/shared/ympgVehicle/{}"


def fetch_one(vid):
    req = urllib.request.Request(URL.format(vid),
                                 headers={"Accept": "application/json"})
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                rec = json.loads(r.read().decode("utf-8"))
                rec["vehicleId"] = int(vid)
                return rec
        except Exception as e:
            if attempt == 2:
                return {"vehicleId": int(vid), "error": str(e)[:80]}
            time.sleep(2)


def main():
    veh = pd.read_csv(os.path.join(HERE, "vehicles.csv"), low_memory=False)
    ids = veh.loc[veh.mpgData == "Y", "id"].astype(int).tolist()

    done = set()
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["vehicleId"])
                except (json.JSONDecodeError, KeyError):
                    continue
    todo = [v for v in ids if v not in done]
    print(f"{len(ids):,} flagged vehicles; {len(done):,} cached; "
          f"{len(todo):,} to fetch")

    n = 0
    t0 = time.time()
    with open(CACHE, "a", encoding="utf-8") as out:
        with ThreadPoolExecutor(max_workers=4) as ex:
            for rec in ex.map(fetch_one, todo):
                out.write(json.dumps(rec) + "\n")
                n += 1
                if n % 500 == 0:
                    out.flush()
                    rate = n / (time.time() - t0)
                    print(f"{n:,}/{len(todo):,} ({rate:.1f}/s, "
                          f"~{(len(todo)-n)/rate/60:.0f} min left)")
    print(f"done: fetched {n:,}; cache now {len(done) + n:,} records")


if __name__ == "__main__":
    main()
