import time
import requests
import re
import os
import sys
import json
import datetime
from flask import request, Flask, jsonify

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

def Download(info,session):
   VHEADERS['User-Agent'] = VH2
   video_bin = session.get(info['addr'], timeout = 5, headers = VHEADERS)
   is_wm = info['is_wm'] 
   filename = info['id']
   if is_wm == 1:
      filename = info['id'] + "_wm"

   with open('%s.mp4' % (filename),'wb') as fb: # 将下载的图片保存到对应的文件夹中
      fb.write(video_bin.content)
   VHEADERS['User-Agent'] = VH1
   
   return True

#抓取视频接口
@app.route('/video', methods=['POST'])
def video():
   try:
      json = request.json
      if json:
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
            #下载视频
            Download(info,session)
            return jsonify({"code": 200, "msg": "success"})
      else:
         return jsonify({"code": 500, "msg": "参数非法"})
   except Exception as e:
      return jsonify({"code": 500, "msg": '下载失败', "error": str(e)})
if __name__ == '__main__':
   app.run(debug=True, host='127.0.0.1', port=5000)
      


