import requests
    
url = "https://www.onemap.gov.sg/api/public/revgeocodexy?location=24291.97788882387%2C31373.0117224489&buffer=40&addressType=All&otherFeatures=N"
    
headers = {"Authorization": "Bearer **********************"}
    
response = requests.get(url, headers=headers)
    
print(response.text)