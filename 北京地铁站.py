import pandas as pd
import urllib
import json
import openpyxl

url = 'http://map.amap.com/service/subway?_1469083453978&srhdata=1100_drw_beijing.json'

html = urllib.request.urlopen(url)
hjson = json.loads(html.read().decode("utf-8"))
print(hjson)
l_ = hjson['l']
df = []
ln = []
n = []
lng = []
lat = []
for a in range(len(l_)):
    path=0
    ln_ = l_[a]['ln']
    st_ = l_[a]['st']
    for b in range(len(st_)):
        path +=1
        print(path)
        n_ = st_[b]['n']
        lng_ = st_[b]['sl'].split(',')[0]
        lat_ = st_[b]['sl'].split(',')[1]
        ln.append(ln_)
        n.append(n_)
        lng.append(lng_)
        lat.append(lat_)
        df = pd.DataFrame({'名字':n,'lng':lng,'lat':lat,'所在线路':ln})
# df.to_csv(r'C:\Users\steve\Desktop\北京火车站.csv',mode = 'a')
df.to_excel('/Users/wangyuxuan/Downloads/exceltxt.xlsx')
print('finish')
