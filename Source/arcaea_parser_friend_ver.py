import json
import arcaeaAsyncAPI as arc
import os
import asyncio


async def admin_login():
    import pickle
    with open('login_info.pickle', 'rb') as pkf:
        admin = pickle.load(pkf)
    await arc.user_login(admin['id'], admin['pw'], change_device_id=False)
    return admin


def set_uuid_into_file():
    with open('static_uuid.txt', 'w') as fw:
        import uuid
        arc.static_uuid = arc.headers['DeviceId'] = str(uuid.uuid4()).upper()
        fw.write(arc.static_uuid)


def get_uuid_from_file():
    with open('static_uuid.txt', 'r') as fr:
        arc.static_uuid = arc.headers['DeviceId'] = fr.readline().strip()


async def admin_del_all_friends(admin):
    user_info_json = await arc.user_info()
    if user_info_json['value'][0]['value']['name'] != admin['id']:
        return
    friends = user_info_json['value'][0]['value']['friends']
    for friend in friends:
        await arc.friend_del(friend['user_id'])


async def admin_setting():
    if os.path.exists('./static_uuid.txt'):
        get_uuid_from_file()
    else:
        set_uuid_into_file()

    admin = await admin_login()
    await admin_del_all_friends(admin=admin)
    return admin


async def get_user_name(friend_code):  # include admin add friend
    add_rlt = await arc.friend_add(friend_code)
    user_name = add_rlt['value']['friends'][0]['name']
    return user_name


def get_songinfo():
    with open('./ArcSonglist.json', 'r', encoding="utf-8") as songlist_f:
        songlist = json.loads(songlist_f.read())

    songlist = songlist['songs']

    song_info = []
    for song in songlist:
        for diff in song['difficulties']:
            song_info.append({
                'id': song['id'], 'name': song['title_localized']['en'],
                'rating class': diff['ratingClass'],
                'level': diff['rating'],
                'base potential': diff['fixedValue']
            })

    return song_info


def pttCalc(score, fixedValue):
    # if score <= 9800000:
    #     bouns = (score - 9500000) / 300000
    # elif score > 9800000 and score < 9950000:
    #     bouns = (score - 9800000) / 400000 + 1
    # elif score >= 9950000 and score < 10000000:
    #     bouns = (score - 9950000) / 100000 + 1.5
    # elif score >= 10000000:
    #     bouns = 2
    if score <= 9800000:
        bonus = (score - 9500000) / 300000
    elif score < 10000000:
        bonus = (score - 9800000) / 200000 + 1
    elif score >= 10000000:
        bonus = 2
    return bonus + fixedValue if bonus + fixedValue > 0 else 0


diff = ['PAST', 'PRESENT', 'FUTURE']
clear_mode = [
    'Track Lost', 'Track Complete (Normal Gauge)',
    'Full Recall', 'Pure Memory',
    'Track Complete (Easy Gauge)', 'Track Complete (Hard Gauge)']


async def get_score(song_info, score_queue):
    score_dic = {
        "song_name": song_info['name'],
        "difficulty": diff[song_info['rating class']],
        "level": song_info['level'],
        "detail level": song_info['base potential']}
    score_json = await arc.rank_friend(
        song_info['id'], song_info['rating class'], 0, 1)
    if not score_json['success']:
        print(song_info['name'], diff[song_info['rating class']], ": failed")
        score_dic['best_clear_type'] = 'Load Failed'
        await score_queue.put(score_dic)
    else:
        print(song_info['name'], diff[song_info['rating class']], ": success")
    score = score_json['value']
    if len(score) > 0:
        score_dic['best_clear_type'] = clear_mode[score[0]['best_clear_type']]
        row = [
            'score', 'shiny_perfect_count', 'perfect_count',
            'near_count', 'miss_count']
        for r in row:
            score_dic[r] = score[0][r]
        score_dic['potential'] = pttCalc(
            score[0]['score'], song_info['base potential'])
    await score_queue.put(score_dic)


async def get_limit_scores(song_info, limit):
    if len(limit['mode']) > 0:
        song_info = [
            song for song in song_info if song['rating class'] in limit['mode']]
    if len(limit['level']) == 1:
        song_info = [song for song in song_info if song['level'] >= limit['level'][0]]
    if len(limit['level']) == 2:
        song_info = [
            song for song in song_info
            if limit['level'][0] <= song['level'] <= limit['level'][1]]
    if len(limit['base potential']) == 1:
        song_info = [
            song for song in song_info
            if song['base potential'] >= limit['base potential'][0]]
    if len(limit['base potential']) == 2:
        song_info = [
            song for song in song_info
            if limit['base potential'][0] <= song['base potential'] and
            song['base potential'] <= limit['base potential'][1]]
    score_queue = asyncio.Queue()
    for song in song_info:
        asyncio.create_task(get_score(song, score_queue))
        await asyncio.sleep(0.01)
    await score_queue.join()
    all_score = []
    while len(all_score) < len(song_info):
        score = await score_queue.get()
        all_score.append(score)
        score_queue.task_done()
    return all_score


async def get_all_score(song_info):
    score_queue = asyncio.Queue()
    for song in song_info:
        asyncio.create_task(get_score(song, score_queue))
        await asyncio.sleep(0.01)
    await score_queue.join()
    all_score = []
    while len(all_score) < len(song_info):
        score = await score_queue.get()
        all_score.append(score)
        score_queue.task_done()
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


async def main():
    admin = await admin_setting()

    user_name = await get_user_name(
        friend_code=input('input your friend-add code > '))

    all_score = await get_all_score(song_info=get_songinfo())

    score_file_write(score=all_score, user_name=user_name)

    await admin_del_all_friends(admin=admin)

if __name__ == "__main__":
    asyncio.run(main())
