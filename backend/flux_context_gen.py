# NOT IN USE - IMPLEMENTED IN FLASK_APP.PY

import os
import requests
import time

request = requests.post(
    'https://api.bfl.ai/v1/flux-kontext-pro',
    headers={
        'accept': 'application/json',
        'x-key': os.environ.get("BFL_API_KEY"),
        'Content-Type': 'application/json',
    },
    json={
        'prompt': 'A small furry elephant pet looks out from a cat house',
    },
).json()

print(request)
request_id = request["id"]
polling_url = request["polling_url"] # Use this URL for polling'

while True:
  time.sleep(0.5)
  result = requests.get(
      polling_url,
      headers={
          'accept': 'application/json',
          'x-key': os.environ.get("BFL_API_KEY"),
      }
  ).json()
  
  if result['status'] == 'Ready':
      print(f"Image ready: {result['result']['sample']}")
      break
  elif result['status'] in ['Error', 'Failed']:
      print(f"Generation failed: {result}")
      break