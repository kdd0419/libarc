import asyncio
import aiohttp
import uuid
import base64
import json

ARCAEA_API_VERSION = '10'
MAIN_ADDRESS = 'https://arcapi.lowiro.com/' + ARCAEA_API_VERSION

static_uuid = ''
auth_str = ''

headers = {
    'Accept-Language': 'ko-KR',
    'Accept': '*/*',
    'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    'Accept-Encoding': 'br, gzip, deflate',
    'AppVersion': '2.6.0',
    'User-Agent': 'CFNetwork/976 Darwin/18.2.0',
    'Authorization': auth_str
}


def calc_score(
        shiny_perfect_count: int, perfect_count: int, near_count: int, miss_count: int):
    return shiny_perfect_count + int(
        10**7 / (perfect_count + near_count + miss_count) * (perfect_count + 0.5 * near_count))


async def user_register(
        name: str, password: str, email: str, *,
        add_auth: bool=True, platform: str='ios', change_device_id: bool=False):
    '''
    usage:
        name: username (maximum length: 15)
        password: password
        email: email address
        add_auth:
            whether to use the (new) authorization code
            for following functions
        platform: 'ios' or 'android' (or 'web'?)
        change_device_id:
            whether to change (and use) a new device id
            instead of using default device id
    example:
        user_register('holy616', '616isgod', 'love616forever@gmail.com')
    '''

    register_data = {
        'name': name,
        'password': password,
        'email': email,
        'device_id': static_uuid,
        'platform': platform
    }

    if change_device_id:
        register_data['device_id'] = static_uuid = str(uuid.uuid4()).upper()
        print('new_uuid: ' + static_uuid)

    if 'Authorization' in headers:
        headers.pop('Authorization')

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(MAIN_ADDRESS+'/user', params=register_data) as res:
            register_json = await res.json()

            if register_json['success'] and add_auth:
                auth_str = 'Bearer ' + register_json['value']['access_token']
            headers['Authorization'] = auth_str

    return register_json


async def user_login(
        name: str, password: str, *,
        add_auth: bool=True, change_device_id: bool=False):
    '''
    attention:
        your account will be banned for a while
        if it is logged into more than 2 devices of different uuid
    usage:
        name: username
        password: password
        add_auth:
            whether to use the (new) authorization code for following functions
        change_device_id:
            whether to change (and use) a new device id
            instead of using default device id
    example:
        user_login('tester2234', 'tester223344')
    '''
    if change_device_id:
        headers['device_id'] = static_uuid = str(uuid.uuid4()).upper()
        print('new_uuid: ' + static_uuid)

    headers['Authorization'] = 'Basic ' + str(
        base64.b64encode(f'{name}:{password}'.encode('utf-8')), 'utf-8')

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(MAIN_ADDRESS+'/auth/login', data={'grant_type': 'client_credentials'}) as res:
            login_json = await res.json()

            if login_json['success'] and add_auth:
                auth_str = f"{login_json['token_type']} {login_json['access_token']}"
            headers['Authorization'] = auth_str
            headers.pop('DeviceId')
    return login_json


async def user_info():
    '''
    usage:
        run directly to get your user info
    '''

    user_info_params = {
        'calls': json.dumps(
            [
                {"id": 0, "endpoint": "user/me"},
                {"id": 1, "endpoint": "purchase/bundle/pack"},
                {"id": 2, "endpoint": "serve/download/me/song?url=false"}
            ]
        )
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(MAIN_ADDRESS+'/compose/aggregate', params=user_info_params) as res:
            user_info_json = await res.json()

    return user_info_json


async def rank_friend(
        song_id: str, difficulty: int, start: int, limit: int):
    '''
    usage:
        song_id: please check song_id.json
        dificcuty: 0=pst, 1=prs, 2=ftr
        start: larger start, higher rank (start from you: start=0)
        limit: returns at most 21 records due to the number limit of friends
    example:
        rank_friend('themessage', 2, 0, 10)
    '''

    rank_friend_params = {
        'song_id': song_id,
        'difficulty': difficulty,
        'start': start,
        'limit': limit
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(MAIN_ADDRESS+'/score/song/friend', params=rank_friend_params) as res:
            rank_friend_json = await res.json()

    return rank_friend_json


async def rank_world(
        song_id: str, difficulty: int, start: int, limit: int):
    '''
    usage:
        song_id: please check song_id.json
        dificcuty: 0=pst, 1=prs, 2=ftr
        start: must be 0
        limit: returns at most 100 records when limit>=100
    example:
        rank_world('themessage', 2, 0, 10)
    '''

    rank_friend_params = {
        'song_id': song_id,
        'difficulty': difficulty,
        'start': start,
        'limit': limit
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(MAIN_ADDRESS+'/score/song', params=rank_friend_params) as res:
            rank_world_json = await res.json()

    return rank_world_json


async def rank_me(
        song_id: str, difficulty: int, start: int, limit: int):
    '''
    usage:
        song_id: please check song_id.json
        dificcuty: 0=pst, 1=prs, 2=ftr
        start: larger start, higher rank (start from you: start=0)
        limit: returns at most 101 records when limit>=100
        in theory, you can get the whole rank list via rank_me
    example:
        rank_me('themessage', 2, 0, 10)
    '''

    rank_friend_params = {
        'song_id': song_id,
        'difficulty': difficulty,
        'start': start,
        'limit': limit
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(MAIN_ADDRESS+'/score/song/me', params=rank_friend_params) as res:
            rank_me_json = await res.json()

    return rank_me_json


async def friend_del(friend_id: int):
    '''
    usage:
        friend_id: the (private) id of the user that you want to delete
    example:
        friend_del(1919810)
    '''

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(MAIN_ADDRESS+'/friend/me/delete', data={'friend_id': friend_id}) as res:
            friend_del_json = await res.json()
    return friend_del_json


async def friend_add(friend_code):
    '''
    usage:
        friend_code:
            the 9-digit code of the user that you want to add as a friend
        by adding a friend you may check his/her best30 data via rank_friend
    example:
        friend_add(114514810)
    '''
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(MAIN_ADDRESS+'/friend/me/add', data={'friend_code': friend_code}) as res:
            friend_add_json = await res.json()
    return friend_add_json
