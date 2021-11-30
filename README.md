# Notes

## Setup

1. Setup Python virtual environment

    ```bash
    python3 -m venv venv
    ```

2. Source venv

    ```bash
    source venv/bin/activate
    ```

3. Install requirements

    ```bash
    pip install -r requirements
    ```

4. Create a copy of .env-template as .env, fill in required environment variable values
5. Source .env and run python script

    ```bash
    source .env
    python ./main.py
    ```
