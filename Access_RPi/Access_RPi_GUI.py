#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado.ioloop import IOLoop, PeriodicCallback
from tornado import gen
from tornado.websocket import websocket_connect
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QTimer
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import fingerpi as fpi
from Verify import verifier
from Enroll import enrolling
from Delete import Deleting

import sys, json

class Enrolling(QtGui.QMainWindow):
	def __init__(self,parent=None):
                self.Enroll_result= None
                self.Delete_result=None
        	super(Enrolling,self).__init__(parent)

                self.addUser_btn=QtGui.QPushButton("Add User",self)
                self.addUser_btn.clicked.connect(self.Enroll)

                self.deleteUser_btn=QtGui.QPushButton("Delete User",self)
                self.deleteUser_btn.clicked.connect(self.Delete)

                self.name_lbl=QtGui.QLabel(self)
                self.name_lbl.setText("Name")

                self.Enteredname=QtGui.QLineEdit(self)
                self.Enteredname.setPlaceholderText("Enter user name")

                self.buttonbox=QtGui.QVBoxLayout()
                self.buttonbox.addWidget(self.addUser_btn)
                self.buttonbox.addWidget(self.deleteUser_btn)
                self.hBox=QtGui.QHBoxLayout()
                self.Labelbox = QtGui.QHBoxLayout()
                self.Labelbox.addWidget(self.name_lbl)
                self.Labelbox.addWidget(self.Enteredname)
                self.hBox.addLayout(self.Labelbox)
                self.hBox.addLayout(self.buttonbox)
                wid = QtGui.QWidget(self)
                self.setCentralWidget(wid)
                wid.setLayout(self.hBox)
                self.setGeometry(50,50,600,400)
                self.show()

	def Enroll(self):
        	my_Enroll = enrolling()
                self.Enroll_result = my_Enroll.runscript()
        	if self.Enroll_result is None:
        		self.statusBar().showMessage("Registration Unsuccessful")	
        	else:
			
        		self.statusBar().showMessage("Registration Successful")
	def Delete(self):
		my_Delete = Deleting()
		self.Delete_result = my_Delete.runscript()
		if self.Delete_result is None:
			self.statusBar().showMessage("Deletion failed")
		else:
			self.statusBar().showMessage("Deleted successfully")

