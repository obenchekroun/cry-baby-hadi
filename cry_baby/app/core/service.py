import queue
import threading
from typing import Optional
import time

import paho.mqtt.client as paho
from paho import mqtt

import hexalog.ports

from cry_baby.app.core import ports


class CryBabyService(ports.Service):
    def __init__(
        self,
        logger: hexalog.ports.Logger,
        classifier: ports.Classifier,
        recorder: ports.Recorder,
        repository: ports.Repository,
    ):
        self.logger = logger
        self.classifier = classifier
        self.recorder = recorder
        self.repository = repository

        self.client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
        self.client.on_connect = self.on_connect

        # enable TLS for secure connection
        self.client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        # set username and password
        self.client.username_pw_set("<login>", "<password>")
        # connect to HiveMQ Cloud on port 8883 (default for MQTT)
        self.client.connect("<Cluster URL>", 8883)

        # setting callbacks, use separate functions like above for better visibility
        self.client.on_subscribe = self.on_subscribe
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish

        # subscribe to all topics of encyclopedia by using the wildcard "#"
        self.client.subscribe("#", qos=1)

        self.client.loop_start()

    def evaluate_from_microphone(
        self,
    ) -> float:
        """
        Record audio and classify it
        return the probability that the audio contains a baby crying
        """
        self.logger.info("Service beginning to evaluate audio from microphone")
        audio_file = self.recorder.record()
        return self.classifier.classify(audio_file)

    def continously_evaluate_from_microphone(self) -> Optional[queue.Queue]:
        file_written_notification_queue = self.recorder.continuously_record()
        signal_thread = threading.Thread(
            target=self._handle_files_written,
            args=(file_written_notification_queue, self.classifier),
        )
        signal_thread.daemon = True
        signal_thread.start()
        self.logger.info(
            "Service beginning to continuously evaluate audio from microphone"
        )
        self.thread = signal_thread

    def _handle_files_written(
        self, file_written_queue: queue.Queue, classifier: ports.Classifier
    ):
        last_exec = 0
        while True:
            file_path = file_written_queue.get()
            self.logger.debug(f"File written: {file_path}")
            prediction = classifier.classify(file_path)
            if (prediction > 0.1):
                now = time.time()
                if now - last_exec >= 15:
                    # a single publish, this can also be done in loops, etc.
                    text = f'Bébé pleure avec un facteur de {round(prediction*100,1)} %'
                    self.client.publish("push_notif", payload=text, qos=1)
                    last_exec = now
            self.logger.debug(f"Prediction: {prediction}")
            self.repository.save(file_path, prediction)

    def stop_continuous_evaluation(self):
        self.recorder.tear_down()
        self.logger.info("Service stopping continuous evaluation")
        print(self.thread)

    def on_connect(self, client, userdata, flags, rc, properties=None):
        """
            Prints the result of the connection with a reasoncode to stdout ( used as callback for connect )

            :param client: the client itself
            :param userdata: userdata is set when initiating the client, here it is userdata=None
            :param flags: these are response flags sent by the broker
            :param rc: stands for reasonCode, which is a code for the connection result
            :param properties: can be used in MQTTv5, but is optional
        """
        print("CONNACK received with code %s." % rc)


    # with this callback you can see if your publish was successful
    def on_publish(self, client, userdata, mid, properties=None):
        """
            Prints mid to stdout to reassure a successful publish ( used as callback for publish )

            :param client: the client itself
            :param userdata: userdata is set when initiating the client, here it is userdata=None
            :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
            :param properties: can be used in MQTTv5, but is optional
        """
        print("mid: " + str(mid))


    # print which topic was subscribed to
    def on_subscribe(self, client, userdata, mid, granted_qos, properties=None):
        """
            Prints a reassurance for successfully subscribing

            :param client: the client itself
            :param userdata: userdata is set when initiating the client, here it is userdata=None
            :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
            :param granted_qos: this is the qos that you declare when subscribing, use the same one for publishing
            :param properties: can be used in MQTTv5, but is optional
        """
        print("Subscribed: " + str(mid) + " " + str(granted_qos))


    # print message, useful for checking if it was successful
    def on_message(self, client, userdata, msg):
        """
            Prints a mqtt message to stdout ( used as callback for subscribe )

            :param client: the client itself
            :param userdata: userdata is set when initiating the client, here it is userdata=None
            :param msg: the message with topic and payload
        """
        print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
