#!/usr/bin/python3.8git
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests, datetime, re, json, telebot, ssl, config
from aiohttp import web

WEBHOOK_LISTEN = "0.0.0.0"
WEBHOOK_PORT = 8443

WEBHOOK_SSL_CERT = "/etc/letsencrypt/live/YOUR.DOMAIN/fullchain.pem"
WEBHOOK_SSL_PRIV = "/etc/letsencrypt/live/YOUR.DOMAIN/privkey.pem"

API_TOKEN = '968634485:AAER3wucMp_6YWYac_tnqSqtoGSV8V_4fMw'
bot = TeleBot(API_TOKEN)

app = web.Application()

# process only requests with correct bot token
async def handle(request):
    if request.match_info.get("token") == bot.token:
        request_body_dict = await request.json()
        update = telebot.types.Update.de_json(request_body_dict)
        bot.process_new_updates([update])
        return web.Response()
    else:
        return web.Response(status=403)

app.router.add_post("/{token}/", handle)

help_string = []
help_string.append("*Some bot* - just a bot.\n\n")
help_string.append("/start - greetings\n")
help_string.append("/help - shows this help")

# - - - messages

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, "Ololo, I am a bot")

@bot.message_handler(commands=["help"])
def send_help(message):
    bot.send_message(message.chat.id, "".join(help_string), parse_mode="Markdown")

# - - -

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

# start aiohttp server (our bot)
web.run_app(
    app,
    host=WEBHOOK_LISTEN,
    port=WEBHOOK_PORT,
    ssl_context=context,
)

def telegram_bot_sendtext(id, bot_message):
    bot_token = '968634485:AAER3wucMp_6YWYac_tnqSqtoGSV8V_4fMw'
    seb_bot = telebot.TeleBot(bot_token)
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
