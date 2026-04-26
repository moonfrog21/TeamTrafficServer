import requests

sample_data = [
    {"user": "Alice",   "latitude": "-33.9249", "Longitude": "18.4241",  "time": "08:00 AM"},
    {"user": "Bob",     "latitude": "-26.2041", "Longitude": "28.0473",  "time": "08:01 AM"},
    {"user": "Charlie", "latitude": "-29.8587", "Longitude": "31.0218",  "time": "08:02 AM"},
]

for payload in sample_data:
    try:
        r = requests.post(BASE, json=payload)
        print(f"Sent {payload['user']}: {r.status_code} {r.json()}")
    except requests.exceptions.ConnectionError:
        print("Connection failed — make sure the server is running (python run.py)")
        break