import discord
from discord.ext import commands
import pickle
import os
import google_sheet_write as xlsx_w

bot = commands.Bot(
    command_prefix='#',
    help_command=commands.DefaultHelpCommand()
)

with open('bot_token.pickle', 'rb') as token_f:
    TOKEN = pickle.load(token_f)


def decode_limit(limit):
    decode_limit.error = 'Wrong input' 
    diff_mode = {
        'PAST': 0, 'PRESENT': 1, 'FUTURE': 2,
        'PST': 0, 'PRS': 1, 'FTR': 2
    }
    rlt = {'mode': [], 'level': [], 'base potential': []}
    for i in limit:
        if i.upper() in diff_mode.keys():
            rlt['mode'].append(diff_mode[i.upper()])
        else:
            try:
                if float(i) < 1 or float(i) >= 12:
                    return decode_limit.error
                if '.' not in i:
                    rlt['level'].append(int(i))
                    if len(rlt['level']) > 2:
                        return decode_limit.error
                else:
                    rlt['base potential'].append(float(i))
                    if len(rlt['base potential']) > 2:
                        return decode_limit.error
            except ValueError:
                return decode_limit.error
    for k in rlt.keys():
        rlt[k].sort()
    return rlt


@bot.event
async def on_ready():
    print("Logged in as")
    print(bot.user.name)
    print("=============")

    await bot.change_presence(
        activity=discord.Activity(
            name="Command : '#help'",
            type=discord.ActivityType.watching),
        status=discord.Status.online
    )


@bot.command()
async def sheet(ctx, friend_code, *limit):
    '''
    friend_code : input your friend add code (9-digit)
    limit : (optional) if is not inputted,
            it is going to write all score.
            you can input the following three kinds.
            difficulty mode - PAST, PRESENT, FUTURE (PST, PRS, FTR)
            level - 1~9, 10(9+), 11(10) (integer)
            base potential - 1.0 ~ 11.2 (decimal)
            if you input two or three kinds,
            it must be 'and' not 'or'.
    ex) #sheet XXXXXXXXX => write all score
        #sheet XXXXXXXXX PRESENT => write PRESENT score
        #sheet XXXXXXXXX PAST FUTURE
        => write PAST and FUTURE score (exclude PRESENT)
        #sheet XXXXXXXXX 7
        => write score whose level is higher than 7
        #sheet XXXXXXXXX 5 9
        => write score whose level is between 5 and 9
        #sheet XXXXXXXXX 9.0
        => write score whose base potential is higher than 9.0
           (including dropdead FTR)
        #sheet XXXXXXXXX 8.7 9.2
        => write score whose base potential is between 8.7 and 9.2
    '''
    await ctx.send('writing spreadsheet...')

    creds = xlsx_w.credential()

    sheet_service = xlsx_w.build('sheets', 'v4', credentials=creds)
    drive_service = xlsx_w.build('drive', 'v3', credentials=creds)

    admin = xlsx_w.arc_parse.admin_setting()
    user_name = xlsx_w.arc_parse.get_user_name(friend_code)
    if len(limit) > 0:
        limit = decode_limit(limit)
        if limit == decode_limit.error:
            await ctx.send("You inputted incorrectly.\nPlease look '#help' and type command again")
            return
        else:
            all_score = await xlsx_w.arc_parse.get_limit_scores(
                song_info=xlsx_w.arc_parse.get_songinfo(), limit=limit)
    else:
        all_score = await xlsx_w.arc_parse.get_all_score(
            song_info=xlsx_w.arc_parse.get_songinfo())
    for song in range(len(all_score)):
        all_score[song] = list(all_score[song].values())
    all_score.insert(0, xlsx_w.arc_parse.fieldnames)
    xlsx_w.arc_parse.admin_del_all_friends(admin)

    if os.path.exists("./spread_sheet/"+user_name+'_sheet_create_rlt.json'):
        response = xlsx_w.get_sheet_info_file(user_name)
        spread_id = response['spreadsheetId']
        spread_url = response['spreadsheetUrl']

        xlsx_w.clear_sheet(sheet_service, spread_id)
    else:
        response = xlsx_w.create_sheet(sheet_service, user_name)
        spread_id = response['spreadsheetId']
        spread_url = response['spreadsheetUrl']
        xlsx_w.set_sheet_info_file(response, user_name)

        xlsx_w.set_share_sheet(drive_service, spread_id)

    xlsx_w.write_sheet(sheet_service, spread_id, all_score)
    xlsx_w.update_sheet(sheet_service, spread_id, len(all_score))
    print(user_name + ":" + spread_url)
    await ctx.send(spread_url)

bot.run(TOKEN)
