守护进程启动video服务

nohup gunicorn -w 4 -b 0.0.0.0:5000 video_server:app &
