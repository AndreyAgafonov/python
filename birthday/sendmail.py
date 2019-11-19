#!/usr/bin/env python3

import os
import smtplib
import sys
import configparser
#from configparser import ConfigParser
 

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

    print(smtp_host, smtp_port ,smtp_tls, smtp_login, smtp_password, smtp_from_addr)
    if not str(smtp_tls):
        print("tls na zadan")
    if not str(smtp_from_addr):
        print("отправитель такой же как  логин")
    

    BODY = "\r\n".join((
        "С днем рождения коллега"
        #<center>
        #<img alt="Кот Саймона" 
        #src="https://www.google.com/url?sa=i&source=images&cd=&cad=rja&uact=8&ved=2ahUKEwiqm-nf_-7lAhWOfZoKHY5mAOAQjRx6BAgBEAQ&url=%2Furl%3Fsa%3Di%26source%3Dimages%26cd%3D%26ved%3D2ahUKEwjbjrvX_-7lAhXkx6YKHTHoBSwQjRx6BAgBEAQ%26url%3Dhttps%253A%252F%252Fwww.pinterest.com%252Fpin%252F421719952598337553%252F%26psig%3DAOvVaw2ZWi5mJy0oX9RYx0VZbHyp%26ust%3D1574002831482749&psig=AOvVaw2ZWi5mJy0oX9RYx0VZbHyp&ust=1574002831482749">
        #</center>''
    ))
    
    #sys.exit(1)
    server = smtplib.SMTP(smtp_host, smtp_port)
        
    if smtp_tls == "yes":
        server.starttls()
    
    #server.login(smtp_login, smtp_password)
    server.login("python@cloud16.ru", "eholot22")
    server.sendmail(smtp_from_addr, to_addr, body_text)
    server.quit()

subject = "Test email from Python"
to_addr = "aagafonov@inbox.ru"    
body_text = "Python rules them all!"
send_email(subject, to_addr, body_text)

print("!")
print("!")
print("!")
print("!")
print("!")
print("!")
print("!")