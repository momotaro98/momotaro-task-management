from flask import request, render_template, session, redirect, url_for, current_app, abort
from .. import db
from ..models import User, Task
from . import main
from flask.ext.wtf import Form
from wtforms import StringField, SelectField, HiddenField, BooleanField, SubmitField, validators
from flask.ext.login import current_user
import datetime

from . import main
from ..email import send_email # emailディレクトリは作成予定


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
            default='no',
            )
    Hours = HiddenField('')
    Minutes = HiddenField('')
    remained_time = HiddenField('')
    serial_passed_time = HiddenField('')


@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@main.route('/', methods=['POST', 'GET'])
def setting_page():
    form = TaskInputForm()
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
        mail_success_flag = True

        done_datetime = datetime.datetime.now()
        set_hour = set_time // 3600
        set_minute = (set_time % 3600) // 60
        serial_passed_hour = serial_passed_time // 3600
        serial_passed_minute = (serial_passed_time % 3600) // 60

        over_time = serial_passed_time - set_time
        over_hour = over_time // 3600
        over_minute = (over_time % 3600) // 60

        if current_user.is_authenticated:
            # Done Task Registration
            task = Task(task_title=task_title,
                        set_time=set_time,
                        remained_time=remained_time,
                        serial_passed_time=serial_passed_time,
                        user=current_user._get_current_object())
            db.session.add(task)

        # Mail Sending
        send_to_mail_address = current_user.email if current_user.is_authenticated else ''

        if send_mail_or_not:
            if send_to_mail_address:
                try:
                    # 関数send_emailの引数
                    # def send_email(to, subject, template, **kwargs):
                    send_email(send_to_mail_address, task_title, 'mail/task_done',
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
                except:
                    mail_success_flag = False
            else:
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
                            mail_address=send_to_mail_address,
                            )

    return redirect(url_for('.setting_page'))


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    tasks = user.tasks.order_by(Task.timestamp.desc()).all()
    return render_template('user.html', user=user, tasks=tasks)
