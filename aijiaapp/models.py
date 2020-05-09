# -----------------------------------------------
# -*- coding: utf-8 -*-
# @Time    : 2020/4/29 12:02
# @Author  : miri_chen
# @Email   : 825689698@qq.com
# @File    : models.py
# -----------------------------------------------
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

from aijiaapp import constants
from . import db


class BaseModel(object):
    """模型基类，为每个模型补充创建时间与更新时间"""

    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class User(BaseModel, db.Model):
    """用户"""

    __tablename__ = "ih_user_profile"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    mobile = db.Column(db.String(11), nullable=False)
    real_name = db.Column(db.String(32))
    id_card = db.Column(db.String(18))
    avatar_url = db.Column(db.String(128))
    houses = db.relationship('House', backref='user')
    orders = db.relationship('Order', backref='user')

    @property
    def password(self):
        # 读属性的时候被调用
        raise AttributeError("这个属性只能设置，不能读取")

    @password.setter
    def password(self, value):
        """设置属性"""
        self.password_hash = generate_password_hash(value)

    # def generate_password_hash(self, origin_password):
    #     """对密码进行加密"""
    #     self.password_hash = generate_password_hash(origin_password)

    def check_password(self, password):
        """检验密码的正确性"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """将对象转换成字典"""
        user_dict = {
            "user_id": self.id,
            "name": self.name,
            "mobile": self.mobile,
            "avatar": constants.QINIU_URL_DOMAIN + self.avatar_url if self.avatar_url else "",
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        return user_dict

    def auth_to_dict(self):
        """将实名信息转换成字典"""
        auth_dict = {
            "user_id": self.id,
            "real_name": self.real_name,
            "id_card": self.id_card
        }
        return auth_dict


class Area(BaseModel, db.Model):
    """城区"""

    __tablename__ = "ih_area_info"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    houses = db.relationship("House", backref="area")

    def to_dict(self):
        # 将对象装换成字典
        area_dict = {
            "aid": self.id,
            "aname": self.name
        }
        return area_dict


# 房屋设施表，建立房屋与设施的多对多关系
house_facility = db.Table(
    "ih_house_facility",
    db.Column("house_id", db.Integer, db.ForeignKey("ih_house_info.id"), primary_key=True),  # 房屋编号
    db.Column("facility_id", db.Integer, db.ForeignKey("ih_facility_info.id"), primary_key=True)  # 设施编号
)


class House(BaseModel, db.Model):
    """房屋信息"""

    __tablename__ = 'ih_house_info'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('ih_user_profile.id'), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('ih_area_info.id'), nullable=False)
    title = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Integer, default=0)  # 单位：分
    address = db.Column(db.String(512), default="")  # 地址
    room_count = db.Column(db.Integer, default=1)  # 房间数目
    acreage = db.Column(db.Integer, default=0)  # 房屋面积
    unit = db.Column(db.String(32), default="")  # 房屋单元， 如几室几厅
    capacity = db.Column(db.Integer, default=1)  # 房屋容纳的人数
    beds = db.Column(db.String(64), default="")  # 房屋床铺的配置
    deposit = db.Column(db.Integer, default=0)  # 房屋押金
    min_days = db.Column(db.Integer, default=1)  # 最少入住天数
    max_days = db.Column(db.Integer, default=0)  # 最多入住天数，0表示不限制
    order_count = db.Column(db.Integer, default=0)  # 预订完成的该房屋的订单数
    index_image_url = db.Column(db.String(256), default="")  # 房屋主图片的路径
    facilities = db.relationship("Facility", secondary=house_facility)  # 房屋的设施
    images = db.relationship("HouseImage")  # 房屋的图片
    orders = db.relationship("Order", backref="house")  # 房屋的订单

    def to_basic_dict(self):
        """"""
        house_dict = {
            "house_id": self.id,
            "address": self.address,
            "area_name": self.area.name,
            "title": self.title,
            "price": self.price,
            "room_count": self.room_count,
            "order_count": self.order_count,
            "ctime": self.create_time.strftime("%Y-%m-%d"),
            "user_avatar": constants.QINIU_URL_DOMAIN + self.user.avatar_url if self.user.avatar_url else "",
            "img_url": constants.QINIU_URL_DOMAIN + self.index_image_url if self.index_image_url else ""
        }
        return house_dict

    def to_full_dict(self):
        """将详细信息转换为字典数据"""
        house_dict = {
            "hid": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name,
            "user_avatar": constants.QINIU_URL_DOMAIN + self.user.avatar_url if self.user.avatar_url else "",
            "title": self.title,
            "price": self.price,
            "address": self.address,
            "room_count": self.room_count,
            "acreage": self.acreage,
            "unit": self.unit,
            "capacity": self.capacity,
            "beds": self.beds,
            "deposit": self.deposit,
            "min_days": self.min_days,
            "max_days": self.max_days,
        }

        # 房屋图片
        img_urls = []
        for image in self.images:
            img_urls.append(constants.QINIU_URL_DOMAIN + image.url)
        house_dict["img_urls"] = img_urls

        # 房屋设施
        facilities = []
        for facility in self.facilities:
            facilities.append(facility.id)
        house_dict["facilities"] = facilities

        # 评论信息
        comments = []
        orders = Order.query.filter(Order.house_id == self.id, Order.status == "COMPLETE", Order.comment != None)\
            .order_by(Order.update_time.desc()).limit(constants.HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS)
        for order in orders:
            comment = {
                "comment": order.comment,  # 评论的内容
                "user_name": order.user.name if order.user.name != order.user.mobile else "匿名用户",  # 发表评论的用户
                "ctime": order.update_time.strftime("%Y-%m-%d %H:%M:%S")  # 评价的时间
            }
            comments.append(comment)
        house_dict["comments"] = comments
        return house_dict


class Facility(BaseModel, db.Model):
    """设施信息"""

    __tablename__ = 'ih_facility_info'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)


class HouseImage(BaseModel, db.Model):
    """房屋图片"""

    __tablename__ = 'ih_house_image'

    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey('ih_house_info.id'), nullable=False)
    url = db.Column(db.String(256), nullable=False)


class Order(BaseModel, db.Model):
    """订单信息"""

    __tablename__ = 'ih_order_info'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("ih_user_profile.id"), nullable=False)  # 下订单的用户编号
    house_id = db.Column(db.Integer, db.ForeignKey("ih_house_info.id"), nullable=False)  # 预订的房间编号
    begin_date = db.Column(db.DateTime, nullable=False)  # 预订的起始时间
    end_date = db.Column(db.DateTime, nullable=False)  # 预订的结束时间
    days = db.Column(db.Integer, nullable=False)  # 预订的总天数
    house_price = db.Column(db.Integer, nullable=False)  # 房屋的单价
    amount = db.Column(db.Integer, nullable=False)  # 订单的总金额
    status = db.Column(
        db.Enum(
            "WAIT_ACCEPT",  # 待接单,
            "WAIT_PAYMENT",  # 待支付
            "PAID",  # 已支付
            "WAIT_COMMENT",  # 待评价
            "COMPLETE",  # 已完成
            "CANCELED",  # 已取消
            "REJECTED"  # 已拒单
        ),
        default="WAIT_ACCEPT", index=True)
    comment = db.Column(db.Text)
