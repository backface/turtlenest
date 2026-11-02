from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.projects import models
from apps.projects.views import MAX_SEARCH_LENGTH


class EmbeddingModelCacheTests(SimpleTestCase):
    def setUp(self):
        patcher = mock.patch.object(models, "_embedding_model", None)
        patcher.start()
        self.addCleanup(patcher.stop)

    @mock.patch.object(models, "Embedding")
    def test_model_is_loaded_once(self, embedding):
        embedding.return_value.embed.side_effect = lambda text: iter([[0.1, 0.2]])
        self.assertEqual(models.create_embeddings("one"), [0.1, 0.2])
        models.create_embeddings("two")
        models.create_embeddings("three")
        embedding.assert_called_once()
        self.assertEqual(embedding.return_value.embed.call_count, 3)


class SearchQueryLengthTests(TestCase):
    @mock.patch("apps.projects.views.create_embeddings", return_value=[0.0] * 384)
    def test_semantic_query_is_truncated(self, create_embeddings):
        response = self.client.get(
            reverse("projects:search", args=["semantic"]), {"q": "x" * 10000}
        )
        self.assertEqual(response.status_code, 200)
        create_embeddings.assert_called_once_with("x" * MAX_SEARCH_LENGTH)
