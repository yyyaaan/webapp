import json
from logging import getLogger
from openai import OpenAI

client = OpenAI()
logger = getLogger("chat.service")


class ChatService:

    file_output_dir: str = "/mnt/"

    def save_chat_state(self, id, content, title: str = "chat_default"):
        
        file_name = f"{self.file_output_dir}/{title}_{id}.json"
        logger.info(f"Saving state {file_name}...")

        try:
            content_str = json.dumps(content, indent=2)
            with open(file_name, "w+", encoding="utf-8") as f:
                f.write(content_str)
            logger.info(f"Saved, length={len(content_str)}")

        except Exception as e:
            raise Exception(f"Failed to save chat state: {e}")


chat_service = ChatService()