import requests
import sys
from datetime import *
from dateutil.relativedelta import *
import smtplib
import os
import re
from dotenv import load_dotenv
from email.message import EmailMessage
from constants import (
    PASSPORT_SUBDOMAIN,
    AVAILABILITY_URL,
    INTENTS_URL,
    CITIZENSHIP_SUBDOMAIN
)

def get_env():
    print("Accessing credentials from .env file...")
    load_dotenv()
    email = os.getenv('EMAIL') # sender
    password = os.getenv('PASSWORD') # google app-specific passwords can be created at https://myaccount.google.com/apppasswords
    destination_email = os.getenv('DESTINATION_EMAIL') # receiver
    template_path = os.getenv('TEMPLATE_PATH') 
    return email, password, destination_email, template_path

def handle_bad_response(response: requests.Response):
    if response.status_code == 429: # https://ycbm.stoplight.io/#rate-limits
        print(f"Rate limit reached for {response.request.url} - ERROR: {response.status_code}, {response.content}")
        sys.exit(1)
    else:
        print(f"Failed to fetch data from {response.request.url} - ERROR: {response.status_code}, {response.content}")
        sys.exit(1)

def fetch_intent(subdomain: str):
    print(f"Fetching {subdomain} intent...")
    data = {
	"subdomain": subdomain,
    "selections": {
		"timeZone": "UTC"
	    }
    }

    response = requests.post(INTENTS_URL, json=data)
    if not response.ok:
        handle_bad_response(response)

    data = response.json()
    intent_id = data['id']

    return intent_id


def fetch_availability_key(intent_id, from_date=datetime.today().date()) -> str:
    search_date = from_date
    print(f"Searching from {search_date}...")
    search_url = f"{INTENTS_URL}/{intent_id}/availabilitykey?startSearchAt={search_date}"
    print("search_url:", search_url)
    response = requests.get(search_url)   

    if not response.ok:
        handle_bad_response(response)

    data = response.json()
    key = data['key']
    print("availability key:", key)
    return key


def fetch_available_slots(intent_id: str, from_date=datetime.today().date()):
    print("Scraping appointments...")
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
            handle_bad_response(response)

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
    print("Converting slot data into readable format...")
    
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

def fill_email_text(template_path, passport_text, citizenship_text):
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    email_text = re.sub(r"###PASSPORT_TEXT###", passport_text, template)
    email_text = re.sub(r"###CITIZENSHIP_TEXT###", citizenship_text, email_text)

    return email_text

def send_email(subject, text):
    try:
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
        print("Email sent.")
        # terminating the session
        smtp_server.quit()
    except:
        print("ERROR: An error occured while attempting to create and send email.")
        sys.exit(1)

def get_passport_apt_text():
    passport_intent_id = fetch_intent(PASSPORT_SUBDOMAIN)
    passport_slots = fetch_available_slots(passport_intent_id)
    passport_text = extract_readable_data(passport_slots)

    return passport_text

def get_citizenship_apt_text():
    citizenship_intent_id = fetch_intent(CITIZENSHIP_SUBDOMAIN)
    citizenship_slots = fetch_available_slots(citizenship_intent_id)
    citizenship_text = extract_readable_data(citizenship_slots)

    return citizenship_text

if __name__ == "__main__":
    EMAIL, PASSWORD, DESTINATION_EMAIL, TEMPLATE_PATH = get_env()

    passport_text = get_passport_apt_text()
    citizenship_text = get_citizenship_apt_text()
    
    email_text = fill_email_text(TEMPLATE_PATH, passport_text, citizenship_text)
    # print(email_text)

    send_email("Available Appointments - Jamaican High Commission", email_text)

    print("Scraper executed successsfully.")
    
