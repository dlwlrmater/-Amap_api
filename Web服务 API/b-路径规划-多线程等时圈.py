import pandas as pd
import numpy as np
import requests
import threading
from tqdm import trange
import json
import urllib
import math
import csv
import random

# 本代码是基于高德Web服务API中的路径规划功能  对现状路网通行能力进行评估
# 结合Arcgis中Model Builders使用 可以批量化高效生成基于实时路网的等时圈
# 此代码只提供od点之间的基于私家车出行的高德地图出行时间预测
# od点获得和效果展示均在arcgis中操作
# 以o点为中心选取特定范围，进行栅格化处理，通过提取栅格中心点坐标，与o点形成od对，通过api保住得到两点之间通行时间，再在arcgis中通过反重力权重工具，生成等时圈图



# 第一步数据整合
def Zhenghe(path,diming,odianming):
    # 读取经过Arcgis处理过5000*5000栅格文件中心点坐标,作为d点
    df_sts = pd.read_excel(path+'{}wgs_5k.xls'.format(diming))
    # 读取Arcgis导出各地市政府位置,作为o点
    odian_origin = pd.read_excel(path+ odianming +'.xlsx')
    aaaindex = list(odian_origin['name']).index(diming)
    # print(aaaindex)
    odian = pd.DataFrame({'o_lng': odian_origin['lng'][aaaindex], 'o_lat': odian_origin['lat'][aaaindex]}, index=[0])
    # 生成dataframe文件 为后面发送请求做准备
    matrix = pd.merge(odian, df_sts[['POINT_X', 'POINT_Y']], right_index=True, left_index=True, how='outer').fillna(
        method='ffill').rename(columns={'POINT_X': 'd_lng', 'POINT_Y': 'd_lat'})
    # print(matrix)
    return matrix

