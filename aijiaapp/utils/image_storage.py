# -----------------------------------------------
# -*- coding: utf-8 -*-
# @Time    : 2020/5/6 10:27
# @Author  : miri_chen
# @Email   : 825689698@qq.com
# @File    : image_storage.py
# -----------------------------------------------
from qiniu import Auth, put_file, etag, put_data
import qiniu.config

# 需要填写你的 Access Key 和 Secret Key
access_key = 'cgWRi1Gb_d-2rrEywmV8gdRSyogTcrT4VzPzKVUR'
secret_key = 'l-gI9facDaP9D51Ej4UI4qr--TFUaCXwdhEtOf5K'


def storage(file_data):
    """
    上传文件到七牛
    """

    # 构建鉴权对象
    q = Auth(access_key, secret_key)

    # 要上传的空间
    bucket_name = 'cxf-aijia'

    # 上传后保存的文件名
    # key = 'my-python-logo.png'

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    ret, info = put_data(token, None, file_data)
    if info.status_code == 200:
        return ret.get("key")
    else:
        raise Exception("上传七牛失败")


if __name__ == '__main__':
    with open("./1.jpg", 'rb') as f:
        file_data = f.read()
        ret = storage(file_data)
    print(ret)
