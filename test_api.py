import requests

try:
    print("Testing API...")
    resp = requests.get("http://localhost:8001/companies/search?limit=1")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Search OK. Found: {len(data)}")
        if data:
            cid = data[0]['id']
            print(f"Testing Pitch for ID {cid}...")
            resp2 = requests.get(f"http://localhost:8001/companies/{cid}/pitch")
            print(resp2.json())
    else:
        print(f"Search Failed: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")
