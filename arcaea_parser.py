import json
import libarc as arc
import os


def set_uuid():
    with open('static_uuid.txt', 'w') as fw:
        import uuid
        arc.headers['DeviceId'] = str(uuid.uuid4()).upper()
        arc.static_uuid = arc.headers['DeviceId']
        fw.write(arc.static_uuid)


def get_uuid():
    with open('static_uuid.txt', 'r') as fr:
        arc.headers['DeviceId'] = fr.readline().strip()
        arc.static_uuid = arc.headers['DeviceId']


def get_songinfo():
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

    return song_info


def login():
    from getpass import getpass
    login.user_name = input('input username > ')
    login.user_pw = getpass('input PW > ')
    arc.user_login(
        login.user_name, login.user_pw, change_device_id=False)


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


diff = ['PAST', 'PRESENT', 'FUTURE']
clear_mode = [
    'Track Lost', 'Track Complete (Normal Gauge)',
    'Full Recall', 'Pure Memory',
    'Track Complete (Easy Gauge)', 'Track Complete (Hard Gauge)']


def get_all_score(song_info):
    rlt = []
    for i in range(len(song_info)*3):
        score_json = arc.rank_me(song_info[i // 3]['id'], i % 3, 0, 0)

        if not score_json['success']:
            print(song_info[i // 3]['name'], diff[i % 3], ": failed")
            continue
        else:
            print(song_info[i // 3]['name'], diff[i % 3], ": success")

        score = score_json['value']

        tmp_dic = {
            "song_name": song_info[i // 3]['name'], "difficulty": diff[i % 3],
            "level": song_info[i // 3]['level'][i % 3][0],
            "detail level": song_info[i // 3]['level'][i % 3][1]}

        if len(score) <= 0:
            rlt.append(tmp_dic)

        else:
            tmp_dic['best_clear_type'] = clear_mode[
                score[0]['best_clear_type']]

            row = [
                'score', 'shiny_perfect_count', 'perfect_count',
                'near_count', 'miss_count', 'rank']

            for r in row:
                tmp_dic[r] = score[0][r]

            tmp_dic['potential'] = pttCalc(
                score[0]['score'], song_info[i // 3]['level'][i % 3][1])

            rlt.append(tmp_dic)
    return rlt


def score_file_write(score, user_name):
    import csv
    if not os.path.isdir("./"+user_name):
        os.mkdir("./"+user_name)

    with open(
        "./"+user_name+'/arcaea result.csv', 'w',
        newline="\n", encoding='utf-8'
            ) as csv_f:

        fieldnames = [
            'song_name', 'difficulty', 'level', 'detail level', 'score',
            'shiny_perfect_count', 'perfect_count', 'near_count',
            'miss_count', 'best_clear_type', 'rank', 'potential']
        writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
        writer.writeheader()
        for song in score:
            writer.writerow(song)


def character_file_write(user_name):
    if not os.path.isdir("./"+user_name):
        os.mkdir("./"+user_name)
    with open('./'+user_name+'/character.json', 'w') as chara_fw:
        json.dump(arc.get_character_info(), chara_fw)


def user_info_file_write(user_name):
    if not os.path.isdir("./"+user_name):
        os.mkdir("./"+user_name)
    with open('./'+user_name+'/user.json', 'w') as user_fw:
        json.dump(arc.user_info(), user_fw)


def map_file_write(user_name):
    if not os.path.isdir("./"+user_name):
        os.mkdir("./"+user_name)
    with open('./'+user_name+'/map.json', 'w') as map_fw:
        json.dump(arc.get_world_map(), map_fw)


def main():
    if os.path.exists('./static_uuid.txt'):
        get_uuid()
    else:
        set_uuid()

    login()

    all_score = get_all_score(song_info=get_songinfo())

    score_file_write(score=all_score, user_name=login.user_name)

if __name__ == "__main__":
    main()
