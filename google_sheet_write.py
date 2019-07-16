from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    import arcaea_parser_friend_ver as arc_parse
    
    song_rlt_list = []
    song_rlt_list.append(arc_parse.fieldnames)
    for song in arc_parse.song_rlt:
        song_rlt_list.append(list(song.values()))

    sheet_append_body = {
        "values" : song_rlt_list
    }

    if os.path.exists("./"+arc_parse.user_name+'/sheet_create_rlt.json'):
        with open("./"+arc_parse.user_name+"/sheet_create_rlt.json", 'r') as f:
            response = json.load(f)
            spread_id = response['spreadsheetId']
            spread_url = response['spreadsheetUrl']
        request = service.spreadsheets().values().clear(spreadsheetId=spread_id, range='Arcaea Score')
        response = request.execute()
    else:
        sheet_create_body = {
            "properties" : {
                "title" : "arcaea_result_" + arc_parse.user_name,
                "autoRecalc" : "ON_CHANGE",
                "timeZone" : "GMT+09:00"
            },
            "sheets" : [
                {
                    "properties" : {
                        "sheetId" : 0,
                        "title" : "Arcaea Score"
                    }
                }
            ]
        }

        request = service.spreadsheets().create(body=sheet_create_body)
        response = request.execute()
        spread_id = response['spreadsheetId']
        spread_url = response['spreadsheetUrl']

        with open("./"+arc_parse.user_name+"/sheet_create_rlt.json", 'w') as f:
            json.dump(response, f)
        
    request = service.spreadsheets().values().append(spreadsheetId=spread_id, range='Arcaea Score!A1',
        includeValuesInResponse=False, valueInputOption="USER_ENTERED", insertDataOption="OVERWRITE",
        body=sheet_append_body
    )
    response = request.execute()
    print(response)

    print(spread_url)


if __name__ == '__main__':
    main()
