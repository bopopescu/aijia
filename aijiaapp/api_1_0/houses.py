# -----------------------------------------------
# -*- coding: utf-8 -*-
# @Time    : 2020/5/6 12:08
# @Author  : miri_chen
# @Email   : 825689698@qq.com
# @File    : houses.py
# -----------------------------------------------
import json
from datetime import datetime

from flask import request, jsonify, current_app, g, session

from aijiaapp import db, constants, redis_store
from aijiaapp.models import Area, House, Facility, HouseImage, Order
from aijiaapp.utils.commons import login_required
from aijiaapp.utils.image_storage import storage
from aijiaapp.utils.response_code import RET
from . import api


@api.route("/areas")
def get_area_info():
    """获取城区信息"""
    # 尝试从redis读取数据
    try:
        resp_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    else:
        # 有数据就直接返回
        if resp_json is not None:
            current_app.logger.info("hit redis area_info")
            return resp_json, 200, {"Content-Type": "application/json"}

    # 查询数据库信息
    try:
        area_list = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    # 将对象装换成字典
    area_dict_li = []
    for area in area_list:
        area_dict_li.append(area.to_dict())

    # 将数据转换成json字符串
    resp_dict = dict(errno=RET.OK, errmsg="OK", data=area_dict_li)
    resp_json = json.dumps(resp_dict)

    # 将数据保存到redis中
    try:
        redis_store.setex("area_info", constants.AREA_INFO_REDIS_CACHE_EXPIRES, resp_json)
    except Exception as e:
        current_app.logger.error(e)

    return resp_json, 200, {"Content-Type": "application/json"}


@api.route("/houses/info", methods=["POST"])
@login_required
def sava_house_info():
    """
    保存房屋基本信息
    :return:
    """

    # 获取数据
    user_id = g.user_id
    req_dict = request.get_json()

    title = req_dict.get("title")
    price = req_dict.get("price")
    area_id = req_dict.get("area_id")
    address = req_dict.get("address")
    room_count = req_dict.get("room_count")
    acreage = req_dict.get("acreage")
    unit = req_dict.get("unit")
    capacity = req_dict.get("capacity")
    beds = req_dict.get("beds")
    deposit = req_dict.get("deposit")
    min_days = req_dict.get("min_days")
    max_days = req_dict.get("max_days")

    # 校验参数
    if not all(
            [title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断金额是否正确
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 判断城区id是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据异常")

    if area is None:
        return jsonify(errno=RET.NODATA, errmsg="城区信息有误")

    # 保存房屋信息
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )

    db.session.add(house)

    # 处理房屋的设施信息
    facility_ids = req_dict.get("facility")
    if facility_ids:
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库异常")

        if facilities:
            # 表示有合法设施数据
            # 保存设施数据
            house.facilities = facilities

    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    # 返回成功的数据
    return jsonify(errno=RET.OK, errmsg="OK", data={"house_id": house.id})


@api.route("/houses/image", methods=["POST"])
@login_required
def sava_house_image():
    """保存房屋图片"""

    image_file = request.files.get("house_image")
    house_id = request.form.get("house_id")

    if not all([image_file, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if house is None:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    image_data = image_file.read()
    # 保存图片到七牛中
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="保存图片失败")

    house_image = HouseImage(house_id=house_id, url=file_name)
    db.session.add(house_image)

    if not house.index_image_url:
        house.index_image_url = file_name
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片数据异常")

    image_url = constants.QINIU_URL_DOMAIN + file_name
    return jsonify(errno=RET.OK, errmsg="OK", data={"image_url": image_url})


@api.route("/user/houses")
@login_required
def get_user_houses():
    """"""
    user_id = g.user_id
    try:
        houses = House.query.filter_by(user_id=user_id).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取数据失败")

    houses_li = []
    for house in houses:
        houses_li.append(house.to_basic_dict())
    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_li})


@api.route("/houses/index")
def get_house_index():
    """"""
    # 尝试从redis读取数据
    try:
        resp_json = redis_store.get("home_page_data")
    except Exception as e:
        current_app.logger.error(e)
    else:
        # 有数据就直接返回
        if resp_json is not None:
            current_app.logger.info("hit redis home_page_data")
            return resp_json, 200, {"Content-Type": "application/json"}

    # 获取销量降序房屋数据
    try:
        houses = House.query.filter(House.index_image_url != "").order_by(House.order_count.desc()).limit(
            constants.HOME_PAGE_MAX_HOUSES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not houses:
        return jsonify(errno=RET.NODATA, errmsg="查询无数据")

    houses_list = []

    for house in houses:
        houses_list.append(house.to_basic_dict())

    # 将数据加入缓存
    resp_dict = dict(errno=RET.OK, errmsg="OK", data=houses_list)
    resp_json = json.dumps(resp_dict)
    try:
        redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, resp_json)
    except Exception as e:
        current_app.logger.error(e)

    return resp_json, 200, {"Content-Type": "application/json"}


@api.route("/houses/<int:house_id>")
def get_house_detail(house_id):
    """获取房屋详情"""
    # 前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示，
    # 所以需要后端返回登录用户的user_id
    # 尝试获取用户登录的信息，若登录，则返回给前端登录用户的user_id，否则返回user_id=-1
    user_id = session.get("user_id", "-1")

    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数缺失")

    # 先从redis缓存中获取信息
    try:
        ret = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("hit house info redis")
        return '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, ret), \
               200, {"Content-Type": "application/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 将房屋对象数据转换为字典
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据出错")

    # 存入到redis中
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_house)
    except Exception as e:
        current_app.logger.error(e)

    return '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, json_house), \
           200, {"Content-Type": "application/json"}


# GET /api/v1.0/houses?sd=2020-05-01&ed=2020-05-05&aid=10&sk=new&p=1
@api.route("/houses")
def get_house_list():
    """获取房屋列表信息"""

    # 获取参数
    start_date = request.args.get("sd")
    end_date = request.args.get("ed")
    area_id = request.args.get("aid")
    sort_key = request.args.get("sk")
    page = request.args.get("p")

    # 处理时间
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期参数有误")

    # 判断区域id
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="区域参数有误")

    # 处理页数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 过滤条件的参数列表容器
    filter_params = []

    # 填充过滤参数
    # 时间条件
    conflict_orders = None

    # 查询冲突的订单
    try:
        if start_date and end_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            conflict_orders = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            conflict_orders = Order.query.filter(Order.end_date >= start_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if conflict_orders:
        # 从订单中获取冲突房屋id
        conflict_house_ids = [order.house_id for order in conflict_orders]

        # 如果冲突的房屋id不为空，向查询参数中添加条件
        if conflict_house_ids:
            filter_params.append(House.id.notin_(conflict_house_ids))

    # 区域条件
    if area_id:
        filter_params.append(House.area_id == area_id)

    # 查询数据库
    # 补充排序条件
    if sort_key == 'booking':  # 入住最多
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())  # *li解包
    elif sort_key == "price-inc":
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key == "price-des":
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 处理分页
    try:
        page_obj = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    # 获取页面数据
    house_li = page_obj.items
    houses = []
    for house in house_li:
        houses.append(house.to_basic_dict())

    # 获取总页数
    total_page = page_obj.pages

    return jsonify(errno=RET.OK, errmsg="OK", data={"total_page": total_page, "houses": houses, "current_page": page})
