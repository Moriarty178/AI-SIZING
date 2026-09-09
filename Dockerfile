# A1 — image chạy Sizing Copilot (giao diện Streamlit).
#
# Xây:   docker build -t sizing-copilot:dev --build-arg COMMIT=$(git rev-parse --short HEAD) .
# Chạy:  docker run --rm -p 8501:8501 \
#           -e SIZING_COPILOT_API_KEY=... \
#           -v "$PWD/config/settings.yaml:/app/config/settings.yaml:ro" \
#           sizing-copilot:dev
#
# Ba điều cố ý:
#
# 1. `config/settings.yaml` KHÔNG nằm trong image — nó chứa endpoint nội bộ, và
#    khoá API thì không bao giờ ở đâu ngoài biến môi trường. Mount lúc chạy.
# 2. Commit được NƯỚNG vào image qua `--build-arg COMMIT`. Container không có
#    `.git`, mà chính dự án này đã đốt ba lượt chạy model vì không nhận ra mình
#    đang chạy mã cũ (`src/version.py`). Trong image thì `git` cũng không cứu
#    được, nên phải đóng dấu lúc build.
# 3. Chạy bằng user thường, không phải root.

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Lớp phụ thuộc tách riêng để đổi mã nguồn không phải cài lại từ đầu.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[ui]"

COPY config ./config
COPY ui ./ui
COPY scripts ./scripts

# Đóng dấu phiên bản (xem lý do 2 ở trên).
ARG COMMIT=unknown
ENV SIZING_COPILOT_COMMIT=${COMMIT}

# Đệm lời gọi model (2.12) ghi vào `.cache/llm`. Để trong image thì mất khi
# container chết; mount ra ngoài nếu muốn giữ giữa các lần chạy.
RUN mkdir -p /app/.cache \
    && useradd --create-home --uid 10001 copilot \
    && chown -R copilot:copilot /app
USER copilot

EXPOSE 8501

# Streamlit tự có `/_stcore/health`. Dùng chính nó thay vì đoán.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health',timeout=4).status==200 else 1)"

ENTRYPOINT ["streamlit", "run", "ui/app.py", \
            "--server.address=0.0.0.0", "--server.port=8501", \
            "--server.headless=true", "--browser.gatherUsageStats=false"]
