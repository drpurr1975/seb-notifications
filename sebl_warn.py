from bs4 import BeautifulSoup
import requests, datetime, re, json, telebot, sys

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

ids = ['1111185', '143151797', '-1001909756834'] # all receivers
months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
          'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
streets = ['Авиагородок', 'Авиогородок'] #, 'Проектируемая', 'Пушкина', 'Манас', 'Школьная']
url = 'http://chupes.nesk.kg'
path = '/ru/abonentam/perechen-uchastkov-rabot/'
#url = 'http://afi.kg'
#path = '/ru/abonentam/perechen-uchastkov-rabot'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'}
time_template = '^\d{1,2}[-:]\d{2}'
time_interval = {'start': '', 'end': ''}
date_template = '\sна\s(0|[1-3])?[0-9]-?\s[A-Яa-я]+'
month_num = 0
date_str_out = ""
looking_region = 'Чуйской'
looking_area = 'Сокулукский'
template_area = 'ский$'
town = 'Манас'
#town = 'Новопавловка'
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

# пробуем загрузить словарь уведомлений из noted.json и, если его нет, создаем файл
try:
    with open(noted_filename, 'r') as nf:
        noted = json.load(nf)
except:
    with open(noted_filename, 'w') as nf:
        json.dump(noted, nf)

if datetime.datetime.now().time() < split_day_time:
    day_start_delta = 0
# формируем путь к странице списка дат отключений, загружаем страницу и парсим ее в soup_bol
bo_list_url = url + path
r = requests.get(bo_list_url, timeout=20, headers=headers)
soup_bol = BeautifulSoup(r.text, features='html.parser')
#bo_r = requests.get(url + path, timeout=20, headers=headers)
#soup_bo = BeautifulSoup(bo_r.text, features='html.parser')

day_today = datetime.date.today()

# blackout_list = soup_bol.find_all(class_='post-title')
blackout_list = soup_bol.find(class_='block-paragraph_block')

for blackout in blackout_list:
    # ищем дату по regexp
    date_str = re.search(date_template, blackout.text)
    if date_str:
        for month in months:
            # если нашли шаблон даты, то ищем по имени в списке индекс и сохраняем в month_num
            if date_str.group().find(month) > -1:
                month_num = months.index(month) + 1
                # в строке ссылки ищем день по шаблону regexp и сохраняем в day
                date_str_out = date_str.group()
                day = re.search('\d?\d', date_str_out).group()
                # формируем переменную даты every_day для загруженной страницы с отключениями на этот день
                every_day = datetime.datetime.strptime(day + '.' + str(month_num) + '.' + str(day_today.year) , '%d.%m.%Y').date()
                # findtoday_alt = ' ' + str(every_day.day).zfill(2) + ' ' + months[every_day.month - 1]
                # и заодно формируем строку findtoday для вывода
                findtoday = ' ' + str(every_day.day) + ' ' + months[every_day.month - 1]
                # findtoday = every_day.strftime('%d.%m.%Y')
        # если нашли дату и она сегодняшняя или будущая, то сохраняем ссылку, загружаем и парсим в soup_bo
        if day_today <= every_day:
            date_url = url + blackout.contents[0].attrs['href']
            bo_r = requests.get(date_url, timeout=20, headers=headers)
            soup_bo = BeautifulSoup(bo_r.text, features='html.parser')
            # формируем список строк для поиска отключений
            rows = soup_bo.find_all('tr')
            for row in rows[2:]:
                cells = row.find_all('td')
                for cell in cells:
                    # ищем построчно в таблице сначала район и сохраняем в current_area
                    if re.search(template_area, cell.get_text().strip()):
                        current_area = cell.get_text().strip()
                    # потом временной интервал по шаблону и сохраняем в словарь time_interval
                    if re.search(time_template, cell.get_text().strip()):
                        time_interval['start'] = cell.get_text().strip()
                        time_interval['end'] = cell.next_sibling.next_sibling.get_text().strip()
                        # если нашли время то дальше уже не ищем в этой строке
                        break
                if current_area == looking_area:
                    # если район совпадает с искомым
                    for cell in cells:
                        for street in streets:
                            # то ищем совпадения комбинации населенного пункта и улицы
                            found_town_street = re.search(rf'(?i){town} *\([^(]*{street}[^)]*\)', cell.text)
                            if  (re.search(rf'(?i){town} *\([^(]*{street}[^)]*\)', cell.text)) and (looking_area == current_area):
                                # если нашли, то читаем из файла количество разосланных уведомлений,
                                # поднимаем флаг и проверяем на достигнут ли лимит уведомлений на эту дату
                                if str(every_day) in noted:
                                    shows = noted[str(every_day)]
                                found_bo = True
                                if shows < shows_limit:
                                    # если не достигнут, то формируем строку вывода и рассылаем уведомления по списку
                                    output_string = str('<a href="' + bo_list_url + '">В списке профилактических работ Северэлектро на{} найдено &quot;{}, {}&quot;, отключение с {start} до {end}</a>'.format(
                                        findtoday, current_area, found_town_street.group(), **time_interval))
                                    # если есть аргумент командной строки, то рассылаем в телеграм, иначе только в консоль
                                    if "--telegram" in sys.argv[1:]:
                                        for id in ids:
                                            telegram_bot_sendtext(id, output_string)
                                    else:                                        
                                        print(output_string)

                                    # если есть флаг и есть запись о количестве уведомлений, то увеличиваем на единицу и записываем обратно
                                    # если нет, то записываем единицу
                                    if found_bo:
                                        if str(every_day) in noted:
                                            noted[str(every_day)] += 1
                                        else:
                                            noted[str(every_day)] = 1



