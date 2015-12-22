# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)

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
        set_time = int(request.form["set_time"])
        Hours = int(request.form["Hours"])
        Minutes = int(request.form["Minutes"])
        remained_time = int(request.form["remained_time"])
        serial_passed_time = int(request.form["serial_passed_time"])

        set_hour = set_time // 3600
        set_minute = (set_time % 3600) // 60
        if set_hour and set_minute:
            set_time_output = "{0} 時間 {1} 分".format(set_hour, set_minute)
        elif set_hour:
            set_time_output = "{0} 時間".format(set_hour)
        else:
            set_time_output = "{0} 分".format(set_minute)

        start_time = "{0} 時 {1} 分".format(Hours, Minutes)
    return render_template('done.html',
                        set_time_output=set_time_output,
                        start_time=start_time,
                        remained_time=remained_time,
                        serial_passed_time=serial_passed_time)

if __name__ == '__main__':
    app.debug = True
    app.run(host='127.0.0.1')
