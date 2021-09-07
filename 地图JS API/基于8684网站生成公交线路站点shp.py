import requests
import json
from lxml import etree
import time
import numpy as np
import math
import pandas as pd
import shapefile

# 每次都得改list(a)

def get_lines(cityE):
    # 通过8684公交网获得目标城市的公交线路名称
    lst = []
    a = [1,2,3,4,5,6,7,8,9,'C','D','E','G','H','K','L','Q','S','W','X','Y','Z']
    for i in a:
        url = 'http://{}.8684.cn/list{}'.format(cityE,i)
#         print(url)
        r = requests.get(url).text
        et = etree.HTML(r)
        # 正则表达式提取线路名
        line = et.xpath('//div[@class="list clearfix"]//a/text()')
        for l in line:
            lst.append(l)
            # print(lst)
    return lst

def get_dt(city, line):
    try:
        # key为JS API中的key
        # 通过目标城市和公交线路名称进行request请求，获得线路途径站点和线路通行路径
        url = 'https://restapi.amap.com/v3/bus/linename?s=rsv3&extensions=all&key=&output=json&city={}&offset=1&keywords={}&platform=JS'.format(
            city, line)
        r = requests.get(url).text
        print(requests.get(url).url)
        rt = json.loads(r)
        # 得到线路名称、公交站点坐标、线路路径、公交站点名称
        if rt['buslines']:
            print('data avaliable..')
            if len(rt['buslines']) == 0:
                print('no data in list..')
            else:
                dt = {}
                dt['line_name'] = rt['buslines'][0]['name']
                dt['polyline'] = rt['buslines'][0]['polyline']
                dt['total_price'] = rt['buslines'][0]['total_price']

                st_name = []
                st_coords = []
                for st in rt['buslines'][0]['busstops']:
                    st_name.append(st['name'])
                    st_coords.append(st['location'])

                dt['station_name'] = st_name
                dt['station_corrds'] = st_coords

                dm = pd.DataFrame([dt])
                print(dm)
                # lines的文件
                dm.to_csv('D:/!!python result/bus_station/咸阳/{}_8684_lines.csv'.format(city),mode='a',header=False)
        else:
            pass
    except:
        print('error..try it again..')
        time.sleep(2)

x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 偏心率平方


def gcj02_to_wgs84(lng, lat):
    """
    GCJ02(火星坐标系)转GPS84
    :param lng:火星坐标系的经度
    :param lat:火星坐标系纬度
    :return:
    """
    if out_of_china(lng, lat):
        return [lng, lat]
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [lng * 2 - mglng, lat * 2 - mglat]

def _transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 *
            math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 *
            math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret

def _transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 *
            math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 *
            math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret

def out_of_china(lng, lat):
    """
    判断是否在国内，不在国内不做偏移
    :param lng:
    :param lat:
    :return:
    """
    return not (lng > 73.66 and lng < 135.05 and lat > 3.86 and lat < 53.55)

def st_wgs84_station(x):
    lng = float(x.split(',')[0])
    lat = float(x.split(',')[1])
    return gcj02_to_wgs84(lng,lat)

def lines_wgs84(x):
    lst = []
    for i in x:
        lng = float(i.split(',')[0])
        lat = float(i.split(',')[1])
        lst.append(gcj02_to_wgs84(lng,lat))
    return lst

if __name__ == "__main__":
    t1 = time.time()
    cityE = 'xianyang'
    city = '咸阳'

    lines_list = get_lines(cityE)
    print('{}：有 {} 条公交线路'.format(city,len(lines_list)))
    time.sleep(5)

    for i,line in enumerate(lines_list):
        print('id {}:{}================'.format(i,line))
        get_dt(city, line)
        time.sleep(1)

    t2 = time.time()
    print('耗时{}秒'.format(t2-t1))
    print('ALL DONE!')




    df_lines = pd.read_csv(r'D:\!!python result\bus_station\咸阳\咸阳_8684_lines.csv',encoding='UTF-8',
                           names=['id','line_name','lines','station_coords','station_name','price'])
    df_sts = df_lines[['station_coords','station_name']]

    # print(df_sts['station_coords'][0])
    df_sts_1 = df_sts.copy()
    # print(df_sts_1.head(1))
    df_sts_1['station_coords'] = df_sts_1['station_coords'].apply(lambda x:x.replace('[','').replace(']','').replace('\'','').split(', '))
    print(len(df_sts_1['station_coords']))
    df_sts_1['station_name'] = df_sts_1['station_name'].apply(lambda x:x.replace('[','').replace(']','').replace('\'','').split(', '))
    # print(type(df_sts_1['station_coords']))
    # 数据拆分
    st_all = pd.DataFrame(\
                         np.column_stack((\
                                         np.hstack(df_sts_1['station_coords'].repeat(list(map(len,df_sts_1['station_coords'])))),
                                         np.hstack(df_sts_1['station_name'].repeat(list(map(len,df_sts_1['station_name'])))),
                                         )),
                          columns=['station_coords', 'station_names']
                         )
    st_all = st_all.drop_duplicates()
    #print(st_all.head(1))
    # 获得站点csv
    st_all.to_csv(r'D:\!!python result\bus_station\咸阳\咸阳_8684_station.csv')
    # print(df_lines.columns)
    df_ls = df_lines[['line_name','lines']]
    df_ls_1 = df_ls.copy()
    df_ls_1['lines'] = df_ls_1['lines'].apply(lambda x:x.split(';'))
    print(df_ls_1.head(1))
    df_ls_1.to_json(r'D:\!!python result\bus_station\咸阳\咸阳_8684_lines.json')
    df_sts_station = pd.read_csv(r'D:\!!python result\bus_station\咸阳\咸阳_8684_station.csv')
    print(df_sts_station.head())


    # 坐标转换
    df_sts_station['st_coords_wgs84'] = df_sts_station['station_coords'].apply(st_wgs84_station)
    # 生成点图层
    w_station = shapefile.Writer(r'D:\!!python result\bus_station\咸阳\咸阳_8684_wgs84_station.shp')
    w_station.field('name', 'C')
    for i in range(len(df_sts_station)):
        w_station.point(df_sts_station['st_coords_wgs84'][i][0], df_sts_station['st_coords_wgs84'][i][1])
        w_station.record(df_sts_station['station_names'][i].encode('gbk'))
    w_station.close()

    df_ls = pd.read_json(r'D:\!!python result\bus_station\咸阳\咸阳_8684_lines.json')

    # 坐标转换
    df_ls['lines_wgs84'] = df_ls['lines'].apply(lines_wgs84)
    # 生成面图层
    w_lines = shapefile.Writer(r'D:\!!python result\bus_station\咸阳\咸阳_8684_lines.shp')
    w_lines.field('name', 'C')
    for i in range(len(df_ls)):
        w_lines.line([df_ls['lines_wgs84'][i]])
        w_lines.record(df_ls['line_name'][i].encode('gbk'))
    w_lines.close()
