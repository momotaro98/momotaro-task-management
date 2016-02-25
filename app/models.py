from werkzeug.security import generate_password_hash, check_password_hash
from app import db

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
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        # passwordにはアクセスできないよとうエラーを発生させる
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password): # パスワードが設定されるとき(代入されるとき)に実行する
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {0}>'.format(self.username)
