import csv
import requests
import datetime

#提供文件位置:D:\!!python result\geocodering\location_dizhi.csv
#结果位置:D:\!!python result\geocodering\{}_gcj09_georecodingresult.csv

def file_address(path):
    f = csv.reader(open(path,'r',encoding='UTF-8'))
    text = []
    for i in f:
        address = i[1]
        text.append(address)
    return text

def file_province(path):
    f = csv.reader(open(path,'r',encoding='UTF-8'))
    text = []
    for i in f:
        province = i[2]
        text.append(province)
    return text

def file_city(path):
    f = csv.reader(open(path,'r',encoding='UTF-8'))
    text = []
    for i in f:
        city = i[3]
        text.append(city)
    return text

def get_params(s,e,o,k):
    p = []
    s_num = 0
    e_num = 0
    o_num = 0
    for a,b,c in zip(s,e,o):
            s_num += 1
            e_num += 1
            o_num += 1
            params = {
                'address': a,
                'city': b,
                '&city':c,
                'output': 'json',
                'key': k
            }
            p.append([params,s_num,e_num,o_num])
    return (p)

def get_url(u,p):
    r = requests.get(u,p)
    print(r.url)
    return r.json()

def get_datal(js,p):
    global lng_,lat_,province_,district_,adcode_,level_
    #print(js)
    #print(js)
    status_ = js['status']
    count_= js['count']
    #print(count_)
    address_ = p['address']
    city_ =p['city']
    if count_ == '1':
        #print(js)
        geocodes_ = js['geocodes'][0]
        #print(geocodes_)
        #location_ = geocodes_['location'].split(',')
        lng_ = geocodes_['location'].split(',')[0]
        lat_ = geocodes_['location'].split(',')[1]
        province_ = geocodes_['province']
        city_1 = geocodes_['city']
        district_ = geocodes_['district']
        adcode_ =geocodes_['adcode']
        level_ = geocodes_['level']
        print(address_)
        print(level_)
        data_dic = dict([['address',address_],['city',city_1],['lng',lng_],['lat',lat_],['province',province_],['district',district_],['adcode',adcode_],['level',level_]])
        return data_dic
    else:
        lng_ = "无法找到相应数据"
        lat_ = ""
        province_ = ""
        city_1 = ""
        district_ = ""
        adcode_ = ""
        level_ = ""
        data_dic = dict([['address', address_],['city',city_1],['lng', lng_],['lat', lat_], ['province', province_],['district', district_],['adcode',adcode_],['level', level_]])
        return data_dic

def main():
    keys = ''

    url = 'http://restapi.amap.com/v3/geocode/geo?'

    path = 'D:\\!!python result\\geocodering\\'



    address_ = file_address(path + 'location_dizhi.csv')
    province_ = file_province(path + 'location_dizhi.csv')
    city_ = file_city(path + 'location_dizhi.csv')
    address_ = address_[1:]
    province_ = province_[1:]
    #print(address_)
    city_ = city_[1:]
    #print(city_)

    f_result = open(path + '{}_gcj02_georecodingresult.csv'.format(project_name),mode = 'a',encoding='gbk')
    f_result.seek(0)
    f_result.write('num\t,address\t,city\t,lng\t,lat\t,province\t,district\t,adcode\t,地址类型\n')



    pathID = 0

    p = get_params(address_,province_,city_,keys)
    #print(p)

    for p,lat,lng,keys in p:
        pathID += 1
        print(pathID)
        r_js = get_url(url,p)
        data1 = get_datal(r_js,p)
        #print(data1)
        f_result.writelines([
            str(pathID), ',',
            str(p['address']),',',
            str(data1['city']), ',',
            str(data1['lng']),',',
            str(data1['lat']),',',
            str(data1['province']),',',
            str(data1['district']), ',',
            str(data1['adcode']), ',',
            str(data1['level']),'\n'
        ])
    f_result.close()

if __name__ == '__main__':
    project_name = '天水景区'
    start = datetime.datetime.now()
    main()
    end = datetime.datetime.now()
    print('finished')
    print('Running time: %s' %(end-start))