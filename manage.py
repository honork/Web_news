from flask import session
# 导入扩展flask-script
from flask_script import Manager
# 导入扩展flask-migrate
from flask_migrate import Migrate, MigrateCommand
# 导入info模块创建的程序实例app
from info import create_app, db
# 导入models
from info import models

# 调用工厂方法，获取app
from info.models import User

app = create_app('development')

# 实例化管理器对象
manage = Manager(app)
# 使用迁移框架
Migrate(app, db)
# 通过管理器对象集成迁移命令
manage.add_command('db', MigrateCommand)


# 创建管理员账户
# 在script扩展，自定义脚本命令，以自定义函数的形式实现创建管理员用户
# 以终端启动命令的形式实现；
# 在终端使用命令：python manage.py create_supperuser -n admin -p 123456
@manage.option('-n', '-name', dest='name')
@manage.option('-p', '-password', dest='password')
def create_supperuser(name, password):
    if not all([name, password]):
        print('参数缺失')
    user = User()
    user.nick_name = name
    user.mobile = name
    user.password = password
    user.is_admin = True
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
    print('管理员创建成功')


if __name__ == '__main__':
    # 输出路由映射
    print(app.url_map)
    manage.run()
