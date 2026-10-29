"""Offline, CPU-only sentence embeddings using a pinned MiniLM ONNX model.

The WordPiece tokenizer and encoder are pretrained. Attention-mask mean
pooling and cosine normalization are implemented here; no remote inference
or executable model-repository code is used.
"""
from pathlib import Path
import numpy as np
from app.config import EMBED_PATH


class SentenceEncoder:
    def __init__(self, model_dir=EMBED_PATH):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        model_dir = Path(model_dir)
        self.tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=256)
        self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(model_dir / "onnx" / "model_quint8_avx2.onnx"),
                                            sess_options=options, providers=["CPUExecutionProvider"])
        self.input_names = {item.name for item in self.session.get_inputs()}

    def encode(self, texts, batch_size=32):
        if not texts:
            return np.empty((0, 384), dtype=np.float32)
        batches = []
        for start in range(0, len(texts), batch_size):
            encoded = self.tokenizer.encode_batch(texts[start:start+batch_size])
            inputs = {"input_ids": np.array([item.ids for item in encoded], dtype=np.int64),
                      "attention_mask": np.array([item.attention_mask for item in encoded], dtype=np.int64),
                      "token_type_ids": np.array([item.type_ids for item in encoded], dtype=np.int64)}
            output = self.session.run(None, {name: value for name, value in inputs.items() if name in self.input_names})[0]
            if output.ndim == 3:
                mask = inputs["attention_mask"].astype(np.float32)[..., None]
                vectors = (output * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1e-9)
            else:
                vectors = output
            normalized = vectors / np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
            batches.append(normalized.astype(np.float32))
        return np.concatenate(batches)
