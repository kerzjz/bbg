import requests

url = "https://api.itick.org/symbol/list?type=stock&region=US&code=BA"

headers = {
"accept": "application/json", 
"token": "0db3f9f7513a404f8f4b304ebf031286e45baecfbf114acab3245e1ab931339b"
}

response = requests.get(url, headers=headers)

print(response.text)