#第二步 坐标转换
# 提供wgs 百度坐标 火星坐标之间转换
class Zuobiaozhuanhuan():
    x_pi = 3.14159265358979324 * 3000.0 / 180.0
    pi = 3.1415926535897932384626  # π
    a = 6378245.0  # 长半轴
    ee = 0.00669342162296594323  # 偏心率平方


    def gcj02_to_bd09(self,lng, lat):
        """
        火星坐标系(GCJ-02)转百度坐标系(BD-09)
        谷歌、高德——>百度
        :param lng:火星坐标经度
        :param lat:火星坐标纬度
        :return:
        """
        z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * self.x_pi)
        theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * self.x_pi)
        bd_lng = z * math.cos(theta) + 0.0065
        bd_lat = z * math.sin(theta) + 0.006
        return [bd_lng, bd_lat]

    def bd09_to_gcj02(self,bd_lon, bd_lat):
        """
        百度坐标系(BD-09)转火星坐标系(GCJ-02)
        百度——>谷歌、高德
        :param bd_lat:百度坐标纬度
        :param bd_lon:百度坐标经度
        :return:转换后的坐标列表形式
        """
        x = bd_lon - 0.0065
        y = bd_lat - 0.006
        z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * self.x_pi)
        theta = math.atan2(y, x) - 0.000003 * math.cos(x * self.x_pi)
        gg_lng = z * math.cos(theta)
        gg_lat = z * math.sin(theta)
        return [gg_lng, gg_lat]

    def wgs84_to_gcj02(self, lng, lat):
        """
        WGS84转GCJ02(火星坐标系)
        :param lng:WGS84坐标系的经度
        :param lat:WGS84坐标系的纬度
        :return:
        """
        if self.out_of_china(lng, lat):  # 判断是否在国内
            return [lng, lat]
        dlat = self._transformlat(lng - 105.0, lat - 35.0)
        dlng = self._transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * self.pi
        magic = math.sin(radlat)
        magic = 1 - self.ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((self.a * (1 - self.ee)) / (magic * sqrtmagic) * self.pi)
        dlng = (dlng * 180.0) / (self.a / sqrtmagic * math.cos(radlat) * self.pi)
        mglat = lat + dlat
        mglng = lng + dlng
        return [mglng, mglat]

    def gcj02_to_wgs84(self,lng, lat):
        """
        GCJ02(火星坐标系)转GPS84
        :param lng:火星坐标系的经度
        :param lat:火星坐标系纬度
        :return:
        """
        if self.out_of_china(lng, lat):
            return [lng, lat]
        dlat = self._transformlat(lng - 105.0, lat - 35.0)
        dlng = self._transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * self.pi
        magic = math.sin(radlat)
        magic = 1 - self.ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((self.a * (1 - self.ee)) / (magic * sqrtmagic) * self.pi)
        dlng = (dlng * 180.0) / (self.a / sqrtmagic * math.cos(radlat) * self.pi)
        mglat = lat + dlat
        mglng = lng + dlng
        return [lng * 2 - mglng, lat * 2 - mglat]

    def bd09_to_wgs84(self,bd_lon, bd_lat):
        lon, lat = self.bd09_to_gcj02(bd_lon, bd_lat)
        return self.gcj02_to_wgs84(lon, lat)

    def wgs84_to_bd09(self,lon, lat):
        lon, lat = self.wgs84_to_gcj02(lon, lat)
        return self.gcj02_to_bd09(lon, lat)

    def _transformlat(self,lng, lat):
        ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
              0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
        ret += (20.0 * math.sin(6.0 * lng * self.pi) + 20.0 *
                math.sin(2.0 * lng * self.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lat * self.pi) + 40.0 *
                math.sin(lat / 3.0 * self.pi)) * 2.0 / 3.0
        ret += (160.0 * math.sin(lat / 12.0 * self.pi) + 320 *
                math.sin(lat * self.pi / 30.0)) * 2.0 / 3.0
        return ret

    def _transformlng(self,lng, lat):
        ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
              0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
        ret += (20.0 * math.sin(6.0 * lng * self.pi) + 20.0 *
                math.sin(2.0 * lng * self.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lng * self.pi) + 40.0 *
                math.sin(lng / 3.0 * self.pi)) * 2.0 / 3.0
        ret += (150.0 * math.sin(lng / 12.0 * self.pi) + 300.0 *
                math.sin(lng / 30.0 * self.pi)) * 2.0 / 3.0
        return ret

    def out_of_china(self,lng, lat):
        """
        判断是否在国内，不在国内不做偏移
        :param lng:
        :param lat:
        :return:
        """
        return not (lng > 73.66 and lng < 135.05 and lat > 3.86 and lat < 53.55)

    def st_bd09_wgs84(self,x):
        lng = float(x.split(',')[0])
        lat = float(x.split(',')[1])
        return self.bd09_to_wgs84(lng,lat)

    def st_wgs84_gcj02(self,x):
        lng = float(x.split(',')[0])
        lat = float(x.split(',')[1])
        return self.wgs84_to_gcj02(lng, lat)

    def st_gcj02_wgs84(self,x):
        lng = float(x.split(',')[0])
        lat = float(x.split(',')[1])
        return self.gcj02_to_wgs84(lng,lat)

    def gc_wgs(self,df_sts):
        df_sts['o_gcj'] = df_sts['o_lng	'].map(str) + ',' + df_sts['o_lat	'].map(str)
        df_sts['d_gcj'] = df_sts['d_lng	'].map(str) + ',' + df_sts['d_lat	'].map(str)
        df_sts['o_wgs'] = df_sts['o_gcj'].apply(self.st_gcj02_wgs84)
        df_sts['d_wgs'] = df_sts['d_gcj'].apply(self.st_gcj02_wgs84)
        # print(df_sts['st_coords_wgs84'][0][0])
        olng_wgs = []
        olat_wgs = []
        dlng_wgs = []
        dlat_wgs = []
        gctowgs = pd.DataFrame()
        for i in range(len(df_sts)):
            a = df_sts['o_wgs'][i][0]
            olng_wgs.append(a)
            b = df_sts['o_wgs'][i][1]
            olat_wgs.append(b)
            c = df_sts['d_wgs'][i][0]
            dlng_wgs.append(c)
            d = df_sts['d_wgs'][i][1]
            dlat_wgs.append(d)
        gctowgs['olng_wgs'] = pd.Series(olng_wgs)
        gctowgs['olat_wgs'] = pd.Series(olat_wgs)
        gctowgs['dlng_wgs'] = pd.Series(dlng_wgs)
        gctowgs['dlat_wgs'] = pd.Series(dlat_wgs)
        return gctowgs

    def wgs_gc(self,df_sts):
        df_sts['o_wgs'] = df_sts['o_lng'].map(str) + ',' + df_sts['o_lat'].map(str)
        df_sts['d_wgs'] = df_sts['d_lng'].map(str) + ',' + df_sts['d_lat'].map(str)
        df_sts['o_gcj'] = df_sts['o_wgs'].apply(self.st_wgs84_gcj02)
        df_sts['d_gcj'] = df_sts['d_wgs'].apply(self.st_wgs84_gcj02)
        # print(df_sts['st_coords_wgs84'][0][0])
        olng_gcj = []
        olat_gcj = []
        dlng_gcj = []
        dlat_gcj = []
        wgstogc = pd.DataFrame()
        for i in range(len(df_sts)):
            a = df_sts['o_gcj'][i][0]
            olng_gcj.append(a)
            b = df_sts['o_gcj'][i][1]
            olat_gcj.append(b)
            c = df_sts['d_gcj'][i][0]
            dlng_gcj.append(c)
            d = df_sts['d_gcj'][i][1]
            dlat_gcj.append(d)
        wgstogc['olng_gcj'] = pd.Series(olng_gcj)
        wgstogc['olat_gcj'] = pd.Series(olat_gcj)
        wgstogc['dlng_gcj'] = pd.Series(dlng_gcj)
        wgstogc['dlat_gcj'] = pd.Series(dlat_gcj)
        # print(wgstogc.head())
        return wgstogc

