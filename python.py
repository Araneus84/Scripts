import requests

url = "https://staging.cloudwm.com/service/server/{4e7f72a0-3f78-46c3-9ed0-2352728da58c}"

payload = ""
headers = {
  "Content-Type": "application/json"
}
response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)