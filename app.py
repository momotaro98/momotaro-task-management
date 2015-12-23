# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, flash
import sys
import logging
import datetime

app = Flask(__name__)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

@app.route('/')
def setting_page():
    return render_template('setting.html')

@app.route('/todo', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        todo_name = request.form["task_title"]
        hour = request.form["hour"]
        minute = request.form["minute"]
        set_time = 3600 * int(hour) + 60 * int(minute)
        if not todo_name or not set_time:
            return redirect(url_for('setting_page'))
        return render_template('index.html',
                        todo_name=todo_name,
                          set_time=set_time)
    return render_template('setting.html')

@app.route('/done', methods=['POST', 'GET'])
def done_page():
    if request.method == 'POST':
        task_title = request.form["task_title"]
        set_time = int(request.form["set_time"]) # 設定時間
        start_hour = int(request.form["Hours"]) # 開始時間 時
        start_minute = int(request.form["Minutes"]) # 開始時間 分
        remained_time = int(request.form["remained_time"]) # 残り時間
        serial_passed_time = -1 * int(request.form["serial_passed_time"]) # 経過時間

        done_datetime = datetime.datetime.now()
        set_hour = set_time // 3600
        set_minute = (set_time % 3600) // 60
        serial_passed_hour = serial_passed_time // 3600
        serial_passed_minute = (serial_passed_time % 3600) // 60

        over_time = serial_passed_time - set_time
        over_hour = over_time // 3600
        over_minute = (over_time % 3600) // 60

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
                            over_minute=over_minute
                            )

    return render_template('setting.html')

if __name__ == '__main__':
    app.debug = True
    app.run(host='127.0.0.1')
