from flask import Flask, render_template, request, jsonify
import g4f
import os
import pandas as pd
import re

from langchain.agents import create_csv_agent
import os

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType
import openai

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def search_bot(query):
    # # Compose a prompt for the model

    # # Generate a response from the model
    # response = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=[{"role": "user", "content": query}]
    # )

    # # Extract and return the model's response
    # return response.message.content

    stream = False
    response = g4f.ChatCompletion.create(model='gpt-4', provider=g4f.Provider.Bing, messages=[
                                        {"role": "user", "content": query}
                                        ], stream=stream)
    
    return response

def send_email_notification(subject, body, recipient_email):
    gmail_username = 'akk67730102@gmail.com'
    gmail_password = 'lonogaothfnhhopw'

    sender_email = gmail_username

    # Create the email message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject

    # Attach the email body
    message.attach(MIMEText(body, "plain"))

    # Connect to the Gmail SMTP server
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    # Login to the Gmail account
    server.login(gmail_username, gmail_password)

    # Send the email
    server.sendmail(sender_email, recipient_email, message.as_string())

    # Close the connection
    server.quit()

os.environ["OPENAI_API_KEY"] = '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'

agent = create_csv_agent(
    ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613"),
    "../loadboard.csv",
    verbose=True,
    agent_type=AgentType.OPENAI_FUNCTIONS,
)

app = Flask(__name__)

# Dictionary to store conversation history
conversation_history = {}

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/copilot')
def copilot():
    return render_template('base.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    # try:
        user_id = request.form.get("user_id")
        input_text = request.form.get("message")

        if 'distance' in input_text:
            bot_response = search_bot(input_text)
            bot_response = re.sub(r'\[\d+\]:.*?$', '', "r'" + bot_response + "'" , flags=re.MULTILINE)
            bot_response = bot_response.strip("r'").strip(' ').strip('\n')
            bot_response = re.sub(r'\[.*?\]', '', bot_response)
        else:
            flag1 = False
            flag2 = False
            
            if 'Send me an email' in input_text or 'Notify me' in input_text: 
                input_text = input_text.replace('Send me an email', 'Show me')
                flag1 = True
            if 'Send the booking request' in input_text:
                input_text = input_text.replace('Send the booking request', 'Show me details in field name : value format')
                flag2 = True
            if 'send the booking request' in input_text:
                input_text = input_text.replace('send the booking request', 'Show me details in field name : value format')
                flag2 = True
        
            response = agent.run(input_text)

            bot_response = response

            if flag1:
                subject = 'Loadboard Price ALERT for saved route'
                body = f'Notification from LOGTRACK for your query {input_text}. \n The corresponding response has been detected {bot_response}'
                recipient_mail = 'kadithya2403@gmail.com'

                send_email_notification(subject, body, recipient_mail)

            if flag2:
                subject = 'Freight booking request'
                body = f'Hi there, \n  \n I am interested in booking your load from the following cargo obtained from LOGTRACK \n \n {bot_response}. \n \n Please call me to discuss additional details. \n Number: +1-(435)-753-2376. \n Best, \n Adithya'
                recipient_mail = 'kadithya2403@gmail.com'

                send_email_notification(subject, body, recipient_mail)

            if flag1 or flag2: bot_response += 'Sent an email to the corresponding party. Please check inbox'

        bot_response = bot_response.replace("\n","<br />")
        bot_response = bot_response.replace('Bing', 'LogBot')
        bot_response = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', bot_response)

        print('bot_Response', bot_response)

        return jsonify(bot_response)
    # except Exception as e:
    #     return jsonify(str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)