from flask import Flask, render_template, request, jsonify
import g4f
import os
import pandas as pd
import re

from langchain.agents import create_csv_agent
import os

# from langchain.llms import OpenAI
# from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType
from pandasai import SmartDataframe
from pandasai.llm import OpenAI
import openai

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from tqdm import tqdm
from datetime import datetime, timedelta

def convert_age_to_datetime(age_str):
    unit_mapping = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days', 'w': 'weeks'}

    value, unit = int(age_str[:-1]), age_str[-1]
    if unit not in unit_mapping:
        raise ValueError("Invalid unit")

    delta = timedelta(**{unit_mapping[unit]: value})
    current_time = datetime.now()
    result_time = current_time - delta

    print(result_time)
    return result_time

def create_csv(origin, destination, origin_radius, destination_radius):
    if origin_radius == '_': origin_radius = 100
    if destination_radius == '_': destination_radius = 100
    global agent, df
    driver = webdriver.Chrome()
    driver.get("https://www.google.com")
    url = f'https://loadboard.doft.com/panel#fid=567831&oad={origin}%3B%20&odist={origin_radius}&olat=&olon=&dad={destination}%3B%20&ddist={destination_radius}&dlat=&dlon=&price=&permile='
    driver.get(url)

    # Get the expanded page source
    html = driver.page_source

    # Parse the HTML
    soup = BeautifulSoup(html, "html.parser")

    # Add code for handling login (adjust these according to the structure of the login form)
    username = 'akk67730102@gmail.com'
    password = '******'

    # Locate the username and password input fields and submit button
    email_field = driver.find_element(By.ID, 'driver_email')
    password_field = driver.find_element(By.ID, 'driver_password')
    submit_button = driver.find_element(By.ID, 'submitBtn')  # Replace 'submit' with the actual ID or other locator of the submit button

    # Input your credentials
    email_field.send_keys(username)
    password_field.send_keys(password)

    # Click the submit button
    submit_button.click()
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, 'dTable')))

    # Expand the page by clicking the "Show more" button until it is no longer available
    while True:
        try:
            show_more_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'moreBtn')))
            show_more_button.click()
            time.sleep(5)
        except:
            break

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    # Find all article containers
    result = soup.find_all('div', class_="b-load")

    print(len(result))
    overall = []
    # Extract and append the cleaned text content of each <li> element
    for item in tqdm(result):
        soup = BeautifulSoup(str(item), 'html.parser')
        # Extract data from specific elements
        try: age = convert_age_to_datetime(soup.select_one('.c-age span').text)
        except: age = '-'
        try: pickup = soup.select_one('.c-pu span').text
        except: pickup = '-'
        try: origin_city = soup.select_one('.c-orig .c-addr').text
        except: origin_city = '-'
        try: origin_state = soup.select_one('.c-orig .c-state').text
        except: origin_state = '-'
        try: destination_city = soup.select_one('.c-dest .c-addr').text
        except: destination_city = '-'
        try: destination_state = soup.select_one('.c-dest .c-state').text
        except: destination_state = '-'
        try: wt = soup.select_one('.c-weight').text
        except: wt = '-'
        try: size = soup.select_one('.c-size span')['title']
        except: size = '-'
        try: dist = soup.select_one('.c-dist').text
        except: dist = '-'
        try: truck = soup.select_one('.c-eq span')['title']
        except: truck = '-'
        forecast_per_mile = 0
        price = 0
        price_per_mile = 0
        forecast_price = 0
        try:
            try: forecast_price = int(soup.select_one('.c-price a')['data'][1:])
            except: price = int(soup.select_one('.c.c-price span').text[1:])
            try: forecast_per_mile = float(soup.select_one('.c-permile a')['data'][1:])
            except: price_per_mile = float(soup.select_one('.c.c-permile span').text[1:])
        except: pass
        company = soup.find('div', class_='c c-company').text
        try: contact_links = soup.select_one('.phone-link')['href']
        except: contact_links = '-'
        demand = soup.select_one('.c-demand').text if soup.select_one('.c-demand') else None

        overall.append([age, pickup, origin_city, origin_state, destination_city, destination_state, wt, size, dist, truck, price, forecast_price, price_per_mile, forecast_per_mile, company, contact_links, demand])
            
    driver.quit()

    df = pd.DataFrame(columns = ['Posted', 'Pickup', 'Origin City', 'Origin State', 'Destination City', 'Destination State', 'Wt', 'Size', 'Dist', 'Truck', 'Price', 'Forecast Price', 'Price Per Mile', 'Forecast Per Mile', 'Company', 'Contact Links', 'Demand'])
    for item_list in overall:
        df.loc[len(df.index)] = item_list 

    # df.to_csv('../doft_loads.csv')
    # agent = create_csv_agent(
    #     ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613"),
    #     "../doft_loads.csv",
    #     verbose=True,
    #     agent_type=AgentType.OPENAI_FUNCTIONS,
    # )

    llm = OpenAI(api_token = ' ')
    df = SmartDataframe(df, config={"llm": llm})

