import requests
import sys
from datetime import *
from dateutil.relativedelta import *
import smtplib
import os
from dotenv import load_dotenv
from email.message import EmailMessage

# visit url > intent created > intent used to fetch availability key > availability key used to fetch availabilities
# intents can be used to create multiple availability keys (last created 6:20)
# availability keys expire around 2-3 minutes after they are used to fetch slots data

# TODO
# intents created for every browser session, find way to automate retrieval of new intent value

AVAILABILITY_URL = "https://api.youcanbook.me/v1/availabilities"
INTENTS_URL = "https://api.youcanbook.me/v1/intents"

passport_intent_id = "itt_00d55e5a-bcb7-418f-983b-970d70c980e8"
citizenship_intent_id = "itt_8536231b-c31c-49d0-b26f-7b4518a13189"

def get_env():
    load_dotenv()
    email = os.getenv('EMAIL') # sender
    password = os.getenv('PASSWORD') # google app-specific passwords can be created at https://myaccount.google.com/apppasswords
    destination_email = os.getenv('DESTINATION_EMAIL') # receiver
    return email, password, destination_email

def fetch_availability_key(intent_id, from_date=datetime.today().date()) -> str:
    search_date = from_date
    print(f"Searching from {search_date}...")
    search_url = f"{INTENTS_URL}/{intent_id}/availabilitykey?startSearchAt={search_date}"
    print("search_url:", search_url)
    response = requests.get(search_url)   

    if not response.ok:
        print(f"Failed to fetch data from {search_url} - ERROR: {response.status_code}, {response.content}")
        sys.exit(1)

    data = response.json()
    key = data['key']
    print("availability key:", key)
    return key


def fetch_available_slots(intent_id: str, from_date=datetime.today().date()):
    base_month = from_date.replace(day=1)

    monthly_slots = []

    # Fetch data for the current month plus the next 4 months (5 months total)
    for i in range(5):
        month_date = base_month + relativedelta(months=i)

        # Fetch the availability key for this month
        availability_key = fetch_availability_key(intent_id, month_date)
        slots_url = f"{AVAILABILITY_URL}/{availability_key}"

        response = requests.get(slots_url)
        if not response.ok:
            print(f"Failed to fetch data from {slots_url} - ERROR: {response.status_code}, {response.content}")
            sys.exit(1)

        data = response.json()
        slots_data = data.get('slots', []) # provide empty list if no values found
        monthly_slots.append({
            'month_date': month_date,
            'slots': slots_data
        })

    return monthly_slots


def extract_readable_data(monthly_slots):
    """
    monthly_slots is a list of lists, where each sublist represents
    all the slots for a given month.
    """
    overall_text = ""

    for item in monthly_slots:
        month_date = item['month_date']
        slots_data = item['slots']

        # Always generate a month/year label from month_date
        month_label = month_date.strftime('%B %Y')  # e.g. "June 2025"
        month_text = f"=== {month_label} ===\n"

        if slots_data:
            for slot in slots_data:
                num_free_slots = slot['freeUnits']
                apt_timestamp_ms = slot['startsAt']
                appointment_timestamp = int(apt_timestamp_ms) / 1000
                appointment_dt = datetime.fromtimestamp(appointment_timestamp)

                # Day of week, numeric day/month, and HH:MM
                day_of_week = appointment_dt.strftime('%a')     # e.g. "Thu"
                day_month   = appointment_dt.strftime('%d/%m')  # e.g. "16/06"
                hour_minute = appointment_dt.strftime('%H:%M')  # e.g. "11:10"

                # Pluralize 'slot' if needed
                slots_word = "slots" if num_free_slots > 1 else "slot"
                month_text += f"{day_of_week} {day_month} at {hour_minute} | {num_free_slots} {slots_word}\n"
        else:
            month_text += "No slots available.\n"

        overall_text += month_text + "\n"

    print(overall_text)
    return overall_text


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
print("Scraping passport appointments...")
passport_slots = fetch_available_slots(passport_intent_id)
passport_text = extract_readable_data(passport_slots)
print("Scraping citizenship appointments...")
citizenship_slots = fetch_available_slots(citizenship_intent_id)
citizenship_text = extract_readable_data(citizenship_slots)

email_text = f'''
Hello,

Below are the upcoming appointment dates for the United Kingdom Jamaican High Commission passport and citizenship services:

Passport appointments:

{passport_text}

For more information or to schedule your passport appointment, visit:
https://jhcukconsular.youcanbook.me/



Citizenship appointments:

{citizenship_text}

For more information or to schedule your citizenship appointment, visit:
https://jhcukconsular-3.youcanbook.me/


For urgent consular matters only, please send an email to consular@jhcuk.com [NOT AFFILIATED WITH 'The Jamaica Scraping Team']

Kind regards,

The Jamaica Scraping Team
'''

# print(email_text)
send_email("Available Appointments - Jamaican High Commission", email_text)
