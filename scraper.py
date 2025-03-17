import requests
import sys
from datetime import *
from dateutil.relativedelta import *
import smtplib
import os
from dotenv import load_dotenv
from email.message import EmailMessage

# Jamaica passport application appointment web link: https://jhcukconsular.youcanbook.me/
# Jamaica citizenship application appointment web link: https://jhcukconsular-3.youcanbook.me/

# visit url > intent created > intent used to fetch availability key > availability key used to fetch availabilities
# intents can be used to create multiple availability keys (last created 6:20)
# availability keys expire around 2-3 minutes after they are used to fetch slots data

# TODO
# intents created for every browser session, find way to automate retrieval of new intent value
# startSearchAt should be incremented by (1) month when slots_data is empty, use iteration

AVAILABILITY_URL = "https://api.youcanbook.me/v1/availabilities"
INTENTS_URL = "https://api.youcanbook.me/v1/intents"

def get_env():
    load_dotenv()
    email = os.getenv('EMAIL') # sender
    password = os.getenv('PASSWORD') # google app-specific passwords can be created at https://myaccount.google.com/apppasswords
    destination_email = os.getenv('DESTINATION_EMAIL') # receiver
    return email, password, destination_email

def fetch_availability_key(from_date=datetime.today().date()) -> str:
    search_date = from_date
    search_url = f"{INTENTS_URL}/itt_00d55e5a-bcb7-418f-983b-970d70c980e8/availabilitykey?startSearchAt={search_date}"
    print("search_url:", search_url)
    response = requests.get(search_url)   

    if not response.ok:
        print(f"Failed to fetch data from {search_url} - ERROR: {response.status_code}, {response.content}")
        sys.exit(1)

    data = response.json()
    key = data['key']
    print("availability key:", key)
    return key


def fetch_available_slots(from_date=datetime.today().date()):
    availability_key = fetch_availability_key(from_date)
    slots_url = f"{AVAILABILITY_URL}/{availability_key}"
    print("slots url:", slots_url)
    slots_response = requests.get(slots_url)
    print("slots_response:", slots_response.status_code)

    if not slots_response.ok:
        print(f"Failed to fetch data from {slots_url} - ERROR: {slots_response.status_code}, {slots_response.content}")
        sys.exit(1)

    data = slots_response.json()
    slots_data = data['slots']
    # print("slots_data:", slots_data)

    if not slots_data:
        attempts = 0
        print(f"No available slots from {slots_url} - ERROR: {slots_response.status_code}")
        print("retrying...")
        
        while attempts < 7:
            attempts += 1
            today = datetime.today()
            print(today.date())
            next_month_date = (today+relativedelta(months=+attempts)).date()
            slots_data = fetch_available_slots(next_month_date)

    return slots_data

def extract_readable_data(slots_data):
    text = ""
    for slot in slots_data:
        num_free_slots = slot['freeUnits']
        apt_timestamp_ms = slot['startsAt']
        appointment_timestamp = int(apt_timestamp_ms) / 1000
        appointment_dt = datetime.fromtimestamp(appointment_timestamp)

        # Day of week (Mon, Tue, Wed...), numeric month/day, and HH:MM
        day_of_week = appointment_dt.strftime('%a')
        month_day = appointment_dt.strftime('%d/%m')
        hour_minute = appointment_dt.strftime('%H:%M')

        slots_word = "slots" if num_free_slots > 1 else "slot"
        text += f"{num_free_slots} {slots_word} | {day_of_week} {month_day} at {hour_minute}\n"

    print("text:", text)
    return text

def send_email(subject, text):
    smtp_server = smtplib.SMTP('smtp.gmail.com', 587) # creates SMTP session
    smtp_server.starttls()
    smtp_server.login(EMAIL, PASSWORD)
    # construct message to be sent
    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = EMAIL
    message['To'] = DESTINATION_EMAIL
    message.set_content(text)
    smtp_server.send_message(message)
    # terminating the session
    smtp_server.quit()


EMAIL, PASSWORD, DESTINATION_EMAIL = get_env()
passport_slots = fetch_available_slots()
passport_text = extract_readable_data(passport_slots)

email_text = f'''
Hello,

Below are the upcoming appointment dates for Jamaican High Commission passport and citizenship services:

Passport appointments:

{passport_text}

For more information or to schedule your passport appointment, visit:
https://jhcukconsular.youcanbook.me/



Citizenship appointments:

{'<placeholder>'}

For more information or to schedule your citizenship appointment, visit:
https://jhcukconsular-3.youcanbook.me/



Kind regards,

Nile
'''

print(email_text)
# send_email("Available Appointments - Jamaican High Commission", email_text)
