import unittest
import time
from app import create_app, db
from app.models import User


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # 通常はクライアントがリクエストを送ると自動的に
        # コンテキストが生成されるが
        # テストでは手動で
        # create_app('testing').app_context().push()
        # を実行してテスト用ユーザのコンテキストを生成する

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


    def test_password_setter(self):
        '''パスワードハッシュが生成されるかのテスト'''
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        '''パスワードにアクセスできないようになっているかのテスト
        with self.assertRaises(AttributeError):内の処理のとき
        AttributeErrorが正しく生成されるかを確認する
        '''
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password # AttributeErrorが発生する

    def test_password_verification(self):
        '''Userモデルのverify_passwordメソッドが正しく動作するかのテスト
        '''
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        '''同等のパスワードでもハッシュ値が異なるかのテスト
        '''
        u = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_valid_confirmation_token(self):
        '''メール送信でのトークン認証が正しく行われるかのテスト
        '''
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token() # このトークンを含んだURLをメールで送信する
        self.assertTrue(u.confirm(token)) # 認証チェック

    def test_invalid_confirmation_token(self):
        '''異なったトークンで認証を正しくはじくかのテスト
        '''
        u1 = User(password='cat')
        u2 = User(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm(token))

    def test_expired_confirmation_token(self):
        '''itsdangerousのSerializerにおける時間制限機能(expiration)が正しく動作するかのテスト
        '''
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(u.confirm(token))
