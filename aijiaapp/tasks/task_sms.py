# -----------------------------------------------
# -*- coding: utf-8 -*-
# @Time    : 2020/5/6 16:32
# @Author  : miri_chen
# @Email   : 825689698@qq.com
# @File    : task_sms.py
# -----------------------------------------------
from celery import Celery

from aijiaapp.libs.sms import yunqixun

celery_app = Celery("ihome", broker="redis://127.0.0.1:6379/1")


@celery_app.task
def send_msg(to, text):
    """"""
    yunqixun.send_single_msg(to, text)
