import requests

url = "https://www.eneco-emobility.com/api/chargemap/search-clusters"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/142.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Referer": "https://www.eneco-emobility.com/be-nl/chargemap",
    "Origin": "https://www.eneco-emobility.com",
}

payload = {
    "bounds": {
        "northWest": [53.20932249705369, -0.8514404296875],
        "northEast": [53.20932249705369, 9.695434570312502],
        "southEast": [50.60764573009061, 9.695434570312502],
        "southWest": [50.60764573009061, -0.8514404296875]
    },
    "filters": {
        "fastCharging": False,
        "ultraFastCharging": False
    },
    "zoomLevel": 8
}

r = requests.post(url, json=payload, headers=headers, timeout=20)

print(r.status_code)
print(r.text[:2500])