import paho.mqtt.client as mqtt  # import the client1
import time
import random
broker_address = "localhost"
# broker_address="xxxxxxxxxxxxx"
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import json
import numbers
from commands import *
from IClient import IClient
from pprint import pprint

GPIO.setmode(GPIO.BOARD)

## List with systemID, Broker IP and Port
## and target IP for video streaming 
with open('settings.json') as data_file:
        settingsdata = json.load(data_file)
        
## List with configurations for developers        
with open('config.json') as data_file:
        configdata = json.load(data_file)

## List with commands, the system should be able to execute
with open('lookuptable.json') as data_file:
        lookuptable = json.load(data_file)

systemID = settingsdata["systemid"]
## The system connects to a topic that is the main topic and the systemID as a 
baseTopic = configdata["baseTopic"] + "/" + systemID
connectionInfoMessage = configdata["connectionInfoMessage"]
## Element from library that makes the servo moves smoother
servoblaster = open('/dev/servoblaster','w')

def on_message(client, userdata, message):
    print("message received ", str(message.payload.decode("utf-8")))
    print("message topic=", message.topic)
    print("message qos=", message.qos)
    print("message retain flag=", message.retain)


def on_log(client, userdata, level, buf):
    print('log: ', buf)


def on_disconnect(client, userdata, rc=0):
    print("Disconnect: ", str(rc))
    logging.debug("Disconnected: " + str(rc))
    # client.reconnect()
    client.loop_stop()


def on_publish(client, userdata, mid):
    print("mid: ", str(mid))


def send_data_to_broker(message, topic):
    print("creating new instance")

class mqttClient(IClient):
    """
    Main Class for the current system. Implements IClient.
    """


    def initalize(self, systemID):
        """
        Initialize mqtt Client of paho library
        :param systemID: The specific ID of the RaspberryPi system
        :return: Returns an mqtt-library object that takes command (e.g. connect)
        
        """
        client = mqtt.Client(client_id = systemID)
        return client

    def connect (self, client, mqttBrokerAddress, mqttBrokerPort):
        """
        Connects to specific mqttBroker with connect function of mqtt library
        :param client: client object
        :param mqttBrokerAddress: IP-Address of Mqtt Broker
        :para mqttBroker Port: Port of Mqtt Broker
        """        
        client.connect(mqttBrokerAddress, mqttBrokerPort)
       

    def subscribe (self, client):
        """
        subscribe a client to a topic
        :param client: client object
        """
        client.subscribe(baseTopic + "/#")
        print(connectionInfoMessage + " : " + baseTopic)

    def react(self, client):
        """
        Uses the on_message function of the mqtt library.
        When there is a new message execute reactOnMessages() function
        :param client: client object
        """
        client.on_message = self.reactOnMessages
        client.loop_forever()
        
    def reactOnMessages(self, client, userdata, msg):
        """
        Compares an incoming message (last subtopic) with the lookuptable.json
        and executes functions from the commands module.
        
        :param client: client object
        :param userdata: user defined data of any type that is passed as the userdata parameter to callbacks
        :param msg: The whole message object with msg.payload, msg.topic, ...
        """

        print(msg.topic + str(msg.payload))

        # get The last subtopic of the message, that represents the function that should be executed.
        subtopic = msg.topic.rsplit('/',1)[1]

        try:
            # Match the subtopic with the command name
            commandName = lookuptable[subtopic][0]["Command"]
            # Get Possible parameters that should be executed when calling the command
            commandOptionNames = (lookuptable[subtopic][0]["Options"])
            # Store the command Paramers in an array
            commandOptions= []
            for command in commandOptionNames:
                commandOptions.append(configdata[command])

            ## Create the command Class
            constructor = globals()[commandName]
            ## give the command block possible parameters (stored in lookuptable)
            try:
                command = constructor(commandOptions)   
            except TypeError:
                command = constructor()

            ## This is need when the variable movedata is needed    
            if lookuptable[subtopic][0]["Servoblaster"] == "true" and lookuptable[subtopic][0]["VaryingMoves"] == "true" :
                command.execute(servoblaster, str(msg.payload))
            ## For static moves
            elif lookuptable[subtopic][0]["Servoblaster"] == "true" :
                command.execute(servoblaster)
            ## For all other functions
            else:
                command.execute()
        ## If the command is unkown , do nothing        
        except KeyError:
           pass
        
        ## Has to be called after every move	        
        servoblaster.flush()
        

    client = mqtt.Client("P1", protocol=mqtt.MQTTv311)  # create new instance

    client.on_message = on_message

    client.on_publish = on_publish

    # client.on_log = on_log

    client.on_disconnect = on_disconnect

    print("connecting to broker located in: ", broker_address)
    # connect to broker
    client.connect(broker_address, keepalive=100)
    print("Subscribing to topic: ", topic)
    client.subscribe(topic=topic)
    print("Publishing message to: ", topic)
    client.publish(topic, message)
    time.sleep(4)


while True:
    print("\n\n\n\n\n\n[1]: Manual Data Entry \n[2]: Temperature Simulation\n\tSends Message if T > 40 °C\n[3]: Distance Simulation\n\tSends Message if you go further than 300 cm\n")
    Scenario = input(
        "What kind of scenario would like to simulated?(input number)")
    if Scenario == '1':
        topic = input("What topic would you like to store your data under: ")
        message = input("what do you want do you want to send: ")
        send_data_to_broker(message, topic)
    elif Scenario == '2':
        T = random.triangular(20, 47)
        if T >= 40:
            send_data_to_broker(T, "Temperature")
        else:
            print("Temperature turned out less than 40: ", T)
            time.sleep(2)
    elif Scenario == '3':
        print("Simulating distance values...")
        time.sleep(2)
        D = random.randint(0, 300)
        if D >= 300:
            send_data_to_broker(D, "Distance")
        else:
            print("You're still close!! ( "+str(D * 0.01) +" Meters)")
            time.sleep(2)
    else:
        pass
