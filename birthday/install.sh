#!/bin/bash

workdir=`dirname $0`

yum update -y
yum install python3 -y
pip3 install atlassian-python-api bs4 lxml html5lib pandas
if ! [ -d /opt/sender ] ; # Проверяем наличие папки
        then 
        mkdir -p /opt/sender
fi

cp $workdir/sendmail.py /opt/sender/
cp $workdir/*.conf /opt/sender/
chmod +x /opt/sender/sendmail.py
cp $workdir/mailsender.service /etc/systemd/system/mailsender.service
cp $workdir/mailsender.timer /etc/systemd/system/mailsender.timer
systemctl daemon-reload
systemctl enable mailsender.service
systemctl enable mailsender.timer
systemctl start mailsender.timer
systemctl start mailsender.service
