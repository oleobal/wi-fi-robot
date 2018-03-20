#!/usr/bin/python3
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT) # left forwards
GPIO.setup(13, GPIO.OUT) # left backwards
GPIO.setup(15, GPIO.IN)  # left speed sensor
GPIO.setup(29, GPIO.OUT) # right forwards
GPIO.setup(31, GPIO.OUT) # right backwards
GPIO.setup(33, GPIO.IN)  # right speed sensor
motLF = GPIO.PWM(11, 1000)
motLB = GPIO.PWM(13, 1000)
motLS = GPIO.input(15)
motRF = GPIO.PWM(29, 1000)
motRB = GPIO.PWM(31, 1000)
motRS = GPIO.input(33)
GPIO.cleanup()
