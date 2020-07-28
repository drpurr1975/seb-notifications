#!/usr/bin/python3.8
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests, datetime, re, json, os, time, sys
import telebot
from flask import Flask
import config

#bot = telebot.TeleBot(API_TOKEN)


def telegram_bot_sendtext(id, bot_message):
    seb_bot = telebot.TeleBot(API_TOKEN)
    seb_bot.send_message(chat_id=id, text=bot_message, parse_mode='HTML')
#    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + id + '&parse_mode=MarkdownV2&text=' + bot_message

#    response = requests.get(send_text)

#    return response.json()
    return

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)

ids = ['143151797', '1111185']
months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
          'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
streets = ['Авиагородок', 'Школьная', 'Авиогородок']
url = 'https://www.severelectro.kg'
path = '/content/article/69-planovye-otklyucheniya'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'}
time_template = '^\d{1,2}[-:]\d{2}'
time_interval = {'start': '', 'end': ''}
looking_region = 'Чуйской'
looking_area = 'Сокулукский'
template_area = 'ский$'
town = 'Манас'
noted = {}
noted_filename = 'noted.json'
shows = 0
shows_limit = 3
day_start_delta = 1
split_day_time = datetime.time(12, 00)

try:
    with open(noted_filename, 'r') as nf:
        noted = json.load(nf)
except:
    with open(noted_filename, 'w') as nf:
        json.dump(noted_filename, nf)

if datetime.datetime.now().time() < split_day_time:
    day_start_delta = 0

r = requests.get(url + path, timeout=20, headers=headers)
soup_bol = BeautifulSoup(r.text, features='html.parser')

blackout_list = soup_bol.find_all(class_='post-title')
day_today = datetime.date.today()
for blackout in blackout_list:
    for every_day in daterange(day_today + datetime.timedelta(days=day_start_delta),
                               day_today + datetime.timedelta(days=4)):
        bo_announce = blackout.contents[1].contents[0]
        findtoday = ' ' + str(every_day.day) + ' ' + months[every_day.month - 1]
        if bo_announce.find(findtoday) > -1 and bo_announce.find(looking_region) > -1:
            date_url = url + blackout.contents[1].get('href')
            bo_r = requests.get(date_url, timeout=20, headers=headers)
            soup_bo = BeautifulSoup(bo_r.text, features='html.parser')

            rows = soup_bo.find_all('tr')
            for row in rows[2:]:
                cells = row.find_all('td')
                for cell in cells:
                    if re.search(template_area, cell.get_text().strip()):
                        current_area = cell.get_text().strip()
                    if re.search(time_template, cell.get_text().strip()):
                        time_interval['start'] = cell.get_text().strip()
                        time_interval['end'] = cell.next_sibling.next_sibling.get_text().strip()
                        break
                for cell in cells:
                    if str(every_day) in noted:
                        shows = noted[str(every_day)]
                    for street in streets:
                        found_town_street = re.search(rf'{town} *\([^(]*{street}[^)]*\)', cell.text)
                        if  (re.search(rf'{town} *\([^(]*{street}[^)]*\)', cell.text)) and (looking_area == current_area) and (
                                shows < shows_limit):
                            output_string = str('<a href="' + date_url + '">В списке профилактических работ Северэлектро на{} найдено &quot;{}, {}&quot;, отключение с {start} до {end}</a>'.format(
                                findtoday, current_area, found_town_street.group(), **time_interval))
#                            for id in ids:
#                               telegram_bot_sendtext(id, output_string)
                            print(output_string)
                            if noted.get(str(every_day)):
                                noted[str(every_day)] += 1
                            else:
                                noted[str(every_day)] = 1
                            break

for key in list(noted):
    if datetime.datetime.strptime(str(key), '%Y-%m-%d').date() < datetime.date.today():
        del noted[key]

with open(noted_filename, 'w') as nf:
    json.dump(noted, nf)
