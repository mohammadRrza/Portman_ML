import os
import smtplib, ssl
import sys
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders


class Mail():
    from_addr = ''
    to_addr = ''
    msg_body = ''
    msg_subject = ''
    attachment = ''

    @staticmethod
    def Send_Mail(mail_info):
        try:
            msg = MIMEMultipart()
            msg['From'] = mail_info.from_addr
            msg['To'] = mail_info.to_addr
            msg['Subject'] = mail_info.msg_subject
            body = mail_info.msg_body
            msg.attach(MIMEText(body, 'plain'))
            text = msg.as_string()
            server = smtplib.SMTP('mail.pishgaman.net', 587)
            server.connect('mail.pishgaman.net', 587)
            server.starttls()
            server.ehlo()
            server.login("oss-problems@pishgaman.net", "Oss_9r0@123")
            server.sendmail(mail_info.from_addr, mail_info.to_addr, text)

            return 'class method called', mail_info
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(str(e) + '////' + str(exc_tb.tb_lineno))

    @staticmethod
    def Send_Mail_With_Attachment(mail_info):
        try:
            msg = MIMEMultipart()
            msg['From'] = mail_info.from_addr
            msg['To'] = mail_info.to_addr
            msg['Subject'] = mail_info.msg_subject
            body = mail_info.msg_body
            msg.attach(MIMEText(body, 'plain'))
            filename = "/opt/portmanv3/portman_web/users/document.pdf"
            with open(filename, "rb") as attachment:
                file = MIMEBase("application", "octet-stream")
                file.set_payload(attachment.read())
            encoders.encode_base64(file)
            file.add_header(
                "Content-Disposition",
                "attachment; filename= document.pdf",
            )
            msg.attach(file)
            text = msg.as_string()
            server = smtplib.SMTP('mail.pishgaman.net', 587)
            server.connect('mail.pishgaman.net', 587)
            server.starttls()
            server.ehlo()
            server.login("oss-problems@pishgaman.net", "Oss_9r0@123")
            server.sendmail(mail_info.from_addr, mail_info.to_addr, text)

            return 'class method called', mail_info
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(str(e) + '////' + str(exc_tb.tb_lineno))


class Ticket():
    Queue = ''
    Requestor = ''
    Subject = ''
    Cc = ''
    AdminCc = ''
    Owner = ''
    Status = ''
    Priority = ''
    InitialPriority = ''
    FinalPriority = ''
    TimeEstimated = ''
    Starts = ''
    Due = ''
    Text = ''
