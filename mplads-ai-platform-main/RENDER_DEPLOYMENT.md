# Render Free Deployment Notes

## Backend location
Use this service root directory in Render:

`mplads-ai-platform-main/backend`

## Commands
Build:
`pip install --upgrade pip && pip install -r requirements.txt`

Start:
`uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`

## Python
Use Python 3.11.9. The project includes both `runtime.txt` and `.python-version`.

## Memory optimization
This build intentionally does NOT install PyTorch or the `sentence-transformers` Python package.

Sentence-BERT is still used semantically through the official `sentence-transformers/all-MiniLM-L6-v2` ONNX export, executed with ONNX Runtime. The quantized AVX2 ONNX file is downloaded only on the first semantic duplicate-analysis request.

The application also:
- keeps one Uvicorn worker;
- does not load Sentence-BERT during FastAPI startup;
- removes pandas from the ML engine;
- lazily initializes scikit-learn models;
- limits ONNX Runtime to one CPU thread;
- batches Sentence-BERT inference in small batches;
- caches historical 384-dimensional embeddings in float32;
- falls back to TF-IDF if ONNX initialization/inference is unavailable.

## Expected behavior
The first backend health request should not load Sentence-BERT. The first `/projects/analyze` request may take longer because the quantized MiniLM ONNX model (~23 MB) and tokenizer are downloaded to `/tmp/mplads-sbert`.

The model is still `sentence-transformers/all-MiniLM-L6-v2` and produces semantic embeddings for duplicate-project detection.

## Render environment variables
Recommended:
- `PYTHON_VERSION=3.11.9`
- `SBERT_MODEL=sentence-transformers/all-MiniLM-L6-v2`
- `SBERT_ONNX_FILE=onnx/model_quint8_avx2.onnx`
- `SBERT_BATCH_SIZE=2`
- `OMP_NUM_THREADS=1`
- `MKL_NUM_THREADS=1`
- `OPENBLAS_NUM_THREADS=1`
- `NUMEXPR_NUM_THREADS=1`

Do not add a normal PyTorch package or a CUDA-enabled PyTorch package to requirements.
