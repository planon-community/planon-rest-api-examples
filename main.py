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

if __name__ == "__main__":

    ### LOAD CACHE
    with open(file='cache/identities.json', mode='r') as file:
        identities = json.load(file)

    with open(file='cache/departments.json', mode='r') as file:
        departments = json.load(file)

    with open(file='cache/positions.json', mode='r') as file:
        positions = json.load(file)

    ### LOAD IDENTITIES

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

    end_time = time.time()

    ### READ BO
    filter = {
        "filter": {
            "Code": {'eq': 471}
        }
    }
    response = session.post(url=f"{url}/read/Person", json=filter)
    log.info(f"Found [{len(response.json()['records'])}] records for filter={filter}")
