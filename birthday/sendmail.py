#!/usr/bin/env python3
import os
import sys
import configparser
import datetime
import smtplib
from atlassian import Confluence
import json
from bs4 import BeautifulSoup
import pandas as pd
from lxml.html import parse
from email.mime.text import MIMEText
from email.header    import Header
import re
# Для работы требуется установка расширений pip install atlassian-python-api bs4 lxml html5lib pandas

def analize(table_analyze):    
    #Конфиг
    base_path = os.path.dirname(os.path.abspath(__file__))
    #применяем конфигурацию по умолчанию
    # К сожалению не удалось пока сделать так что бы  применялась конфигурация по умолчанию если заполнены не все поля.
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
    general_dlmtr = cfg.get(section, "delimiter")
    general_col_name  = cfg.get(section, "column_date_of_birth")
    general_mail  = cfg.get(section, "column_mail")
    sendto =[]
    sendwho = []
    fired = []
    admin_notif = []
    admin_notif_mail = []
    bd = []
    today = datetime.date.today()

    table_range=range(len(table_analyze.index))
    #описываем разделитель даты
    pattern=str('%d')+general_dlmtr+str('%m')    
    pattern_mail=r"^[a-zA-Z0-9]{1,100}[@][a-z]{2,6}\.[a-z]{2,4}"
    number_re=re.compile(pattern_mail)
    for element in table_range:
        #print(str(table_analyze[(element):(element+1)][general_mail].values[0]) )
        number_re=re.compile(pattern_mail)
        if ( "уволен" in str(table_analyze[(element):(element+1)]).upper().lower() or 
            "fired"  in str(table_analyze[(element):(element+1)]).upper().lower() or 
            "uvolen" in str(table_analyze[(element):(element+1)]).upper().lower() ):  # ищем уволенных:
            fired += [element]
        elif number_re.findall(str(table_analyze[(element):(element+1)][general_mail].values[0]) ):

            try: # проверяем формат даты.
                dateofbr=str(table_analyze[(element):(element+1)][general_col_name].values[0])
                dempldp = datetime.date(datetime.date.today().year, datetime.datetime.strptime( dateofbr, pattern).month, datetime.datetime.strptime( dateofbr, pattern).day)
                diff = int(today.toordinal()) - int(dempldp.toordinal())
                # Заполняем списки - кого нужно поздравить и кому нужно отправить приглашение
                if -1 < diff < 7 :
                    # Если да то Заполняем список кого поздравить                     
                    sendwho += [element]
                    if diff == 0 :
                        bd += [element]
                else:
                    # иначе заполняем список кому оптравить напоминание
                    sendto += [element]
            except ValueError as err:
                #Сделал задел для логирования  пока  уведомления по сути бесполезное :)
                #print("Ошибка! Не верный формат дня рождению. Формат должен быть в виде День.месяц (например: 26.10). Текст ошибки:", err)
                admin_notif += [element]# отправить сообщение Одмину о  том что нужно исправить наполнение таблицы.
            #Прроверяем на наличие "криво заполненной почты!"
        else:
            admin_notif_mail += [element]
    return sendwho,sendto,fired,admin_notif,bd,admin_notif_mail

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


    if not str(smtp_tls):
        print("tls не задан спользуем подключение без TLS")
    if not str(smtp_from_addr):
        print("В конфиге не указан отправитель. Используем такой же как и логин")
        smtp_from_addr = smtp_login

    msg = MIMEText(body_text, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = smtp_from_addr
    msg['To'] = to_addr    
    server = smtplib.SMTP(smtp_host, smtp_port)  
    #server.set_debuglevel(1)      
    if smtp_tls == "yes":
        server.starttls()    
    server.login(smtp_login, smtp_password)
    server.sendmail(msg['From'], to_addr, msg.as_string())
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
    general_col_name  = cfg.get(section, "column_date_of_birth")
    # Подключение к конфлюенсе
    confluence = Confluence(
        url=confluence_url,
        username=confluence_user,
        password=confluence_passwd)
    content1 = confluence.get_page_by_id(confluence_pageid,expand="body.storage")
    ##Первая колонка  это порядковый номер -  используем ее как индекс index_col=0
    ##Заголовок в первой строке - ее тоже не учитываем header=0
    ##
    df_list = pd.read_html(content1['body']['storage']['value'], header=0,index_col=0, na_values=['No Acquirer'],converters={general_col_name:str})
    table=df_list[0]
    table.index.name = "Number"
    return table

#=====================================================================================
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
general_date_of_birth = cfg.get(section, "column_date_of_birth")
general_admin_mail = cfg.get(section, "admin_mail")


# Получаем данные из Конфлюенсе
confluence_get_page()
table=confluence_get_page()
# анализируем данные 
analize(table)
sendwho,sendto,fired,admin_notif,bd,admin_notif_mail=analize(table)

#Осуществляем рассылку 
birthday_name=[]
birthday_date=[]
if sendwho and sendto:    
    #print("Кого поздравляем:")    
    for send1 in range(len(sendwho)):

        birthday_name+= [str(table[int(sendwho[send1]):(int(sendwho[send1])+1)][general_full_name].values[0])]
        birthday_date+= [str(table[int(sendwho[send1]):(int(sendwho[send1])+1)][general_date_of_birth].values[0])]
    #print(birthday_name,birthday_date)
    #print("Кому отправляем: ")
    for send1 in range(len(sendto)):
        #print(str(table[int(sendto[send1]):(int(sendto[send1])+1)]["FN"].values[0]),":[",sendto[send1],"]")
        to_name = str(table[int(sendto[send1]):(int(sendto[send1])+1)][general_full_name].values[0])
        msg = "Уважаемый "+ str(to_name) + "!\n"
        msg += "Скоро одному или нескольким нашим сотрудникам будет день рождения! Не забудьте поздравить!\n"
        msg += "Наши именниники:\n"
        for i in range(len(birthday_name)):
            #print(birthday_name[i])
            msg += str(birthday_name[i])+" - "+str(birthday_date[i])+"\n"
        #print(msg)
        subject = str('У кого то скоро ДР не забудьте поздравить')
        #print(subject)
        to = str(table[int(sendto[send1]):(int(sendto[send1])+1)][general_column_mail].values[0])       
        #print(to)
        send_email(subject, to, msg)

#else:
#     print(" Некого поздравлять или  некому отправлять поздравляения")

#Сделал задел для логирования - но т.к. пока его нет отключаю
#if fired:
    #print("Уволен, уведомления не оптравляем и не анализируем: ")
#    for send1 in range(len(fired)):
        #print(str(table[(int(fired[send1])-1):int(fired[send1])]["FN"].values[0]),":[",fired[send1],"]")
#else:
#    print("уволенных нет")    


msg =""
problem_user_mail = ""
problem_user_date = ""
if admin_notif:
    #print("У пользователей не верно заполнен поле дата")
    msg +="У пользователей: \n"
    for send1 in range(len(admin_notif)):
        problem_user_date = (str(table[int(admin_notif[send1]):(int(admin_notif[send1])+1)][general_full_name].values[0]))
        #print(problem_user_date)
        msg += problem_user_date + "\n"
    msg +="Не верно заполнено поле даты рождения, для корректной работы рассылки пожалуйста заполните поле даты дня рождения. \n"
if admin_notif_mail:
    #print("У пользователей не верно заполнен поле почта")
    msg +="У пользователя: \n"
    for send1 in range(len(admin_notif_mail)):
        problem_user_mail = (str(table[int(admin_notif_mail[send1]):(int(admin_notif_mail[send1])+1)][general_full_name].values[0]))
        #print(problem_user)
        msg +=str(problem_user_mail) + "\n"
        #print(msg)
    msg +="Не верно заполнено поле почта, для корректной работы рассылки пожалуйста заполните поле почта \n"
if admin_notif or admin_notif_mail:
    subject = "У пользователей не верно заполнены данные"
    send_email(subject, general_admin_mail, msg)
    

        #general_column_mail