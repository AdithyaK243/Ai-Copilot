import g4f
import pandas as pd
import re

file = pd.ExcelFile('/home/adithya/Desktop/Adi/Highers/Columbia/Spring_23/CBL/chatbot/Load-Posting-Template.xlsx')
data = file.parse('Loads')

data1 = data.iloc[:100]

def remove_links(input_text):
    # Remove links using regular expression
    output_text = re.sub(r'https?://\S+', '', input_text)
    return output_text

# Set with provider
stream = False
response = g4f.ChatCompletion.create(model='gpt-4', provider=g4f.Provider.Bing, messages=[
                                    #  {"role": "user", "content": "Can you send an email, if I give you the mail id?"},
                                     {"role": "user", "content": "Can you tell the give recent papers in the topic of Verification of internal model principle using Reinforcement learning"}
                                    ], stream=stream)

# if stream:
#     for message in response:
#         print(message)
# else:   
#     print(response)

# Remove [1] to [5] points and entire links
bot_response = re.sub(r'\[\d+\]:.*?$', '', "r'" + response + "'" , flags=re.MULTILINE)
bot_response = bot_response.strip("r'").strip(' ').strip('\n')
cleaned_text = re.sub(r'\[.*?\]', '', bot_response)


print(cleaned_text)