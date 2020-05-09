# -----------------------------------------------
# -*- coding: utf-8 -*-
# @Time    : 2020/4/30 10:12
# @Author  : miri_chen
# @Email   : 825689698@qq.com
# @File    : commons.py
# -----------------------------------------------
from werkzeug.routing import BaseConverter
from flask import session, jsonify, g
from aijiaapp.utils.response_code import RET
import functools


# 定义正则转换器
class ReConverter(BaseConverter):
    """正则转换器"""

    def __init__(self, url_map, regex):
        # 调用父类初始化方法
        super(ReConverter, self).__init__(url_map)
        # 保存正则表达式
        self.regex = regex


# 登录验证装饰器
def login_required(view_func):

    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        # 判断用户的登录状态
        user_id = session.get("user_id")

        # 如果是登录的，执行视图函数，如果未登录，但会未登录信息
        if user_id is not None:
            # 将user_id保存到g对象中，在视图函数中可以通过g对象获取保存数据
            g.user_id = user_id
            return view_func(*args, **kwargs)
        else:
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    return wrapper
