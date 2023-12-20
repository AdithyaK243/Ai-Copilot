from flask import Flask, render_template, request, jsonify
import g4f
import os
import pandas as pd
import re

file = pd.ExcelFile('/home/adithya/Desktop/Adi/Highers/Columbia/Spring_23/CBL/chatbot/Load-Posting-Template.xlsx')
data = file.parse('Loads')

data1 = data.iloc[:80]

app = Flask(__name__)

# Dictionary to store conversation history
conversation_history = {}

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    # try:
        user_id = request.form.get("user_id")
        input_text = request.form.get("message")
                      

        # Retrieve or create conversation history for the user
        if user_id in conversation_history:
            conversation = conversation_history[user_id]
        else:
            conversation = []

        conversation.append({"role": "user", "content": f"{data1.to_string()} this is the loadboard data." + " " + input_text})

       
        response = g4f.ChatCompletion.create(model='gpt-4', messages=[{"role": "user", "content": f"{data1.to_string()} this is the loadboard data" + " " + input_text}], provider=g4f.Provider.Bing, stream=False)

        bot_response = response
        bot_response = bot_response.replace("\n","<br />")
        bot_response = bot_response.replace('Bing', 'LogBot')
        bot_response = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', bot_response)


        print('bot_Response', bot_response)

        # Append the chatbot's response to the conversation history
        conversation.append({"role": "bot", "content": bot_response})

        # Update the conversation history for the user
        conversation_history[user_id] = conversation

        return jsonify(bot_response)
    # except Exception as e:
    #     return jsonify(str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)