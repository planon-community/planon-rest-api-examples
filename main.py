import os
import time
import sys
import logging

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

session.headers = {
    "Content-Type": "application/json",
    "Authorization": f"PLANONKEY accesskey={os.environ.get('PLN_API_KEY')}"
}

# *********************************************** #
# CONFIGURATION
# *********************************************** #

bo = "Person"
code = "100000123"

# *********************************************** #
# MAIN
# *********************************************** #

if __name__ == "__main__":

    ### CREATE BO
    log.info(f"Creating instance of business object {bo}")
    body = {
        "values": {
            "FirstName": "John",
            "Initials": "JD",
            "LastName": "Doe",
            "RefBOStateUserDefined": 1079,
        }
    }
    response = session.post(url=f"{url}/execute/{bo}/BomAdd", json=body)
    log.debug(f"API response: {response.json()}")

    ### READ BO
    filter = {
        "filter": {
            "Code": {'eq': 471}
        }
    }
    response = session.post(url=f"{url}/read/{bo}", json=filter)
    log.info(f"Found [{len(response.json()['records'])}] records for filter={filter}")
