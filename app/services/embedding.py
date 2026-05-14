import os
import numpy as np
from sentence_transformers import SentenceTransformer

# 强制离线模式
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'

class EmbeddingService:
    def __init__(self, model_name: str = '/app/local_model'):
        self.model = SentenceTransformer(model_name)
        self.dimension = 384

    def encode(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(texts, show_progress_bar=False)

embedding_service = EmbeddingService()