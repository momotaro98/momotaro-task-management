from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask.ext.login import UserMixin
from . import db, login_manager

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
    # backrefを記述することで、Userモデルにdb.relationship('role')が記述されたことと同じになる
    # TODO lazyはRoleに関係するアイテムがロードされるタイミングを指定するものらしい
    # が、よく理解できていない

    def __repr__(self):
        return '<Role {0}>'.format(self.name)


# class User(db.Model):
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    goals = db.relationship('Goal', backref='user', lazy='dynamic')

    # propertyでself.passwordを管理する
    @property
    def password(self):
        # passwordにはアクセスできないよとうエラーを発生させる
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password): # パスワードが設定されるとき(代入されるとき)に実行する
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # SerializerはトークンとIDを紐付けるために必要なオブジェクトという認識である
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token) # 与えられたトークンでシリアライザ-からロードができるか
            # トークンとIDは一対一のハッシュ関係
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True # rowインスタンスのconfirmedカラムをTrueにする
        db.session.add(self) # confirmedされたことをデータベースへ更新する
        return True

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def __repr__(self):
        return '<User {0}>'.format(self.username)


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    task_title = db.Column(db.String(128))
    set_time = db.Column(db.Integer) # 設定時間 秒数
    remained_time = db.Column(db.Integer) # 残り時間 秒数
    serial_passed_time = db.Column(db.Integer) # 経過時間 秒数
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'))


class Goal(db.Model):
    __tablename__ = 'goals'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    goal_name = db.Column(db.String(64))
    achieved = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tasks = db.relationship('Task', backref='goal', lazy='dynamic')

    # TODO: need to use property?
    def get_goal_name(self):
        return str(self.goal_name)

    # TODO: need to use property?
    def set_achieved(self):
        self.achieved = True

    # TODO: need to use property?
    def restore_tonot_achived(self):
        self.achieved = False


# 何かしらの処理の度にセッションにおけるユーザを再ロードするためのコールバック関数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