def search_bot(query):
    # # Compose a prompt for the model

    # # Generate a response from the model
    # response = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=[{"role": "user", "content": query}]
    # )

    # # Extract and return the model's response
    # return response.message.content
    openai.api_key = ' '
    chat_completion = openai.ChatCompletion.create(stream=True,
        model='gpt-3.5-turbo', messages=[{'role': 'user', 'content': query}])

    res = ''
    for token in chat_completion:
        content = token['choices'][0]['delta'].get('content')
        if content != None:
            res += content        
    return res.strip()

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

os.environ["OPENAI_API_KEY"] = ' '

# agent = create_csv_agent(
#     ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613"),
#     "../doft_loads.csv",
#     verbose=True,
#     agent_type=AgentType.OPENAI_FUNCTIONS,
# )
df = pd.DataFrame(columns = ['Posted', 'Pickup', 'Origin City', 'Origin State', 'Destination City', 'Destination State', 'Wt', 'Size', 'Dist', 'Truck', 'Price', 'Forecast Price', 'Price Per Mile', 'Forecast Per Mile', 'Company', 'Contact Links', 'Demand'])
llm = OpenAI(api_token = ' ')
df = SmartDataframe(df, config={"llm": llm})

app = Flask(__name__)

# Dictionary to store conversation history
conversation_history = []


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
            if 'destination and origin' in input_text:
                origin = 'NY'
                destination = 'PA'
                pattern = re.compile(r'(?P<Origin>[A-Z]{2,}) to (?P<Destination>[A-Z]{2,}) within 100 miles of destination and origin')

                match = pattern.search(input_text)

                if match:
                    origin = match.group('Origin')
                    destination = match.group('Destination')
                create_csv(origin, destination, 100, 100)
                bot_response = "Copilot Ready. Please ask further questions."
            elif 'Connect me to load boards' in input_text:
                bot_response =  "Sure, please enter an abbreviated origin and destination from this list - Alaska (AK), Alabama (AL), Arkansas (AR), Arizona (AZ), California (CA), Colorado (CO), Connecticut (CT), District of Columbia (DC), Delaware (DE), Florida (FL), Georgia (GA), Hawaii (HI), Iowa (IA), Idaho (ID), Illinois (IL), Indiana (IN), Kansas (KS), Kentucky (KY), Louisiana (LA), Massachusetts (MA), Maryland (MD), Maine (ME), Michigan (MI), Minnesota (MN), Missouri (MO), Mississippi (MS), Montana (MT), North Carolina (NC), North Dakota (ND), Nebraska (NE), New Hampshire (NH), New Jersey (NJ), New Mexico (NM), Nevada (NV), New York (NY), Ohio (OH), Oklahoma (OK), Oregon (OR), Pennsylvania (PA), Rhode Island (RI), South Carolina (SC), South Dakota (SD), Tennessee (TN), Texas (TX), Utah (UT), Virginia (VA), Vermont (VT), Washington (WA), Wisconsin (WI), West Virginia (WV), Wyoming (WY), Alberta (AB), British Columbia (BC), Manitoba (MB), New Brunswick (NB), Newfoundland and Labrador (NL), Nova Scotia (NS), Northwest Territories (NT), Nunavut (NU), Ontario (ON), Prince Edward Island (PE), Quebec (QC), Saskatchewan (SK), Yukon (YT) \n \n \n. Enter as Origin to Destination within 100 miles of destination and origin"
            else:    
                flag1 = False
                flag2 = False
                
                if 'Send me an email' in input_text or 'Notify me' in input_text: 
                    input_text = input_text.replace('Send me an email', 'Show me details in field name : value format')
                    flag1 = True
                if 'Send the booking request' in input_text:
                    input_text = input_text.replace('Send the booking request', 'Show me details in field name : value format')
                    flag2 = True
                if 'send the booking request' in input_text:
                    input_text = input_text.replace('send the booking request', 'Show me details in field name : value format')
                    flag2 = True

                response = df.chat(input_text)
                bot_response = response

                if flag1:
                    subject = 'Loadboard Price ALERT for saved route'
                    body = f'Notification from LOGTRACK for your query {input_text}. \n The corresponding response has been detected {bot_response}'
                    recipient_mail = 'kadithya2403@gmail.com'

                    send_email_notification(subject, body, recipient_mail)

                if flag2:
                    res = {}
                    subject = 'Freight booking request'
                    # body = f'Dear {res["Company"]}, I want to book the load from {res["Origin City"]}, {res["Origin State"]} to {res["Destination City"]}, {res["Destionation State"]} for the price of {res["Price"]} .My truck currently is in {res["Origin City"]}, {res["Origin State"]}  Please reach out to discuss the process. \n Best, \n Adithya'
                    body = f'Hi, I want to book the request for the following load, \n {bot_response}. Please reach out to discuss the process. \n Best, \n Adithya'
                    recipient_mail = 'hhamidov@gmail.com'

                    send_email_notification(subject, body, recipient_mail)


                if flag1 or flag2: bot_response += 'Sent an email to the corresponding party. Please check inbox'
            

        bot_response = bot_response.replace("\n","<br />")
        bot_response = bot_response.replace('Bing', 'LogBot')
        bot_response = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', bot_response)
            
        # print('bot_Response', bot_response, conversation_history)

        return jsonify(bot_response)
    # except Exception as e:
    #     return jsonify(str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)