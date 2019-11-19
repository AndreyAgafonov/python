#!/usr/bin/env python3
import os
import smtplib
import sys
import configparser
import datetime
import smtplib
from atlassian import Confluence
import json
from bs4 import BeautifulSoup
import pandas as pd
from lxml.html import parse
# Исходные даные

# Общий план
# Получить таблицу
# Для получения требуется установка pip install atlassian-python-api
#  спарсить ее
# найти  нуные данные
# отправить кому нужно
#

# Задачи
# +Проверить соответствие формата даты формату
# +проверить наличие даты

# +Если поздравлять некого или некому отправлять - не оптравляем
# +проверить что сотрудник не уволен
# +выделить сотрудников  которым нужно разослать
    # Итоговая таблица в которой - сотрудник кро
# Спарсить таблицу - найти нужные номера строк
# Найти колонку 
# Заполнить пустые строки хоть чем то
# Контролируем что писать в лог а что отправить в почту уведомление
#  Установка расширения pip install atlassian-python-api
# sudo pip install bs4 lxml html5lib (вероятно нужно только bs4)
# pip install pandas
# Исправить  использоватние конфигов по умолчанию
# Нарисовать схема данных по фйункциями
#Не хвататет поиска колонки с ДР
# Логгирование сделать
# сделать сервис
# Сделать инсталятор
# сделать докер образ


def analize(table_analyze):
    # Фиксируем сегодняшнюю дату
    #table = [["FIO","tell","date","status"], ["Andrey","+79274000000","15/11",""], ["Tanya","+79274000000","10/11",""], ["Sergey","+79274000000","15/11","Уволена" ], ["Olga","+79274000000","25/07",""]]
    #print(table_analyze)
    #Конфиг
    base_path = os.path.dirname(os.path.abspath(__file__))
    #применяем конфигурацию по умолчанию
    config_path_default = os.path.join(base_path, "dafault.conf")
    config_path = os.path.join(base_path, "config.conf")
    if os.path.exists(config_path):
        
        #cfg = ConfigParser._read_defaults
        cfg = configparser.ConfigParser()
        cfg.read(config_path_default)
        cfg.read(config_path)
    else:
        print("Конфиг не обнаружен! см. документацию по настройке https://github.com/AndreyAgafonov/python/tree/master/birthday")
        sys.exit(1)
    # Парсим конфиг файл
    section = "general"
    # Разделитель для даты
    general_dlmtr = cfg.get(section, "delimiter")
    col_name  = cfg.get(section, "column_date_of_birth")
    sendto =[]
    sendwho = []
    fired = []
    admin_notif = []
    bd = []
    today = datetime.date.today()

    table_range=range(len(table_analyze.index))
    #описываем разделитель даты
    pattern=str('%d')+general_dlmtr+str('%m')    
    for element in table_range:
        if ( "уволен" in str(table_analyze[(element):(element+1)]).upper().lower() or 
            "fired"  in str(table_analyze[(element):(element+1)]).upper().lower() or 
            "uvolen" in str(table_analyze[(element):(element+1)]).upper().lower() ):  # ищем уволенных:
            fired += [element]
        else:
            try: # проверяем формат даты.
                dateofbr=str(table_analyze[(element):(element+1)][col_name].values[0])
                dempldp = datetime.date(datetime.date.today().year, datetime.datetime.strptime( dateofbr, pattern).month, datetime.datetime.strptime( dateofbr, pattern).day)
                diff = int(today.toordinal()) - int(dempldp.toordinal())
                # Заполняем списки - кого нужно поздравить и кому нужно отправить приглашение
                if -1 < diff < 7 :
                    # Если да то Заполняем список кого поздравить                     
                    sendwho += [element]
                    if diff == 0 :
                        bd += [element]
                else:
                    # Если да то Заполняем список кому оптравить напоминание
                    sendto += [element]
            except ValueError as err:
                print("Ошибка! Не верный формат дня рождению. Формат должен быть в виде День.месяц (например: 26.10). Текст ошибки:", err)
                admin_notif += [element]# отправить сообщение Одмину о  том что нужно исправить наполнение таблицы.
    return sendwho,sendto,fired,admin_notif,bd

