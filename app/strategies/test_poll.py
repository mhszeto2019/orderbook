
import time
import select
import configparser
import os
config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_folder', 'credentials.ini')
config.read(config_file_path)

config_source = 'localdb'
dbusername = config[config_source]['username']
dbpassword = config[config_source]['password']
dbname = config[config_source]['dbname']

import psycopg2
import select
import time
import json
# Database configuration values
db_config = {
    'user': dbusername,       # Replace with your DB username
    'password': dbpassword,   # Replace with your DB password
    'host': 'localhost',        # DB host (usually 'localhost' for local connections)
    'port': 5432,               # DB port (default PostgreSQL port is 5432)
    'database': dbname     # Replace with your DB name
}

def listen_for_notifications(filter_username=None):
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(
            dbname=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            host=db_config['host'],
            port=db_config['port']
        )
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Start listening to the 'algo_dets_channel'
        cur.execute("LISTEN algo_dets_channel;")
        print("Listening for notifications on 'algo_dets_channel'...")

        while True:
            # Wait for a notification with a timeout
            if select.select([conn], [], [], 5) == ([], [], []):
                print("No notification received within 5 seconds.")
                continue

            # Poll the connection for notifications
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop()
                try:
                    # Parse the payload as JSON
                    payload = json.loads(notify.payload)
                    print('payload',payload)
                    operation = payload.get('operation')
                    data = payload.get('data')
                    username = data.get('username')

                    print(data,username)
                    # Check if the username matches the filter
                    if filter_username is None or username == filter_username:
                        print(
                            f"Notification received for user '{username}': {operation} - {data}"
                        )
                    else:
                        continue
                        print(f"Ignored notification for user '{username}'.")

                except json.JSONDecodeError:
                  print(f"Received invalid JSON payload: {notify.payload}")

    except Exception as e:
        print(f"Error listening for notifications: {e}")
        time.sleep(5)  # Retry delay
        listen_for_notifications(filter_username)  # Retry listening

if __name__ == "__main__":
    try:
        # Pass the username you want to filter by, or None for no filtering
        listen_for_notifications(filter_username="brennan")
    except KeyboardInterrupt:
        print("Listener stopped by user.")