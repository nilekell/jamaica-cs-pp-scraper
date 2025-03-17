import requests
import sys
import datetime as dt
import smtplib
import os
from dotenv import load_dotenv
from email.message import EmailMessage

# visit url > intent created > intent used to fetch availability key > availability key used to fetch availabilities
# intents created for every browser session, find way to automate retrieval of new intent value
# startSearchAt should be incremented by a month when slots_data is empty, use iteration

# Jamaica passport application appointment web link: https://jhcukconsular.youcanbook.me/
# Jamaica citizenship application appointment web link: https://jhcukconsular-3.youcanbook.me/

AVAILABILITY_URL = "https://api.youcanbook.me/v1/availabilities"
INTENTS_URL = "https://api.youcanbook.me/v1/intents"

def get_intent_urls():
    # current_date = dt.datetime.today().strftime('%Y-%m-%d')
    # current_date = "2025-06-11" # date from available appointments
    current_date = "2025-06-01"
    # https://api.youcanbook.me/v1/intents/itt_00d55e5a-bcb7-418f-983b-970d70c980e8/availabilitykey?startSearchAt=2025-06-14
    passport_url = f"{INTENTS_URL}/itt_00d55e5a-bcb7-418f-983b-970d70c980e8/availabilitykey?startSearchAt={current_date}"
    citizenship_url = f"{INTENTS_URL}/itt_8fc262a2-50fc-493c-a82b-cb0e2e41763b/availabilitykey?startSearchAt={current_date}"
    return passport_url, citizenship_url

def get_env():
    load_dotenv()
    email = os.getenv('EMAIL') # sender
    password = os.getenv('PASSWORD') # google app-specific passwords can be created at https://myaccount.google.com/apppasswords
    destination_email = os.getenv('DESTINATION_EMAIL')
    return email, password, destination_email

def fetch_availability_key(intents_url):
    print("intents url:", intents_url)

    response = requests.get(intents_url)   

    if not response.ok:
        print(f"Failed to fetch data from {intents_url} - ERROR: {response.status_code}, {response.content}")
        sys.exit(1)

    data = response.json()
    key = data['key'] # availability keys expire after they are used to fetch data
    print("availability key:", key)
    return key


def fetch_available_slots(availability_key):
    slots_url = f"{AVAILABILITY_URL}/{availability_key}"
    print("slots url:", slots_url)
    dates_response = requests.get(slots_url)
    print("dates_response:", dates_response.status_code)

    if not dates_response.ok:
        print(f"Failed to fetch data from {slots_url} - ERROR: {dates_response.status_code}, {dates_response.content}")
        sys.exit(1)

    data = dates_response.json()
    slots_data = data['slots']
    print("slots_data:", slots_data)

    if slots_data == []:
        print(f"No available slots from {slots_url} - ERROR: {dates_response.status_code}")
        sys.exit(0)

    return slots_data

def extract_readable_data(slots_data):
    text = ""
    for slot in slots_data:
        num_free_slots = slot['freeUnits']
        apt_timestamp_ms = slot['startsAt']
        appointment_timestamp = int(apt_timestamp_ms) / 1000

        appointment_datetime = dt.datetime.fromtimestamp(appointment_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        text += f"{num_free_slots} slots available at {appointment_datetime}\n"

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


PASSPORT_INTENTS_URL, CITIZENSHIP_INTENTS_URL = get_intent_urls()
EMAIL, PASSWORD, DESTINATION_EMAIL = get_env()
passport_availability_key = fetch_availability_key(PASSPORT_INTENTS_URL)
passport_slots = fetch_available_slots(passport_availability_key)
passport_text = extract_readable_data(passport_slots)
# send_email("Available Appointments - Jamaican High Commission", passport_text)
