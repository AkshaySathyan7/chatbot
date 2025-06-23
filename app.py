# app.py
from flask import Flask, render_template, request, redirect, url_for, session
from bson.objectid import ObjectId
from datetime import datetime
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# MongoDB connection (Local)
client = MongoClient('mongodb://localhost:27017/')
db = client['chatbot_db']
users_col = db['users']
chats_col = db['chats']

# Emotion-based responses
responses = {
    "sad": "I'm really sorry you're feeling sad. 💛 Do you want to talk more about it?",
    "lonely": "You're not alone. I'm here with you. Would you like to share what's going on?",
    "angry": "It’s okay to feel angry sometimes. Do you want to tell me what made you feel this way?",
    "happy": "I'm so glad to hear that! 😄 What made your day good?",
    "tired": "You’ve been doing a lot. It’s okay to take a break. 💩",
    "anxious": "Anxiety can be overwhelming. Try taking a deep breath. Want to chat more about it?",
    "stressed": "Life can be stressful. Let’s talk it out, I’m here for you.",
    "lost": "It’s okay to not have all the answers. Want me to ask you something fun?"
}

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        nickname = request.form['nickname']
        age = request.form['age']
        gender = request.form['gender']

        user = {
            "name": name,
            "nickname": nickname if nickname else name,
            "age": age,
            "gender": gender,
            "created_at": datetime.now()
        }
        user_id = users_col.insert_one(user).inserted_id
        session['user_id'] = str(user_id)
        return redirect(url_for('chat'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        user = users_col.find_one({"name": name})
        if user:
            session['user_id'] = str(user['_id'])
            return redirect(url_for('chat'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = users_col.find_one({'_id': ObjectId(session['user_id'])})

    chats = [
        {**chat, '_id': str(chat['_id'])}
        for chat in chats_col.find({'user_id': ObjectId(session['user_id'])})
    ]

    selected_chat = None
    messages = []

    if 'chat_id' in request.args:
        selected_chat = chats_col.find_one({'_id': ObjectId(request.args['chat_id'])})
        messages = selected_chat['messages']

    if request.method == 'POST':
        message = request.form['message']
        bot_reply = f"Hey {user.get('nickname', user['name'])}, how's it going?"

        for keyword in responses:
            if keyword in message.lower():
                bot_reply = responses[keyword]
                break

        new_message = [
            {"role": "user", "text": message},
            {"role": "bot", "text": bot_reply}
        ]

        if selected_chat:
            chats_col.update_one(
                {'_id': ObjectId(request.args['chat_id'])},
                {'$push': {'messages': {'$each': new_message}}}
            )
        else:
            chat_doc = {
                'user_id': ObjectId(session['user_id']),
                'title': f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                'messages': new_message,
                'created_at': datetime.now()
            }
            chat_id = chats_col.insert_one(chat_doc).inserted_id
            return redirect(url_for('chat', chat_id=str(chat_id)))

        return redirect(url_for('chat', chat_id=request.args.get('chat_id')))

    return render_template('index.html', user=user, chats=chats, messages=messages)

if __name__ == '__main__':
    app.run(debug=True)