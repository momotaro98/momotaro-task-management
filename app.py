# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/todo', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        todo_name = request.form["task_title"]
        hour = request.form["hour"]
        minute = request.form["minute"]
        set_time = 3600 * int(hour) + 60 * int(minute)
        return render_template('index.html',
                        todo_name=todo_name,
                          set_time=set_time)
    return render_template('setting.html')
@app.route('/')
def setting():
    return render_template('setting.html')

if __name__ == '__main__':
    app.debug = True
    app.run(host='127.0.0.1')
