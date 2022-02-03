import requests
import time
import pymysql
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from slack_sdk import WebClient
                        #IP Address, ID, PASSWORD, DATABASE_NAME
conn = pymysql.connect(host="", user = "" , password="",database="") #,as_dict = True)
cursor = conn.cursor()

sql = "INSERT INTO bot_data (user_name,timestamp,text) VALUES (%s, %s, %s)"
update_sql = "UPDATE bot_data SET answer = %s WHERE user_name = %s and timestamp = %s"
select_sql = "SELECT answer FROM bot_data WHERE user_name = %s and timestamp = %s"



class SlackAPI:
    """
    슬랙 API 핸들러
    """
    def __init__(self, token):
        # 슬랙 클라이언트 인스턴스 생성
        self.client = WebClient(token)
        
    def get_channel_id(self, channel_name):
        """
        슬랙 채널ID 조회
        """
        # conversations_list() 메서드 호출
        result = self.client.conversations_list()
        # # 채널 정보 딕셔너리 리스트
        channels = result.data['channels']
        # 채널 명이 'test'인 채널 딕셔너리 쿼리
        channel = list(filter(lambda c: c["name"] == channel_name, channels))[0]
        # 채널ID 파싱
        channel_id = channel["id"]
        return channel_id

    def get_messages(self, channel_id, history_period:int=10)->list:
        """
        슬랙 채널 내 메세지 조회
        """
        # conversations_history() 메서드 호출
        
        now = datetime.now()
        before_dt = now -timedelta(minutes=history_period)
        
        result = self.client.conversations_history(channel=channel_id, oldest=before_dt.timestamp())
        # 채널 내 메세지 정보 딕셔너리 리스트
        messages = result.data['messages']
           
        return messages

    def post_thread_message(self, channel_id, message_ts, text):
        """
        슬랙 채널 내 메세지의 Thread에 댓글 달기
        """
        # chat_postMessage() 메서드 호출
        result = self.client.chat_postMessage(
            channel=channel_id,
            text = text,
            thread_ts = message_ts
        )
        return result
    
  
        
token = "" #Your Token Name
slack = SlackAPI(token)
channel_name = "" #Your Channel Name
channel_id = slack.get_channel_id(channel_name)

while(True):
    
    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')
        query = "안녕하세요"
        text = "반가워요"

        # 채널ID 파싱

        # 메세지ts 파싱
        #message_ts = slack.get_messages(channel_id)
        # 댓글 달기

        messages = slack.get_messages(channel_id)
        messages = [message for message in messages]
        

        for message in messages:
            
            if not messages:
                pass
            else:
                user = messages[0]['user']
                time_stamp = messages[0]['ts']
                message_text = messages[0]['text']
                
                cursor.execute(select_sql,(user,time_stamp))    
                row = cursor.fetchone()
                #print(row)
                
                if row == None:
                    # cursor.execute(sql,(message_ts[0]['user'],message_ts[0]['ts'],message_ts[0]['text']))
                    cursor.execute(sql,(user,time_stamp,message_text))
                    conn.commit()                
                    if message['text'] == "안녕하세요":
                        slack.post_thread_message(channel_id, message['ts'], "반가워요")
                        
                    elif message['text'] == "지금 시각은?":
                        slack.post_thread_message(channel_id,message['ts'], "지금 시간은 {} 입니다.".format(current_time))
                        
                    elif message['text'] == "오늘 날짜는?":
                        slack.post_thread_message(channel_id,message['ts'], "오늘 날짜는 {} 입니다.".format(current_date))
                    
                    elif message['text'] == "코로나확진자수?":
                        url = 'http://ncov.mohw.go.kr/'
                        response = requests.get(url)
                        if response.status_code == 200:
                            html = response.text
                            soup = BeautifulSoup(html, 'html.parser')                        
                            title = soup.select_one('#content > div > div > div.liveboard_layout > div.liveToggleOuter > div > div.live_left > div.occurrenceStatus > div.occur_graph > table > tbody > tr:nth-child(1) > td:nth-child(5) > span')    
                            print(title)
                            corona_count = title.get_text()
                            slack.post_thread_message(channel_id,message['ts'], "오늘 {}일 기준  확진자수 는 {} 입니다.".format(current_date, corona_count))
                    elif message['text'] == "퇴근":
                        if current_time < '18:00:00':
                            slack.post_thread_message(channel_id,message['ts'], "퇴근을 거부당했습니다.")
                        else:
                            slack.post_thread_message(channel_id,message['ts'], "퇴근 하셔도 좋습니다!")
                            
                    elif message['text'] == "날씨":
                        url='https://weather.naver.com/today/'  
                        response = requests.get(url)                                              
                        if response.status_code == 200:
                            html = response.text
                            soup = BeautifulSoup(html, 'html.parser') 
                            temp_txt = soup.select_one('#content > div > div.section_center > div.card.card_today > div.today_weather > div.weather_area > div.weather_now > div > strong')  
                            feel_temp_txt = soup.select_one('#content > div > div.section_center > div.card.card_today > div.today_weather > div.weather_area > div.weather_now > p > span.weather')
                            temp = temp_txt.get_text()
                            feel_temp = feel_temp_txt.get_text()
                            print(response)
                            print(temp_txt)
                            print(feel_temp_txt)
                            slack.post_thread_message(channel_id,message['ts'], "{}이며 날씨는 {} 입니다.".format(temp, feel_temp))
                                                    
    except Exception as e:
        text = f"동작 중 에러가 발생하였습니다: {e}"
        slack.post_thread_message(channel_id,message['ts'], text)
        ## 에러 났을 땐 1분간 쉬기
        time.sleep(60)               
                
            
    time.sleep(1)


