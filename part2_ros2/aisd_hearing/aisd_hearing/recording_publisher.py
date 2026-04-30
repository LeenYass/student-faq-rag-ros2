#!/usr/bin/env python
from ament_index_python.packages import get_package_share_directory 
from sys import byteorder
import sys
from array import array
from struct import pack
import os

import pyaudio
import wave
import audioop

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16

class RecordingPublisher(Node):
    def __init__(self):
        super().__init__('recording_publisher')
        self.publisher_ = self.create_publisher(String, 'recording', 10)
        self.listening = False
        self.create_timer(1,self.listen) # check once per second

    def listen(self):
        if self.listening:
            return
        else:
            self.listening = True
        ##################################
        # TODO (not required for Assignment 3) Change the audio_path to a parameter
        ##################################
        audio_path = get_package_share_directory('aisd_hearing')
        audio_path =  audio_path + "/recordings"
        os.makedirs(audio_path, exist_ok=True)
        device = find_device(sys.argv)
        rate = 48000
        while 1:
            current_time = str(self.get_clock().now().nanoseconds)
            audio_file = "{}/{}.wav".format(audio_path, current_time)

            try:
                record_to_file(audio_file, rate=rate, device=device)
            except Exception as e:
                print(f"Error recording audio: {e}")
                sys.exit(1)
        
            msg = String()
            msg.data = audio_file
            self.publisher_.publish(msg)

##############################
# There are 6 methods needed from unr_deepspeech_client.py
# Your task here is to figure out which methods those are, and paste them
# here in place of this comment
# You are not required to make those methods part of the
# RecordingPublsher class definition, but that would be better programming style.
##############################
def is_silent(snd_data):
    "Returns 'True' if below the 'silent' threshold"
    return max(snd_data) < THRESHOLD

def normalize(snd_data):
    "Average the volume out"
    MAXIMUM = 16384
    times = float(MAXIMUM)/max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i*times))
    return r

def trim(snd_data):
    "Trim the blank spots at the start and end"
    def _trim(snd_data):
        snd_started = False
        r = array('h')

        for i in snd_data:
            if not snd_started and abs(i)>THRESHOLD:
                snd_started = True
                r.append(i)

            elif snd_started:
                r.append(i)
        return r

    # Trim to the left
    snd_data = _trim(snd_data)

    # Trim to the right
    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data

def add_silence(snd_data, seconds, rate):
    "Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
    r = array('h', [0 for i in range(int(seconds*rate))])
    r.extend(snd_data)
    r.extend([0 for i in range(int(seconds*rate))])
    return r

def record(rate, device):
    """
    Record a word or words from the microphone and
    return the data as an array of signed shorts.

    Normalizes the audio, trims silence from the
    start and end, and pads with 0.5 seconds of
    blank sound to make sure VLC et al can play
    it without getting chopped off.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=rate,
        input=True, output=True, frames_per_buffer=CHUNK_SIZE,
        input_device_index=device)

    num_silent = 0
    snd_started = False

    r = array('h')

    while 1:
        # little endian, signed short
        snd_data = array('h', stream.read(CHUNK_SIZE, exception_on_overflow=False))
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

        silent = is_silent(snd_data)

        if silent and snd_started:
            num_silent += 1
        elif not silent and not snd_started:
            snd_started = True

        if snd_started and num_silent > 30:
            break

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    r = normalize(r)
    r = trim(r)
    r = add_silence(r, 0.5, rate)
    return sample_width, r

def record_to_file(path, rate, device):
    "Records from the microphone and outputs the resulting data to 'path'"
    sample_width, data = record(rate, device)

    if rate != 16000:
        data_16GHz = audioop.ratecv(data, sample_width, 1, rate, 16000, None)[0]
    else:
        data_16GHz = pack('<' + ('h'*len(data)), *data)
        
    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(16000)
    wf.writeframes(data_16GHz)
    wf.close()
    
def find_device(args):
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    
    device = -1
    
    if len(args) > 1 and args[1] != "--ros-args":
        if args[1] == "-1":
            print("\nListing audio devices and exiting: ")
            # Print audio devices
            # Ref: https://stackoverflow.com/a/39677871
            for i in range(0, numdevices):
                if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                    print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
            sys.exit(0)
        else:
            try:
                device = int(args[1])
            except ValueError:
                print("Invalid audio device id.")
                print("usage: ros2 run aisd_hearing recording_publisher [audio_device_index]")
                sys.exit(1)
    elif len(args) == 1 or (len(args) > 1 and args[1] == "--ros-args"): # search for default device        
        for i in range(0, numdevices):
             if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                 if p.get_device_info_by_host_api_device_index(0, i).get('name') == 'default':
                     device = i
                     print("Using device {}".format(i))
                     break
        if device == -1:
            print("Unable to find default device. Here are the available audio devices: ")
            for i in range(0, numdevices):
                if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                    print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
            sys.exit(1)
    else:
        print("usage: ros2 run aisd_hearing recording_publisher [audio_device_index]")
        sys.exit(1)

    return device
        
def main(args=None):
    rclpy.init(args=args)

    # Create an instance of your node
    node = RecordingPublisher()

    # Keep the node running so timers and callbacks keep working
    rclpy.spin(node)

    # Clean up when the node is stopped (Ctrl+C)
    node.destroy_node()
    rclpy.shutdown() 
    
if __name__ == "__main__":
    main()
