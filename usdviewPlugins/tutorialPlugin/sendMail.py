import os
import json
import smtplib
import tempfile
import platform

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from time import strftime, gmtime

from pxr.Usdviewq.qt import QtWidgets


USERNAME = os.getenv('USERNAME')
if platform.system() == 'Windows':
    CONFIG_PATH = 'C:/Users/{0}/Documents/sendmail.json'.format(USERNAME)
else:
    CONFIG_PATH = '/usr/{0}/sendmail.json'.format(USERNAME)    


class MailInfo():
    def __init__(self, usdviewApi, from_addr='', to_addr='', subject_text='', body_text='', image_type=''):
        self._usdviewApi = usdviewApi
        self.sender = from_addr
        self.sendee = to_addr
        self.subject = subject_text
        self.body = body_text
        self.imagetype = image_type

        self.generate_default_info()

    def read_mail_info_config(self):
        if not os.path.exists(CONFIG_PATH):
            return None

        with open(CONFIG_PATH, 'r') as file:
            mail_info = json.load(file)
            self.sender = mail_info['sender']
            self.sendee = mail_info['sendee']

    def write_mail_info_config(self):
        if not os.path.exists(CONFIG_PATH):
            return None
        
        with open(CONFIG_PATH, 'w') as file:
            json.dump({'sender': self.sender, 'sendee': self.sendee}, file)


    def valid_mail_info(self):
        return (self.sender and 
                self.sendee and 
                self.subject and 
                self.body and 
                self.imagetype)

    def generate_default_info(self):
        current_time = strftime('%b %d, %Y, %H:%m:%S', gmtime())

        self.read_mail_info_config()
        self.subject = 'Usdview Screenshot'
        self.body = '''
            Usdview screenshot, taken {0}
            ----------------------------------------
            File: {1}
            Selected Prim Paths: {2}
            Current Frame: {3}
            Complexity: : {4}
            Camera Info: {5}
            ----------------------------------------
            '''.format(current_time, 
                       str(self._usdviewApi.stageIdentifier),
                       ','.join(map(str, self._usdviewApi.selectedPrims)),
                       str(self._usdviewApi.frame),
                       str(self._usdviewApi.dataModel.viewSettings.complexity),
                       str(self._usdviewApi.currentGfCamera))
        

class SendMailDialog(QtWidgets.QDialog):
    def __init__(self, mail_info, parent=None):
        super(SendMailDialog, self).__init__(parent)

        self.email_info = mail_info

        self.setWindowTitle('Send Screenshot...')

        self.sender_label = QtWidgets.QLabel('From: ')
        self.sendee_label = QtWidgets.QLabel('To: ')
        self.subject_label = QtWidgets.QLabel('Subject: ')
        self.body_label = QtWidgets.QLabel('Message: ')

        self.sender_field = QtWidgets.QLineEdit()
        self.sendee_field = QtWidgets.QLineEdit()
        self.subject_field = QtWidgets.QLineEdit()
        self.body_field = QtWidgets.QTextEdit()

        self.cancel_button = QtWidgets.QPushButton('Cancel')
        self.accept_button = QtWidgets.QPushButton('Send')

        self.screen_capture_combobox = QtWidgets.QComboBox()
        self.screen_capture_combobox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.screen_capture_combobox.addItems(['Window', 'Viewport'])

        self.setMinimumWidth(parent.size().width()/2)

        self._generate_layout()
        self._connect_buttons()
        self._set_init_value()

        self.exec_()

    def _set_init_value(self):
        self.sender_field.setText(self.email_info.sender)
        self.sendee_field.setText(self.email_info.sendee)
        self.subject_field.setText(self.email_info.subject)
        self.body_field.setText(self.email_info.body)

    def _fill_data_from_dialog(self):
        self.email_info.sender = self.sender_field.text()
        self.email_info.sendee = self.sendee_field.text()
        self.email_info.subject = self.subject_field.text()
        self.email_info.body = self.body_field.toPlainText()
        self.email_info.imagetype = self.screen_capture_combobox.currentText()
        self.email_info.write_mail_info_config()
        self.close()

    def _generate_layout(self):
        sender_layout = QtWidgets.QHBoxLayout()
        sender_layout.addWidget(self.sender_field)
        
        sendee_layout = QtWidgets.QHBoxLayout()
        sendee_layout.addWidget(self.sendee_field)

        subject_layout = QtWidgets.QHBoxLayout()
        subject_layout.addWidget(self.subject_field)

        body_layout = QtWidgets.QHBoxLayout()
        body_layout.addWidget(self.body_field)

        field_layout = QtWidgets.QVBoxLayout()
        field_layout.addWidget(self.sender_label)
        field_layout.addLayout(sender_layout)
        field_layout.addWidget(self.sendee_label)
        field_layout.addLayout(sendee_layout)
        field_layout.addWidget(self.subject_label)
        field_layout.addLayout(subject_layout)
        field_layout.addWidget(self.body_label)
        field_layout.addLayout(body_layout)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(0.5)
        button_layout.addWidget(self.screen_capture_combobox)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.accept_button)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(field_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _connect_buttons(self):
        self.cancel_button.clicked.connect(self.close)
        self.accept_button.clicked.connect(self._fill_data_from_dialog)
    

def send_mail(usdviewApi):
    with tempfile.NamedTemporaryFile(suffix='.jpeg', delete=False) as tempimagefile:
        mail_info = MailInfo(usdviewApi)
        sendmail_dialog = SendMailDialog(mail_info, parent=usdviewApi.qMainWindow)
        
        if not mail_info.valid_mail_info():
            return None
        
        imagedata = None    
        if mail_info.imagetype == 'Window':
            imagedata = usdviewApi.GrabWindowShot()
        else:
            imagedata = usdviewApi.GrabViewportShot()
            
        if not imagedata or not imagedata.save(tempimagefile.name):
            return None
        
        message = MIMEMultipart()
        message['Subject'] = mail_info.subject
        message['From'] = (mail_info.sender.strip() if 
                           mail_info.sender.strip() else None)
        message['To'] = ','.join(addr.strip() for addr in mail_info.sendee.split(',') if 
                                 addr.strip())
        
        if (not message['From']) or len(message['To'].split(',')) == 0:
            return None
        
        message.attach(MIMEText(mail_info.body))
        message.attach(MIMEImage(tempimagefile.read(), _subtype='jpeg'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        #TODO: Input your gmail app password
        server.login(message['From'], '')

        server.sendmail(message['From'],
                        message['To'].split(','),
                        message.as_string())
        
        server.quit()
        mail_info.write_mail_info_config()
    os.remove(tempimagefile.name)