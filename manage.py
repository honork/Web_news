from flask import Flask
# 导入扩展flask-script
from flask_script import Manager

# 导入配置对象
from config import Config

app = Flask(__name__)
# 使用配置对象
app.config.from_object(Config)



# 实例化管理器对象
manage = Manager(app)


@app.route('/')
def index():
    return 'index'





if __name__ == '__main__':
    # app.run(debug=True)
    manage.run()