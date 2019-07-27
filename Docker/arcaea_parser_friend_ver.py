import json
import libarc as arc
import os
import asyncio


def admin_login():
    import pickle
    with open('login_info.pickle', 'rb') as pkf:
        admin = pickle.load(pkf)
    arc.user_login(admin['id'], admin['pw'], change_device_id=False)
    return admin


def set_uuid_into_file():
    with open('static_uuid.txt', 'w') as fw:
        import uuid
        arc.headers['DeviceId'] = str(uuid.uuid4()).upper()
        arc.static_uuid = arc.headers['DeviceId']
        fw.write(arc.static_uuid)


def get_uuid_from_file():
    with open('static_uuid.txt', 'r') as fr:
        arc.headers['DeviceId'] = fr.readline().strip()
        arc.static_uuid = arc.headers['DeviceId']


def admin_del_all_friends(admin):
    user_info_json = arc.user_info()
    if user_info_json['value'][0]['value']['name'] != admin['id']:
        return
    friends = user_info_json['value'][0]['value']['friends']
    for friend in friends:
        arc.friend_del(friend['user_id'])


def get_user_name(friend_code):  # include admin add friend
    add_rlt = arc.friend_add(friend_code)
    user_name = add_rlt['value']['friends'][0]['name']
    return user_name


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

async def get_score(song_info, diff_i):
    score_dic = {
        "song_name": song_info['name'],
        "difficulty": diff[diff_i],
        "level": song_info['level'][diff_i][0],
        "detail level": song_info['level'][diff_i][1]}
    score_json = arc.rank_friend(song_info['id'], diff_i, 0, 1)
    if not score_json['success']:
        print(song_info['name'], diff[diff_i], ": failed")
        score_dic['best_clear_type'] = 'Load Failed'
        return score_dic
    else:
        print(song_info['name'], diff[diff_i], ": success")
    score = score_json['value']
    if len(score) > 0:
        score_dic['best_clear_type'] = clear_mode[score[0]['best_clear_type']]
        row = ['score', 'shiny_perfect_count', 'perfect_count', 'near_count', 'miss_count']
        for r in row:
            score_dic[r] = score[0][r]
        score_dic['potential'] = pttCalc(score[0]['score'], song_info['level'][diff_i][1])
    return score_dic


async def get_future_scores(song_info):
    tasks = [
        asyncio.create_task(get_score(song, 2)) for song in song_info]
    future_scores = await asyncio.gather(*tasks)
    return future_scores


async def get_all_score(song_info):
    tasks = [
        asyncio.create_task(get_score(song, i)) for song in song_info for i in range(3)    
    ]
    all_score = await asyncio.gather(*tasks)
    return all_score

fieldnames = [
    'song_name', 'difficulty', 'level', 'detail level', 'score',
    'shiny_perfect_count', 'perfect_count', 'near_count',
    'miss_count', 'best_clear_type', 'potential']


def score_file_write(score, user_name):
    import csv
    if not os.path.isdir("./"+user_name):
        os.mkdir("./"+user_name)

    with open(
        "./"+user_name+'/arcaea result.csv', 'w',
        newline="\n", encoding='utf-8'
            ) as csv_f:

        writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
        writer.writeheader()
        for song in score:
            writer.writerow(song)


def main():
    if os.path.exists('./static_uuid.txt'):
        get_uuid_from_file()
    else:
        set_uuid_into_file()

    admin = admin_login()
    admin_del_all_friends(admin=admin)

    user_name = get_user_name(
        friend_code=input('input your friend-add code > '))

    all_score = asyncio.run(get_all_score(song_info=get_songinfo()))

    score_file_write(score=all_score, user_name=user_name)

    admin_del_all_friends(admin=admin)

if __name__ == "__main__":
    main()

