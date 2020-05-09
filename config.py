# -----------------------------------------------
# -*- coding: utf-8 -*-
# @Time    : 2020/4/29 10:34
# @Author  : miri_chen
# @Email   : 825689698@qq.com
# @File    : config.py
# -----------------------------------------------
import redis


class Config(object):
    """"""

    SECRET_KEY = 'Ji2dw0IWJFij320jc0)(U#jdij'

    # 数据库
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:123456@127.0.0.1:3306/aijia?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # flask session配置
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True  # 对cookie中session_id进行隐藏处理
    PERMANENT_SESSION_LIFETIME = 86400  # session数据的有效期


class DevelopConfig(Config):
    """"""

    DEBUG = True


class ProductionConfig(Config):
    """"""

    DEBUG = False


config_map = {
    'develop': DevelopConfig,
    'production': ProductionConfig
}
