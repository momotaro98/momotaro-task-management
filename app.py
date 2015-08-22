# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    todo_name = "Make report of physics sciety's class"
    hour = 0
    minute = 30
    second = 15
    set_time = 3600 * hour + 60 * minute + second
    return render_template('index.html',
                    todo_name=todo_name,
                      set_time=set_time)
@app.route('/setting')
def setting():
    return render_template('setting.html')

if __name__ == '__main__':
    app.debug = True
    app.run(host='127.0.0.1')
