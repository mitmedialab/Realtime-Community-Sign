#!/usr/bin/python

import ConfigParser					# for parsing config params in ini file
import serial					   	# for interacting with the sign
import urllib						# for encoding url args
import httplib						# for talking to our server
from threading import Thread
from threading import Lock
import time							# for timing how often data is refreshed
import os
import sys
from datetime import datetime
from xml.etree import ElementTree as ET
import xml.dom.minidom
from xml.dom.minidom import Node
from xml.dom.minidom import parse, parseString

# what config file should we initialize from
CONFIG_FILE_PATH = "config.ini"

# global instance
config = None
controller = None
CODE_VERSION = "2.0.0"
#Changed
PROTOCOL_VERSION = "1.1"

PID_libsignctrl = '/var/run/lib-sign-ctrl.pid'

class LedSign:
	'''
	This class can be used to display information on a MovingSign led sign (supporting the v2.1 
	protocol).  This class should maintain state about the serial port working or not, and report
	it via the public isWorking method.  If it isn't working, this class is the one to re-open it.
	'''

	DEFAULT_PORT = "/dev/tty.usbserial"
	BAUDRATE = 9600

	_writeToSerial = True
	_serial = None
	_portname = None
	_working = False

	# header constants for comms to the sign
	COMM_TEXT_FILE_NAME_0 = ['0']
	COMM_CMD_START = ['\x00','\x00','\x00','\x00','\x00']
	COMM_START_OF_HEAD = ['\x01']
	COMM_SEND_ADDR_PC = ['F','F']
	COMM_RECEIVER_ADDR_BCAST = ['0','0']
	COMM_START_OF_TEXT = ['\x02']

	# commands for the sign
	COMM_CMD_WRITE_TEXT = ['A']
	COMM_CMD_WRITE_VAR = ['C']
	COMM_CMD_WRITE_GRAPHICS = ['E']
	COMM_CMD_WRITE_SPECIAL = ['W']
	COMM_CMD_READ_SPECIAL = ['R']

	# use these to control how a body of text is shown
	COMM_DISPLAY_MODE_AUTO = ['A']
	COMM_DISPLAY_MODE_FLASH = ['B'] 
	COMM_DISPLAY_MODE_HOLD = ['C'] 
	COMM_DISPLAY_MODE_INTERLOCK = ['D'] 
	COMM_DISPLAY_MODE_ROLLDOWN = ['E'] 
	COMM_DISPLAY_MODE_ROLLUP = ['F'] 
	COMM_DISPLAY_MODE_ROLLIN = ['G']
	COMM_DISPLAY_MODE_ROLLOUT = ['H']
	COMM_DISPLAY_MODE_ROLLLEFT = ['I']
	COMM_DISPLAY_MODE_ROLLRIGHT = ['J']
	COMM_DISPLAY_MODE_ROTATE = ['K']
	COMM_DISPLAY_MODE_SLIDE = ['L']
	COMM_DISPLAY_MODE_SNOW = ['M']
	COMM_DISPLAY_MODE_SPARKLE = ['N']
	COMM_DISPLAY_MODE_SPRAY = ['O']
	COMM_DISPLAY_MODE_STARBURST = ['P']
	COMM_DISPLAY_MODE_SWITCH = ['Q']
	COMM_DISPLAY_MODE_TWINKLE = ['R']
	COMM_DISPLAY_MODE_WIPEDOWN = ['S']
	COMM_DISPLAY_MODE_WIPEUP = ['T']
	COMM_DISPLAY_MODE_WIPEIN = ['U']
	COMM_DISPLAY_MODE_WIPEOUT = ['V']
	COMM_DISPLAY_MODE_WIPELEFT = ['W']
	COMM_DISPLAY_MODE_WIPERIGHT = ['X']
	COMM_DISPLAY_MODE_CYCLECOLOR = ['Y']
	COMM_DISPLAY_MODE_CLOCK = ['Z']

	# metadata about how to show the text
	COMM_DISPLAY_SPEED_3 = ['3']
	COMM_PAUSE_TIME_2 = ['2']
	COMM_PAUSE_TIME_5 = ['5']
	COMM_PAUSE_TIME_9 = ['9']
	COMM_SHOW_DATE_NONE = ['0','0']
	COMM_START_SHOW_TIME_NONE = ['0','0','0','0']
	COMM_END_SHOW_TIME_NONE = ['2','3','5','9']
	COMM_PREPARATAVE_PLACEHOLDER = ['\xff','\xff','\xff'] 

	# how text is aligned on the sign
	COMM_ALIGN_MODE_LEFT = ['1']
	COMM_ALIGN_MODE_ALIGN = ['2']
	COMM_ALIGN_MODE_RIGHT = ['3']

	COMM_TEXT_DATA_FONT_SS7 = ['\xfe','E']
	COMM_TEXT_DATA_COLOR_AUTO = ['\xfd','A']
	
	# footer constants for comms to the sign
	COMM_EFFICACY_START = ['\x00']			# checksum
	COMM_END_OF_TEXT = ['\x03']
	COMM_END_OF_TRANSMISSION = ['\x04']
		
	# special symbols supported by the sign
	COMM_SPECIAL_ASTERIX = '\xd0'
	COMM_SPECIAL_CLOCK = '\xd1'
	COMM_SPECIAL_PHONE = '\xd2'
	COMM_SPECIAL_SUNGLASSES = '\xd3'
	COMM_SPECIAL_FAUCET = '\xd4'
	COMM_SPECIAL_UKNOWN1 = '\xd5'
	COMM_SPECIAL_KEY = '\xd6'
	COMM_SPECIAL_SHIRT = '\xd7'
	COMM_SPECIAL_HELICOPTER = '\xd8'
	COMM_SPECIAL_CAR = '\xd9'
	COMM_SPECIAL_GENIE_LAMP = '\xda'
	COMM_SPECIAL_PYRAMID = '\xdb'
	COMM_SPECIAL_DUCK = '\xdc'
	COMM_SPECIAL_SCOOTER = '\xdd'
	COMM_SPECIAL_BICYCLE = '\xde'
	COMM_SPECIAL_CROWN = '\xdf'
	COMM_SPECIAL_UNKNOWN2 = '\xe0'
	COMM_SPECIAL_RIGHT_ARROW = '\xe1'
	COMM_SPECIAL_LEFT_ARROW = '\xe2'
	COMM_SPECIAL_DOWN_LEFT_ARROW = '\xe3'
	COMM_SPECIAL_UP_LEFT_ARROW = '\xe4'
	COMM_SPECIAL_TEA_CUP = '\xe5'
	COMM_SPECIAL_CHAIR = '\xe6'
	COMM_SPECIAL_HIGH_HEEL = '\xe7'
	COMM_SPECIAL_COCKTAIL = '\xe8'
	COMM_SPECIAL_ENVELOPE = '\xe9'
	COMM_SPECIAL_BELL = '\xea'
	COMM_SPECIAL_SMILEY = '\xeb'
	
	# use this for two-line signs
	COMM_TEXT_LINE_BREAK = '\x7f'

	def __init__(self, port, writeToSerial=True):
		'''
		Constructor doesn't do much
		'''
		self._serial = None
		self._portname = port
		self._writeToSerial = writeToSerial
		self._open()
		
	def _open(self):
		'''
		Open the serial port by name
		'''
		try:
			self._serial = serial.Serial(self._portname, self.BAUDRATE, timeout=1)
			self._working = True
		except Exception as e:
			self._working = False
		return self.isWorking()
	
	def resetPort(self):
		self._close()
		self._open()
	
	def isWorking(self):
		return self._working
	
	def _close(self):
		'''
		Close the previously opened serial port
		'''
		if self._serial:
			self._working = False
			self._serial.close()
	
	def write(self, text, displayMode=COMM_DISPLAY_MODE_AUTO, align=COMM_ALIGN_MODE_LEFT, 
				displaySpeed=COMM_DISPLAY_SPEED_3, pauseTime=COMM_PAUSE_TIME_9):
		'''
		Write text to the sign - returns True if sign acknowledges it worked
		'''
		
                #Text is currently ok, only contains message ([0])
		#print text
		
		if self._serial == None:
			return False
		
		if not self._writeToSerial:
			return True
	
		# try to re-open it if it wasn't working
		if not self.isWorking():
			self.resetPort()

		newText = text.encode('ascii','ignore')
		#assemble the message		
		msgHeader = self.COMM_CMD_START + self.COMM_START_OF_HEAD + self.COMM_SEND_ADDR_PC 
		msgHeader+= self.COMM_RECEIVER_ADDR_BCAST
		#print msgHeader
		msgData = self.COMM_START_OF_TEXT + self.COMM_CMD_WRITE_TEXT + self.COMM_TEXT_FILE_NAME_0 
		msgData+= displayMode + displaySpeed + pauseTime
		msgData+= self.COMM_SHOW_DATE_NONE +  self.COMM_START_SHOW_TIME_NONE
		msgData+= self.COMM_END_SHOW_TIME_NONE + self.COMM_PREPARATAVE_PLACEHOLDER
		msgData+= align
		msgData+= self.COMM_TEXT_DATA_FONT_SS7 + self.COMM_TEXT_DATA_COLOR_AUTO
		[msgData.append(c) for c in newText]
		msgData+= self.COMM_END_OF_TEXT			
		#print msgData
		msgFooter = []
		msgFooter+= self.COMM_EFFICACY_START
		checksumInt = 0
		for c in msgData:
			checksumInt += ord(c)
		checksumStr = "%0.4X" % checksumInt
		[msgFooter.append(c) for c in checksumStr]
		msgFooter+= self.COMM_END_OF_TRANSMISSION
		#print msgFooter
		
		
		# send the message to the sign
		try:
			
			# for some reason, these need to be sent separately, it fails if I send them all at once
			self._serial.write( str(''.join(msgHeader)) )
			self._serial.write( str(''.join(msgData)) )
			self._serial.write( str(''.join(msgFooter)) )
			self._serial.flush()
						
			# now check for ok and done signs back
			#time.sleep(1)
			result = self._serial.read()
			if len(result)==0 or ord(result) != 4 :			
				debug( "Didn't get EOT (0x04) in response!")
				if len(result) > 0:
					debug("  got ", str(ord(result)))
				self._working = False
			else:
			#	time.sleep(1)
				result = self._serial.read()
				if len(result)==0 or ord(result) != 1:
					debug("Didn't get SOH (0x01) in response!")
					if len(result) > 0:
						debug("  got ", str(ord(result)))
					self._working = False
				else:
					self._working = True

		except Exception as e:
			debug(str(e))
			self._working = False

		#time.sleep(1)
		
		return self.isWorking()


