from flask import request, render_template, session, redirect, url_for, current_app, abort, flash
from .. import db
from ..models import User, Task, Goal
from . import main
from flask.ext.wtf import Form
from wtforms import StringField, SelectField, HiddenField, BooleanField, SubmitField, validators
from flask.ext.login import current_user, login_required
import datetime

from . import main
from ..email import send_email


class TaskInputForm(Form):
    task_title = StringField('タスク名: ')
    hour = SelectField('時間', choices=[(i, i) for i in range(0, 6)])
    min_list = [0, 1, 3] + [i for i in range(5, 60 ,5)]
    minute = SelectField('分', choices=[(i, i) for i in min_list])
    submit = SubmitField('設定!')
    goal_name = SelectField('目標')

class TaskEditForm(Form):
    task_name = StringField('タスク名: ')
    serial_passed_hour = SelectField('実行時間(時間)', coerce=int, choices=[(i, i) for i in range(0, 6)])
    min_list = [0, 1, 3] + [i for i in range(5, 60 ,5)]
    serial_passed_minute = SelectField('実行時間(分)', coerce=int, choices=[(i, i) for i in min_list])
    goal_name = SelectField('目標')
    submit = SubmitField('変更！')

    @classmethod
    def dynamize_goal_select(cls):
        form = TaskEditForm()
        if current_user.is_authenticated:
            user = User.query.filter_by(username=current_user.username).first_or_404()
            goal_select = [''] + [ goal.goal_name \
                        for goal in user.goals.order_by(Goal.timestamp.desc()) ]
            form.goal_name.choices = [ (g, g) for g in goal_select]
        else:
            form.goal_name.choices = [('', '')]
        return form

class DoneForm(Form):
    submit = SubmitField('DONE!')
    send_mail_or_not = SelectField(
            '実行結果をメールしますか:',
            choices=[('no', 'いいえ'), ('yes', 'はい')],
            default='no',
            )
    Hours = HiddenField('')
    Minutes = HiddenField('')
    remained_time = HiddenField('')
    serial_passed_time = HiddenField('')


class GoalForm(Form):
    goal_name = StringField('目標')
    submit = SubmitField('送信！')


@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@main.route('/', methods=['POST', 'GET'])
def setting_page():
    form = TaskInputForm()
    if current_user.is_authenticated:
        user = User.query.filter_by(username=current_user.username).first_or_404()
        goal_select = [''] + [ goal.goal_name \
                    for goal in user.goals.order_by(Goal.timestamp.desc()) ]
        form.goal_name.choices = [ (g, g) for g in goal_select]
    else:
        form.goal_name.choices = [('', '')]
    # タスク設定
    not_task_title = False
    not_set_time = False

    if request.method == 'POST':
        task_title = request.form["task_title"]
        hour = request.form["hour"]
        minute = request.form["minute"]
        goal_name = request.form["goal_name"]
        set_time = 3600 * int(hour) + 60 * int(minute)
        # session
        session["task_title"] = task_title
        session["set_time"] = set_time
        session["goal_name"] = goal_name

        if not task_title and not set_time:
            not_task_title = True
            not_set_time = True
        elif not task_title:
            not_task_title = True
        elif not set_time:
            not_set_time = True
        else:
            return redirect(url_for('.index'))

    if 'task_title' in session and 'set_time' in session:
        set_task_title = session['task_title']
    else:
        set_task_title = ''

    return render_template('setting.html',
                            form=form,
                            not_task_title=not_task_title,
                            not_set_time=not_set_time,
                            set_task_title=set_task_title,
                            name=session.get('name', 'guest'),
                            known=session.get('known', False),
                            )

@main.route('/todo')
def index():
    if not 'task_title' in session or not 'set_time' in session:
        return redirect(url_for('.setting_page'))

    form = DoneForm()
    return render_template('index.html',
                            form=form,
                            task_title=session["task_title"],
                            set_time=session["set_time"],
                            )

