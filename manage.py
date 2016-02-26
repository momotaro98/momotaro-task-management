# -*- coding: utf-8 -*-
#!/usr/bin/env python

import sys
import os
import logging
from app import create_app, db
from app.models import User, Role
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
# ↑os.getenv(環境変数)は環境変数が無いときはNonTypeClassが返る
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


if __name__ == '__main__':
    manager.run()
