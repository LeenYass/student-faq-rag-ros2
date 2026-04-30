#!/usr/bin/env python3

import os
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from ollama import Client


class OllamaPublisher(Node):
    def __init__(self):
        super().__init__('ollama_publisher')

        self.declare_parameter('model', 'qwen2.5:0.5b')
        self.declare_parameter('rag_path', '/home/aisd/aisd_ali/knowledge/ragfile.txt')

        self.model = self.get_parameter('model').get_parameter_value().string_value
        self.rag_path = self.get_parameter('rag_path').get_parameter_value().string_value

        self.client = Client(host='http://localhost:11434')
        self.rag_context = ""

        if os.path.isfile(self.rag_path):
            try:
                with open(self.rag_path, 'r', encoding='utf-8') as f:
                    self.rag_context = f.read().strip()
                self.get_logger().info(f'Loaded RAG file: {self.rag_path}')
            except Exception as e:
                self.get_logger().error(f'Failed to read RAG file: {e}')
        else:
            self.get_logger().warn(f'RAG file not found: {self.rag_path}')

        self.pub = self.create_publisher(String, 'ollama_reply', 10)
        self.sub = self.create_subscription(String, 'words', self.cb, 10)
        self.busy = False

    def cb(self, msg: String):
        text = msg.data.strip()

        if text == "" or self.busy:
            return

        self.busy = True
        self.get_logger().info(f'WORDS: "{text}"')

        try:
            reply = self.ask_ollama(text)
        except Exception as e:
            self.get_logger().error(f'Ollama error: {e}')
            self.busy = False
            return

        reply = (reply or "").strip()

        if reply:
            out = String()
            out.data = reply
            self.pub.publish(out)
            self.get_logger().info(f'OLLAMA_REPLY: "{out.data}"')

        self.busy = False

    def ask_ollama(self, user_text: str) -> str:
        system_parts = [
            "You are a helpful university student FAQ assistant.",
            "Answer using only the background facts provided below.",
            "Only answer the specific question being asked.",
            "Do not use unrelated sections.",
            "If the answer is not in the background facts, say you could not find it in the provided student documents.",
            "Reply in one short helpful sentence."
        ]

        if self.rag_context:
            system_parts.append("Background facts:")
            system_parts.append(self.rag_context)

        system_prompt = "\n\n".join(system_parts)

        res = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        )

        return res["message"]["content"]


def main(args=None):
    rclpy.init(args=args)
    node = OllamaPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