class Access(QtGui.QMainWindow):
    """
    The top-level class of the project2 Hub R Pi GUI-
    Controls everything on the R Pi for this demo
    """

    def __init__(self, use_websockets=False):
        """
        Setup the GUI, setup the Websockets Connection,
        provide timer and button callback updates, and display info
        """
	self.use_websockets=use_websockets

        super(Access,self).__init__()

	# connection variables
        self.ws_url = "ws://52.34.209.113:8080/websocket"
        self.ws_timeout  = 500
        self.ws_gui_timeout = 250 
        self.first_time=True
        self.drop_count = 0
        self.toggle = 0

	# Tornado Variables
        self.ws_ioloop = IOLoop.instance()
        self.ws = None

        # verify Variables
        self.verify_result=None

	# initalize the GUI
        self.initUI()

	
        if self.use_websockets: 
            # Connect to the Websockets server
            #self.connect()
        
            # setup the Websocket IO Loop
            self.my_p_callback = PeriodicCallback(self.keep_alive, self.ws_timeout, io_loop=self.ioloop)
            self.my_p_callback.start()
            self.ioloop.start()
        else:
            self.rootCAPath="/home/pi/Desktop/root-CA.crt"
            self.privateKeyPath="/home/pi/Desktop/Access01.private.key"
            self.certificatePath="/home/pi/Desktop/Access01.cert.pem"
            self.host="a1qhmcyp5eh8yq.iot.us-west-2.amazonaws.com"

            self.setupAWS()



    def cbkLoggedInUser(self, client, userdata, message):
        print("Received a new message: ")
        my_user = json.loads(message.payload)['message']
        print(my_user)
        self.user_data.setText("Welcome, "+str(my_user))



    def setupAWS(self):

        self.myAWSIoTMQTTClient = AWSIoTMQTTClient("basicPubSub")
        self.myAWSIoTMQTTClient.configureEndpoint(self.host, 8883)
        self.myAWSIoTMQTTClient.configureCredentials(self.rootCAPath, self.privateKeyPath, self.certificatePath)

        # AWSIoTMQTTClient connection configuration
        self.myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
        self.myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        self.myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
        self.myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
        self.myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
        
        # Connect and subscribe to AWS IoT
        self.myAWSIoTMQTTClient.connect()
        self.myAWSIoTMQTTClient.subscribe("AccessControl/LoggedInUser", 1, self.cbkLoggedInUser)
       


    def pubAccessState(self, state):
        armData = {}
        armData['armState']=str(state) 
        jsonData = json.dumps(armData)
        self.myAWSIoTMQTTClient.publish("AccessControl/armState", str(jsonData), 1)



    def pubLoggedInUser(self, uname, passwd):
        unameData = {}
        unameData['uname']=str(uname)
        unameData['passwd']=str(passwd)
        jsonData = json.dumps(unameData)
        self.myAWSIoTMQTTClient.publish("AccessControl/loggedInUser", str(jsonData), 1)


        
    def initUI(self):
        """ 
        Initialize + configure all QT modules used in the GUI
        And place them on the screen in the application
        """
	
	# create QT font
        font = QtGui.QFont()
        font.setFamily(QtCore.QString.fromUtf8("FreeMono"))
        font.setBold(True)
        font.setPointSize(20)

	# Create user-name label
        self.user_data=QtGui.QLabel(self)
        self.user_data.setFont(font)
        self.user_data.setText("Name")

	# Create alarm-state label
        self.state=QtGui.QLabel(self)
        self.state.setFont(font)
        self.state.setText("State")
	self.state.setStyleSheet("color: blue")

        # Label for username
        self.input1Label=QtGui.QLabel(self)
        self.input1Label.setText("Username")

        # Create text input
        self.input1=QtGui.QLineEdit(self)
        #self.input1.setHint("Username")
	
        self.unamebox = QtGui.QHBoxLayout()
        self.unamebox.addWidget(self.input1Label)
        self.unamebox.addWidget(self.input1)

        # Label for username
        self.input2Label=QtGui.QLabel(self)
        self.input2Label.setText("Password")

        # Create text input
        self.input2=QtGui.QLineEdit(self)
        self.input2.setEchoMode(QtGui.QLineEdit.Password)
        #self.input2.setHint("Password")

	# Password Button
	self.Submit_btn=QtGui.QPushButton("Submit", self)
	self.Submit_btn.clicked.connect(self.sendLoggedInUser)
        
        self.passwdbox = QtGui.QHBoxLayout()
        self.passwdbox.addWidget(self.input2Label)
        self.passwdbox.addWidget(self.input2)
        self.passwdbox.addWidget(self.Submit_btn)

	# Create status bar
	self.statusBar()
	self.statusBar().setStyleSheet("color: red; font-size:18pt")

	# Create Arm button        
	Arm_btn=QtGui.QPushButton("Arm",self)
        Arm_btn.clicked.connect(self.sendArm)
	
	# Create Disarm button        
	Disarm_btn=QtGui.QPushButton("Disarm",self)
        Disarm_btn.clicked.connect(self.sendDisarm)
        
        #Create Fingerprint button
        self.fingerprint_btn=QtGui.QPushButton("Fingerprint",self)
        self.fingerprint_btn.clicked.connect(self.verify)

	# Now create layout

        wid = QtGui.QWidget(self)
        self.setCentralWidget(wid)

	# put buttons in an hbox
	hbox = QtGui.QHBoxLayout()
        hbox.addWidget(Arm_btn)
        hbox.addWidget(Disarm_btn)
        
	# put buttons + status in a vbox
	vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.user_data)
        vbox.addWidget(self.state)
        vbox.addLayout(self.unamebox)
        vbox.addLayout(self.passwdbox)
        
        #fingerprint button
        fingerprintbox = QtGui.QVBoxLayout()
        fingerprintbox.addWidget(self.fingerprint_btn)
        fingerprintbox.addLayout(vbox)
        # combine layouts
        fingerprintbox.addLayout(hbox)
	wid.setLayout(fingerprintbox)

        self.setGeometry(50,50,600,400)
        self.setWindowTitle('Project 2 Demo')
        self.show()
    
    def verify(self):
        my_verify = verifier()
        print("Verification")
        self.verify_result = my_verify.runscript()
        if self.verify_result is None:
    		self.pubAccessState("Armed")
        	self.statusBar().showMessage("Access Denied")	
        else:
    		self.pubAccessState("Disarmed")
		self.hide()
        	self.newWindow= Enrolling(self)
                


    def sendLoggedInUser(self):
        print("SEND USER")
        uname =self.input1.text()
        passwd=self.input2.text()
        self.pubLoggedInUser(uname, passwd)
        
    def sendArm(self):
        """
        Change the state of the Arm_status table in MySQL to 'armed'
        """

        print("ARM SYSTEM")        
        self.pubAccessState(state="Armed")
        
        #if self.ws is None:
        #    self.connect()
        #else:
        #    print("ARM SYSTEM")        
        #    self.ws.write_message("set_arm")


    def sendDisarm(self):
        """
        Change the state of the Arm_status table in MySQL to 'disarmed'
        """
        
        print("DISARM SYSTEM")        
        self.pubAccessState(state="Disarmed")

        #if self.ws is None:
        #    self.connect()
        #else:
        #    print("DISARM SYSTEM")        
        #    self.ws.write_message("set_dis")

        
    @gen.coroutine
    def connect(self):
        """
        Connect to the websockets server
        on our ec2 server
        """

        #print "trying to connect"

        try:
            self.ws = yield websocket_connect(self.url)
        except Exception, e:
            print "connection error"
        else:
            #print "connected"
            pass


    def sendAndRead(self):
        """ 
        query for login and arm/disarm status and read responses
        """

        #print("Sending messages!")
        self.toggle = 1 - self.toggle

        if self.toggle == 1:
		self.ws.write_message("login_status")
		self.readInput()
        else:
		self.ws.write_message("arm_status")
		self.readInput()



    @gen.coroutine
    def readInput(self):
        """
        read a message back from websockets and set update
        """
 
        try:
            msg = yield self.ws.read_message()
        except:
            self.drop_count += 1
            if self.drop_count >= 2:
		    self.statusBar().showMessage('Connection Error!')
                    self.user_data.setText("Disconnected!")
                    self.state.setText("")
            return

        self.drop_count = 0

        # data is sent 
        self.statusBar().clearMessage()
        indata = msg.split(":")
        if indata[0] == "name" :
            self.user_data.setText("Welcome, "+indata[1])
        elif indata[0] == "state" :
            self.state.setText("Arm/Disarm state is: "+indata[1])
        #print ("Received Data: '"+indata[1]+"'")


        
    def keep_alive(self):
        """ 
        heartbeat function of program- send commands
        and receive data to display
        """
        
        # reconnect if connection has been lost
        if self.ws is None:
            self.connect()
        else:
            if self.first_time:
                self.first_time = False
            else:
                try:
                    self.ioloop.start()
                except:
                    self.connect()
            
            self.sendAndRead()
            
            self.ioloop.stop()
            self.my_p_callback.stop()
            QTimer.singleShot(self.gui_timeout, self.poll_websockets)
            

    def poll_websockets(self):
        """ Take control from GUI for websockets"""

        self.my_p_callback.start()
        self.ioloop.start()


if __name__ == "__main__":
    """ Run program if called as main function """
    app = QtGui.QApplication(sys.argv)
    access=Access()
    sys.exit(app.exec_())
