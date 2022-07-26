# pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

from __future__ import print_function
import datetime

import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import re

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

# The ID of a sample document.
EE_DOCUMENT_ID = '1TB5AR1xkLTPphnbDmQbqqZ3pCi-9ZTI5hUbbTKKiCA4'
DERPY_DOCUMENT_ID = '1B4yVuvYlT062HXP7-7gbgpb0MH2d-mWBqWOYGOtbceY'

USA_DATE_EXPRESSION = '(0[1-9]|1[012]|[1-9])[- /.](0[1-9]|[12][0-9]|3[01]|[1-9])[- /.](19|20)\d\d'


def parse_ee_date(document):
    body = document.get("body")["content"][1:]
    for el in body:
        for element in el["paragraph"]["elements"]:
            content = element["textRun"]["content"]
            result = re.search(r'(\d+/\d+/\d+)', content)
            if result is not None:
                date = result.group(1)
                date = datetime.datetime.strptime(date,"%m/%d/%Y")
                return date.strftime("%d/%m/%Y")

def parse_derpy_date(document):
    body = document.get("body")["content"]
    for i in range(len(body) - 1, -1, -1): # Traverse backwards
        el = body[i]
        for element in el["paragraph"]["elements"]:
            content = element["textRun"]["content"]
            result = re.search(r'(\d+/\d+/\d+)', content)
            if result is not None:
                date = result.group(1)
                date = datetime.datetime.strptime(date,"%d/%m/%Y")
                return date.strftime("%d/%m/%Y")

def get_document(document_id):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('docs', 'v1', credentials=creds)
        # Retrieve the documents contents from the Docs service.
        document = service.documents().get(documentId=document_id).execute()
        return document

    except HttpError as err:
        print(err)
        return None

def main():
    derpy_document = get_document(DERPY_DOCUMENT_ID)
    print(f"Derpy latest:{parse_derpy_date(derpy_document)}")
    ee_document = get_document(EE_DOCUMENT_ID)
    print(f"EE latest:{parse_ee_date(ee_document)}")



if __name__ == '__main__':
    main()
