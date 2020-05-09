# -----------------------------------------------
# -*- coding: utf-8 -*-
# @Time    : 2020/4/30 11:42
# @Author  : miri_chen
# @Email   : 825689698@qq.com
# @File    : constans.py
# -----------------------------------------------

# 图片验证码有效期，单位：秒
IMAGE_CODE_REDIS_EXPIRES = 180

# 短信验证码有效期，单位：秒
SMS_CODE_REDIS_EXPIRES = 300

# 发送短信验证码间隔，单位：秒
SEND_SMS_CODE_INTERVAL = 60

# 登录错误尝试次数
LOGIN_ERROR_MAX_TIMES = 5

# 登录错误禁止时间，单位：秒
LOGIN_ERROR_FORBID_TIMES = 600

# 七牛空间域名
QINIU_URL_DOMAIN = "http://q9w1z8m9y.bkt.clouddn.com/"

# 城区信息的保存时间，单位：秒
AREA_INFO_REDIS_CACHE_EXPIRES = 7200

# 首页显示房屋数量
HOME_PAGE_MAX_HOUSES = 5

# 首页缓存时间
HOME_PAGE_DATA_REDIS_EXPIRES = 7200

# 房屋详情页缓存时间
HOUSE_DETAIL_REDIS_EXPIRE_SECOND = 7200

# 房屋详情评价展示条数
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 30

# 房屋列表每页数据容量
HOUSE_LIST_PAGE_CAPACITY = 2