def send_email(subject, to_addr, body_text):
    """
    Send an email
    """
    #Конфиг
    base_path = os.path.dirname(os.path.abspath(__file__))
    #применяем конфигурацию по умолчанию
    config_path_default = os.path.join(base_path, "dafault.conf")
    config_path = os.path.join(base_path, "config.conf")
    if os.path.exists(config_path):
        
        #cfg = ConfigParser._read_defaults
        cfg = configparser.ConfigParser()
        cfg.read(config_path_default)
        cfg.read(config_path)
    else:
        print("Конфиг не обнаружен! см. документацию по настройке https://github.com/AndreyAgafonov/python/tree/master/birthday")
        sys.exit(1)
    # Парсим конфиг файл
    section = "smtp"
    smtp_host = cfg.get(section, "smtp_server")
    smtp_port = cfg.get(section, "smtp_port")
    smtp_tls = cfg.get(section, "smtp_tls")
    smtp_login = cfg.get(section, "smtp_login")
    smtp_password = cfg.get(section, "smtp_password")
    smtp_from_addr = cfg.get(section, "smtp_sender")

    section = "general"
    general_column_mail = cfg.get(section, "column_mail")
    print(smtp_host, smtp_port ,smtp_tls, smtp_login, smtp_password, smtp_from_addr)
    if not str(smtp_tls):
        print("tls не задан спользуем подключение без TLS")
    if not str(smtp_from_addr):
        print("В конфиге не указан отправитель. Используем такой же как и логин")
        smtp_from_addr = smtp_login


    BODY = "\r\n".join((
        "From: %s" % smtp_from_addr,
        "To: %s" % to_addr,
        "Subject: %s" % subject ,
        "",
        body_text
        ))
    #sys.exit(1)
    server = smtplib.SMTP(smtp_host, smtp_port)        
    if smtp_tls == "yes":
        server.starttls()    
    #server.login(smtp_login, smtp_password)
    server.login("python@cloud16.ru", "eholot22")
    server.sendmail(smtp_from_addr, to_addr, BODY)
    #server.sendmail("python@cloud16.ru", "aagafonov@inbox.ru", "Hi!")
    server.quit()

def confluence_get_page():
    #Конфиг
    base_path = os.path.dirname(os.path.abspath(__file__))
    #применяем конфигурацию по умолчанию
    #config_path_default = os.path.join(base_path, "dafault.conf")
    config_path = os.path.join(base_path, "config.conf")
    if os.path.exists(config_path):
        cfg = configparser.ConfigParser()
        #cfg.read(config_path_default)
        cfg.read(config_path)
    else:
        print("Конфиг не обнаружен! см. документацию по настройке https://github.com/AndreyAgafonov/python/tree/master/birthday")
        sys.exit(1)
    # Парсим конфиг файл
    section = "confluence"
    confluence_url = cfg.get(section, "confluence_connection_string")
    confluence_pageid = cfg.get(section, "confluence_pageid")
    confluence_user = cfg.get(section, "confluence_user")
    confluence_passwd = cfg.get(section, "confluence_passwd")

    section = "general"
    col_name  = cfg.get(section, "column_date_of_birth")
    # Подключение к конфлюенсе
    confluence = Confluence(
        url=confluence_url,
        username=confluence_user,
        password=confluence_passwd)
    content1 = confluence.get_page_by_id(confluence_pageid,expand="body.storage")
    ##Первая колонка  это порядковый номер -  используем ее как индекс index_col=0
    ##Заголовок в первой строке - ее тоже не учитываем header=0
    ##
    df_list = pd.read_html(content1['body']['storage']['value'], header=0,index_col=0, na_values=['No Acquirer'],converters={col_name:str})
    #parse_dates=["Birthday"]
    table=df_list[0]
    table.index.name = "Number"
    #print (table[2:5]["FN"])
    return table
    #print(len(table.index))
    