class SignManager(Thread):
	'''
	This class is a thread wrapper around a serial-port based LedSign.  The point is 
	to allows sign content updates to happen asyncronously from the content fetching.
	'''

	_contentLock = Lock()
	_content = None
	
	_signLock = Lock()
	_sign1 = None
	_sign1Working = None
	
	def _hasSigns(self):
		# override this!
		hasSigns = False
		with self._signLock:
			if (self._sign1 != None):
				hasSigns = True
		return hasSigns

	def _hasContent(self):
		hasContent = False
		with self._contentLock:
			if self._content != None:
				hasContent = True
		return hasContent
		
	def run(self):
		'''
		loop showing the content
		'''
		while True:

			# wait until we have signs
			if not self._hasSigns():
				time.sleep(1)
				continue
	
			# wait until we have content
			if not self._hasContent():
				time.sleep(1)
			else:
				self._updateSign()
				time.sleep(1)
	
	def _updateSign(self):
		'''
		Send the content to the sign - override this for different sign configurations
		'''
		content = ""
		#Content only has the message.
		with self._contentLock:
			content = self._content
		
		transition = LedSign.COMM_DISPLAY_MODE_ROLLLEFT
		#Changed
		if content.find(LedSign.COMM_TEXT_LINE_BREAK) != -1:
			transition = LedSign.COMM_DISPLAY_MODE_ROLLUP		
		with self._signLock:
			self._sign1Working = self._sign1.write(content, transition)
		with self._contentLock:
			self._content = None

	def setLedSigns(self, signList):
		# override this!
		with self._signLock:
			self._sign1 = signList[0]
		
	def setContent(self, msgs):
		# override this!
		with self._contentLock:
                        #Changed...?
			self._content = msgs
		
	def clear(self):
		with self._contentLock:
			self._content = None	
	
	def isSignOk(self):
		lastStatus = None
		with self._signLock:
			lastStatus = self._sign1Working
		return lastStatus
		
	def loopingContent(self):
		return False

