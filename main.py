import os
import time
import sys
import logging
import json
import random

import requests

# *********************************************** #
# LOGGING
# *********************************************** #

log_level = str.upper(os.environ.get('LOG_LEVEL', 'DEBUG'))
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(stream = sys.stdout, level = log_level, format = log_format)

# Set the log to use GMT time zone
logging.Formatter.converter = time.gmtime

# Add milliseconds
logging.Formatter.default_msec_format = '%s.%03d'

log = logging.getLogger(__name__)

# *********************************************** #
# SETUP
# *********************************************** #

session = requests.Session()

url = os.environ.get("PLN_API_URL")

session.headers.update({
    "Content-Type": "application/json",
    "Authorization": f"PLANONKEY accesskey={os.environ.get('PLN_API_KEY')}"
})

# *********************************************** #
# CONFIGURATION
# *********************************************** #

max_pages = 15
max_results = 5000
time_sleep = 120
seed = "dartmouth"

# *********************************************** #
# CACHE
# *********************************************** #

################# IDENTITIES #################
identities = []
for page in range(1, max_pages):
    # TODO: cache additional identies, left off at page 7
    response = requests.get(url=f"https://randomuser.me/api?seed={seed}&results={max_results}&page={page}")

    # Throttling
    log.info(f"Sleeping for {time_sleep} seconds")
    time.sleep(time_sleep)

    if response.ok:
        identities = identities + response.json()['results']

with open(file='cache/identities.json', mode='w') as file:
    file.write(json.dumps(identities))

################# DEPARTMENTS #################

departments = session.post(url=f"{url}/read/Department", json={}).json()['records']

with open(file='cache/departments.json', mode='w') as file:
    file.write(json.dumps(departments))

################# DEPARTMENTS #################

positions = session.post(url=f"{url}/read/PersonPosition", json={}).json()['records']

with open(file='cache/positions.json', mode='w') as file:
    file.write(json.dumps(positions))

# *********************************************** #
# MAIN
# *********************************************** #

### LOAD CACHE
with open(file='cache/identities.json', mode='r') as file:
    identities = json.load(file)

with open(file='cache/departments.json', mode='r') as file:
    departments = json.load(file)

with open(file='cache/positions.json', mode='r') as file:
    positions = json.load(file)

### LOAD IDENTITIES

failed = []
request_statistics = []
records = []

start_time = time.time()
for identity in identities:
    log.info(f"Creating instance of Person object {identity['name']['last']}, {identity['name']['first']}")

    ### CREATE BO
    body = {
        "values": {
            "FirstName": identity['name']['first'],
            "Initials": f"{identity['name']['first'][0]}{identity['name']['last'][0]}",
            "LastName": identity['name']['last'],
            "RefBOStateUserDefined": 1079,
            "PersonPositionRef": random.choice(positions)['Syscode'],
            "DepartmentRef": random.choice(departments)['Syscode']
        }
    }

    try:
        request_start_time = time.time()
        response = session.post(url=f"{url}/execute/UsrEmployee/BomAdd", json=body)
        request_end_time = time.time()

        request_statistics.append({
            "start": request_start_time,
            "end": request_end_time,
            "response_code": response.status_code
        })

        response.raise_for_status()

        records = records + response.json()['records']

    except Exception as e:
        log.error(repr(e))
        failed.append({
            'body': body,
            'error': repr(e)
        })

end_time = time.time()
total_duration = (end_time - start_time) / 60

# *********************************************** #
# STATISTICS
# *********************************************** #

log.info("# ======================= STATISTICS ======================= #")
log.info(f"TOTAL DURATION (seconds): {total_duration}")
log.info(f"TOTAL SOURCE RECORDS: {len(identities)}")
log.info(f"TOTAL PLANON RECORDS: {len(records)}")

# *********************************************** #
# CLEANUP
# *********************************************** #

chunk_size = 1000
syscodes = [record['Syscode'] for record in records]
chunked_records = [syscodes[i:i + chunk_size] for i in range(0, len(syscodes))]

'''{
    "filter": {
        "Syscode": {"ge": 1},
        "Syscode": {"le": 100}
    }
}'''

for chunk in chunked_records:
    body = f'''{{
        "filter": {{
            "Syscode": {{"ge": {chunk[0]}}},
            "Syscode": {{"le": {chunk[-1]}}}
        }}
    }}'''

    # b'{"uuid":"334ead57-11a1-4e0f-a6bf-f010a075d055","message":"Execute on multiple BO\'s not implemented"}'
    # response = session.post(url=f"{url}/execute/UsrEmployee/BomDelete", data=body)

    response = session.post(url=f"{url}/read/UsrEmployee", data=body)
    len(response.json()['records']) == chunk_size