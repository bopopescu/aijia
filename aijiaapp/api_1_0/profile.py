# -----------------------------------------------
# -*- coding: utf-8 -*-
# @Time    : 2020/5/6 10:39
# @Author  : miri_chen
# @Email   : 825689698@qq.com
# @File    : profile.py
# -----------------------------------------------
from flask import request, jsonify, current_app, g, session

from aijiaapp import db
from aijiaapp.constants import QINIU_URL_DOMAIN
from aijiaapp.models import User
from aijiaapp.utils.commons import login_required
from aijiaapp.utils.image_storage import storage
from aijiaapp.utils.response_code import RET
from . import api


@api.route("/users/avatar", methods=["POST"])
@login_required
def set_user_avatar():
    """设置用户头像"""
    # 装饰器的代码已经将user_id保存到g对象中
    user_id = g.user_id

    # 获取图片
    image_file = request.files.get("avatar")

    if image_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg="未上传图片")

    image_data = image_file.read()

    # 上传图片到七牛
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, error="上传图片失败")

    # 保存图片信息到数据库中
    try:
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片信息失败")

    avatar_url = QINIU_URL_DOMAIN + file_name
    return jsonify(errno=RET.OK, errmsg="保存成功", data={"avatar_url": avatar_url})


@api.route("/user")
@login_required
def get_user_profile():
    """用户信息"""
    user_id = g.user_id

    # 查询数据
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询出错")

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="无效操作")

    return jsonify(errno=RET.OK, errmsg="保存成功", data=user.to_dict())


@api.route("/users/name", methods=["PUT"])
@login_required
def change_user_name():
    """修改用户名"""
    user_id = g.user_id

    req_dict = request.get_json()
    name = req_dict.get("name")

    if name is None:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断名字是否重复

    # 保存名字到数据库中
    try:
        User.query.filter_by(id=user_id).update({"name": name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="修改用户名失败")

    session["name"] = name
    return jsonify(errno=RET.OK, errmsg="保存成功", data={"name": name})


@api.route("/users/auth", methods=["GET", "POST"])
@login_required
def get_user_auth():
    """实名信息"""
    user_id = g.user_id

    if request.method == "GET":
        # 查询数据
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库查询出错")

        if user is None:
            return jsonify(errno=RET.NODATA, errmsg="无效操作")

        return jsonify(errno=RET.OK, errmsg="查询成功", data=user.auth_to_dict())

    if request.method == "POST":
        # 获取请求参数
        req_dict = request.get_json()
        real_name = req_dict.get("real_name")
        id_card = req_dict.get("id_card")

        if not all([real_name, id_card]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

        # 查询并修改数据
        try:
            User.query.filter_by(id=user_id, real_name=None, id_card=None) \
                .update({"id_card": id_card, "real_name": real_name})
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="保存实名数据失败")

        return jsonify(errno=RET.OK, errmsg="保存成功")

