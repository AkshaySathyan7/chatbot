from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client['chatbot_db']
users_col = db['users']
chats_col = db['chats']
