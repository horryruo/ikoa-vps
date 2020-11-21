import os
import subprocess
import re
import time
from threading import Lock,Thread
from collections import deque
import requests
from flask import Flask, request, redirect, url_for, flash, render_template, jsonify
from werkzeug.urls import url_parse
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, ValidationError, Optional, Regexp
from flask_apscheduler import APScheduler
from flask_socketio import SocketIO
from loadini import read_config


conf_data = read_config()
down_time = int(conf_data['down_time'])
#print(conf_data)

APP = Flask(__name__)
APP.config.update(
    SECRET_KEY=conf_data['secret_key'],
    ADMINUSER=conf_data['adminUser'],
    ADMINPASSWORD=conf_data['adminPassword'],
    APPLICATIONMODE='noproduction'
)


REGEXNUMSTRING = r"^[a-zA-Z]{1,10}\-[0-9]{1,10}(?:,[a-zA-Z]{1,10}\-[0-9]{1,10})*$"
REGEXCIDSTRING = r"^[\w]{3,20}(?:,[\w]{3,20})*$"
REGEXMGSSTRING = r"^(?:\d{3})?[a-zA-Z]{2,6}-\d{3,5}(?:,(?:\d{3})?[a-zA-Z]{2,6}-\d{3,5})*$"
REGEXPIDSTRING = r"^[\w]{3,25}(?:,[\w]{3,25})*$"
REGEXNUM = re.compile(REGEXNUMSTRING)
REGEXCID = re.compile(REGEXCIDSTRING, flags=re.ASCII)
REGEXMGS = re.compile(REGEXMGSSTRING)
REGEXPID = re.compile(REGEXPIDSTRING)


LOGIN_MANAGER = LoginManager()
LOGIN_MANAGER.login_view = "login"
LOGIN_MANAGER.init_app(APP)

SCHEDULER = APScheduler()
SCHEDULER.init_app(APP)
SCHEDULER.start()

ASYNC_MODE = 'eventlet'
THREAD_LOCK = Lock()
SOCKETIO = SocketIO(async_mode=ASYNC_MODE)
SOCKETIO.init_app(APP,cors_allowed_origins="*")


class Task:
    def __init__(self):
        self.task_id = 0
        self.task_index = 0
        self.task_queue = deque([])
        self.pushlog_finished = False
        self.background_thread = None
        self.task_status = 0

class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id = user_id
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class DownloadForm(FlaskForm):
    id_type = SelectField('id_type',
                          choices=[('cid', 'cid'), ('pid', 'pid'), ('num', 'num'), ('mgs', 'mgs')])
    id_value = StringField('id_value', validators=[DataRequired()])
    id_tag = StringField('id_tag',
                         validators=[Optional(), Regexp(r"^[\w]{1,15}$", message="Invalid tag!")])
    submit = SubmitField('Submit')

    def validate_id_value(self, field):
        if self.id_type.data == "cid":
            match_cid = REGEXCID.match(field.data or "")
            if not match_cid:
                raise ValidationError('Invalid cid format!')
            return match_cid
        if self.id_type.data == "pid":
            match_pid = REGEXPID.match(field.data or "")
            if not match_pid:
                raise ValidationError('Invalid pid format!')
            return match_pid
        if self.id_type.data == "num":
            match_num = REGEXNUM.match(field.data or "")
            if not match_num:
                raise ValidationError('Invalid num format!')
            return match_num
        if self.id_type.data == "mgs":
            match_mgs = REGEXMGS.match(field.data or "")
            if not match_mgs:
                raise ValidationError('Invalid mgs format!')
            return match_mgs


TASK = Task()
ADMIN = User(0, APP.config['ADMINUSER'], APP.config['ADMINPASSWORD'])


@SCHEDULER.task('interval', id='dyno', minutes=14, misfire_grace_time=3600)
def prevent_idiling():
    url = '0.0.0.0:{}'.format(conf_data['runport'])
    ts_status = subprocess.check_output(
        "awk 'NR == 1 { print $7 }' | ts", shell=True, universal_newlines=True)
    if ts_status.rstrip() == '[run=1/1]':
        requests.get(url)


@APP.before_request
def before_request():
    if not request.is_secure and APP.config['APPLICATIONMODE'] == 'production':
        url = request.url.replace("http://", "https://", 1)
        code = 301
        return redirect(url, code=code)


@APP.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        if ADMIN.username == form.username.data and ADMIN.check_password(form.password.data):
            login_user(ADMIN)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
        flash('Invalid username or password!')
        return redirect(url_for('login'))
    return render_template('login.html', form=form)


def add_ts_task(id_value, id_type, id_tag):
    TASK.task_index += 1
    TASK.task_id = 0
    id_list = id_value.split(',')
    TASK.task_status = 1
    #list_group = [id_list[n:n + down_time] for n in range(0, len(id_list), down_time)]
    #list_group = [id_list[:]]
    #for item in list_group:
    command = 'bash task.sh {} {} {} {} {} {} {} {} {} | ts'.format(','.join(id_list), id_type, TASK.task_id, conf_data['destination_path'], conf_data['log_path'],conf_data['drive'],conf_data['monthly_only'],down_time,conf_data['accounts'], id_tag)
    process = subprocess.Popen(command, shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT, universal_newlines=True)
    for line in process.stdout:
        #print(line.strip())
        SOCKETIO.emit('progress', {'data': line.strip()}, namespace='/logging')
        SOCKETIO.sleep(0)
    if process.poll() == 0:
        TASK.task_status = 0
    TASK.task_queue.append(TASK.task_id)
    TASK.task_id += 1


@APP.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = DownloadForm()
    return render_template('index.html', form=form)


@APP.route('/postform', methods=['POST'])
@login_required
def postform():
    form = DownloadForm()
    if form.validate_on_submit():
        if TASK.task_status == 1:
            SOCKETIO.emit('message', {'data': 'error :  task exists'}, namespace='/logging')
            return jsonify({'status': 'error', 'message': form.errors})
        try:
            task_thread = Thread(target=add_ts_task, args=(form.id_value.data, form.id_type.data, form.id_tag.data))
            task_thread.daemon = True
            task_thread.start()
            return jsonify({'status': 'success', 'message': 'task added'})
        except Exception as e:
            SOCKETIO.emit('message', {'data': str(e)}, namespace='/logging')
            return jsonify({'status': 'error', 'message': form.errors})
    return jsonify({'status': 'error', 'message': form.errors})


def push_log():
    pass


@SOCKETIO.on('connect', namespace='/logging')
def connect_handler():
    print('Client connected')


@SOCKETIO.on('disconnect', namespace='/logging')
def disconnect_handler():
    print('Client disconnected')


@SOCKETIO.on('message', namespace='/logging')
def message_handler(message):
    pass


@SOCKETIO.on_error_default
def default_error_handler(error):
    print('An error has occurred: ' + str(error))
    print(request.event['message'])
    print(request.event['args'])


@SOCKETIO.on_error(namespace='/logging')
def logging_error_handler(error):
    print('An error has occurred: ' + str(error))


@APP.errorhandler(404)
def page_not_found(error):
    return "Page not found!"


@LOGIN_MANAGER.user_loader
def load_ser(user_id):
    return ADMIN


if __name__ == '__main__':
    APP.run(debug=True, host='0.0.0.0', port=5000)
    