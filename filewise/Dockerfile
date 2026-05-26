FROM python:3.12-slim AS build
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir build && python -m build --wheel

FROM python:3.12-slim
WORKDIR /app
COPY --from=build /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl
ENV FILEWISE_EMBED_MODEL=fake \
    FILEWISE_LLM=fake:echo \
    FILEWISE_VECTORS_PATH=/data/vectors.npy
VOLUME ["/data"]
EXPOSE 8000
CMD ["uvicorn", "filewise.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
