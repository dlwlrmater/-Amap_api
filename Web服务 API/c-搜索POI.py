import requests
import pandas as pd
import csv
import datetime
from tqdm import trange
import random

def get_url(u,p):
    r = requests.get(u,p)
    #print(r.url)
    return r.json()

def read_file(path):
    f = csv.reader(open(path,'r',encoding='utf-8'))
    text = []
    for i in f:
        adcode = i[1]
        text.append(adcode)
    return text

# 文件所处路径
path = r'D:\!!python result\地点检索\AMap_adcode_citycode_高德2.csv'
# path = r'D:\!!python result\地点检索\AMap_adcode_citycode_高德for铁路站2.csv'

start = datetime.datetime.now()

# Web服务 API放入即可
KEYS = []


# z = read_file(path)
# z = z[1:]
z = ['西藏']
for x in z:
    for i in range(1,47):
        print(x,i)
        url = 'https://restapi.amap.com/v3/place/text?'
        parmas = {
            'types':'110200',
            # 'keywords':'旅游景点',
            'city':x,
            'page':i,
            'output':'json',
            'key':random.choice(KEYS),
            'extensions':'all'
        }
        #print(parmas)
        r_js = get_url(url, parmas)

        count_ = r_js['count']

# 写入参数，字典格式


        pois_ = r_js['pois']
        index = 0
        #print('page_size is '+ str(a))
        df = []
        name = []
        lng = []
        lat = []
        type = []
        pname = []
        cityname = []
        adname = []
        rating = []
        #print(len(pois_))
        #print(pois_[0]['name'])
        for index in range(len(pois_)):
            name_ = pois_[index]['name']
            name.append(name_)
            location_ = pois_[index]['location']
            lng.append(location_.split(',')[0])
            lat.append(location_.split(',')[1])
            type_ = pois_[index]['type']
            type.append(type_)
            pname_ = pois_[index]['pname']
            pname.append(pname_)
            cityname_ = pois_[index]['cityname']
            cityname.append(cityname_)
            adname_ = pois_[index]['adname']
            adname.append(adname_)

            rating_ = pois_[index]['biz_ext']['rating']
            if rating_ is None:
                rating_ == 0
                rating.append(rating_)
            else:
                rating.append(rating_)

        dt = pd.DataFrame({'name': name, 'lng': lng, 'lat':lat,'type':type,'pname':pname,'cityname':cityname,'adname':adname,'rating':rating})
        #print(r_js['status'])


        mingzi = '110200_西藏_types'
        # mingzi = 'tianshui_subwaystation'


        dt.to_csv(r'D:\!!python result\地点检索\gcj-02_{}.csv'.format(mingzi),mode='a',index=0)

end = datetime.datetime.now()

print('Running time: %s' %(end-start))








