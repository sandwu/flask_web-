import os
from threading import Thread

from flask import Flask, render_template, session, redirect, flash, url_for
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate, MigrateCommand
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_script import Manager
from flask_mail import Mail, Message
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import pymysql

"""
__name__意思是当前文件(hello.py)的名字，Flask传入该参数表示
hello.py所在的文件夹为项目的根路径，后续的templates(模版文件夹)、
static(静态文件夹都将会在该根路径下查找)
"""
app = Flask(__name__)

#4章：定义加密参数，加密参数的配置是主要为了加密session。
#4章：这个字符串随便定义，定义越长，以及字符串内容庞杂则加密效果越好
app.config['SECRET_KEY'] = 'fafafafjkjooqkopwkqjigroiwg'

"""
5章：
basedir：获取项目的动态路径，通过os.path模块，获得当前的绝对路径，__file__返回hello.py文件名，
os.path.dirname则返回hello.py的文件夹名，通过abspath获得hello.py所在的绝对路径
配置数据库config，'SQLALCHEMY_DATABASE_URI'指定数据库链接为sqlite
'SQLALCHEMY_TRACK_MODIFICATIONS'字面意思是追踪修改,False即表示不追踪数据库的修改记录，设置的目的是不设置
会报错，是flask-sqlAlchemy强制要求设置，设置为False，因为数据库变更无须追踪；
'SQLALCHEMY_COMMIT_ON_TEARDOWN'这句命令作用很大，表示数据库如果修改数据了，会自动提交数据。
"""
basedir = os.path.abspath(os.path.dirname(__file__))
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
# 用mysql来实现，依据书本46页可知配置如下，我的用户名是root，密码是123456，host(域名)是127.0.0.1(表示本机)，数据库名是flask_web
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@127.0.0.1/flask_web'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

"""
实例化对象：将Bootstrap和Moment类实例化，传入的app表示当前应用程序。
"""
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

#邮件设置
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '邮箱账号'
app.config['MAIL_PASSWORD'] = '邮箱密码'
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_MAIL_SENDER'] = '邮箱账号'
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN')

#必须定义在config下面！
mail = Mail(app)

#配置上下文，发送邮件
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

#定义发送的函数send_mail
def send_email(to, subject, template, **kwargs):
    #Message封装了多个默认参数，这里传入主题、发件人、收件人就行
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    #定义发送的内容
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    #通过另一个线程来发送邮件
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


#类似于@app.route('/')，起到当浏览器访问的地址在路由上找不到时，
#服务器端返回404(状态码，表示找不到该网址)，此时则由该路由接收
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#同404的逻辑，500状态码
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

#<name>尖括号表示动态路由，可以将变量存入，可以根据url的不同，定位到不同的网址
@app.route('/user/<int:name>')
def user(name):
    # 通过render_template将数据传给前端，实现前后端的交互
    return render_template('user.html', name=name)

# 4章：继承至FlaskForm表单，是flask_wtf封装的表单模块，这边看源码知道Form已经被废除
class NameForm(FlaskForm):
    # 定义文本字段表单，等同于html定义属性为type='text'的<input>，
    # Required已经被废除，更改为DataRequired，表示表单内容不能为空
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')

#4章：路由定义methods，表示该路由可接收GET或POST请求，如果不定义，则默认只接收GET请求
#4章：GET和POST的区别是，前者适用于向浏览器获取数据(如页面刷新)，后者适用于向浏览器发送数据(如账号密码登录)
@app.route('/', methods=['GET', 'POST'])
def index():
    #实例话NameForm类，此时每次填写即表示单独一个实例
    form = NameForm()
    #判断是否提交，如果提交了，则将提交的数据赋值到name变量，传给模版
    if form.validate_on_submit():
        #过滤查询username==输入框输入的数据，并查询出第一条
        user = User.query.filter_by(username=form.name.data).first()
        #判断user是否有数据，有的话说明该名字之前已经记录到数据库，没有的话则将数据录入数据库
        if user is None:
            # 将数据录入数据库
            user = User(username=form.name.data)
            # 录入后要提交，但因为我们定义了app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True，所以即使不提交问题也不大
            db.session.add(user)
            db.session.commit()
            #给session配上标志位，False则说明user为空，此时刷新语句为please meet you，反之相反
            session['known'] = False
            if app.config['FLASKY_ADMIN']:
                send_email(app.config['FLASKY_ADMIN'], 'New User',
                           'mail/new_user', user=user)
        else:
            session['known'] = True
    #渲染模版，同时传回数据给模版，name=name第一个name表示变量name，即前端可以通过name变量获得值，
    #后一个name则表示数据，再这里就是form.name.data
    return render_template('index.html', form=form, name=session.get('name'),
                           known=session.get('known', False))

#定义Role类，一个类对应一个数据表
class Role(db.Model):
    # 表名为roles，不定义的话，SQLAlchemy会默认定义。
    __tablename__ = 'roles'
    # 依次定义id、name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    #1对多：relationship表示链接的外键关系，第一个参数是链接外键所在的类名
    #backref==>back reference即回引，即可以通过一个表获得关系表的数据，
    # 举例：Role.users通过Role获得users的数据(下方定义)，User.role(下方定义)获得role数据
    # lazy=dynamic表示动态加载，意思是当Role.users时不会立马返回结果(好处是不用立马查询数据库，利于性能优化)，
    users = db.relationship('User', backref='role', lazy='dynamic')
    # 定义__repr__便于在操作数据库时可以在控制台查询对象
    def __repr__(self):
        return '<Role %r>' % self.name

# 这个了解下就好，后续的数据库都是通过数据库迁移来完成数据库的录入和修改
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username

if __name__ == '__main__':
    manager.run()