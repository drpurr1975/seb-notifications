from bs4 import BeautifulSoup
import requests, datetime, re, json, telebot

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

#ids = ['1111185'] #test receivers list
ids = ['143151797', '1111185', '-1001909756834'] #all receivers
months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
          'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
streets = ['Авиагородок', 'Авиогородок']#, 'Пушкина', 'Манас', 'Школьная']
url = 'http://chupes.nesk.kg'
path = '/ru/abonentam/informaciya-ob-otklyucheniyah/'
#url = 'http://afi.kg'
#path = '/ru/abonentam/perechen-uchastkov-rabot'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'}
time_template = '^\d{1,2}[-:]\d{2}'
time_interval = {'start': '', 'end': ''}
date_template = '\sна\s(0|[1-3])?[0-9]\s[A-Яa-я]+\s'
month_num = 0
date_str_out = ""
looking_region = 'Чуйской'
looking_area = 'Сокулукский'
template_area = 'ский$'
town = 'Манас'
#street = 'Авиагородок'
found_bo = False
noted = {}
noted_filename = 'noted.json'
shows = 0
shows_limit = 1
day_start_delta = 1
split_day_time = datetime.time(12, 00)
every_day = datetime.date(1900, 1, 1)
findtoday = ''

try:
    with open(noted_filename, 'r') as nf:
        noted = json.load(nf)
except:
    with open(noted_filename, 'w') as nf:
        json.dump(noted, nf)

if datetime.datetime.now().time() < split_day_time:
    day_start_delta = 0

#r = requests.get(url + path, timeout=20, headers=headers)
#soup_bol = BeautifulSoup(r.text, features='html.parser')
bo_r = requests.get(url + path, timeout=20, headers=headers)
soup_bo = BeautifulSoup(bo_r.text, features='html.parser')
day_today = datetime.date.today()
bo_list_url = url + path

'''
blackout_list = soup_bol.find_all(class_='post-title')
blackout_list = soup_bol.find_all(class_='block-paragraph_block')

for blackout in blackout_list:
    for every_day in daterange(day_today + datetime.timedelta(days=day_start_delta),
                               day_today + datetime.timedelta(days=4)):
        bo_announce = blackout.contents[0].contents[0].contents[0].contents[0]
        findtoday_alt = ' ' + str(every_day.day).zfill(2) + ' ' + months[every_day.month - 1]
        findtoday = ' ' + str(every_day.day) + ' ' + months[every_day.month - 1]
        findtoday = every_day.strftime('%d.%m.%Y')
        if (bo_announce.find(findtoday) > -1):
            date_url = url + blackout.contents[0].contents[0].get('href')
            bo_r = requests.get(date_url, timeout=20, headers=headers)
            soup_bo = BeautifulSoup(bo_r.text, features='html.parser')
'''
header_list = soup_bo.find_all('strong')
for header in header_list:
    date_str = re.search(date_template, header.text)
    if date_str:
        for month in months:
            if date_str.group().find(month) > -1:
                month_num = months.index(month) + 1
                date_str_out = date_str.group()
                day = re.search('\d?\d', date_str_out).group()
                every_day = datetime.datetime.strptime(day + '.' + str(month_num) + '.' + str(day_today.year) , '%d.%m.%Y').date()
                findtoday_alt = ' ' + str(every_day.day).zfill(2) + ' ' + months[every_day.month - 1]
                findtoday = ' ' + str(every_day.day) + ' ' + months[every_day.month - 1]
#                findtoday = every_day.strftime('%d.%m.%Y')

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
            found_town_street = re.search(rf'(?i){town} *\([^(]*{street}[^)]*\)', cell.text)
            if  (re.search(rf'(?i){town} *\([^(]*{street}[^)]*\)', cell.text)) and (looking_area == current_area):
                found_bo = True
                if shows < shows_limit:
                    output_string = str('<a href="' + bo_list_url + '">В списке профилактических работ Северэлектро на{} найдено &quot;{}, {}&quot;, отключение с {start} до {end}</a>'.format(
                        findtoday, current_area, found_town_street.group(), **time_interval))
                    for id in ids:
                        telegram_bot_sendtext(id, output_string)
#                        print(output_string)

if found_bo:
    if str(every_day) in noted:
        noted[str(every_day)] += 1
    else:
        noted[str(every_day)] = 1

for key in list(noted):
    if datetime.datetime.strptime(str(key), '%Y-%m-%d').date() < datetime.date.today():
        del noted[key]

with open(noted_filename, 'w') as nf:
    json.dump(noted, nf)
