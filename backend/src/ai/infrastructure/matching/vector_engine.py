import torch
import time
import re
import numpy as np
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer, util
from loguru import logger
from rank_bm25 import BM25Okapi

from src.ai.domain.models import SearchCandidate


class HybridSearchEngine:
    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Initializing HybridSearchEngine on device: {self.device}")

        try:
            self.model = SentenceTransformer(model_name, device=self.device)
            logger.info(f"Model {model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise RuntimeError(f"Semantic model loading failed: {e}")

        self.products: List[Dict] = []
        self.embeddings: Optional[torch.Tensor] = None
        self.bm25: Optional[BM25Okapi] = None

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\w+', text.lower())

    def index_products(self, products: List[Dict]) -> None:
        if not products:
            logger.warning("No products provided for indexing")
            return

        self.products = products

        logger.info(f"Starting HYBRID indexing for {len(products)} products...")
        start_time = time.time()

        texts_to_embed = [f"passage: {p['name_pl']}" for p in products]
        try:
            self.embeddings = self.model.encode(
                texts_to_embed,
                batch_size=32,
                convert_to_tensor=True,
                device=self.device,
                normalize_embeddings=True,
                show_progress_bar=False
            )
        except RuntimeError as e:
            if "out of memory" in str(e):
                logger.warning("CUDA OOM during indexing, falling back to CPU")
                self.embeddings = self.model.encode(
                    texts_to_embed,
                    batch_size=16,
                    convert_to_tensor=True,
                    device="cpu",
                    normalize_embeddings=True
                )
            else:
                raise e

        tokenized_corpus = [self._tokenize(p['name_pl']) for p in products]
        self.bm25 = BM25Okapi(tokenized_corpus)

        elapsed = time.time() - start_time
        logger.info(f"Hybrid Indexing complete in {elapsed:.2f}s")

    def search(self, query: str, top_k: int = 20, alpha: float = 0.3) -> List[SearchCandidate]:
        if not self.products or self.embeddings is None or self.bm25 is None:
            logger.warning("Search called on empty index")
            return []

        query_vec = self.model.encode(
            [f"query: {query}"],
            convert_to_tensor=True,
            device=self.device,
            normalize_embeddings=True
        )
        vector_scores = util.cos_sim(query_vec, self.embeddings)[0].cpu().numpy()

        tokenized_query = self._tokenize(query)
        bm25_scores = self.bm25.get_scores(tokenized_query)

        if len(tokenized_query) > 0 and bm25_scores.max() > 0:
            bm25_norm = bm25_scores / bm25_scores.max()
        else:
            bm25_norm = np.zeros_like(bm25_scores)

        vector_norm = np.clip(vector_scores, 0, 1)

        final_scores = (alpha * vector_norm) + ((1 - alpha) * bm25_norm)

        top_indices = np.argsort(final_scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            idx = int(idx)
            product = self.products[idx]

            debug_info = f"Hybrid(V={vector_norm[idx]:.2f}, B={bm25_norm[idx]:.2f}, Final={final_scores[idx]:.2f})"

            results.append(SearchCandidate(
                product_id=product['id'],
                name=product['name_pl'],
                category=product.get('category', 'UNKNOWN'),
                score=float(final_scores[idx]),
                passed_guard=False,
                notes=debug_info
            ))

        return results

    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        for p in self.products:
            if p['id'] == product_id:
                return p
        return None
