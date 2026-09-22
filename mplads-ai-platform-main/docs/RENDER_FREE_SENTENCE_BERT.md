# Render Free-Tier Sentence-BERT Deployment

This deployment keeps `sentence-transformers/all-MiniLM-L6-v2` for semantic duplicate detection.

## Memory optimizations

- Sentence-BERT is lazy-loaded instead of loading during FastAPI import.
- Sentence Transformers uses the CPU ONNX backend.
- The official `all-MiniLM-L6-v2` quantized ONNX graph is requested first.
- If the host CPU cannot load that graph, the official float32 ONNX graph is used.
- Historical embeddings are generated once, not for every request.
- Duplicate checks reuse the stored historical embeddings.
- Embedding batch size is limited to 4.
- ONNX/BLAS thread counts are limited to 1 to reduce peak memory.
- Render runs one Uvicorn worker so the model is not duplicated across processes.

## Render

The included `render.yaml` contains the recommended service configuration. If you create the service manually, use:

Build command:

```text
pip install --upgrade pip && pip install -r requirements.txt
```

Start command:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
```

Recommended environment variables:

```text
PYTHON_VERSION=3.11.9
SBERT_MODEL=sentence-transformers/all-MiniLM-L6-v2
SBERT_ONNX_FILE=onnx/model_qint8_avx512_vnni.onnx
SBERT_BATCH_SIZE=4
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1
```

The first request that performs a semantic analysis can take longer because the Sentence-BERT model is loaded lazily. Subsequent requests reuse the same model and historical embeddings.
