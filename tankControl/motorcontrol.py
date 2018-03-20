import RPi.GPIO as GPIO
import signal
import sys
import time

def handler_int(signal, frame):
	print("SIGINT, Cleaning up pins")
	stopMotors()
	GPIO.cleanup()
	sys.exit(0)

def handler_segv(signal, frame):
	print("SIGSEV, Cleaning up pins")
	stopMotors()
	GPIO.cleanup()
	sys.exit(-1)



#signal.signal(signal.SIGINT, handler_int)
#signal.signal(signal.SIGSEGV, handler_segv)



	
class Motor :
	def __init__(self, position, pinF, pinB) :
		self.position = position
		self.pinF = pinF
		self.pinB = pinB
		self.status = ("stopped", 0)
		self.modifierF = 1.0
		self.modifierB = 1.0
		self.speedSensor = None
		self.speedEvents = None
	
	# two modifiers which are multiplicated to given speed when enabling the engines
	# keep in mind speed won't go over 100
	def setModifiers(self, modF, modB):
		self.modifierF = modF
		self.modifierB = modB
	
	def setSpeedSensor(self, pinS):
		self.speedSensor = pinS
		# I did think about using a queue and averaging values to iron out irregularities but I don't think it'd be worth it
		self.speedEvents = [time.clock(),time.clock()]
		GPIO.add_event_detect(self.speedSensor, GPIO.RISING, callback=self.updateSpeed)
	
	def updateSpeed(self, pinSpeed) :
		self.speedEvents[0] = self.speedEvents[1]
		self.speedEvents[1] = time.clock()
	
	# speed 0-100
	def goForwards(self, speed) :
		#self.stop()
		self.status = ("forwards", speed)
		self.pinB.ChangeDutyCycle(0)
		self.pinF.ChangeDutyCycle(speed*self.modifierF)
		
	# speed 0-100
	def goBackwards(self, speed) :
		#self.stop()
		self.status = ("backwards", speed)
		self.pinF.ChangeDutyCycle(0)
		self.pinB.ChangeDutyCycle(speed*self.modifierB)
	
	# Sets duty cycle of pins to zero
	def halt(self):
		self.status = ("halted", 0)
		self.pinF.ChangeDutyCycle(0)
		self.pinB.ChangeDutyCycle(0)
	
	# stops all pins
	def stop(self):
		self.status = ("stopped", 0)
		self.pinF.stop()
		self.pinB.stop()
	
	# returns a tuple (string, int) with direction and speed
	# (speed given without the modifiers applied)
	def getStatus(self) :
		return self.status

	# if the speed sensor for this motor hasn't been set up (setSpeedSensor()), returns None
	# else, returns the time between the two last rises of the speed sensor (as a floating point thing in seconds)
	# on our DD-1 robot that should be the time for 1/4th of a turn
	def getSensorSpeed(self) :
		if self.speedSensor is None :
			return None
		else:
			return self.speedEvents[1] - self.speedEvents[0]

def initialize():
	# initializing 2 engines
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
	
	# start à 0 pour pouvoir utiliser ChangeDutyCycle plus tard sans démarrer les moteurs maintenant
	motLF.start(0)
	motLB.start(0)
	motRF.start(0)
	motRB.start(0)

	motorLeft  = Motor("left", motLF, motLB)
	#motorLeft.setSpeedSensor(motLS)
	motorRight = Motor("right", motRF, motRB)
	#motorRight.setSpeedSensor(motRS)
	
	return motorLeft, motorRight
