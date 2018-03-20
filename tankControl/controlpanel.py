#!/usr/bin/python3
# -*- coding: utf-8 -*-

import signal
import sys
import time
import logging
import os

import motorcontrol as mc

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import tornado.escape # json_decode()

from tornado.options import define, options

define("port", default=7780, help="run on the given port", type=int)
define("heartbeatPeriod", default=500, help="rate at which heartbeats are sent (in ms)", type=int)

class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("index.html")

class VideoStreamHandler(tornado.websocket.WebSocketHandler):

	stdinStream = None
	# garde une liste de toutes les connexions actives pour leur donner le flux vidéo
	activeConnections = []	

	@staticmethod
	def initStream():
		# créer un pipe pour récupérer les données vidéo de l'entrée standard
		VideoStreamHandler.stdinStream = tornado.iostream.PipeIOStream(sys.stdin.fileno())
		VideoStreamHandler.stdinStream.set_nodelay(True)

		# envoie les données du flux à toutes les connexions actives
		VideoStreamHandler.stdinStream.read_until_close(streaming_callback=VideoStreamHandler.feedActiveConnections)
	
	# envoie les données de la caméra à toutes les connexions websocket actives
	@staticmethod
	def feedActiveConnections(data):
		for socket in VideoStreamHandler.activeConnections:
			socket.newData(data)	
	
	def newData(self, data):
		#print("Received data from camera !")
		try:
			self.write_message(data, binary=True)
		except tornado.websocket.WebSocketClosedError:
			self.on_close()	

	def open(self):
		VideoStreamHandler.activeConnections.append(self)
		logging.info("Socket connection opened with " + self.request.remote_ip + " for video stream")
		self.set_nodelay(True)
		
	def on_close(self):
		VideoStreamHandler.activeConnections.remove(self)
		logging.warning("Socket connection closed with " + self.request.remote_ip + " for video stream")


class CommandWebSocket(tornado.websocket.WebSocketHandler):	

	def open(self):
		logging.info("Socket connection opened with " + self.request.remote_ip)
		
		# envoyer periodiquement un message au client pour vérifier l'état de la connexion. Si le client ne répond pas d'ici la prochaine vérification, on termine la connexion immédiatement pour éviter de perdre le contrôle du véhicule.
		self.periodicPing = tornado.ioloop.PeriodicCallback(self.poke, options.heartbeatPeriod)
		self.periodicPing.start()
		self.terminate = False

	def on_message(self, message):
		logging.info("Received command: " + message)
		
		# on décode le message en un objet JSON (ici dictionnaire python) avec les champs "left" et "right"
		data  = tornado.escape.json_decode(message)
		left, right  = data["left"], data["right"]

		# left et right ne peuvent être compris qu'entre -100 et 100
		# Toutes autres valeur sont considérées comme une erreur et les moteurs sont donc arrêtés
		if left >= -100 and left <= 100 \
		and right >= -100 and right <= 100:
			if left > 0:
				motorLeft.goForwards(left)
			elif left < 0:
				motorLeft.goBackwards(-left)
			else:
				motorLeft.halt()
			
			if right > 0:
				motorRight.goForwards(right)
			elif right < 0:
				motorRight.goBackwards(-right)
			else:
				motorRight.halt()
				
		else:
			motorLeft.halt()
			motorRight.halt()
			
		self.write_message(u"Received (L = {} ; R = {})".format(data["left"], data["right"]))
		
	def on_close(self):
		logging.warning("Socket connection with " + self.request.remote_ip + " closed")

		motorLeft.halt()
		motorRight.halt()

		if self.periodicPing.is_running():
			self.periodicPing.stop()
	
	# si le client répond, on annule la terminaison
	def on_pong(self, data):
		self.terminate = False
		logging.info(data.decode())
	
	# envoie une requête pour vérifier l'état de la connexion.
	# Si aucune réponse n'est reçue du client, on_pong n'est jamais appelée, self.terminate est donc True et on termine la connexion.
	def poke(self):
		if self.terminate:
			logging.error("Client is not responding. Emergency shutdown initiated.")
			self.close()
			self.on_close() # self.close ne ferme pas le websocket immédiatement (il y a un timeout du au handshake TCP), on appelle donc on_close manuellement pour faire un arrêt d'urgence
		else:
			self.terminate = True
			self.ping(str.encode("Heartbeat"))

def strsignal(s):
	return {getattr(signal, n): n for n in dir(signal) if __import__("re").match("SIG[A-Z]+", n)}[s]; # python pls
	
def handler_int(sig, frame):
	logging.warning("Received terminating signal " + strsignal(sig))
	logging.info("Stopping server and exitting.")
	io_loop = tornado.ioloop.IOLoop.current()
	io_loop.add_callback_from_signal(http_server.stop)
	io_loop.stop()
	VideoStreamHandler.stdinStream.close()
	motorLeft.stop()
	motorRight.stop()
	mc.GPIO.cleanup()


def main():
	# initialisation de l'application Tornado
	tornado.options.parse_command_line()
	application = tornado.web.Application([
		(r"/", MainHandler),
		(r"/video", VideoStreamHandler),
		(r"/socket", CommandWebSocket),
		(r"/(.*)", tornado.web.StaticFileHandler, {"path": "/home/pi/tankControl/"}),
	])
	
	# initialisation du serveur HTTP
	global http_server
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(options.port)
	
	# initialisation du flux vidéo
	VideoStreamHandler.initStream()
	
	# initialisation des gestionnaires de signaux
	signal.signal(signal.SIGINT, handler_int)  # Ctrl+C
	signal.signal(signal.SIGQUIT, handler_int) # Ctrl+\
	signal.signal(signal.SIGTERM, handler_int)
	
	# initialisation des moteurs
	global motorLeft
	global motorRight
	motorLeft, motorRight = mc.initialize()
	
	# début de la boucle I/O
	tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
	main()
