import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..config import settings

MAIL_DEFAULT_FROM = settings.MAIL_SENDER_NAME
MAIL_SERVER = settings.MAIL_SERVER
MAIL_USERNAME = settings.MAIL_USERNAME
MAIL_PASSWORD = settings.MAIL_PASSWORD
MAIL_PORT = settings.MAIL_PORT
MAIL_USE_TLS = settings.MAIL_USE_TLS


class Message:

    def __init__(self, sender=None, recipients=None, subject=None, body=None, html=False):
        self.sender = sender if sender else MAIL_DEFAULT_FROM
        self.recipients = []
        if recipients:
            if type(recipients) == str:
                self.recipients.append(recipients)
            elif type(recipients) in [tuple, list]:
                self.recipients = [recipient for recipient in recipients]
        self.subject = subject
        self.body = body
        self.html = html

    def is_valid(self):
        """
        Just a basic check to ensure all required elements needed to send an email have been set.

        TODO: Define Explicit Exceptions for each attribute.
        """

        if not self.sender:
            raise Exception('Sender not set.')
        if not self.recipients or len(self.recipients) == 0:
            raise Exception('No recipients specified.')
        if not self.subject:
            raise Exception('Email must have a subject.')
        # if not self.body:
        #     raise Exception('Email must contain a body.')
        return True

    def add_recipient(self, recipient):
        self.recipients.append(recipient)


message = Message()


class Mail:
    """
    Class used to send emails.
    """
    def __init__(self, msg=None):
        self.message = msg
        self._server = MAIL_SERVER
        self._port = MAIL_PORT
        self._username = MAIL_USERNAME
        self._password = MAIL_PASSWORD
        self._use_tls = MAIL_USE_TLS
        self._context = ssl.create_default_context()

    def send(self, msg=None) -> bool:
        if msg:
            self.message = msg

        if not self.message:
            raise Exception('Please include the message to be sent.')

        if not isinstance(self.message, Message):
            raise Exception('message must be an instance of Message.')
        try:
            self.message.is_valid()
            pass
        except Exception:
            raise

        # message is clean and good for sending.
        return self._send_mail()

    def _send_mail(self) -> bool:
        msg = MIMEMultipart('alternative')
        part1 = MIMEText(self.message.body if self.message.body else '', 'plain')
        msg.attach(part1)
        if self.message.html:
            part2 = MIMEText(self.message.html, 'html')
            msg.attach(part2)

        msg['Subject'] = self.message.subject
        msg['From'] = f"{self.message.sender}<{self._username}>"

        with smtplib.SMTP(self._server, self._port) as server:

            if self._use_tls:
                server.starttls(context=self._context)
            server.login(self._username, self._password)

            for recipient in self.message.recipients:
                _msg = msg
                _msg['To'] = recipient
                server.sendmail(from_addr=msg['From'], to_addrs=recipient, msg=_msg.as_string().encode('UTF-8'))
            server.quit()

        return True


mail = Mail()
