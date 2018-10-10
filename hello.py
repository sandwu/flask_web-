from datetime import datetime
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_moment import Moment

"""
__name__意思是当前文件(hello.py)的名字，Flask传入该参数表示
hello.py所在的文件夹为项目的根路径，后续的templates(模版文件夹)、
static(静态文件夹都将会在该根路径下查找)
"""
app = Flask(__name__)

"""
实例化对象：将Bootstrap和Moment类实例化，传入的app表示
当前应用程序。
"""
bootstrap = Bootstrap(app)
moment = Moment(app)

#类似于@app.route('/')，起到当浏览器访问的地址在路由上找不到时，
#服务器端返回404(状态码，表示找不到该网址)，此时则由该路由接收
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#同404的逻辑，500状态码
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

#路由逻辑，定位到127.0.0.1:5000/
@app.route('/')
def index():
    # datetime模块下的utcnow方法能够返回当前的utc时间(即格林威治时间，标准时间。)
    # 各地区再依照时区的不同，来获得对应当地的时间，这里通过format('LLL')实现
    return render_template('index.html',
                           current_time=datetime.utcnow())

#<name>尖括号表示动态路由，可以将变量存入，可以根据url的不同，定位到不同的网址
@app.route('/user/<int:name>')
def user(name):
    # 通过render_template将数据传给前端，实现前后端的交互
    return render_template('user.html', name=name)


if __name__ == '__main__':
    app.run(debug=True)