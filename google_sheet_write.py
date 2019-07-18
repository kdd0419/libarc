import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
import arcaea_parser_friend_ver as arc_parse

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def credential():
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
    return creds


def getArcScore():
    all_score = arc_parse.get_all_score(
        song_info=arc_parse.get_songinfo())
    for song in range(len(all_score)):
        all_score[song] = list(all_score[song].values())
    all_score.insert(0, arc_parse.fieldnames)
    return all_score


def create_sheet(sheet_service, user_name):
    sheet_create_body = {
        "properties": {
            "title": "arcaea_result_" + user_name,
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
    return request.execute()


def set_share_sheet(drive_service, spread_id):
    drive_service.permissions().create(
        fileId=spread_id,
        body={'type': 'anyone', 'role': 'writer'}
    ).execute()


def update_sheet(sheet_service, spread_id, length):
    update_body = {
        "requests": [
            {
                "addBanding": {
                    "bandedRange": {
                        "bandedRangeId": 1,
                        "range": {
                            "sheetId": 0,
                            "startRowIndex": 0,
                            "endRowIndex": length,
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
                            "endRowIndex": length,
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


def clear_sheet(sheet_service, spread_id):
    sheet_service.spreadsheets().batchUpdate(
        spreadsheetId=spread_id,
        body={"requests": [{"deleteBanding": {"bandedRangeId": 1}}]}
    ).execute()

    sheet_service.spreadsheets().values().clear(
        spreadsheetId=spread_id, range='Arcaea Score'
    ).execute()


def write_sheet(sheet_service, spread_id, all_score):
    sheet_service.spreadsheets().values().append(
        spreadsheetId=spread_id, range='Arcaea Score!A1',
        includeValuesInResponse=False, valueInputOption="USER_ENTERED",
        insertDataOption="OVERWRITE", body={"values": all_score}
    ).execute()


def set_sheet_info_file(response, user_name):
    if not os.path.isdir("./spread_sheet"):
        os.mkdir("./spread_sheet")
    with open("./spread_sheet/"+user_name+"_sheet_create_rlt.json", 'w') as f:
        json.dump(response, f)


def get_sheet_info_file(user_name):
    with open("./spread_sheet/"+user_name+"_sheet_create_rlt.json", 'r') as f:
        return json.load(f)


def main():
    creds = credential()

    sheet_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    if os.path.exists('./static_uuid.txt'):
        arc_parse.get_uuid_from_file()
    else:
        arc_parse.set_uuid_into_file()

    admin = arc_parse.admin_login()
    arc_parse.admin_del_all_friends(admin)
    user_name = arc_parse.get_user_name(
        friend_code=input('input your friend-add code > '))
    all_score = getArcScore()
    arc_parse.admin_del_all_friends(admin)

    if os.path.exists("./spread_sheet/"+user_name+'_sheet_create_rlt.json'):
        response = get_sheet_info_file(user_name)
        spread_id = response['spreadsheetId']
        spread_url = response['spreadsheetUrl']

        clear_sheet(sheet_service, spread_id)
    else:
        response = create_sheet(sheet_service, user_name)
        spread_id = response['spreadsheetId']
        spread_url = response['spreadsheetUrl']
        set_sheet_info_file(response, user_name)

        set_share_sheet(drive_service, spread_id)

    write_sheet(sheet_service, spread_id, all_score)
    update_sheet(sheet_service, spread_id, len(all_score))
    print(spread_url)


if __name__ == '__main__':
    main()
