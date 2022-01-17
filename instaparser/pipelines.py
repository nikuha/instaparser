from pymongo import MongoClient
from hashlib import sha1


class InstaparserPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongobase = client.instagram

    def process_item(self, item, spider):
        item['_id'] = self.get_item_hash(item)
        collection = self.mongobase[spider.name]
        try:
            collection.insert_one(item)
        except:
            pass
        return item

    @staticmethod
    def get_item_hash(item):
        d_hash = sha1()
        d_hash.update(f"{item['follow_type']}{item['from_user_id']}{item['user_id']}".encode())
        return d_hash.hexdigest()


