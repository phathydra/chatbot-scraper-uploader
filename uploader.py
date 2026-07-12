from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def upload(file_path: Path):
    """
    Upload file to vector store
    """
    with open(file_path, "rb") as file_stream:
        result = (
            client.vector_stores.files.upload_and_poll(
                vector_store_id=os.getenv("VECTOR_STORE_ID"),
                file= file_stream
            )
        )

    return result

def remove(file_id):
    """
    Remove old file from the vector store
    """
    return client.vector_stores.files.delete(
        vector_store_id=os.getenv("VECTOR_STORE_ID"),
        file_id=file_id
    )

