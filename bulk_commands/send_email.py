if __name__ == '__main__':
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import ssl

    # Set Up SMTP Server
    smtp_server = 'mail.pishgaman.net'
    smtp_port = 587

    # Create the Emai
    from_email = 'm.mohammadian@pishgaman.net'
    to_email = 'm.pourgharib@pishgaman.net'
    subject = 'Texsxt Exmxaxil'
    body = 'This is a test exmxaxixl sxexnxt from Alaki.'

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Send the Email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print("Failed to send email: !!")