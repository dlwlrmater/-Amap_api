import pandas as pd
import requests
import time
import shapefile
import math
import schedule

# 用于批量爬取特定时间路段拥堵数据
# 数据基于实时地图道路数据进行分类，返回值为高德自定等级
# 数据接口20201231已下线


class LocaDiv(object):
    # 把范围按照特定比例分割
    def __init__(self,loc_all,divd):
        self.loc_all = loc_all
        self.divd = divd
    # 经度划分
    def lat_all(self):
        lat_sw = float(self.loc_all.split(',')[1])
        lat_ne = float(self.loc_all.split(',')[3])
        lat_list = [str(lat_ne)]
        while lat_ne - lat_sw > 0:
            m = lat_ne - self.divd
            lat_ne = lat_ne - self.divd
            lat_list.append('%.2f' % m)
        return sorted(lat_list)
    # 纬度划分
    def lng_all(self):
        lng_sw = float(self.loc_all.split(',')[0])
        lng_ne = float(self.loc_all.split(',')[2])
        lng_list = [str(lng_ne)]
        while lng_ne - lng_sw > 0:
            m = lng_ne - self.divd
            lng_ne = lng_ne - self.divd
            lng_list.append('%.2f' % m)
        return sorted(lng_list)

    # 经纬度组合
    def ls_com(self):
        lat = self.lat_all()
        lng = self.lng_all()
        latlng_list = []
        for i in range(0,len(lat)):
            a = lat[i]
            for i2 in range(0,len(lng)):
                b = lng[i2]
                ab = b + ',' + a
                latlng_list.append(ab)
        return latlng_list

    # 获得小栅格西南角和东北角坐标，用于后面Web服务API 交通态势使用
    def ls_row(self):
        lat = self.lat_all()
        lng = self.lng_all()
        latlng_list = self.ls_com()
        ls = []
        for n in range(0,len(lat) - 1):
            for i in range(len(lng)*n,len(lng)*(n+1)-1):
                # print(latlng_list)
                # print(lng)
                # print(lat)
                coor_a = latlng_list[i]
                coor_b = latlng_list[i+len(lng)+1]
                coor = coor_a + ';' + coor_b
                ls.append(coor)
        return ls

def get_url(u,p):
    i = 0
    # 重复三次，如果三次都发生了Request问题，就break
    while i < 3:

        try:
            r = requests.get(u,p,timeout=10)
            # print(r.url)
            return r.json()
        except requests.exceptions.RequestException:
            i +=1

def get_data(r_js):
    try:
        global t
        status_ = r_js['status']
        time_now = time.time()
        t = time.strftime('%Y%m%d_%H', time.localtime(time_now))
        # 读取json文件
        if status_ == '1':
            roads_ =r_js['trafficinfo']['roads']
            # print(len(roads_))
            for i in range(len(roads_)):
                # print(roads_[i]['name'])
                # dt = {}
                # dt['status'] = roads_[i]['status']
                # if dt['status'] == '0':
                #     pass
                # else:
                dt = {}
                dt['name'] = roads_[i]['name']
                dt['status'] = roads_[i]['status']
                dt['direction'] = roads_[i]['direction']
                dt['speed'] = roads_[i]['speed']
                dt['polyline'] = roads_[i]['polyline']
                dm = pd.DataFrame([dt],columns=['name','status','direction','speed','polyline'])
                # print(dm)
                dm.to_csv('D:/!!python result/实时交通情况/北京/csv/北京{}点_lines.csv'.format(t), mode='a', header=False)
        else:
            print('gg')
            pass

    except:
        print('error..try it again..')
        # 如果出现问题，休息3s之后再次请求
        time.sleep(3)
        pass
        #get_data(r_js)

def get_params(all):
    p = []
    for i in all:
        # request请求参数
        parmas = {
            'rectangle': i,
            # key填写Web服务api的key即可
            'key': '',
            'extensions':'all'
        }
        p.append(parmas)
    return(p)

def csv():
    loc = LocaDiv('116.06,39.77,116.68,40.10', 0.01)
    # 得到用于划分分区的坐标
    a = loc.ls_row()
    pae = get_params(a)
    # print(len(a))
    #print(pae)

    url = 'https://restapi.amap.com/v3/traffic/status/rectangle?'
    pathid = 0
    for z in pae:
        r_js = get_url(url, z)
        pathid += 1
        # print(r_js)
        print(str(pathid) + "/" + str(len(a)))
        data1 = get_data(r_js)

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
    # 判断是不是再国内
    return not (lng > 73.66 and lng < 135.05 and lat > 3.86 and lat < 53.55)

def lines_wgs84(x):
    lst = []
    for i in x:
        lng = float(i.split(',')[0])
        lat = float(i.split(',')[1])
        lst.append(gcj02_to_wgs84(lng, lat))
    return lst

def json_shp():
    # 把之前得到的csv生成对应的json文件和shapefile,方便之后再arcgis里面进行后续操作
    df_lines = pd.read_csv(r'D:\!!python result\实时交通情况\北京\csv\北京{}点_lines.csv'.format(t),
                           names=['id', 'name', 'status', 'direction', 'speed', 'polyline'])
    df_ls = df_lines[['name', 'status', 'speed', 'polyline']]
    df_ls_1 = df_ls.copy()

    df_ls_1['polyline'] = df_ls_1['polyline'].apply(lambda x: x.split(';'))

    print(df_ls_1.head(2))
    df_ls_1.to_json(r'D:\!!python result\实时交通情况\北京\json\北京{}点_lines.json'.format(t))
    print(str(time.localtime(time.time()).tm_hour) + '点 json is done')

    # 坐标转换
    df_ls_1['lines_wgs84'] = df_ls_1['polyline'].apply(lines_wgs84)

    # 生成点和面图层
    w_lines = shapefile.Writer(r'D:\!!python result\实时交通情况\北京\shp\北京{}点_lines.shp'.format(t))
    w_lines.field('name', 'C')
    w_lines.field('status', 'N')
    w_lines.field('speed', 'N')
    for i in range(len(df_ls_1)):
        w_lines.line([df_ls_1['lines_wgs84'][i]])
        w_lines.record(df_ls_1['name'][i].encode('gbk'), df_ls_1['status'][i], df_ls_1['speed'][i])
    w_lines.close()
    print(str(time.localtime(time.time()).tm_hour) + '点 shp is done')


if __name__ == '__main__':
    while True:
        current_time = time.localtime(time.time())
        # 根据list i里面的小时，准时爬取，得到对应地区的实时道路数据
        i = [6,7,8,9,10,17,18,19]
        a = current_time.tm_hour
        if a in i:
            if ((current_time.tm_min == 0) and (current_time.tm_sec == 0)):
                csv()
                print(str(a) + '点 csv is done')
                x_pi = 3.14159265358979324 * 3000.0 / 180.0
                pi = 3.1415926535897932384626  # π
                a = 6378245.0  # 长半轴
                ee = 0.00669342162296594323  # 偏心率平方
                json_shp()


# schedule.every(1).hours.do(csv)
# schedule.every(1).hours.do(json_shp)
# while True:
#     schedule.run_pending()
#     time.sleep(3)
