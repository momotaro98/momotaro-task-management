# -*- coding: utf-8 -*-

from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask.ext.script import Manager
from flask.ext.wtf import Form
from wtforms import StringField, SelectField, HiddenField, BooleanField, SubmitField, validators
from flask.ext.mail import Mail
from flask.ext.mail import Message
import sys
import logging
import datetime

app = Flask(__name__)

app.config.update(dict(
    DEBUG = True,
    SECRET_KEY = 'hard to guess string',
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_SSL = False,
    MAIL_USERNAME = 'ochatarodev98@gmail.com',
    MAIL_PASSWORD = 'ochaochaoishii9898',
))
manager = Manager(app)
mail = Mail(app)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

class TaskInputForm(Form):
    task_title = StringField('タスク名: ')
    hour = SelectField('時間', choices=[(i, i) for i in range(0, 6)])
    min_list = [0, 1, 3] + [i for i in range(5, 60 ,5)]
    minute = SelectField('分', choices=[(i, i) for i in min_list])
    submit = SubmitField('設定!')

class DoneForm(Form):
    submit = SubmitField('DONE!')
    '''
    Booleanではvalueを渡せない？ため失敗
    send_mail_or_not = BooleanField(
            label='実行結果をメールする',
            validators=[validators.Required()],
            default=False,
            )
    '''
    send_mail_or_not = SelectField(
            '実行結果をメールしますか:',
            choices=[('no', 'いいえ'), ('yes', 'はい')],
            )
    mail_address = StringField('送信先メールアドレス')
    Hours = HiddenField('')
    Minutes = HiddenField('')
    remained_time = HiddenField('')
    serial_passed_time = HiddenField('')

@app.route('/')
def setting_page():
    form = TaskInputForm()
    is_task_title = False
    is_set_time = False
    return render_template('setting.html',
                            form=form,
                            is_task_title=is_task_title,
                            is_set_time=is_set_time,
                            )

@app.route('/todo', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        task_title = request.form["task_title"]
        hour = request.form["hour"]
        minute = request.form["minute"]
        set_time = 3600 * int(hour) + 60 * int(minute)

        session["task_title"] = task_title
        session["set_time"] = set_time

        if not task_title or not set_time:
            is_task_title = True
            is_set_time = True
            if task_title:
                is_task_title = False
            if set_time:
                is_set_time = False
            form = TaskInputForm()
            return render_template('setting.html',
                                    form=form,
                                    is_task_title=is_task_title,
                                    is_set_time=is_set_time,
                                    )

        form = DoneForm()
        return render_template('index.html',
                                form=form,
                                task_title=task_title,
                                set_time=set_time,
                                )
    return redirect(url_for('setting_page'))

@app.route('/done', methods=['POST', 'GET'])
def done_page():
    if request.method == 'POST':
        task_title = session["task_title"]
        set_time = session["set_time"]
        """
        task_title = request.form["task_title"]
        set_time = int(request.form["set_time"]) # 設定時間
        """
        start_hour = int(request.form["Hours"]) # 開始時間 時
        start_minute = int(request.form["Minutes"]) # 開始時間 分
        remained_time = int(request.form["remained_time"]) # 残り時間
        serial_passed_time = -1 * int(request.form["serial_passed_time"]) # 経過時間

        send_mail_or_not = True if request.form["send_mail_or_not"]=='yes' else False
        mail_address = request.form["mail_address"]
        mail_success_flag = True

        done_datetime = datetime.datetime.now()
        set_hour = set_time // 3600
        set_minute = (set_time % 3600) // 60
        serial_passed_hour = serial_passed_time // 3600
        serial_passed_minute = (serial_passed_time % 3600) // 60

        over_time = serial_passed_time - set_time
        over_hour = over_time // 3600
        over_minute = (over_time % 3600) // 60

        ''' Mail Sending '''
        if send_mail_or_not:
            msg = Message(
                    '{0} @TaskDoApp #TaskDoApp'.format(task_title),
                    sender = 'ochatarodev98@gmail.com',
                    recipients = [mail_address],
                    )

            ### Make Mail Body List Start ###
            body_list = []
            # タスク名
            body_list.append("<h2>タスク名: {0}</h2>".format(task_title))
            # 日付
            body_list.append("<h2>実行日: {0}年{1}月{2}日</h2>".format(\
                                                                 done_datetime.year,
                                                                 done_datetime.month,
                                                                 done_datetime.day,
                                                               ))
            # 設定時間
            if set_hour and set_minute:
                body_list.append("<h2>設定時間: {0}時間{1}分</h2>".format(set_hour, set_minute))
            elif set_hour:
                body_list.append("<h2>設定時間: {0}時間</h2>".format(set_hour))
            elif set_minute:
                body_list.append("<h2>設定時間: {0}分</h2>".format(set_minute))
            # 開始時刻
            body_list.append("<h2>開始時刻: {0}:{1:0>2}</h2>".format(start_hour, start_minute))
            # 終了時刻
            body_list.append("<h2>終了時刻: {0}:{1:0>2}</h2>".format(done_datetime.hour,
                                                                   done_datetime.minute,
                                                                   ))
            # 実行時間
            if serial_passed_hour:
                body_list.append("<h2>実行時間: {0}時間{1}分</h2>".format(serial_passed_hour,
                                                                       serial_passed_minute,
                                                                       ))
            else:
                body_list.append("<h2>実行時間: {0}分</h2>".format(serial_passed_minute))
            # 超過時間
            if over_time>0:
                if over_hour and over_minute:
                    body_list.append("<h2>超過時間: {0}時間{1}分</h2>".format(over_hour,
                                                                          over_minute,
                                                                          ))
                elif set_hour:
                    body_list.append("<h2>超過時間: {0}時間</h2>".format(over_hour))
                elif set_minute:
                    body_list.append("<h2>超過時間: {0}分</h2>".format(over_minute))
            else:
                body_list.append("<h2>設定時間内に実行完了!</h2>")

            body_list.append('This mail was sent by <a href="http://ancient-reaches-5759.herokuapp.com/">Task Do App</a>')

            # Make Mail Body
            # msg.body = "\n".join(body_list)
            msg.html = "\n".join(body_list)

            # Send Mail
            try:
                with app.app_context():
                    mail.send(msg)
            except:
                mail_success_flag = False

        return render_template('done.html',
                            done_datetime=done_datetime,
                            task_title=task_title,
                            set_hour=set_hour,
                            set_minute=set_minute,
                            start_hour=start_hour,
                            start_minute=start_minute,
                            serial_passed_hour=serial_passed_hour,
                            serial_passed_minute=serial_passed_minute,
                            over_time=over_time,
                            over_hour=over_hour,
                            over_minute=over_minute,
                            send_mail_or_not=send_mail_or_not,
                            mail_success_flag=mail_success_flag,
                            mail_address=mail_address,
                            )

    return redirect(url_for('setting_page'))

if __name__ == '__main__':
    manager.run()
    # app.run(host='127.0.0.1')
