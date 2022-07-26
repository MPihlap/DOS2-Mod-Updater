# https://developers.google.com/docs/api/quickstart/python

import datetime

import os.path
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import re
import requests
import json

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

# The ID of a sample document.
EE_DOCUMENT_ID = '1TB5AR1xkLTPphnbDmQbqqZ3pCi-9ZTI5hUbbTKKiCA4'
DERPY_DOCUMENT_ID = '1B4yVuvYlT062HXP7-7gbgpb0MH2d-mWBqWOYGOtbceY'

EPIP_CHANGELOG_URL = "https://www.pinewood.team/epip/patchnotes/"


def parse_ee_date(document):
    body = document.get("body")["content"][1:]
    date = None
    version = None
    for el in body:
        for element in el["paragraph"]["elements"]:
            version_expression = "Patch (?P<Version>\d+):"
            date_expression = '(\d+/\d+/\d+)'
            content = element["textRun"]["content"]
            version_result = re.match(version_expression, content)
            date_result = re.search(date_expression, content)
            if date_result is not None:
                date = date_result.group(1)
                date = datetime.datetime.strptime(date,"%m/%d/%Y")
                date = date.strftime("%d/%m/%Y")
            if version_result is not None:
                version = version_result.group("Version")
            if date is not None and version is not None:
                return version, date


def parse_derpy_date(document):
    body = document.get("body")["content"]
    for i in range(len(body) - 1, -1, -1): # Traverse backwards
        el = body[i]
        for element in el["paragraph"]["elements"]:
            content = element["textRun"]["content"]
            expression = " ?(?P<Date>\d+\/\d+\/\d+) V?(?P<Version>\d+)"
            match = re.match(expression, content)
            #result = re.search(r'(\d+/\d+/\d+)', content)
            if match is not None:
                date = match.group("Date")
                version = match.group("Version")
                date = datetime.datetime.strptime(date,"%d/%m/%Y")
                return version, date.strftime("%d/%m/%Y")


def parse_epip_version(changelog_url):
    grab = requests.get(changelog_url)
    soup = BeautifulSoup(grab.text, 'lxml')
    string = soup.find_all("h2")[0].text
    expression = 'v?(?P<Version>\d+) ?- ?(?P<Date>\d+\/\d+\/\d+)'
    match = re.match(expression, string)
    version_string = match.group("Version")
    date_string = match.group("Date")
    date = datetime.datetime.strptime(date_string,"%d/%m/%y")

    return version_string, date.strftime("%d/%m/%Y")


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
    derpy_version, derpy_date = parse_derpy_date(derpy_document)
    print(f"Derpy latest:{derpy_version, derpy_date}")

    ee_document = get_document(EE_DOCUMENT_ID)
    ee_version, ee_date = parse_ee_date(ee_document)
    print(f"EE latest:{ee_version, ee_date}")

    epip_version, epip_date = parse_epip_version(EPIP_CHANGELOG_URL)
    print(f"Epip latest: {epip_version, epip_date}")

    version_dict = {"Mods":{"EpipEncounters":{}, "Derpy":{}, "EpicEncounters":{}}}
    version_dict["Mods"]["EpipEncounters"]["Version"] = epip_version
    version_dict["Mods"]["EpipEncounters"]["Date"] = epip_date
    version_dict["Mods"]["Derpy"]["Version"] = derpy_version
    version_dict["Mods"]["Derpy"]["Date"] = derpy_date
    version_dict["Mods"]["EpicEncounters"]["Version"] = ee_version
    version_dict["Mods"]["EpicEncounters"]["Date"] = ee_date

    json_object = json.dumps(version_dict, indent=4)

    # Writing to sample.json
    with open("versions.json", "w") as outfile:
        outfile.write(json_object)


if __name__ == '__main__':
    main()
