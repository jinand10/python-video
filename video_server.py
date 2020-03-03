import time
import requests
import re
import os
import sys
import json
import datetime
from flask import request, Flask, jsonify
from hashlib import md5

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

VHEADERS = {
'User-Agent':'Mozilla/5.0 (Linux; U; Android 5.1.1; zh-cn; MI 4S Build/LMY47V) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.146 Mobile Safari/537.36 XiaoMi/MiuiBrowser/9.1.3',
"accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
"accept-encoding":"gzip, deflate, sdch, br",
"accept-language":"en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4",
"cache-control":"no-cache"
}
VH1 = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36 OPR/58.0.3135.65"
VH2 = "Mozilla/5.0 (Linux; U; Android 5.1.1; zh-cn; MI 4S Build/LMY47V) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.146 Mobile Safari/537.36 XiaoMi/MiuiBrowser/9.1.3"

CDN_URL = "http://127.0.0.1"

API_SECRET = "video@2020@access@token"

def encrypt_md5(s):
    # 创建md5对象
    new_md5 = md5()
    # 这里必须用encode()函数对字符串进行编码，不然会报 TypeError: Unicode-objects must be encoded before hashing
    new_md5.update(s.encode(encoding='utf-8'))
    # 加密
    return new_md5.hexdigest()


def GetRealUrl(video_url, is_wm = 1):
   session = requests.Session()
   req = session.get(video_url, timeout = 5, headers = VHEADERS)
   req.encoding = 'utf-8'
   data = req.text
   matchData = re.findall( r'<video id="theVideo" class="video-player" src="([\S]*?)" preload="auto"',data)

   videoId = data.split("itemId: \"")[1].split("\",")[0]
   if is_wm == 1:
      playAddr = matchData[0].replace("/playwm/","/playwm/")
      videoAddr = playAddr.replace("/playwm/","/playwm/")
   else:
      playAddr = matchData[0].replace("/playwm/","/play/")
      videoAddr = playAddr.replace("/playwm/","/play/")
   info = {
      "id": videoId,
      "playAddr": playAddr,
      "addr": videoAddr,
      "is_wm": is_wm
   }
   return info,session

def Download(info,session,filename):
   VHEADERS['User-Agent'] = VH2
   video_bin = session.get(info['addr'], timeout = 5, headers = VHEADERS)

   with open('%s' % (filename),'wb') as fb: # 将下载的图片保存到对应的文件夹中
      fb.write(video_bin.content)
   # VHEADERS['User-Agent'] = VH1
   
   return True

#抓取视频接口
@app.route('/video', methods=['POST'])
def video():
   try:
      sign = request.args.get('sign')
      if sign == "" or sign == None:
         return jsonify({"code": 500, "msg": "签名错误"})

      json = request.json
      if json:
         #校验签名
         server_sign = encrypt_md5(str(json) + API_SECRET)
         if server_sign != sign:
            return jsonify({"code": 500, "msg": "签名错误"})

         #校验url参数
         video_url = json['url']
         if video_url == "":
            return jsonify({"code": 500, "msg": "url不能为空"})

         #校验is_wm参数
         is_wm = json['is_wm']
         wm_list = [0, 1]
         if is_wm not in wm_list:
            return jsonify({"code": 500, "msg": "is_wm参数错误"})

         #解析url
         regx = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+" 
         pattern = re.compile(regx) 
         listurl = re.findall(pattern,repr(video_url))
         if len(listurl) == 0:
            return jsonify({"code": 500, "msg": "解析url失败"})
         else:
            if listurl[0][len(listurl[0])-1] == "'":
               listurl[0] = listurl[0][:-1]
            video_url = listurl[0]
            #获取真实地址  
            info,session = GetRealUrl(video_url, is_wm)
            #文件名
            is_wm = info['is_wm'] 
           
            if is_wm == 1:
               filename = "./upload/iswm/"+info['id']+".mp4"
               cdn_path = "/upload/iswm/"+info['id']+".mp4"
            else:
               filename = "./upload/notwm/"+info['id']+".mp4"
               cdn_path = "/upload/notwm/"+info['id']+".mp4"
            #下载视频
            if os.path.isfile(filename):
               cdn_file = CDN_URL + cdn_path
            else:
               Download(info,session,filename)
               cdn_file = CDN_URL + cdn_path

            return jsonify({"code": 200, "msg": "success", "data": {"url": cdn_file}})

      else:
         return jsonify({"code": 500, "msg": "参数非法"})
   except Exception as e:
      return jsonify({"code": 500, "msg": '下载失败', "error": str(e)})
if __name__ == '__main__':
   app.run(debug=False, host='127.0.0.1', port=5000)
      


