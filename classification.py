import requests
import json

API_KEY = "***"
model_id = "***"
url = f'***/{model_id}/***'
image = "***"

data = {'file': open(image, 'rb')}
response = requests.post(url, auth=requests.auth.HTTPBasicAuth(API_KEY, ''), files=data)
data = json.loads(response.text)

for i in data['result']:
    for j in i['prediction']:
        for k in j['cells']:
            if k['score'] >= 0 and not k['text'].isdigit():
                print(k['text'], k['score'])
