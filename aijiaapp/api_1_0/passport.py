# -----------------------------------------------
# -*- coding: utf-8 -*-
# @Time    : 2020/4/30 15:42
# @Author  : miri_chen
# @Email   : 825689698@qq.com
# @File    : passport.py
# -----------------------------------------------
import re

from flask import request, jsonify, current_app, session
from sqlalchemy.exc import IntegrityError

from aijiaapp import redis_store, db, constants
from aijiaapp.models import User
from aijiaapp.utils.commons import login_required
from aijiaapp.utils.response_code import RET
from . import api


@api.route("/users", methods=["POST"])
def register():
    """
    注册
    :params: 手机号、短信验证码、密码、确认密码
    参数格式:json
    """
    # 提取数据
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    sms_code = req_dict.get("sms_code")
    password = req_dict.get("password")
    password2 = req_dict.get("password2")

    # 检验数据
    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断手机号格式
    if not re.match(r'1[35789]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")

    # 判断密码
    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg="两次密码不一致")

    # 从redis取出数据
    try:
        real_sms_code = redis_store.get("image_code_{}".format(mobile))
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="redis数据库读取短信验证码异常")

    # 判断过期
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码失效")

    # 验证码对比
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码错误")

    # 判断手机号是否已注册
    # try:
    #     user = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    # else:
    #     if user is not None:
    #         # 表示手机号已存在
    #         return jsonify(errno=RET.DATAEXIST, errmsg="手机号已注册")

    # 保存数据到数据库中
    user = User(name=mobile, mobile=mobile)
    user.password = password

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        # 表示手机号重复
        return jsonify(errno=RET.DATAEXIST, errmsg="手机号已注册")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="操作数据库异常")

    # 保存登录状态到session
    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id

    return jsonify(errno=RET.OK, errmsg="注册成功")


@api.route("/sessions", methods=["POST"])
def login():
    """登录"""

    # 提取数据
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    password = req_dict.get("password")

    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断登录次数
    user_ip = request.remote_addr
    try:
        access_nums = redis_store.get("access_nums_{}".format(user_ip))
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_nums is not None and int(access_nums) > constants.LOGIN_ERROR_MAX_TIMES:
            return jsonify(errno=RET.REQERR, errmsg="错误次数过多，请稍后再试")

    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")
    else:
        if user is None or not user.check_password(password):
            try:
                redis_store.incr("access_nums_{}".format(user_ip))
                redis_store.expire("access_nums_{}".format(user_ip), constants.LOGIN_ERROR_FORBID_TIMES)
            except Exception as e:
                current_app.logger.error(e)
            return jsonify(errno=RET.DATAERR, errmsg="用户名或密码错误")

    # 如果验证相同成功，保存登录状态在session中
    session["name"] = user.name
    session["mobile"] = user.mobile
    session["user_id"] = user.id

    return jsonify(errno=RET.OK, errmsg="登录成功")


@api.route("/session", methods=["GET"])
def check_login():
    """检查登录状态"""

    name = session.get("name")
    if name is not None:
        return jsonify(errno=RET.OK, errmsg="true", data={"name": name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg="false")


@login_required
@api.route("session", methods=["DELETE"])
def logout():
    """登出"""
    # csrf_token = session.get("csrf_token")
    session.clear()
    # session["csrf_token"] = csrf_token
    return jsonify(errno=RET.OK, errmsg="登出成功")


