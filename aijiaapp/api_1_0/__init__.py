# -----------------------------------------------
# -*- coding: utf-8 -*-
# @Time    : 2020/4/29 11:05
# @Author  : miri_chen
# @Email   : 825689698@qq.com
# @File    : __init__.py.py
# -----------------------------------------------
from flask import Blueprint

api = Blueprint('api_1.0', __name__)

from . import passport, verify_code, profile, houses, orders
