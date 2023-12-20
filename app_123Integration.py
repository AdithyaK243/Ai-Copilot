from flask import Flask, render_template, request, jsonify
import g4f
import os
import pandas as pd
import re
from langchain.agents import create_csv_agent
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType
import openai, requests
import csv
import pandas as pd

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def search_bot(query):
    stream = False
    response = g4f.ChatCompletion.create(model='gpt-4', provider=g4f.Provider.Bing, messages=[
                                        {"role": "user", "content": query}
                                        ], stream=stream)
    
    return response

def get_nested_value(dictionary, keys, default=""):
    for key in keys:
        if key in dictionary:
            dictionary = dictionary[key]
        else:
            return default
    return dictionary

def create_csv_file(loads):
    print(loads)
    # Flatten the dictionaries into a list of flat dictionaries
    flat_loads = []
    for load in loads['loads']:
        flat_load = {
            "numberOfLoads": load.get("numberOfLoads", ""),
            "origin_latitude": get_nested_value(load, ["originLocation", "geolocation", "latitude"]),
            "origin_longitude": get_nested_value(load, ["originLocation", "geolocation", "longitude"]),
            "origin_city": get_nested_value(load, ["originLocation", "address", "city"]),
            "origin_state": get_nested_value(load, ["originLocation", "address", "state"]),
            "origin_zipCode": get_nested_value(load, ["originLocation", "address", "zipCode"]),
            "destination_latitude": get_nested_value(load, ["destinationLocation", "geolocation", "latitude"]),
            "destination_longitude": get_nested_value(load, ["destinationLocation", "geolocation", "longitude"]),
            "destination_city": get_nested_value(load, ["destinationLocation", "address", "city"]),
            "destination_state": get_nested_value(load, ["destinationLocation", "address", "state"]),
            "destination_zipCode": get_nested_value(load, ["destinationLocation", "address", "zipCode"]),
            "equipmentType": get_nested_value(load, ["equipments", 0, "equipmentType"]),
            "equipmentSpecifications": get_nested_value(load, ["equipments", 0, "equipmentSpecifications"]),
            "loadSize": load.get("loadSize", ""),
            "length": load.get("length", ""),
            "weight": load.get("weight", ""),
            "rate_amount": get_nested_value(load, ["rate", "amount"]),
            "rate_type": get_nested_value(load, ["rate", "type"]),
            "numberOfStops": load.get("numberOfStops", ""),
            "teamDriving": load.get("teamDriving", ""),
            "id": load.get("id", ""),
            "computedMileage": load.get("computedMileage", ""),
            "status": load.get("status", ""),
            "age": load.get("age", ""),
            "poster_id": get_nested_value(load, ["poster", "id"]),
            "poster_prefix": get_nested_value(load, ["poster", "docketNumber", "prefix"]),
            "poster_number": get_nested_value(load, ["poster", "docketNumber", "number"]),
            "poster_purpose": get_nested_value(load, ["poster", "docketNumber", "purpose"]),
            "poster_name": get_nested_value(load, ["poster", "name"]),
            "metadata_hasPrivateNote": get_nested_value(load, ["metadata", "hasPrivateNote"]),
            "metadata_isViewedCounter": get_nested_value(load, ["metadata", "isViewedCounter"]),
            "metadata_isViewed": get_nested_value(load, ["metadata", "userdata", "isViewed"]),
            "metadata_progress": get_nested_value(load, ["metadata", "userdata", "progress"]),
            "sortEquipCode": load.get("sortEquipCode", ""),
            "pricePerMile": load.get("pricePerMile", ""),
            "pickupDateTimesUtc": load.get("pickupDateTimesUtc", [""])[0],
        }
        flat_loads.append(flat_load)

    # Specify the CSV file name
    csv_filename = "loads.csv"

    # Define the fieldnames for the CSV file
    fieldnames = list(flat_loads[0].keys())

    # Write the data to the CSV file
    with open(csv_filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_loads)

    print(f"CSV file '{csv_filename}' has been created.")