class TwoSignManager(SignManager):
	'''
	This is a special case SignManager to handle two 1-line led signs used to create
	a two-line sign.  This is because the two-line sign can't hold one line fixed
	while scrolling the other horizontally.  So annoying.
	'''

	MIN_DURATION = 5
	SECS_PER_CHAR = 0.17
	MAX_CHARS_PER_LINE = 13
	
	_sign2 = None
	_sign2Working = None
	_currContentIdx = 0
	_loopingContent = False

	def _hasSigns(self):
		hasSigns = False
		with self._signLock:
			if (self._sign1 != None) and (self._sign2 != None):
				hasSigns = True
		return hasSigns

	def _updateSign(self):
		
		# grab the next msgs to show, or loop back to beginning
		skip = False
		with self._contentLock:
			line1 = ""
			line2 = ""
			if (self._currContentIdx*2 + 1) < len(self._content):
				self._loopingContent = True
				line1 = self._content[self._currContentIdx*2]
				line2 = self._content[self._currContentIdx*2 + 1]
			else:
				self._loopingContent = False
				self._currContentIdx = 0
				skip = True
		#print " showing ",self._currContentIdx," total len ",len(self._content)
		#print " line1 = ", line1
		#print " line2 = ", line2
		if skip:
			return False
		
		# show the content
		with self._signLock:
			#self._sign1.write("    ")
			#self._sign2.write("    ")
			self._sign1Working = self._sign1.write(line1, LedSign.COMM_DISPLAY_MODE_HOLD)
			line2Transition = LedSign.COMM_DISPLAY_MODE_ROLLLEFT
			if len(line2) <= self.MAX_CHARS_PER_LINE:
				line2Transition = LedSign.COMM_DISPLAY_MODE_HOLD
			self._sign2Working = self._sign2.write(line2, line2Transition)
		
		# delay for a while
		if len(line1)>0 and len(line2)>0:
			sleepDuration = max(self.MIN_DURATION, (self.SECS_PER_CHAR * len(line2)) )
			time.sleep(sleepDuration)
		else:
			time.sleep(1)

		# set up to show the next line
		self._currContentIdx = self._currContentIdx + 1
		return True

	def setContent(self, msgs):
		with self._contentLock:
			signMsgs = msgs.strip().replace('\n', LedSign.COMM_TEXT_LINE_BREAK)
			self._content = signMsgs.split(LedSign.COMM_TEXT_LINE_BREAK)
			self._currContentIdx = 0

	def setLedSigns(self, signList):
		with self._signLock:
			self._sign1 = signList[0]
			self._sign2 = signList[1]
		
	def isSignOk(self):
		lastStatus = None
		with self._signLock:
			lastStatus = (self._sign1Working) and (self._sign2Working)
		return lastStatus
		
	def loopingContent(self):
		isLooping = None
		with self._contentLock:
			isLooping = self._loopingContent
		return isLooping