@main.route('/done', methods=['POST', 'GET'])
def done_page():
    if request.method == 'POST':
        task_title = session["task_title"] # タスク名
        set_time = session["set_time"] # 設定時間
        goal_name = session["goal_name"] # 目標名

        start_hour = int(request.form["Hours"]) # 開始時間 時
        start_minute = int(request.form["Minutes"]) # 開始時間 分
        remained_time = int(request.form["remained_time"]) # 残り時間
        serial_passed_time = -1 * int(request.form["serial_passed_time"]) # 経過時間

        send_mail_or_not = True if request.form["send_mail_or_not"]=='yes' else False
        mail_success_flag = True

        done_datetime = datetime.datetime.now()
        set_hour = set_time // 3600
        set_minute = (set_time % 3600) // 60
        serial_passed_hour = serial_passed_time // 3600
        serial_passed_minute = (serial_passed_time % 3600) // 60

        over_time = serial_passed_time - set_time
        over_hour = over_time // 3600
        over_minute = (over_time % 3600) // 60


        if current_user.is_authenticated:
            # 目標rowオブジェクト取得
            goal = current_user.goals.filter_by(goal_name=goal_name).first()

            # 実行タスク登録
            task = Task(task_title=task_title,
                        set_time=set_time,
                        remained_time=remained_time,
                        serial_passed_time=serial_passed_time,
                        user=current_user._get_current_object(),
                        goal=goal,
                        )
            db.session.add(task)

        # Mail Sending
        send_to_mail_address = current_user.email if current_user.is_authenticated else ''

        if send_mail_or_not:
            if send_to_mail_address:
                try:
                    # 関数send_emailの引数
                    # def send_email(to, subject, template, **kwargs):
                    send_email(send_to_mail_address, task_title, 'mail/task_done',
                                    task_title=task_title,
                                    done_datetime=done_datetime,
                                    set_hour=set_hour,
                                    set_minute=set_minute,
                                    start_hour=start_hour,
                                    start_minute=start_minute,
                                    serial_passed_hour=serial_passed_hour,
                                    serial_passed_minute=serial_passed_minute,
                                    over_time=over_time,
                                    over_hour=over_hour,
                                    over_minute=over_minute,
                                    )
                except:
                    mail_success_flag = False
            else:
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
                            mail_address=send_to_mail_address,
                            )

    return redirect(url_for('.setting_page'))


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.tasks.order_by(Task.timestamp.desc()).paginate(
        page, per_page=current_app.config['APP_POSTS_PER_PAGE'],
        error_out=False)
    tasks = pagination.items

    # localtsは国・地域ごとに異なる変数とする
    # 日本はhours=9
    localts = ( task.timestamp + datetime.timedelta(hours=9) for task in tasks )
    goals = ( Goal.query.filter_by(id=task.goal_id).first() for task in tasks )
    return render_template('user.html',
                           user=user,
                           tasks_localts_goals=zip(tasks, localts, goals),
                           pagination=pagination)


@main.route('/setgoal', methods=['POST', 'GET'])
def set_goal():
    form = GoalForm()
    if form.validate_on_submit():
        goal = Goal(goal_name=form.goal_name.data,
                    user=current_user._get_current_object())
        db.session.add(goal)
        db.session.commit()
        flash('Your goal, "{0}", has been set'.format(form.goal_name.data))
        return redirect(url_for('main.set_goal'))
    goals = current_user.goals.order_by(Goal.timestamp.desc())
    return render_template('set_goal.html', form=form, goals=goals)


@main.route('/editgoal/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_goal(id):
    goal = Goal.query.get_or_404(id)
    if current_user != goal.user:
        abort(403)

    form = GoalForm()
    if form.validate_on_submit():
        goal.goal_name = form.goal_name.data
        db.session.add(goal)
        db.session.commit()
        flash('Your goal name was fixed'.format(form.goal_name.data))
        return redirect(url_for('.set_goal'))
    form.goal_name.data = goal.goal_name
    return render_template('edit_goal.html', form=form, id=id)


@main.route('/deletegoal/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_goal(id):
    goal = Goal.query.get_or_404(id)
    if current_user != goal.user:
        abort(403)

    if request.method == 'POST':
        '''If the goal has no binded tasks,
        `goal.tasks.first()` returns None type object'''
        if not goal.tasks.first(): # 関連するタスクが無いとき
            Goal.query.filter_by(id=id).delete()
            flash('The goal was deleted.')
        else:
            flash('削除しようとした目標に関連づけられたタスクが存在するため削除できません')
        return redirect(url_for('.set_goal'))

    return redirect(url_for('.set_goal'))


@main.route('/edittask/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    task = Task.query.get_or_404(id)
    if current_user != task.user:
        abort(403)

    form = TaskEditForm.dynamize_goal_select()
    if form.validate_on_submit():
        task.task_title = form.task_name.data
        task.serial_passed_time = int(form.serial_passed_hour.data) * 3600 +\
                        int(form.serial_passed_minute.data) * 60
        # 空の目標の場合NoneTypeがgoalに入る
        # TODO: データベース上ではNULLになっている？
        task.goal = current_user.goals.filter_by(goal_name=form.goal_name.data).first()
        db.session.add(task)
        flash('The task was changed.')
        return redirect(url_for('.user', username=current_user.username))

    # 既設定表示
    form.task_name.data = task.task_title
    form.serial_passed_hour.data = task.serial_passed_time // 3600
    form.serial_passed_minute.data = (task.serial_passed_time%3600)//60

    # 空の目標のとき対応
    try:
        form.goal_name.data = Goal.query.filter_by(id=task.goal_id).first().goal_name
    except AttributeError:
        form.goal_name.data = ''
    return render_template('edit_task.html', form=form, id=id)


@main.route('/addtask', methods=['GET', 'POST'])
@login_required
def addtask():
    form = TaskEditForm.dynamize_goal_select()

    if form.validate_on_submit():
        task = Task(\
                task_title=form.task_name.data,
                set_time=0,
                remained_time=0,
                serial_passed_time = int(form.serial_passed_hour.data) * 3600 +\
                    int(form.serial_passed_minute.data) * 60,
                user=current_user._get_current_object(),
                goal=current_user.goals.filter_by(goal_name=form.goal_name.data).first()
                   )
        db.session.add(task)
        flash('Your done task ,{0}, was added.'.format(form.task_name.data))
        return redirect(url_for('.user', username=current_user.username))

    return render_template('task_add.html', form=form)


@main.route('/deletetask/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if current_user != task.user:
        abort(403)

    if request.method == 'POST':
        Task.query.filter_by(id=id).delete()
        flash('The task was deleted.')
        return redirect(url_for('.user', username=current_user.username))

    return redirect(url_for('.user', username=current_user.username))
