# -----------------------------------------------
# -*- coding: utf-8 -*-
# @Time    : 2020/4/30 10:59
# @Author  : miri_chen
# @Email   : 825689698@qq.com
# @File    : verify_code.py
# -----------------------------------------------
import random

from flask import current_app, jsonify, make_response, request

from aijiaapp import redis_store
from aijiaapp.constants import IMAGE_CODE_REDIS_EXPIRES, SMS_CODE_REDIS_EXPIRES, SEND_SMS_CODE_INTERVAL
from aijiaapp.libs.sms import yunqixun
from aijiaapp.models import User
from aijiaapp.utils.captcha.captcha import captcha
from aijiaapp.utils.response_code import RET
from . import api


@api.route("/image_codes/<image_code_id>")
def get_image_code(image_code_id):
    """
    获取图片验证码
    : params: image_code_id 验证码编号
    ：return: 验证码图片 异常：返回JSON
    """

    # 业务逻辑处理
    # 1.生成验证码图片
    name, text, image_data = captcha.generate_captcha()

    # 2.将真实值和编号保存到redis,设置有效期
    # redis 字符串 列表 哈希 集合set 有序集合zset
    # "image_codes":{"编号:"真实值",...} 哈希 hset("image_codes", "id1", "abc")
    # 使用哈希有效期不方便
    # 单条维护记录选用字符串 "image_code_编号":"真实值"
    try:
        # redis_store.set("image_code_{}".format(image_code_id), text)
        # redis_store.expire("image_code_{}".format(image_code_id), )
        redis_store.setex("image_code_{}".format(image_code_id), IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片验证码信息失败")

    # 返回值
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp


# GET /api/v1.0/sms_codes/<mobile>?image_code=xxxx&image_code_id=xxxx
@api.route("/sms_codes/<re(r'1[356789]\\d{9}'):mobile>")
def get_sms_code(mobile):
    """短信验证码"""

    # 提取参数
    image_code = request.args.get("image_code")
    image_code_id = request.args.get("image_code_id")
    print(image_code)

    # 检验参数
    if not all([image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 业务处理
    # 从redis取出图片验证码数据，对比
    try:
        real_image_code = redis_store.get("image_code_{}".format(image_code_id))
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="redis数据库异常")

    # 判断是否过期
    if real_image_code is None:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码失效")

    # 删除图片验证码，防止撞库
    try:
        redis_store.delete("image_code_{}".format(image_code_id))
    except Exception as e:
        current_app.logger.error(e)

    # 判断是否一致，忽略大小写
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误")

    # 手机号60s验证
    try:
        send_flag = redis_store.get("send_sms_code_{}".format(mobile))
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag is not None:
            return jsonify(errno=RET.REQERR, errmsg="请求过于频繁，请60秒后重试")

    # 判断手机号是否已注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            # 表示手机号已存在
            return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")

    # 生成短信验证码并保存
    sms_code = "%06d" % random.randint(0, 999999)
    try:
        redis_store.setex("image_code_{}".format(mobile), SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存发送的手机号记录，防止用户60s多次操作
        redis_store.setex("send_sms_code_{}".format(mobile),SEND_SMS_CODE_INTERVAL, 1)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存短信验证码异常")

    # 发送短信
    text = "您的短信验证码是{},有效期{}分钟".format(sms_code, SMS_CODE_REDIS_EXPIRES / 60)
    try:
        result = yunqixun.send_single_msg(mobile, text)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="发送异常")

    # # 使用celery异步发送短信
    # send_msg.delay(mobile, text)

    if result.get('code') == "0":
        return jsonify(errno=RET.OK, errmsg="发送成功")
    else:
        return jsonify(errno=RET.THIRDERR, errmsg="发送失败")
    # text = "您的短信验证码是{},有效期{}分钟".format(sms_code, SMS_CODE_REDIS_EXPIRES / 60)
    # print(text)
    # return jsonify(errno=RET.OK, errmsg="发送成功")
