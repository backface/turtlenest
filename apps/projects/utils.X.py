from fastembed import TextEmbedding as Embedding
from django.conf import settings
import ollama


# EMBEDDING_MODEL = 'mxbai-embed-large'
EMBEDDING_MODEL = "all-minilm"


def get_embeddings_ollama(text, model=EMBEDDING_MODEL):
    client = ollama.Client(host="http://aim:11434")
    return client.embeddings(model=model, prompt=text)["embedding"]


def get_embeddings_fastembed(text):
    cache_dir = settings.MEDIA_ROOT / "models"
    embedding_model = Embedding(
        model_name="BAAI/bge-small-en", max_length=512, cache_dir=str(cache_dir)
    )
    embeddings_generator = embedding_model.embed(text)  # reminder this is a generator
    return list(embeddings_generator)[0]


def get_embeddings(text, model=EMBEDDING_MODEL):
    return get_embeddings_fastembed(text)
