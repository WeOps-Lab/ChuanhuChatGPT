import uuid
from io import BytesIO

import requests
from PIL import Image
import logging
import os
from modules.models.base_model import BaseLLMModel
import base64


class DallE(BaseLLMModel):
    def __init__(self, model_name, user_name=""):
        super().__init__(model_name=model_name, user=user_name)
        self.api_base = os.getenv("AZURE_DALL_OPENAI_API_BASE_URL", "")
        self.api_key = os.getenv("AZURE_DALL_OPENAI_API_KEY", "")
        self.deploy_name = os.getenv("AZURE_DALL_OPENAI_DEPLOY_NAME", "dall-e-3")
        self.session_id = None
        self.last_conv_id = None
        self.image_bytes = None
        self.image_path = None
        self.chat_history = []
        self.image_size = '1024x1024'
        self.image_quality = 'hd'
        self.image_style = 'vivid'
        self.api_version = "2023-12-01-preview"

    def reset(self, remain_system_prompt=False):
        self.session_id = str(uuid.uuid4())
        self.last_conv_id = None
        return super().reset()

    def image_to_base64(self, image_path):
        # 打开并加载图片
        img = Image.open(image_path)

        # 获取图片的宽度和高度
        width, height = img.size

        # 计算压缩比例，以确保最长边小于4096像素
        max_dimension = 2048
        scale_ratio = min(max_dimension / width, max_dimension / height)

        if scale_ratio < 1:
            # 按压缩比例调整图片大小
            new_width = int(width * scale_ratio)
            new_height = int(height * scale_ratio)
            img = img.resize((new_width, new_height), Image.LANCZOS)

        # 将图片转换为jpg格式的二进制数据
        buffer = BytesIO()
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.save(buffer, format="JPEG")
        binary_image = buffer.getvalue()

        # 对二进制数据进行Base64编码
        base64_image = base64.b64encode(binary_image).decode("utf-8")

        return base64_image

    def try_read_image(self, filepath):
        def is_image_file(filepath):
            # 判断文件是否为图片
            valid_image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"]
            file_extension = os.path.splitext(filepath)[1].lower()
            return file_extension in valid_image_extensions

        if is_image_file(filepath):
            logging.info(f"读取图片文件: {filepath}")
            self.image_bytes = self.image_to_base64(filepath)
            self.image_path = filepath
        else:
            self.image_bytes = None
            self.image_path = None

    def get_answer_at_once(self):
        question = self.history[-1]["content"]
        conv_id = str(uuid.uuid4())
        self.last_conv_id = conv_id
        url = f"{self.api_base}/openai/deployments/{self.deploy_name}/images/generations?api-version={self.api_version}"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        body = {
            "prompt": question,
            "size": self.image_size,
            "n": 1,
            "quality": self.image_quality,
            "style": self.image_style
        }

        submission = requests.post(url, headers=headers, json=body)
        if submission.status_code == 200:
            image_url = submission.json()["data"][0]["url"]
            return f'![{question}]({image_url})', 1
        else:
            return f'![{submission.content}]', 1
