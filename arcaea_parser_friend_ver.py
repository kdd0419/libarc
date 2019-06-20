import json
import csv
import libarc as arc
import os



friend_code = input('input your friend-add code > ')

with open('admin/login_info.json', 'r') as admin_f:
    admin = json.loads(admin_f.read())



with open('static_uuid.txt', 'r') as fr:
    arc.headers['DeviceId'] = fr.readline().strip()
    arc.static_uuid = arc.headers['DeviceId']    

arc.user_login(admin['id'], admin['pw'], change_device_id=False)


def admin_del_all_friends():
    user_info_json = arc.user_info()
    if user_info_json['value'][0]['value']['name'] != admin['id']:
        return
    friends = user_info_json['value'][0]['value']['friends']
    for friend in friends:
        arc.friend_del(friend['user_id'])

admin_del_all_friends()

add_rlt = arc.friend_add(friend_code)
user_name=add_rlt['value']['friends'][0]['name']

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
    score_json = arc.rank_friend(song_info[i // 3]['id'], i % 3, 0, 1)

    if not score_json['success']:
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
            'near_count', 'miss_count']

        for r in row:
            tmp_dic[r] = score[0][r]

        tmp_dic['potential'] = pttCalc(
            score[0]['score'], song_info[i // 3]['level'][i % 3][1])

        song_rlt.append(tmp_dic)

if not os.path.isdir("./"+user_name):
    os.mkdir("./"+user_name)

with open(
    "./"+user_name+'/arcaea result.csv', 'w', newline="\n", encoding='utf-8'
        ) as csv_f:

    fieldnames = [
        'song_name', 'difficulty', 'level', 'detail level', 'score',
        'shiny_perfect_count', 'perfect_count', 'near_count',
        'miss_count', 'best_clear_type', 'potential']
    writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
    writer.writeheader()
    for song in song_rlt:
        writer.writerow(song)