import requests
import sys
import http.server

token = sys.argv[1]

url = 'https://graph.facebook.com/v2.8/246614445801677_246622789134176?access_token='+token+'&fields=reactions&format=json&method=get&pretty=0'

r = requests.get(url)
print(r.status_code)
print(r.json())

