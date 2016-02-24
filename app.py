# -*- coding: utf-8 -*-

import sys
import os
import logging
import datetime
from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask.ext.script import Manager, Shell
from flask.ext.bootstrap import Bootstrap
from flask.ext.wtf import Form
from wtforms import StringField, SelectField, HiddenField, BooleanField, SubmitField, validators
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.mail import Mail
from flask.ext.mail import Message

####### config.py 予定部分 start
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_SSL = False
    MAIL_USERNAME = 'ochatarodev98@gmail.com'
    MAIL_PASSWORD = 'ochaochaoishii9898'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig,
    #'default': TestingConfig,
    #'default': ProductionConfig,
}
####### config.py 予定部分 end

####### app/__init__.py 予定部分 start
bootstrap = Bootstrap()
mail = Mail()
db = SQLAlchemy()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    db.init_app(app)

    # from .main import main as main_blueprint
    # app.register_blueprint(main_blueprint)

    return app
####### app/__init__.py 予定部分 end


####### manage.py 予定部分 start
app = create_app(os.getenv('FLASK_CONFIG') or 'default') # os.getenv(環境変数)は環境変数が無いときはNonTypeClassが返る
manager = Manager(app)
migrate = Migrate(app, db)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

# コマンドラインで実行する際にいちいちimportしないようにする処理
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("db", MigrateCommand)


@manager.command # `python app.py test` で実行できるようになるデコレータ
def test():
    """Run the unit test."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
####### manage.py 予定部分 end


####### app/models.py 予定部分 start
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
    # backrefを記述することで、Userモデルにdb.relationship('role')が記述されたことと同じになる
    # lazyはRoleに関係するアイテムがロードされるタイミングを指定するものらしい

    def __repr__(self):
        return '<Role {0}>'.format(self.name)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User {0}>'.format(self.username)
####### app/models.py 予定部分 end


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


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/', methods=['POST', 'GET'])
def setting_page():
    login_form = NameForm()
    form = TaskInputForm()

    # ログイン機能
    if login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.name.data).first()
        if user is None:
            user = User(username=login_form.name.data) # rowインスタンスを作成
            db.session.add(user)
            session['known'] = False
        else:
            session['known'] = True
        session['name'] = login_form.name.data
        return redirect(url_for('setting_page'))


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
            return redirect(url_for('index'))

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

@app.route('/todo')
def index():
    if not 'task_title' in session or not 'set_time' in session:
        return redirect(url_for('setting_page'))

    form = DoneForm()
    return render_template('index.html',
                            form=form,
                            task_title=session["task_title"],
                            set_time=session["set_time"],
                            )

@app.route('/done', methods=['POST', 'GET'])
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