class SignController:
	'''
	This is the main class, managing fetching content to display on a sign, and 
	telling any attached signs to update to show that content.  This also tracks 
	overall sign state and reports it to the server.
	'''

	# WARNING: keep these in line with the server constants (app/models/display.php)
	STATUS_UKNOWN = 0				# don't know (ie. created on server)
	STATUS_BOOTING = 1				# just starting up
	STATUS_OK = 2					# no probs
	STATUS_SIGN_COMMS_ERROR = 3		# couldn't send to serial
	STATUS_SERVER_CONNECT_ERROR = 4	# can't connect to server
	STATUS_BLANKED_DISPLAY = 5
	STATUS_UNHEARD_FROM = 6
	STATUS_VERSION_MISMATCH = 7 #version of protocol is not same as code

	OFFLINE_THRESHOLD_SECS = 300

	config = None
	_signMgr = None
	_status = None
	_serial_port1 = None
	_serial_port2 = None
	_write_to_serial = True

	ACTION_RESTART='restart'
	PIDFILE = '/var/run/lib-sign-ctrl.pid'

	REFRESH_INTERVAL = 30

	def __init__(self, config):
		self.config = config
		self._status = self.STATUS_BOOTING
		self._last_success = time.time()
		if self.config.has_option('Communication', 'write_to_serial'):
			self._write_to_serial = int(self.config.get('Communication', 'write_to_serial'))
		if self.config.has_option('Server', 'refresh_interval'):
			self.REFRESH_INTERVAL = int(self.config.get('Server', 'refresh_interval'))
		# open serial ports
		signs = self._openSigns()
		if self.config.has_option('Communication', 'serial_path_2'):
			self._signMgr = TwoSignManager()
		else:
			self._signMgr = SignManager()
		self._signMgr.setLedSigns( signs )
		self._signMgr.start()
				
	def refreshContentAfterOneCycle(self):
		return self.config.has_option('Communication', 'serial_path_2')

	def stillCyclingContent(self):
		return self._signMgr.loopingContent()
	
	def _openSigns(self):
		signs = []

		if self.config.has_option('Communication', 'serial_path'):
			path = self.config.get('Communication', 'serial_path')
		else:
			path = '/dev/ttyS0'
		self._serial_port1 = path
		sign1 = LedSign(self._serial_port1, self._write_to_serial)
		serial1Opened = sign1.isWorking()
		if serial1Opened:
			debug("Opened serial port1 at ",path)
		else:
			debug("ERROR: couldn't open serial port1 named "+str(self._serial_port1))
			self._status = self.STATUS_SIGN_COMMS_ERROR
		signs.append(sign1)

		if self.config.has_option('Communication', 'serial_path_2'):
			debug("Has 2 serial ports")
			path = self.config.get('Communication', 'serial_path_2')
			self._serial_port2 = path
			sign2 = LedSign(self._serial_port2, self._write_to_serial)
			serial2Opened = sign2.isWorking()
			if serial2Opened:
				debug("Opened serial port2 at ",path)
			else:
				debug("ERROR: couldn't open serial port2 named "+str(self._serial_port2))
				self._status = self.STATUS_SIGN_COMMS_ERROR
			signs.append(sign2)
		
		return signs
		

	def _write_to_display(self, message):
		'''
		Wrapper around the actual sign comms
		'''
		#async update of sign in separate thread, so we can't check status till afterwards
		lastUpdateWorked = self._signMgr.isSignOk()
		if lastUpdateWorked == False:
			debug("Last update couldn't write to sign.")
			self._status = self.STATUS_SIGN_COMMS_ERROR
		# try to update the sign content (which should reset the ports if they aren't working)
		self._signMgr.setContent(message)
		time.sleep(1)
		
	def update(self):
		'''
		Public method to fetch new data and show it on the sign
		'''
		now = time.time()

		# re-open serial if we need to (redundant - the signMgr should do this too)
		#if (self._status==self.STATUS_SIGN_COMMS_ERROR):
			#self._openSigns()

		# check if we're offline so we don't show stale info
		if (self._status==self.STATUS_SERVER_CONNECT_ERROR) and ((now - self._last_success) > self.OFFLINE_THRESHOLD_SECS):
			self._write_to_display("")
			debug("ERROR: haven't gotten text from server for a while, disabling display")
			self._status = self.STATUS_BLANKED_DISPLAY

		# now fetch normally
		info = self._fetch_text_from_server()
		msg = info[0]
		act = info[1]
                
		if act!= None:
			self._do_actions(act)
				
		if msg != None:
			if(self._status==self.STATUS_SERVER_CONNECT_ERROR or self._status==self.STATUS_BLANKED_DISPLAY):
				debug("Connected to server again happily")
			print self._status
			self._status = self.STATUS_OK
			debug('update: '+str(msg))
			debug('...writing updated message.')
			self._write_to_display(msg)
			self._last_success = now
		else:
			if self._status != self.STATUS_BOOTING and self._status != self.STATUS_VERSION_MISMATCH: # make sure reboot shows up in status log
				self._status = self.STATUS_SERVER_CONNECT_ERROR
				
	def _do_actions(self, actions):
		for i in range (0, len(actions)):
			if actions[i] == self.ACTION_RESTART:
				f = open(PID_libsignctrl,'w')
				f.close()

	def _fetch_text_from_server(self):
		'''
		Hit the server with my info and get the latest info to show on the sign
		'''
		if self.config.has_option('Server', 'host'):
			path = "/x"
			params = dict(serial=self.config.get('Server', 'serial_num'), 
						  secret=self.config.get('Server', 'secret'), 
						  codeVersion=CODE_VERSION,
						  protocolVersion=PROTOCOL_VERSION,
						  status=self._status)
			params = urllib.urlencode(params)
			msg = None
			try:
				conn = httplib.HTTPConnection( self.config.get('Server', 'host'), self.config.get('Server', 'port'))
				print self.config.get('Server', 'host')+":"+self.config.get('Server', 'port')+path+"?"+params
				#sys.exit()
				conn.request("GET", path+"?"+params)
				response = conn.getresponse()
				msg = response.read()
			except Exception, e:
				debug("Error: couldn't fetch from server "+str(e))
				return None
			if(len(msg)==0):
				debug("Error: got empty message from server")
				return None

			#XML parsing
			dom = xml.dom.minidom.parseString(msg)
			information = []
			info=""
			actions=[]
			#Get code version
			version = dom.documentElement.getAttribute("version")
			#Only update sign if version is the same as protocol version
			if version == PROTOCOL_VERSION:
				#Get information for this version
				for node in dom.getElementsByTagName("message"):
					#Get a list of all info tags
					infoTags = node.getElementsByTagName("info")
					info = ""
					for nodeA in infoTags:
						for nodeB in nodeA.childNodes:
							if nodeB.nodeType == Node.TEXT_NODE:
								info += nodeB.data
				#Get commands for this version
				for node in dom.getElementsByTagName("commandlist"):
					#Get list of all command tags
					commandTags = node.getElementsByTagName("command")
					for nodeA1 in commandTags:
						for nodeB1 in nodeA1.childNodes:
							if nodeB1.nodeType == Node.TEXT_NODE:
								actions.append(nodeB1.data)
								
				#Add info and actions
				information = [info, actions]
				#Returning both
				return information
				#return msg.strip().replace('\n', LedSign.COMM_TEXT_LINE_BREAK)
			else:
				self._status = self.STATUS_VERSION_MISMATCH
				debug("Error: version mismatch")
		else:
			debug("Error: no server host configured!")
			sys.exit(1);
		return None

def loadconfig(path):
	'''
	Helper function to load the properties file used to configure the sign
	'''
	config = ConfigParser.ConfigParser()
	try:
		config.read(path)
	except Exception, e:
		debug("Couldn't read config: %s" % e)
		pass
	else:
		pass
	return config

def debug(msg, lvl=10):
	'''
	Helper method to log this to stderr
	'''
	debugLevel = 0
	if config.has_option('Debug', 'verbosity'):
		debugLevel = int( config.get('Debug', 'verbosity') )
	if(debugLevel >= lvl):
		sys.stderr.write("%s:\t%s\n" % (datetime.now().isoformat(' '),msg))


def update(controller):
	'''
	Update the sign and then sleep.  You probably want to call this repeatedly 
	inside of a while loop.
	'''
	controller.update()
	if controller.refreshContentAfterOneCycle():
		while controller.stillCyclingContent():
			time.sleep(1)
	else:
		debug('Sleeping...')
		time.sleep(controller.REFRESH_INTERVAL)

if __name__ == '__main__':
	config = loadconfig( CONFIG_FILE_PATH )
	
	controller = SignController(config)
	
	while True:
		update(controller)

