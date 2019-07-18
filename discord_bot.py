import discord
from discord.ext import commands 
import pickle
import os

bot = commands.Bot(command_prefix='#')

with open('bot_token.pickle', 'rb') as token_f:
    TOKEN = pickle.load(token_f)


@bot.event
async def on_ready():
    print("Logged in as")
    print(bot.user.name)
    print("=============")

    await bot.change_presence(
        activity=discord.Activity(
            name="Command", type=discord.ActivityType.watching,
            details="Command '#sheet <friend code>'"),
        status=discord.Status.online
    )


@bot.command()
async def sheet(ctx, arg):
    await ctx.send('writting spreadsheet...')
    import google_sheet_write as xlsx_w

    creds = xlsx_w.credential()

    sheet_service = xlsx_w.build('sheets', 'v4', credentials=creds)
    drive_service = xlsx_w.build('drive', 'v3', credentials=creds)

    if os.path.exists('./static_uuid.txt'):
        xlsx_w.arc_parse.get_uuid_from_file()
    else:
        xlsx_w.arc_parse.set_uuid_into_file()

    admin = xlsx_w.arc_parse.admin_login()
    xlsx_w.arc_parse.admin_del_all_friends(admin)
    user_name = xlsx_w.arc_parse.get_user_name(friend_code=arg)
    all_score = xlsx_w.getArcScore()
    xlsx_w.arc_parse.admin_del_all_friends(admin)

    if os.path.exists("./"+user_name+'/sheet_create_rlt.json'):
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
    await ctx.send(spread_url)

        

bot.run(TOKEN)
