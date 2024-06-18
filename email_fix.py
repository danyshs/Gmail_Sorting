import os
import re
import pickle
import time
import logging
import functools
import xml.etree.ElementTree as ET
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Configuration constants
SCOPES = ['https://mail.google.com/']
TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'
OUTPUT_FILE = 'output.txt'
XML_FILE = 'mailFilters.xml'
DEFAULT_COUNT = 80000  # Default number of emails to read
COMMS_NUMBER = 50  # How many emails after which to give a status update

def extract_email_address(string):
    email_match = re.search(r'<(.+)>', string)
    return email_match.group(1) if email_match else string

def get_credentials():
    creds = None
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
    except Exception as e:
        print(f"An error occurred while obtaining credentials: {e}")
        print("Please try the following steps to resolve the issue:")
        print("1. Ensure that 'credentials.json' is present and contains valid OAuth client ID and client secret.")
        print("2. Delete 'token.pickle' and run the script again to re-authenticate.")
        print("3. Verify that your Google Cloud project is configured correctly and the OAuth consent screen is set up.")
    return creds

def fetch_messages(service, count):
    fetchTime = time.perf_counter()
    messages = []
    try:
        results = service.users().messages().list(userId='me', maxResults=100).execute()
        messages.extend(results.get('messages', []))

        while len(messages) < count and 'nextPageToken' in results:
            page_token = results['nextPageToken']
            results = service.users().messages().list(userId='me', maxResults=100, pageToken=page_token).execute()
            messages.extend(results['messages'])

        logging.info(f'Successfully fetched {len(messages)} messages.')
        currTime = round(time.perf_counter() - fetchTime,2)
        print(f'Time taken {currTime} seconds.')
        
        return messages[:count]
    except HttpError as error:
        print(f'An error occurred while fetching messages: {error}')
        return messages
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
        return messages

def parse_xml_file(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        xml_emails = set()
        for prop in root.findall(".//apps:property[@name='from']", namespaces={'apps': 'http://schemas.google.com/apps/2006'}):
            value = prop.get('value')
            if value is not None:
                emails = value.split(' OR ')
                xml_emails.update(extract_email_address(email.strip()) for email in emails)
        return xml_emails
    except ET.ParseError as e:
        print(f'Error parsing XML file: {e}')
        return set()
    except FileNotFoundError:
        print(f'XML file {xml_file} not found.')
        return set()
    except Exception as e:
        print(f'An unexpected error occurred while parsing the XML file: {e}')
        return set()

def process_messages(service, messages, xml_emails):
    unique_emails = {}
    total_messages = len(messages)
    start_time = time.perf_counter()
    next_milestone = COMMS_NUMBER
    last_email_process_time = start_time  # Initialize the last email process time

    try:
        with open(OUTPUT_FILE, 'w') as f:
            if not messages:
                f.write('All Mails is Empty\n')
            else:
                for i, message_tuple in enumerate(messages):
                    current_time = time.perf_counter()  # Get current time for this iteration

                    try:
                        message = dict(message_tuple)
                        msg = service.users().messages().get(userId='me', id=message['id']).execute()
                        email_data = msg['payload']['headers']
                        email_processed = False  # Flag to track if email has been processed

                        for values in email_data:
                            if values['name'] == 'From':
                                email = extract_email_address(values['value'])
                                if email not in xml_emails:
                                    unique_emails[email] = unique_emails.get(email, 0) + 1
                                    email_processed = True  # Mark email as processed
                                    last_email_process_time = current_time  # Update last process time

                        if not email_processed:
                            # Check if 10 seconds have passed since the last successful email processing
                            if current_time - last_email_process_time > 10:
                                logging.warning('API LIMIT REACHED, PLEASE WAIT')
                                print('API LIMIT REACHED, PLEASE WAIT')

                    except HttpError as error:
                        logging.error(f'An error occurred with message ID {message["id"]}: {error}')
                        f.write(f'An error occurred with message ID {message["id"]}: {error}\n')
                    except Exception as e:
                        logging.error(f'An unexpected error occurred with message ID {message["id"]}: {e}')
                        f.write(f'An unexpected error occurred with message ID {message["id"]}: {e}\n')

                    if i >= next_milestone:
                        elapsed_time = current_time - start_time
                        estimated_total_time = (elapsed_time / (i + 1)) * total_messages
                        eta = estimated_total_time - elapsed_time
                        print(f'Processed {i}/{total_messages} messages. ETA: {eta // 60:.0f} minutes {eta % 60:.0f} seconds.')
                        logging.info(f'Processed {i}/{total_messages} messages. ETA: {eta // 60:.0f} minutes {eta % 60:.0f} seconds.')

                        next_milestone += COMMS_NUMBER

            unique_emails_alphabetical = sorted(unique_emails.items())
            unique_emails_count = sorted(unique_emails.items(), key=lambda item: item[1], reverse=True)

            f.write("-----------------------------\n")
            f.write("BY ALPHABETICAL\n")
            for email, count in unique_emails_alphabetical:
                f.write(f'{email} || {count}\n')

            f.write("-----------------------------\n")
            f.write("BY FREQUENCY\n")
            for email, count in unique_emails_count:
                f.write(f'{email} || {count}\n')

            f.write("-----------------------------\n")

    except Exception as e:
        logging.error(f'An error occurred while processing messages: {e}')
        print(f'An error occurred while processing messages: {e}')

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    logging.basicConfig(filename='email_processing.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info('Script execution started.')

    user_input = input(f"How many emails would you like to read? (default {DEFAULT_COUNT}): ")

    try:
        count_mess = int(user_input) if user_input else DEFAULT_COUNT
    except ValueError:
        print("Invalid input. Using the default value.")
        count_mess = DEFAULT_COUNT
    print(f"Fetching {count_mess} emails...")

    creds = get_credentials()
    if creds is None:
        print("Failed to obtain credentials. Exiting.")
        return

    try:
        service = build('gmail', 'v1', credentials=creds)
    except Exception as e:
        print(f"An error occurred while building the Gmail service: {e}")
        return

    messages = fetch_messages(service, count_mess)
    messages_tuple = tuple(tuple(message.items()) for message in messages)  # Convert each dict to tuple of key-value pairs
    print("Fetching successful! Beginning processing task")
    xml_emails = parse_xml_file(XML_FILE)
    xml_emails_tuple = tuple(xml_emails)  # Convert set to tuple
    process_messages(service, messages_tuple, xml_emails_tuple)

if __name__ == '__main__':
    main()
