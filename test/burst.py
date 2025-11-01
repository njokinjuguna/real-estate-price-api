import requests, sys
N = int(sys.argv[1]) if len(sys.argv)>1 else 60
KEY = sys.argv[2] if len(sys.argv)>2 else "vip-123"
URL = "http://127.0.0.1:8000/predict"
payload = {"OverallQual":7,"GrLivArea":1710,"GarageCars":2,"TotalBsmtSF":856,"YearBuilt":2003}
codes = {}
for _ in range(N):
    r = requests.post(URL, json=payload, headers={"api-key": KEY})
    codes[r.status_code] = codes.get(r.status_code, 0) + 1
print(codes)
