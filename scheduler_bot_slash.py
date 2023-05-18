import discord
from discord.ext import tasks
import re
import datetime
import editcalendar
import logging
import json

EXIT_SUCCESS = 0
EXIT_ERROR = 1

token_file = "discord_token.json"

with open(token_file) as f:
    d = json.load(f)
TOKEN = d["token"]
CHANNEL_ID = None

fmt = "%(asctime)s %(levelname)s %(name)s :%(message)s"
logging.basicConfig(filename='discord.log', level=logging.DEBUG, format=fmt)
#handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

ec = editcalendar.EditCalendar()

def validate_params(day, year, time_start, time_end):
    #構文が正しいか解析する処理
    ret = []
    
    if re.fullmatch(r"([1-9]|0[1-9]|1[0-2]) ([1-9]|[0-2][0-9]|3[0-1])", day) is None:
        ret.append(EXIT_ERROR)
        ret.append("エラー：日付が不正です")
        return ret
    
    if year is not None and re.fullmatch(r"20[0-9][0-9]", year) is None:
        ret.append(EXIT_ERROR)
        ret.append("エラー：西暦が不正です")
        return ret
    
    #時刻のバリデーション
    if time_start is None or time_end is None:
        time_start = None
        time_end = None
    elif ((re.fullmatch(r"([1-9]|0[1-9]|1[0-9]|2[0-3]):([0-9]|[0-5][0-9])", time_start) is None or re.fullmatch(r"([1-9]|0[1-9]|1[0-9]|2[0-3]):([0-9]|[0-5][0-9])", time_end)) is None) and time_start is  not None:
        ret.append(EXIT_ERROR)
        ret.append("エラー：時刻が不正です")
        return ret
    
    ret.append(EXIT_SUCCESS)
    
    return ret
    

@client.event
async def on_ready():
    await tree.sync()
    morning_call.start()
    channels = client.get_all_channels()
    channel = next(channels).channels[0]
    await channel.send("botが起動しました。/setchannelコマンドでモーニングコールの投稿先設定を行ってください。")
    print(f'We have logged in as {client.user}')
    
@tree.command(
    name="setchannel",
    description="モーニングコールの投稿先を変更します"
)
@discord.app_commands.guild_only()
async def setchannel(interaction:discord.Interaction):
    global CHANNEL_ID
    CHANNEL_ID = interaction.channel_id
    channel = client.get_channel(CHANNEL_ID)
    await channel.send("朝の通知の送信先をこのチャンネルに変更しました。")
    

@tree.command(
    name="hello",
    description="Send Hello world."
    )
async def hello(ctx):
    await ctx.send('Hello!')
    
@tree.command(
    name="addcalendar",
    description="カレンダーに予定を追加"
    )
@discord.app_commands.guild_only()
async def addcalendar(interaction:discord.Interaction, day:str, summary: str, year: str=None, time_start: str=None, time_end: str=None):
    #try:
        summaries = summary.split(" ")

        #構文が正しいか解析する処理
        result_validation = validate_params(day, year, time_start, time_end)
        
        if result_validation[0] == EXIT_ERROR:
            await interaction.response.send_message(result_validation[1])
            logging.info(result_validation[1])
            return
        
        #dateとsummaryの構築
        if year is None:
            year = str(datetime.date.today().year)
            
        
            
        month_and_day = day.split(" ")
        date_str = year + "-" + month_and_day[0] + "-" + month_and_day[1]
        
        result_text: str = "{}年{}月{}日に予定を追加しました：\n".format(year, month_and_day[0], month_and_day[1])
        result_log: str = date_str + "に予定追加："
        
        if time_start is not None and time_end is not None:
            result_insert = ec.insert_event(date_str, summaries[0], time_start, time_end)
            if result_insert[0] == editcalendar.EXIT_SUCCESS:
                result_text = result_text + time_start + "-" + time_end + " " + summary
                result_log = result_log + time_start + "-" + time_end + " " + summary
            else:
                result_text = "エラーが発生しました。内容を以下に記します：\n" + result_insert[1]
        
        else:
            for sum in summaries:
                result_insert = ec.insert_event(date_str, sum)
                #await ctx.send("start:{0}, end:{1}, summary:{2}".format(date_start, date_end, summary))
                if result_insert[0] == editcalendar.EXIT_SUCCESS:
                    result_text = result_text + "・" + sum + "\n"
                    result_log = result_log + " " + sum
                else:
                    result_text = result_text + "・" + sum + "（追加に失敗）" + "\n"
                    result_log = result_log + " " + sum + "（追加に失敗）"
            
        await interaction.response.send_message(result_text)
        logging.info(result_log)
        
        
    #except:
    #    await interaction.response.send_message("何かしらのエラーが発生しました")
    #インデックスエラー、構文エラー
    #await ctx.send(arguments)
    
async def fetch_event(date: datetime.datetime):
    event_list = editcalendar.EditCalendar.reshape_events_items(ec.get_day_events(date))    
    text = ""
    count = 0
    
    
    if event_list:
        for have_period in event_list[0]:
            text = text + "・" + have_period["time_start"] + "〜" + have_period["time_end"] + " " + have_period["summary"] + "\n"
            count = count + 1
        
        text = text + "\n"
        
        for whole_day in event_list[1]:
            text = text + "・" + whole_day + "\n"
            count = count + 1
            
        text_prefix = datetime.datetime.strftime(date, "%Y年%m月%d日") + "の予定は" + str(count) +"つあります：" + "\n"
        
        text = text_prefix + text
        
    else:
        text_prefix = datetime.datetime.strftime(date, "%Y年%m月%d日") + "の予定：" + "\n"
        text = text_prefix + "登録された予定はありません"
    
    return text

@tree.command(
    name="show_events",
    description="指定された日の予定を表示します。指定がなければ今日の予定を表示します。"
)
@discord.app_commands.guild_only()
async def show_events(interaction: discord.Interaction, day: str=None, year: str=None):
    if day == None:
        #引数がなければ今日の予定を表示
        target_datetime = datetime.datetime.today()
    elif re.fullmatch(r"([1-9]|0[1-9]|1[0-2]) ([1-9]|[0-2][0-9]|3[0-1])", day) is None:
        await interaction.response.send_message("日付の入力が不正です")
        return
    else:
        #dateとsummaryの構築
        if year is None:
            year = str(datetime.date.today().year)
            
        month_and_day = day.split(" ")
        date_start = year + "-" + month_and_day[0] + "-" + month_and_day[1]
        target_datetime = datetime.datetime.strptime(date_start, '%Y-%m-%d')
    text = await fetch_event(target_datetime)
    await interaction.response.send_message(text)
    logging.info("today_events is called")

@tasks.loop(seconds=60)
async def morning_call():
    global CHANNEL_ID
    # 現在の時刻
    if CHANNEL_ID == None:
        
        return
    else:
        now = datetime.datetime.now()
        if now.hour == 7 and now.minute == 0:
            channel = client.get_channel(CHANNEL_ID)
            text = "おはようございます。\n本日の予定を通知します。\n"
            text = text + await fetch_event(now)
            await channel.send(text) 
            logging.info("morning call")
            
        elif now.hour == 21 and now.minute == 0:
            channel = client.get_channel(CHANNEL_ID)
            text = "21時になりました。\n明日の予定を通知します。\n"
            tomorrow = now + datetime.timedelta(days=1)
            text = text + await fetch_event(now)
            await channel.send(text) 
            logging.info("night call")


client.run(TOKEN)