# 第三步 计算durantion&distance
class Driving_time:
    def __init__(self,matrix):
        self.matrix = matrix

    def file_read(self):
        """
        创建函数读取坐标点txt文件
        输出一个经纬度列表
        :param path:文件路径
        :return:
        """

        f = self.matrix
        text1 = []
        text2 = []
        for i in range(len(f)):
            # print(i)
            # i = i.replace('\t',',')
            lng1 = f['olng_gcj'][i]
            lat1 = f['olat_gcj'][i]
            text1.append(str(lng1) + ',' + str(lat1))
            lng2 = f['dlng_gcj'][i]
            lat2 = f['dlat_gcj'][i]
            # print(lng1+'**********')
            text2.append(str(lng2) + ',' + str(lat2))
        # print(text2)
        # print(text1)
        return text1, text2

    def get_params(self):
        # 作为request请求中的参数,字典格式即可
        # 通过申请高德api中的Web服务 API 填入KEYS里即可
        KEYS = []
        p = []
        s_num = 0
        e_num = 0
        # o,d点zip 相当于提取两个文件的同一行
        for i, j in zip(list(self.file_read())[0],list(self.file_read())[1]):
            s_num += 1
            e_num += 1
            params = {
                'origin': i,
                'destination': j,
                'output': 'json',
                # 使用random.choice的原因，因为之前并没有上传身份证认证，通过申请多个Web服务api+random.choice可以打破每个key的使用上限（现已修复）
                'key': random.choice(KEYS),
                'extensions': 'all'
            }
            p.append(params)
        return p

    def get_datal(self):
        # 基于url的requset请求
        global o_lat_, o_lng_, d_lng_, d_lat_, distance_, duration_, num
        o_lng = []
        o_lat = []
        d_lng = []
        d_lat = []
        distance = []
        duration = []
        for i in trange(len(self.get_params())):
            # print(i)
            # 前面为Web服务api中的请求url，后面为根据driving（驾车）所需的请求参数
            r = requests.get('http://restapi.amap.com/v3/direction/driving?', self.get_params()[i])
            # print(r.url)
            # 读取json文件
            status_ = r.json()['status']
            p_o = self.get_params()[i]['origin'].split(',')
            p_d = self.get_params()[i]['destination'].split(',')
            o_lng_ = p_o[0]
            o_lat_ = p_o[1]
            d_lng_ = p_d[0]
            d_lat_ = p_d[1]
            o_lng.append(o_lng_)
            o_lat.append(o_lat_)
            d_lng.append(d_lng_)
            d_lat.append(d_lat_)
            # 如果status = 1 则证明两点之间可以到达
            if status_ == '1':
                route_ = r.json()['route']
                paths_ = route_['paths']
                ling_ = paths_[0]
                distance_ = ling_['distance']  # 方案距离
                duration_ = ling_['duration']  # 线路耗时
                distance.append(distance_)
                duration.append(duration_)
            #两种可能性
            # 1.无法到达 所以distance和duration都取极大值，为了方便后面arcgis中反重力权重工具使用
            # 2.key使用达到上限（一般做d点栅格时候就考虑到key调用的限额，一般不会产生）
            else:
                distance_ = '99999999'
                duration_ = '99999999'
                num = '99999999'
                distance.append(distance_)
                duration.append(duration_)
            # 生成o点,d点,实际通行距离,实际通行时间的dataframe
            data_dic = pd.DataFrame({'o_lng_gcj':o_lng,'o_lat_gcj':o_lat,'d_lng_gcj':d_lng,'d_lat_gcj':d_lat,'dis':distance,'time':duration})
        return data_dic


