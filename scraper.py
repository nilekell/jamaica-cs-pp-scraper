import requests
import sys
import datetime as dt

# PASSPORT_APPLICATION_WEB_URL = "https://jhcukconsular.youcanbook.me/"
# CITIZENSHIP_APPLICATION_WEB_URL = "https://jhcukconsular-3.youcanbook.me/"

AVAILABILITY_URL = "https://api.youcanbook.me/v1/availabilities"
INTENTS_URL = "https://api.youcanbook.me/v1/intents"
current_date = dt.datetime.today().strftime('%Y-%m-%d')
search_date = "2025-06-11"

PASSPORT_INTENTS_URL = f"{INTENTS_URL}/itt_8fc262a2-50fc-493c-a82b-cb0e2e41763b/availabilitykey?startSearchAt={search_date}"
CITIZENSHIP_INTENTS_URL = f"{INTENTS_URL}/itt_8fc262a2-50fc-493c-a82b-cb0e2e41763b/availabilitykey?startSearchAt={search_date}"

url = PASSPORT_INTENTS_URL
response = requests.get(url)   

if response.status_code != 200:
    print(f"Failed to fetch data from {url} - ERROR: {response.status_code}")
    sys.exit(1)

data = response.json()
availability_key = data['key'] # availability keys expire after they are used to fetch data
# print(availability_key)

dates_url = f"{AVAILABILITY_URL}/{availability_key}"
print(dates_url)
dates_response = requests.get(dates_url)

if dates_response.status_code != 200:
    print(f"Failed to fetch data from {dates_url} - ERROR: {dates_response.status_code}")
    sys.exit(1)

dates_data = dates_response.json()
# print(dates_data)

slots = dates_data['slots']
if slots == []:
    print(f"No available slots from {dates_url} - ERROR: {dates_response.status_code}")
    sys.exit(0)

for slot in slots:
    num_free_slots = slot['freeUnits']
    apt_timestamp_ms = slot['startsAt']
    appointment_timestamp = int(apt_timestamp_ms) / 1000

    appointment_datetime = dt.datetime.fromtimestamp(appointment_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    print(f"{num_free_slots} slots available at {appointment_datetime}")


