class AudioProcessingException(Exception):
    pass


class TranscriptionFailedException(AudioProcessingException):
    def __init__(self, message: str = "Failed to transcribe audio"):
        self.message = message
        super().__init__(self.message)


class NERExtractionFailedException(AudioProcessingException):
    def __init__(self, message: str = "Failed to extract food items from text"):
        self.message = message
        super().__init__(self.message)


class LLMFallbackException(AudioProcessingException):
    def __init__(self, message: str = "LLM fallback extraction failed"):
        self.message = message
        super().__init__(self.message)


class ProductNotFoundError(AudioProcessingException):
    def __init__(self, product_name: str):
        self.product_name = product_name
        self.message = f"Product '{product_name}' not found in database"
        super().__init__(self.message)


class AudioFormatError(AudioProcessingException):
    def __init__(self, message: str = "Invalid or unsupported audio format"):
        self.message = message
        super().__init__(self.message)


class AudioTooLongError(AudioProcessingException):
    def __init__(self, duration_seconds: float, max_seconds: float = 60.0):
        self.duration_seconds = duration_seconds
        self.max_seconds = max_seconds
        self.message = f"Audio too long: {duration_seconds:.1f}s (max: {max_seconds:.1f}s)"
        super().__init__(self.message)