def Result(yuanshiwenjina,jieguowenjian,path,name):
    a = yuanshiwenjina[['o_lng','o_lat','d_lng','d_lat']]
    b = jieguowenjian[['dis','time']]
    c = pd.merge(a,b,left_index=True,right_index=True,how='outer')
    print('合并好了')
    c['dis'] = pd.to_numeric(c['dis'], errors='coerce')
    c['time'] = pd.to_numeric(c['time'],errors='coerce')
    d = c.to_excel(path+name+'_result_arcgis_wgs.xls')
    return d

def Finally(path,name,odianname):
    # 数据合并
    # 第一个位置是文件所在位置
    # 第二个是目标文件名字  {}wgs_5k.xls
    # 第三个是O点文件名字    {}.xslx
    # he=合并
    hb = Zhenghe(path, name, odianname)
    # print('hb好了')
    # 坐标转换 wgs84 to gcj(火星坐标系)
    gcjzuobiao = Zuobiaozhuanhuan().wgs_gc(hb)
    # print('转换好了')
    # 通过API得到 durantion&distance   DataFrame导入
    jieguo = Driving_time(gcjzuobiao)
    # print('导入好了')
    APIresult = jieguo.get_datal()
    # print('结果好了')
    # 结果导出成.xls
    final = Result(hb, APIresult, path, name)


if __name__ == '__main__':
    # 提供文件所在地址、d点文件名称、o点文件名称
    path = r'C:\Users\steve\Desktop\tibet火车站\\'
    odianname = '火车站'
    # 因为当时项目是以整个西藏的各个大型火车站，使用多线程加快获取速度，提高效率
    t1 = threading.Thread(target=Finally,args=(path,'当雄站',odianname))
    t2 = threading.Thread(target=Finally, args=(path, '安多站', odianname))
    t3 = threading.Thread(target=Finally, args=(path, '日喀则站', odianname))
    t4 = threading.Thread(target=Finally, args=(path, '仁布站', odianname))
    t5 = threading.Thread(target=Finally, args=(path, '曲水县站', odianname))
    t6 = threading.Thread(target=Finally, args=(path, '尼木站', odianname))
    t7 = threading.Thread(target=Finally, args=(path, '那曲站', odianname))
    t8 = threading.Thread(target=Finally, args=(path, '拉萨站', odianname))
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t6.start()
    t7.start()
    t8.start()
    t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()
    t6.join()
    t7.join()
    t8.join()

