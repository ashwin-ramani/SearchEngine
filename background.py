import json, threading

with open("./storage/data.json") as file:
  data = json.load(file)

# in-memory full-page text store (populated by the crawler)
docs = {}