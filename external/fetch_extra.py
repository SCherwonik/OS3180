"""Fetch FARS fatality counts and BEA sales-split series. Run from external/."""
import urllib.request

FETCHES = [
    ("fars_fatalities.json",
     "https://crashviewer.nhtsa.dot.gov/CrashAPI/analytics/GetInjurySeverityCounts"
     "?fromCaseYear=1975&toCaseYear=2023&format=json"),
    ("fred_DAUTOSAAR.csv", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DAUTOSAAR"),
    ("fred_FAUTOSAAR.csv", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FAUTOSAAR"),
    ("fred_DLTRUCKSSAAR.csv", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DLTRUCKSSAAR"),
    ("fred_FLTRUCKSSAAR.csv", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FLTRUCKSSAAR"),
]

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/126.0.0.0 Safari/537.36"),
    "Accept": "application/json,text/csv,*/*",
    "Referer": "https://crashviewer.nhtsa.dot.gov/CrashAPI",
}

for fname, url in FETCHES:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=90) as r, open(fname, "wb") as f:
            f.write(r.read())
        print(fname, "ok")
    except Exception as e:
        print(fname, "FAILED:", e)
