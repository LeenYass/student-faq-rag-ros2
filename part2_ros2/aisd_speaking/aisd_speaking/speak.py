import io
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
from aisd_msgs.srv import Speak

import rclpy
from rclpy.node import Node


class SpeakService(Node):

    def __init__(self):
        super().__init__('speak_service')
        self.srv = self.create_service(
            Speak,              # service type
            'speak',            # service name
            self.speak_callback # callback function
        )

    def speak_callback(self, request, response):
        # Log the text we are about to speak
        self.get_logger().info(f"Speaking: {request.words}")

        # Create an in-memory bytes buffer to store the generated MP3 audio
        with io.BytesIO() as f:
            # Convert the requested words into speech (MP3 format) and write into buffer
            gTTS(text=request.words, lang='en').write_to_fp(f)

            # Move the file pointer back to the start of the buffer
            f.seek(0)

            # Load the MP3 data from the buffer as an AudioSegment
            song = AudioSegment.from_file(f, format="mp3")

            # Play the audio through the default output device
            play(song)

        # Indicate success in the service response
        response.response = "OK"

        # Return the response object
        return response



def main(args=None):
    # Initialize the ROS 2 Python client library
    rclpy.init(args=args)

    # Create an instance of your SpeakService node
    node = SpeakService()

    # Keep the node running to process incoming service requests
    rclpy.spin(node)

    # Clean up on shutdown
    node.destroy_node()
    rclpy.shutdown()



if __name__ == '__main__':
    main()