def populate_table(input_text):
    model_id = "gpt-3.5-turbo"
    completion = openai.ChatCompletion.create(
        model=model_id,
        messages=[{"role": "user", "content": f'''Please select the following information from the given text:

    1. Source City:
    2. Destination City:
    3. Time Frame (in hours):
                    
    Initialize them as None if not mentioend in text.

    Text: {input_text}
    '''}])

    bot_response = completion.choices[0].message.content
    origin, destination, time = bot_response.split('\n')[0].split(':')[1].strip(), bot_response.split('\n')[1].split(':')[1].strip(), bot_response.split('\n')[2].split(':')[1].strip()

    origin = origin.strip()
    destination = destination.strip()
    time = time.strip()

    url = "https://api.dev.123loadboard.com/loads/search"

    city_state = pd.read_csv('uscities.csv')
    ind_o = city_state.index[city_state['city'] == origin].tolist()
    if ind_o == []: ind_o = city_state.index[city_state['state_name'] == origin].tolist()
    ind_d = city_state.index[city_state['city'] == destination].tolist()
    if ind_d == []: ind_d = city_state.index[city_state['state_name'] == destination].tolist()

    print(ind_o, ind_d)
    origin_json = None
    if city_state.index[city_state['city'] == origin].tolist() != []: 
        origin_json = {
        "type": "City",
        "states": [city_state['state_id'][ind_o[0]]],
        "city": origin
    }
    elif origin == None: origin_json = {
        "type": "Anywhere"
    }
    else:
        origin_json = {
        "type": "States",
        "states": [city_state['state_id'][ind_o[0]]],
    }

    destination_json = None
    if city_state.index[city_state['city'] == destination].tolist() != []: 
        destination_json = {
        "type": "City",
        "states": [city_state['state_id'][ind_d[0]]],
        "city": destination
    }
    elif destination == None: destination_json = {
        "type": "Anywhere"
    }
    else:
        destination_json = {
        "type": "States",
        "states": [city_state['state_id'][ind_d[0]]],
    }


    print(origin_json, destination_json)

    payload = {
        "metadata": {
            "type": "Regular",
            "limit": 10,
            "sortBy": {
            "field": "Origin",
            "direction": "Ascending"
            },
            "fields": "all"
        },
        "includeWithGreaterPickupDates": True,
        "origin": origin_json,
        "destination": destination_json,
        "includeLoadsWithoutWeight": True,
        "includeLoadsWithoutLength": True
    }

    headers = {
    "Content-Type": "application/json",
    "123LB-Api-Version": "1.3",
    "User-Agent": "Logtrack-Aicopilot/0.0.2 (adithya@thelogtrack.com)",
    "Authorization": "bearer 7rZnZp76stScSJ_3Wpj0uLm1xKmyMJa2KLl0mQcAxDedfG_TqOHTex1ig6XonD8RxLFy90KzGY3_wgqqLEytolI5qRXTMgWZY2gJ1rw6fTfS7-Jwf56XESPMCQFPy50k8qeKCO5LS73ZCnomeqc9nXBdlCf8lGMYlSaZrRYy4PSmcAtlaknTL-MRGaDUEeFTsvmbPE6b8vOX0qyiH0Uc2ZhRpilOSbB0ORqq3VHS-mJ5RR44au5Fg0RVo-W3bcuNOFOXtHbf0Oox-KWVt799Ktw0e9hbR-B5UjOuCJkmMJnsi0g_ODz1F0mYqGa4tSgm5y90Lw2lhSxnpk9HqPipqDgbI6UETAprhHWAUo1BPGzaq8N2QJKxb-L1XETGeKjknfoRDjXmlLRr6pPmREQ34kwRQMrNj65odGmdyxzmI6a464RgVl9m64nc6nZCqUALp8Qca8ktAmeqqjnvpQsMpo-yEKMs6rhqGqYRgFC2J93DgvTzA25Xwc4eKUDM3lx5twdrx9koxaai4LeY_VwDa1EwFrud9EbrQzIQY_XTpQ7Pnxn1YkkfraUr3OmW3yw_PU9cXPugDPsL9oBKf2QFyn3iT7sHG_tJq7Huv3MR-k8ZODiGUIX3uV3U5_tpUHOz7ChRQqZ_uiHZHl9c2IVWu64fZgqc5aoIYKw3aJ_PYmnPDV5y3s7_LNR1-4CA3oLimPN09vrUNqUwH-2A84YwYijz_kt3Znzq-Q-tdkHysrYRt64QlEyYGM9_zAbMEAJ0dHnlMo-PQMYbnBH6-gZ-AEZzcqv16304GzF_HZt6wtHxrngt1kMzGDxo4hY9E_6AGp64aB2zRq0Okuyr0wZtZkxzgLoYcl4RoIxHJxRZqBoXWXtRxJ2MsM5zciEtKLaWjdNC2IO7OeYD2sDEm_L89g"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    create_csv_file(data)

    ## Need to convert this data to the csv to be used below.
    agent = create_csv_agent(
    ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613"),
    "loads.csv",
    verbose=True,
    agent_type=AgentType.OPENAI_FUNCTIONS,
    )

    return agent, origin,  [city_state['state_id'][ind_o[0]]], destination,  [city_state['state_id'][ind_d[0]]]

os.environ["OPENAI_API_KEY"] = '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'

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
            agent, origin, origin_st, destination, destination_st = populate_table(input_text)
            bot_response = agent.run(input_text.replace(origin, origin_st[0]).replace(destination, destination_st[0]))

        bot_response = bot_response.replace("\n","<br />")
        bot_response = bot_response.replace('Bing', 'LogBot')
        bot_response = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', bot_response)

        print('bot_Response', bot_response)

        return jsonify(bot_response)
    # except Exception as e:
    #     return jsonify(str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)