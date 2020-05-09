# -----------------------------------------------
# -*- coding: utf-8 -*-
# @Time    : 2020/4/29 10:31
# @Author  : miri_chen
# @Email   : 825689698@qq.com
# @File    : __init__.py.py
# -----------------------------------------------
import logging
from logging.handlers import RotatingFileHandler

import pymysql
import redis
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from aijiaapp.utils.commons import ReConverter
from config import config_map

pymysql.install_as_MySQLdb()

# 数据库
db = SQLAlchemy()

# redis
redis_store = None

# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG)
# 创建日志记录器，指明日志保存路径，每个日志大小，保存上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录格式
formatter = logging.Formatter("%(levelname)s %(filename)s:%(lineno)d %(message)s")
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象(flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    """
    创建flask的应用对象
    :param config_name: str 配置模式的名字 "develop" "product"
    :return:
    """

    app = Flask(__name__)

    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    # 用app初始化db
    db.init_app(app)

    # 初始化redis
    global redis_store
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, decode_responses=True)

    # 利用flask_session,将session数据保存到redis中
    Session(app)

    # csrf 防护
    CSRFProtect(app)

    # 为flask添加自定义转换器
    app.url_map.converters['re'] = ReConverter

    # 注册蓝图
    from aijiaapp import api_1_0
    app.register_blueprint(api_1_0.api, url_prefix="/api/v1.0")

    from aijiaapp import web_html
    app.register_blueprint(web_html.html)

    return app


