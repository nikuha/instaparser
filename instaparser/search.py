from pprint import pprint

from pymongo import MongoClient


client = MongoClient('127.0.0.1', 27017)
db = client['instagram']

for user in db.instagram.find({'from_username': 'ceramicsochi', 'follow_type': 'follower'}):
    pprint(user)

for user in db.instagram.find({'from_username': 'ceramicsochi', 'follow_type': 'following'}):
    pprint(user)
