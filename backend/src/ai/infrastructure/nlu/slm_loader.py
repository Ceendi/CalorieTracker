from pathlib import Path
from typing import Optional, Any
from loguru import logger

try:
    from huggingface_hub import hf_hub_download
    from llama_cpp import Llama
except ImportError:
    Llama = None
    hf_hub_download = None


class SLMLoader:
    _instance: Optional['SLMLoader'] = None
    _model: Any = None

    REPO_ID = "second-state/Bielik-4.5B-v3.0-Instruct-GGUF"
    FILENAME = "Bielik-4.5B-v3.0-Instruct-Q5_K_S.gguf"
    
    N_CTX = 2048 
    N_BATCH = 512
    N_GPU_LAYERS = -1 
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SLMLoader, cls).__new__(cls)
        return cls._instance

    def _get_models_dir(self) -> Path:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        models_dir = base_dir / "models"
        models_dir.mkdir(exist_ok=True)
        return models_dir

    def load_model(self) -> Any:
        if self._model is not None:
            return self._model
            
        if Llama is None:
            raise ImportError("llama-cpp-python is not installed")

        models_dir = self._get_models_dir()
        model_path = models_dir / self.FILENAME
        
        if not model_path.exists():
            logger.info(f"Downloading SLM model: {self.FILENAME} from {self.REPO_ID}...")
            try:
                hf_hub_download(
                    repo_id=self.REPO_ID,
                    filename=self.FILENAME,
                    local_dir=str(models_dir)
                )
                logger.info("Model downloaded successfully.")
            except Exception as e:
                logger.error(f"Failed to download model: {e}")
                raise RuntimeError(f"Could not download SLM model: {e}")
        
        logger.info(f"Loading SLM model from {model_path}...")
        try:
            self._model = Llama(
                model_path=str(model_path),
                n_ctx=self.N_CTX,
                n_batch=self.N_BATCH,
                n_gpu_layers=self.N_GPU_LAYERS,
                verbose=False
            )
            logger.info("SLM model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SLM model: {e}")
            raise RuntimeError(f"Could not load SLM model: {e}")
            
        return self._model

    @classmethod
    def get_model(cls) -> Llama:
        loader = cls()
        return loader.load_model()
