import json
import csv
import libarc as arc
from getpass import getpass
import os

user_name = input('input username > ')
user_pw = getpass('input PW > ')

# with open('static_uuid.txt', 'w') as fw:
#     # import uuid
#     # arc.headers['DeviceId'] = str(uuid.uuid4()).upper()
#     # arc.static_uuid = arc.headers['DeviceId']
#     fw.write(arc.static_uuid)

with open('static_uuid.txt', 'r') as fr:
    arc.headers['DeviceId'] = fr.readline().strip()
    arc.static_uuid = arc.headers['DeviceId']

arc.user_login(user_name, user_pw, change_device_id=False)

with open('./ArcSonglist.json', 'r', encoding="utf-8") as songlist_f:
    songlist = json.loads(songlist_f.read())

songlist = songlist['songs']

song_info = []
for song in songlist:
    song_info.append({
        'id': song['id'], 'name': song['title_localized']['en'],
        'level': [
                [diff['rating'], diff['fixedValue']]
                for diff in song['difficulties']
            ]
        })


def pttCalc(score, fixedValue):
    if score <= 9800000:
        bouns = (score - 9500000) / 300000
    elif score > 9800000 and score < 9950000:
        bouns = (score - 9800000) / 400000 + 1
    elif score >= 9950000 and score < 10000000:
        bouns = (score - 9950000) / 100000 + 1.5
    elif score >= 10000000:
        bouns = 2

    ptt = bouns + fixedValue
    if ptt < 0:
        ptt = 0
    return ptt


song_rlt = []
diff = ['PAST', 'PRESENT', 'FUTURE']
clear_mode = [
    'Track Lost', 'Track Complete (Normal Gauge)',
    'Full Recall', 'Pure Memory',
    'Track Complete (Easy Gauge)', 'Track Complete (Hard Gauge)']
for i in range(len(song_info)*3):
    score_json = arc.rank_me(song_info[i // 3]['id'], i % 3, 0, 0)
    if score_json['success'] == False:
        print(song_info[i // 3]['name'], diff[i % 3], ": failed")
        continue
    score = score_json['value']
    tmp_dic = {
        "song_name": song_info[i // 3]['name'], "difficulty": diff[i % 3],
        "level": song_info[i // 3]['level'][i % 3][0],
        "detail level": song_info[i // 3]['level'][i % 3][1]}
    if len(score) <= 0:
        song_rlt.append(tmp_dic)
    else:
        tmp_dic['best_clear_type'] = clear_mode[score[0]['best_clear_type']]
        row = [
            'score', 'shiny_perfect_count', 'perfect_count',
            'near_count', 'miss_count', 'rank']
        for r in row:
            tmp_dic[r] = score[0][r]
        tmp_dic['potential'] = pttCalc(
            score[0]['score'], song_info[i // 3]['level'][i % 3][1])
        song_rlt.append(tmp_dic)

if not os.path.isdir("./"+user_name):
    os.mkdir("./"+user_name)
with open("./"+user_name+'/arcaea result.csv', 'w', newline="\n", encoding='utf-8') as csv_f:
    fieldnames = [
        'song_name', 'difficulty', 'level', 'detail level', 'score',
        'shiny_perfect_count', 'perfect_count', 'near_count',
        'miss_count', 'best_clear_type', 'rank', 'potential']
    writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
    writer.writeheader()
    for song in song_rlt:
        writer.writerow(song)


def character_file_write():
    if not os.path.isdir("./"+user_name):
        os.mkdir("./"+user_name)
    with open('./'+user_name+'/character.json','w' ) as chara_fw:
        json.dump(arc.get_character_info(), chara_fw)

def user_info_file_write():
    if not os.path.isdir("./"+user_name):
        os.mkdir("./"+user_name)
    with open('./k3id/user.json','w' ) as user_fw:
        json.dump(arc.user_info(), user_fw)

def map_file_write():
    if not os.path.isdir("./"+user_name):
        os.mkdir("./"+user_name)
    with open('./k3id/map.json','w' ) as map_fw:
        json.dump(arc.get_world_map(), map_fw)