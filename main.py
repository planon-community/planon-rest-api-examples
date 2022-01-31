import os
import time
import sys
import logging
import json

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

max_pages = 100
max_results = 5000
time_sleep = 120
seed = "dartmouth"

# *********************************************** #
# CACHE
# *********************************************** #

# IDENTITIES
identities = []
for page in range(1, max_pages):
    response = requests.get(url=f"https://randomuser.me/api?seed={seed}&results={max_results}&page={page}")

    # Throttling
    log.info(f"Sleeping for {time_sleep} seconds")
    time.sleep(time_sleep)

    if response.ok:
        identities = identities + response.json()['results']

with open(file='cache/identies.json', mode='w') as file:
    file.write(json.dumps(identities))

# *********************************************** #
# MAIN
# *********************************************** #

if __name__ == "__main__":

    ### Source identities
    source_identities = requests.get(url="https://randomuser.me/api?results=100").json()['results']

    for source_identity in source_identities:
        log.info(f"Creating instance of Person object {source_identity['name']['last']}, {source_identity['name']['first']}")

        ### CREATE BO
        body = {
            "values": {
                "FirstName": source_identity['name']['first'],
                "Initials": f"{source_identity['name']['first'][0]}{source_identity['name']['last'][0]}",
                "LastName": source_identity['name']['last'],
                "RefBOStateUserDefined": 1079,
            }
        }

        try:
            response = session.post(url=f"{url}/execute/UsrEmployee/BomAdd", json=body)
            response.raise_for_status()

            log.debug(f"API response: {response.json()}")
        except Exception as e:
            log.error(repr(e))

    ### READ BO
    filter = {
        "filter": {
            "Code": {'eq': 471}
        }
    }
    response = session.post(url=f"{url}/read/Person", json=filter)
    log.info(f"Found [{len(response.json()['records'])}] records for filter={filter}")
