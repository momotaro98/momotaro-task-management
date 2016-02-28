import unittest
import datetime
from flask import current_app
from app import create_app, db
from app.email import send_email

class SendEmailTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_done_task_send_email(self):
        '''タスク実行結果のメールが正しく送信できるかのテスト
        '''
        SEND_TO = 'ochatarodev98@gmail.com'

        task_title = 'test task'
        done_datetime = datetime.datetime.now()
        set_time = 500
        start_hour = 13
        start_minute = 55
        serial_passed_time = 1000
        set_hour = set_time // 3600
        set_minute = (set_time % 3600) // 60
        serial_passed_hour = serial_passed_time // 3600
        serial_passed_minute = (serial_passed_time % 3600) // 60
        over_time = serial_passed_time - set_time
        over_hour = over_time // 3600
        over_minute = (over_time % 3600) // 60

        send_email(SEND_TO, task_title, 'mail/task_done',
                        task_title=task_title,
                        done_datetime=done_datetime,
                        set_hour=set_hour,
                        set_minute=set_minute,
                        start_hour=start_hour,
                        start_minute=start_minute,
                        serial_passed_hour=serial_passed_hour,
                        serial_passed_minute=serial_passed_minute,
                        over_time=over_time,
                        over_hour=over_hour,
                        over_minute=over_minute,
                        )
