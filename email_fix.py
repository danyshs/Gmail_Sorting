import os
import re
import pickle
import xml.etree.ElementTree as ET
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def extract_email_address(string):
    email_match = re.search(r'<(.+)>', string)
    return email_match.group(1) if email_match else string

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://mail.google.com/']

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    count_mess = 40000
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API
    results = service.users().messages().list(userId='me', maxResults=100).execute()
    messages = results.get('messages', [])

    unique_emails = {}  # Change this line

    while len(messages) < count_mess and 'nextPageToken' in results:
        page_token = results['nextPageToken']
        results = service.users().messages().list(userId='me', maxResults=100, pageToken=page_token).execute()
        messages.extend(results['messages'])

    messages = messages[:count_mess]  # Ensure we only process the last 40000 emails

    with open('output.txt', 'w') as f:
        if not messages:
            f.write('All Mails is Empty\n')
        else:
            for message in messages:
                try:
                    msg = service.users().messages().get(userId='me', id=message['id']).execute()
                    email_data = msg['payload']['headers']
                    for values in email_data:
                        if values['name'] == 'From':
                            email = extract_email_address(values['value'])
                            unique_emails[email] = unique_emails.get(email, 0) + 1  # Change this line
                except HttpError as error:
                    f.write(f'An error occurred with message ID {message["id"]}: {error}\n')
                    try:
                        msg = service.users().messages().get(userId='me', id=message['id']).execute()
                        f.write('Subject: ' + msg['subject'] + '\n')
                        f.write('Snippet: ' + msg['snippet'] + '\n')
                        f.write('Payload: ' + str(msg['payload']) + '\n')
                    except Exception as e:
                        f.write(f'An error occurred while trying to print the contents of the email: {e}\n')

        # Parse the XML file and get the email addresses
        tree = ET.parse('mailFilters.xml')
        root = tree.getroot()

        xml_emails = set()
        for prop in root.findall(".//apps:property[@name='from']", 
                                 namespaces={'apps': 'http://schemas.google.com/apps/2006'}):
            value = prop.get('value')
            if value is not None:
                emails = value.split(' OR ')
                xml_emails.update(extract_email_address(email.strip()) for email in emails)

        # Remove the email addresses that are in the XML file from unique_emails
        unique_emails = {email: count for email, count in unique_emails.items() if email not in xml_emails}

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

if __name__ == '__main__':
    main()