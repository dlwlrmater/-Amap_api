import csv
import requests
import datetime

#提供文件位置:D:\!!python result\geocodering\re_location_dizhi.csv
#结果位置:D:\!!python result\geocodering\{}_gcj09_re_georecodingresult.csv

def file_address(path):
    f = csv.reader(open(path,'r',encoding='UTF-8'))
    text = []
    for i in f:
        address = i[1]
        text.append(address)
    return text

def get_params(s,k):
    p = []
    s_num = 0
    for a in s:
            s_num += 1
            params = {
                'location': a,
                'radius':'1000',
                'output': 'json',
                'extensions':'all',
                'key': k
            }
            p.append([params,s_num])
    return (p)

def get_url(u,p):
    r = requests.get(u,p)
    print(r.url)
    return r.json()

def get_datal(js,p):
    global formatted_address_
    status_ = js['status']
    loc_ = p['location']
    #print(count_)
    if status_ == '1':
        regeocode_ = js['regeocode']
        formatted_address_ = regeocode_['formatted_address']
        data_dic = dict([['formatted_address',formatted_address_]])
        return data_dic
    else:
        formatted_address_ = "无法找到相应数据"
        data_dic = dict([['formatted_address',formatted_address_]])
        return data_dic

def main():
    keys = ''

    url = 'http://restapi.amap.com/v3/geocode/regeo?'

    path = 'D:\\!!python result\\regeocodering\\'



    address_ = file_address(path + 're_location_dizhi.csv')
    address_ = address_[1:]

    f_result = open(path + '{}_gcj02_re_georecodingresult.csv'.format(project_name),mode = 'a')
    f_result.seek(0)
    f_result.write('num\t,lng\t,lat\t,address\n')



    pathID = 0

    p = get_params(address_,keys)
    #print(p)

    for p,keys in p:
        pathID += 1
        print(pathID)
        r_js = get_url(url,p)
        data1 = get_datal(r_js,p)
        #print(data1)
        f_result.writelines([
            str(pathID), ',',
            str(p['location']),',',
            str(data1['formatted_address']),'\n'
        ])
    f_result.close()

if __name__ == '__main__':
    project_name = 'test1'
    start = datetime.datetime.now()
    main()
    end = datetime.datetime.now()
    print('finished')
    print('Running time: %s' %(end-start))