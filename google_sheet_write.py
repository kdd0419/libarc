import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


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

    sheet_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    import arcaea_parser_friend_ver as arc_parse

    if os.path.exists("./"+arc_parse.user_name+'/sheet_create_rlt.json'):
        with open("./"+arc_parse.user_name+"/sheet_create_rlt.json", 'r') as f:
            response = json.load(f)
            spread_id = response['spreadsheetId']
            spread_url = response['spreadsheetUrl']

        sheet_service.spreadsheets().batchUpdate(
            spreadsheetId=spread_id,
            body={"requests": [{"deleteBanding": {"bandedRangeId": 1}}]}
        ).execute()

        sheet_service.spreadsheets().values().clear(
            spreadsheetId=spread_id, range='Arcaea Score'
        ).execute()
    else:
        sheet_create_body = {
            "properties": {
                "title": "arcaea_result_" + arc_parse.user_name,
                "autoRecalc": "ON_CHANGE",
                "timeZone": "GMT+09:00"
            },
            "sheets": [{
                "properties": {
                    "sheetId": 0,
                    "title": "Arcaea Score"
                }
            }]
        }
        request = sheet_service.spreadsheets().create(body=sheet_create_body)
        response = request.execute()
        spread_id = response['spreadsheetId']
        spread_url = response['spreadsheetUrl']

        drive_service.permissions().create(
            fileId=spread_id,
            body={'type': 'anyone', 'role': 'writer'}
        ).execute()

        with open("./"+arc_parse.user_name+"/sheet_create_rlt.json", 'w') as f:
            json.dump(response, f)

    song_rlt_list = []
    song_rlt_list.append(arc_parse.fieldnames)
    for song in arc_parse.song_rlt:
        song_rlt_list.append(list(song.values()))

    sheet_service.spreadsheets().values().append(
        spreadsheetId=spread_id, range='Arcaea Score!A1',
        includeValuesInResponse=False, valueInputOption="USER_ENTERED",
        insertDataOption="OVERWRITE", body={"values": song_rlt_list}
    ).execute()

    update_body = {
        "requests": [
            {
                "addBanding": {
                    "bandedRange": {
                        "bandedRangeId": 1,
                        "range": {
                            "sheetId": 0,
                            "startRowIndex": 0,
                            "endRowIndex": len(arc_parse.song_rlt) + 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(arc_parse.fieldnames)
                        },
                        "rowProperties": {
                            "headerColor": {
                                "red": 150/255,
                                "green": 255/255,
                                "blue": 150/255
                            },
                            "firstBandColor": {
                                "red": 255/255,
                                "green": 255/255,
                                "blue": 255/255
                            },
                            "secondBandColor": {
                                "red": 220/255,
                                "green": 255/255,
                                "blue": 220/255
                            }
                        }
                    }
                }
            },
            {
                "setBasicFilter": {
                    "filter": {
                        "range": {
                            "sheetId": 0,
                            "startRowIndex": 0,
                            "endRowIndex": len(arc_parse.song_rlt) + 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(arc_parse.fieldnames)
                        }
                    }
                }
            }
        ]
    }
    sheet_service.spreadsheets().batchUpdate(
        spreadsheetId=spread_id, body=update_body
    ).execute()

    print(spread_url)


if __name__ == '__main__':
    main()
