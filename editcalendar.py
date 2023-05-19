from __future__ import print_function

import datetime
import json
import os.path

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
# SCOPES = ['https://www.googleapis.com/auth/calendar']

EXIT_SUCCESS = 0
EXIT_ERROR = 1

class EditCalendar:
    def __init__(self):
        self.creds = self.load_credential()
        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
            self.calendarId = self.load_calendar()
        
        except HttpError as error:
                    print('An error occurred: %s' % error)

    def load_credential(self):
        # デフォルトのjsonファイルを探索するはず
        creds, _ = google.auth.default()
        return creds
    
    def load_calendar(self):
        if os.path.exists("calendar_data.json"):
            with open("calendar_data.json") as file_data:
                calendar = json.load(file_data)
        else:
            calendar = self.create_calendar(self.service)
            with open("calendar_data.json", "w") as file:
                json.dump(calendar, file, indent=4, ensure_ascii=False)
        
        calendarId = calendar["id"]
        
        return calendarId

    def create_calendar(self):
        calendar_list = self.service.calendarList().list().execute()
        for calendar_list_entry in calendar_list['items']:
            if calendar_list_entry['summary'] == '予定管理fromDiscordBot':
                return calendar_list_entry
        
        calendar = {
            'summary': '予定管理fromDiscordBot',
            'timeZone': 'Asia/Tokyo'
        }
        
        created_calendar = self.service.calendars().insert(body=calendar).execute()
        return created_calendar

    def insert_event(self, day:str, summary, time_start:str=None, time_end:str=None):
        #カレンダーに追加するイベントのクエリ（json）について調べる
        #終日で追加する
        ret: list
        try:
            new_event = self.create_event(day, summary, time_start, time_end)
            new_event = self.service.events().insert(calendarId=self.calendarId, body=new_event).execute()
            ret = [EXIT_SUCCESS, "追加に成功"]
        except Exception as e:
            ret = [EXIT_ERROR, str(e)]
        return ret
        
    def create_event(self, day: str, summary: str, time_start: str, time_end: str):
        """
        想定している引数の形
        day: yyyy-mm-dd
        summary: 予定の内容
        time_start: x:xx:xx
        time_end: x:xx:xx
        """
        if time_start is not None and time_end is not None:
            start = day + "T" + time_start + ":00"
            end = day + "T" + time_end + ":00"
            event = {
                "summary": summary,
                "start": {
                    "dateTime": start,
                    "timeZone": "Asia/Tokyo"
                    },
                "end": {
                    "dateTime": end,
                    "timeZone": "Asia/Tokyo"
                    }
            }
        else:
            day_datetime = datetime.datetime.strptime(day, "%Y-%m-%d")
            end = datetime.datetime.strftime(day_datetime + datetime.timedelta(days=1), "%Y-%m-%d")
            event = {
                "summary": summary,
                "start": {
                    "date":day
                    },
                "end": {
                    "date":end
                    }
            }
        #print(event)
        return event
    
    def get_day_events(self, day: datetime.datetime):
        tomorrow = day + datetime.timedelta(days=1)
        timeMin = datetime.datetime.strftime(day, '%Y-%m-%d') + "T00:00:00+09:00"
        timeMax = datetime.datetime.strftime(tomorrow, '%Y-%m-%d') + "T00:00:00+09:00"
        events = self.service.events().list(calendarId=self.calendarId, timeMin=timeMin, timeMax=timeMax).execute()
        #print(events)
        return events["items"]

    @staticmethod
    def reshape_events_items(items: list):
        """
        想定するデータ構造
        [
            [
                {
                "summary": "-----",
                "start_dateTime": x:xx,
                "end_dateTime": xx:xx,
                },
            ],
            [---, ---, ---]
        ]
        """
        have_period = []
        whole_day = []
        
        for i in items:
            if "dateTime" in i["start"]:
                have_period.append({
                    "summary": i["summary"],
                    "time_start": i["start"]["dateTime"],
                    "time_end": i["end"]["dateTime"]
                })
            elif "date" in i["start"]:
                whole_day.append(i["summary"])
        
        have_period = sorted(have_period, key=lambda h: h["time_start"])
        
        for j in have_period:
            j["time_start"] = j["time_start"][11:16]
            j["time_end"] = j["time_end"][11:16]
                
            if j["time_start"][0] == "0":
                j["time_start"] = j["time_start"][1:]
                
            if j["time_end"][0] == "0":
                j["time_end"] = j["time_end"][1:]
            
        
        return [have_period, whole_day]        
                    
                
    
def main():
    editCalendar = EditCalendar()
    #start = "2023-05-08"
    #end = "2023-05-09"
    #summary = "スケジュールテスト"
    #editCalendar.insert_event(start, end, summary)
    editCalendar.get_day_events(datetime.datetime(2023, 5, 19))
    print(editCalendar.reshape_events_items(editCalendar.get_day_events(datetime.datetime(2023, 5, 20))))
    
    
if __name__ == '__main__':
    main()