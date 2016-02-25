from flask import request, render_template, session, redirect, url_for, current_app
from .. import db
from ..models import User
from . import main
from flask.ext.wtf import Form
from wtforms import StringField, SelectField, HiddenField, BooleanField, SubmitField, validators
from flask.ext.mail import Message
import datetime

from . import main
from .. import mail


####### forms.py 予定部分 start
class NameForm(Form):
    name = StringField('What is your name?', validators=[validators.Required()])
    submit = SubmitField('Submit')

class TaskInputForm(Form):
    task_title = StringField('タスク名: ')
    hour = SelectField('時間', choices=[(i, i) for i in range(0, 6)])
    min_list = [0, 1, 3] + [i for i in range(5, 60 ,5)]
    minute = SelectField('分', choices=[(i, i) for i in min_list])
    submit = SubmitField('設定!')

class DoneForm(Form):
    submit = SubmitField('DONE!')
    send_mail_or_not = SelectField(
            '実行結果をメールしますか:',
            choices=[('no', 'いいえ'), ('yes', 'はい')],
            )
    mail_address = StringField('送信先メールアドレス')
    Hours = HiddenField('')
    Minutes = HiddenField('')
    remained_time = HiddenField('')
    serial_passed_time = HiddenField('')
####### forms.py 予定部分 end


@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@main.route('/', methods=['POST', 'GET'])
def setting_page():
    login_form = NameForm()
    form = TaskInputForm()

    # ログイン機能
    if login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.name.data).first()
        if user is None:
            user = User(username=login_form.name.data) # rowインスタンスを作成
            # db.session.add(user)
            session['known'] = False
        else:
            session['known'] = True
        session['name'] = login_form.name.data
        return redirect(url_for('.setting_page'))


    # タスク設定
    not_task_title = False
    not_set_time = False

    if request.method == 'POST':
        task_title = request.form["task_title"]
        hour = request.form["hour"]
        minute = request.form["minute"]
        set_time = 3600 * int(hour) + 60 * int(minute)
        # session
        session["task_title"] = task_title
        session["set_time"] = set_time

        if not task_title and not set_time:
            not_task_title = True
            not_set_time = True
        elif not task_title:
            not_task_title = True
        elif not set_time:
            not_set_time = True
        else:
            return redirect(url_for('.index'))

    if 'task_title' in session and 'set_time' in session:
        set_task_title = session['task_title']
    else:
        set_task_title = ''

    return render_template('setting.html',
                            login_form=login_form,
                            form=form,
                            not_task_title=not_task_title,
                            not_set_time=not_set_time,
                            set_task_title=set_task_title,
                            name=session.get('name', 'guest'),
                            known=session.get('known', False),
                            )

@main.route('/todo')
def index():
    if not 'task_title' in session or not 'set_time' in session:
        return redirect(url_for('.setting_page'))

    form = DoneForm()
    return render_template('index.html',
                            form=form,
                            task_title=session["task_title"],
                            set_time=session["set_time"],
                            )

@main.route('/done', methods=['POST', 'GET'])
def done_page():
    if request.method == 'POST':
        task_title = session["task_title"] # タスク名
        set_time = session["set_time"] # 設定時間

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
                app = current_app._get_current_object()
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

    return redirect(url_for('.setting_page'))