#Конфиг General
base_path = os.path.dirname(os.path.abspath(__file__))
#применяем конфигурацию по умолчанию
config_path_default = os.path.join(base_path, "dafault.conf")
config_path = os.path.join(base_path, "config.conf")
if os.path.exists(config_path):
    #cfg = ConfigParser._read_defaults
    cfg = configparser.ConfigParser()
    cfg.read(config_path_default)
    cfg.read(config_path)
else:
    print("Конфиг не обнаружен! см. документацию по настройке https://github.com/AndreyAgafonov/python/tree/master/birthday")
    sys.exit(1)
# Парсим конфиг файл

section = "general"
general_column_mail = cfg.get(section, "column_mail")
general_name = cfg.get(section, "column_name")
general_full_name = cfg.get(section, "column_full_name")




# Получаем данные из Конфлюенсе
confluence_get_page()
table=confluence_get_page()

analize(table)
sendwho,sendto,fired,admin_notif,bd=analize(table)


#Шаблон письма именник (bd)

subject_to = " Уважаемый! Карты нагадали, что скоро у твоих коллег ДР! Не плохобы чего и поздравить!"
#to_addr = "aagafonov@inbox.ru"    


#send_email(subject, to_addr, body_text)
    #BODY = "\r\n".join((
    #    "С днем рождения коллега"
        #<center>
        #<img alt="Кот Саймона" 
        #src="https://www.google.com/url?sa=i&source=images&cd=&cad=rja&uact=8&ved=2ahUKEwiqm-nf_-7lAhWOfZoKHY5mAOAQjRx6BAgBEAQ&url=%2Furl%3Fsa%3Di%26source%3Dimages%26cd%3D%26ved%3D2ahUKEwjbjrvX_-7lAhXkx6YKHTHoBSwQjRx6BAgBEAQ%26url%3Dhttps%253A%252F%252Fwww.pinterest.com%252Fpin%252F421719952598337553%252F%26psig%3DAOvVaw2ZWi5mJy0oX9RYx0VZbHyp%26ust%3D1574002831482749&psig=AOvVaw2ZWi5mJy0oX9RYx0VZbHyp&ust=1574002831482749">
        #</center>''
    #))

#body_text_to = 


if sendwho and sendto:    
    print("Кого поздравляем:")    
    for send1 in range(len(sendwho)):
        print(str(table[int(sendwho[send1]):(int(sendwho[send1])+1)][general_full_name].values[0]),":[",sendwho[send1],"]")
    print("Кому отправляем: ")
    for send1 in range(len(sendto)):
        print(str(table[int(sendto[send1]):(int(sendto[send1])+1)]["FN"].values[0]),":[",sendto[send1],"]")



else:
    
    print(" Некого поздравлять или  некому отправлять поздравляения")

if fired:
    print("Уволен, уведомления не оптравляем и не анализируем: ")
    for send1 in range(len(fired)):
        print(str(table[(int(fired[send1])-1):int(fired[send1])]["FN"].values[0]),":[",fired[send1],"]")
else:
    print("уволенных нет")    



if admin_notif:
    print("У пользователей не верно заполнен поле дата")
    for send1 in range(len(admin_notif)):
        print(str(table[(int(admin_notif[send1])-1):int(admin_notif[send1])]["FN"].values[0]),":[",admin_notif[send1],"]")


subject = " Дорогой коллега! поздравляем Вас с днем рождения! и Желаем Вам побольше котиков!"
if bd:
    print("У пользователя сегодня ДР")
    for send1 in range(len(bd)):
        print(str(table[(int(bd[send1])):(int(bd[send1])+1)][general_full_name].values[0]),":[",bd[send1],"]")
        name = str(table[(int(bd[send1])):(int(bd[send1])+1)][general_name].values[0]).split(' ',1)[1]
        print(name)
        msg = str('"')+str("Эгей, ") + name + str("! Да у тебя сегодня днюха!  Поздравляем! Пусть Этот котик всегда тебя радует:)")+str('"')
        print(msg)
        send_to = str('"')+str(table[(int(bd[send1])-1):int(bd[send1])][general_column_mail].values[0])+str('"')
        print(send_to)
        print(subject)
        #send_email(subject_bd, send_to, body_text_bd)
        send_email(subject, send_to, msg)

#general_column_mail    general_name