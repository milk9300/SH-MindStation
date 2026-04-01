import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    本地向量化服务，使用轻量级多语言模型。
    """
    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        try:
            logger.info(f"Loading embedding model: {model_name}...")
            self.model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            self.model = None

    def get_embedding(self, text: str) -> list:
        if not self.model:
            return []
        # 将文本转化为向量列表
        embedding = self.model.encode(text)
        return embedding.tolist()

# 单例模式
embedding_service = EmbeddingService()
