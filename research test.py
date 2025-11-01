import json

import requests

url = "https://api.brandfetch.io/v2/brands/transaction"

payload = {
    "transactionLabel": "https://www.anthropic.com/",
    "countryCode": "US"
}
headers = {
    "Authorization": "Bearer 4eUmdizABkv1eqxIcbOoLE/nTRIvZ9yfSNfUfaMjjhI=",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
with open("anthopic.json", "w", encoding="utf-8") as f:
    json.dump(response.json(), f, ensure_ascii=False, indent=4)