# удаляем все записи об уведомлениях которые уже неактуальны
for key in list(noted):
    if datetime.datetime.strptime(str(key), '%Y-%m-%d').date() < datetime.date.today():
        del noted[key]

# сохраняем словарь уведомлений в noted.json
with open(noted_filename, 'w') as nf:
    json.dump(noted, nf)

'''for blackout in blackout_list:
    bo_announce = blackout.contents[0].contents[0].contents[0].contents[0]
    for every_day in daterange(day_today + datetime.timedelta(days=day_start_delta),
                               day_today + datetime.timedelta(days=4)):
        findtoday_alt = ' ' + str(every_day.day).zfill(2) + ' ' + months[every_day.month - 1]
        findtoday = ' ' + str(every_day.day) + ' ' + months[every_day.month - 1]
        findtoday = every_day.strftime('%d.%m.%Y')
        if (bo_announce.find(findtoday) > -1):
            date_url = url + blackout.contents[0].contents[0].get('href')
            bo_r = requests.get(date_url, timeout=20, headers=headers)
            soup_bo = BeautifulSoup(bo_r.text, features='html.parser')'''

# for every_day in daterange(day_today + datetime.timedelta(days=day_start_delta),
#                                day_today + datetime.timedelta(days=4)):
#         findtoday_alt = ' ' + str(every_day.day).zfill(2) + ' ' + months[every_day.month - 1]
#         findtoday = ' ' + str(every_day.day) + ' ' + months[every_day.month - 1]
#         findtoday = every_day.strftime('%d.%m.%Y')
#         if (bo_announce.find(findtoday) > -1):
#             date_url = url + blackout.contents[0].contents[0].get('href')
#             bo_r = requests.get(date_url, timeout=20, headers=headers)
#             soup_bo = BeautifulSoup(bo_r.text, features='html.parser')

# header_list = soup_bo.find_all('strong')
# for header in header_list:
#     date_str = re.search(date_template, header.text)
#     if date_str:
#         for month in months:
#             if date_str.group().find(month) > -1:
#                 month_num = months.index(month) + 1
#                 date_str_out = date_str.group()
#                 day = re.search('\d?\d', date_str_out).group()
#                 every_day = datetime.datetime.strptime(day + '.' + str(month_num) + '.' + str(day_today.year) , '%d.%m.%Y').date()
#                 findtoday_alt = ' ' + str(every_day.day).zfill(2) + ' ' + months[every_day.month - 1]
#                 findtoday = ' ' + str(every_day.day) + ' ' + months[every_day.month - 1]
#                 findtoday = every_day.strftime('%d.%m.%Y')