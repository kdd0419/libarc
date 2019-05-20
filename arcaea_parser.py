import json
import csv
import libarc as arc
from getpass import getpass

user_name = input('input username > ')
user_pw = getpass('input PW > ')

arc.user_login(user_name, user_pw, change_device_id=True)

with open('songlist.json', 'r', encoding="utf-8") as songlist_f:
    songlist = json.loads(songlist_f.read())

songlist = songlist['songs']

song_info = []
for song in songlist:
    song_info.append({
        'id': song['id'], 'name': song['title_localized']['en'],
        'level': [diff['rating'] for diff in song['difficulties']]})

song_rlt = []
diff = ['PAST', 'PRESENT', 'FUTURE']
clear_mode = [
    'Track Lost', 'Track Complete (Normal Gauge)',
    'Full Recall', 'Pure Memory',
    'Track Complete (Easy Gauge)', 'Track Complete (Hard Gauge)']
for i in range(len(song_info)*3):
    score = arc.rank_me(song_info[i // 3]['id'], i % 3, 0, 0)['value']
    tmp_dic = {
        "song_name": song_info[i // 3]['name'], "difficulty": diff[i % 3],
        "level": song_info[i // 3]['level'][i % 3]}
    if len(score) <= 0:
        song_rlt.append(tmp_dic)
    else:
        tmp_dic['best_clear_type'] = clear_mode[score[0]['best_clear_type']]
        row = [
            'score', 'shiny_perfect_count', 'perfect_count',
            'near_count', 'miss_count', 'rank']
        for r in row:
            tmp_dic[r] = score[0][r]
        song_rlt.append(tmp_dic)

with open('arcaea result.csv', 'w', newline="\n", encoding='utf-8') as csv_f:
    fieldnames = [
        'song_name', 'difficulty', 'level', 'score',
        'shiny_perfect_count', 'perfect_count', 'near_count',
        'miss_count', 'best_clear_type', 'rank']
    writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
    writer.writeheader()
    for song in song_rlt:
        writer.writerow(song)
