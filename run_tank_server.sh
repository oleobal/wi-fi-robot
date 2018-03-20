#!/bin/bash

# http://fomori.org/blog/?p=1213

raspivid -w 640 -h 480 -n -t 0 -o - | ffmpeg -i - -f mpegts -preset ultrafast -codec:v mpeg1video -q:v 20 -g 50 -threads 4 -frame_drop_threshold -10 -pix_fmt yuv420p  - | tankControl/controlpanel.py

#raspivid -t 0 -o - | ffmpeg -tune zerolatency -i - -f mpegts -preset ultrafast -codec:v mpeg1video -q:v 20 -pix_fmt yuv420p -g 1 -threads 2 - | ./video-server.py

#raspivid -w 640 -h 480 -fps 60 -g 0 -t 0 -o - | avconv -preset ultrafast -tune zerolatency -i - -f mpegts -codec:v mpeg1video - | ./video-server.py

#raspivid -t 0 -o - | avconv -r 30 -i - -f mpegts -codec:v mpeg1video - | ./video-server.py
