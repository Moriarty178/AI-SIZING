# syntax=docker/dockerfile:1.7
# A1 — image chạy Sizing Copilot (API + giao diện Streamlit trong cùng một image).
#
# Xây (máy thường):
#   docker build -t sizing-copilot:dev --build-arg COMMIT=$(git rev-parse --short HEAD) .
#
# Xây (máy nội bộ Viettel — có proxy và TLS MITM, xem docs/docker-mang-noi-bo.md):
#   docker build -t sizing-copilot:dev \
#     --build-arg COMMIT=$(git rev-parse --short HEAD) \
#     --build-arg HTTPS_PROXY=http://10.207.156.52:3128 \
#     --build-arg HTTP_PROXY=http://10.207.156.52:3128 \
#     --secret id=ca_noi_bo,src=viettel-mitm-ca.pem .
#
# Chạy API:  docker run --rm -p 8000:8000 \
#              -e SIZING_COPILOT_API_KEY=... \
#              -v "$PWD/config/settings.yaml:/app/config/settings.yaml:ro" \
#              sizing-copilot:dev
# Chạy UI:   docker run --rm -p 8501:8501 ... sizing-copilot:dev \
#              streamlit run ui/app.py --server.address=0.0.0.0 --server.headless=true
#
# Bốn điều cố ý:
#
# 1. **KHÔNG có `apt-get` nào.** Trên máy nội bộ, proxy trả về rác cho kho apt
#    ("Clearsigned file isn't valid, got NOSPLIT") nên mọi `apt-get install` đều
#    hỏng. Ảnh này không cần gói hệ thống nào — đừng thêm, kể cả `git`.
# 2. Commit ghi ra `/app/.commit` (và biến môi trường). Container không có `.git`,
#    mà dự án này đã đốt ba lượt chạy model vì không nhận ra mình chạy mã cũ.
# 3. Chứng chỉ CA nội bộ đi qua **BuildKit secret**, không qua `COPY`. Secret
#    không nằm lại trong bất kỳ lớp nào của image, nên chứng chỉ nội bộ không
#    theo image ra ngoài. Không có secret thì build vẫn chạy bình thường.
# 4. `config/settings.yaml` KHÔNG nằm trong image — nó có endpoint nội bộ; khoá
#    API thì chỉ đi qua biến môi trường. Mount lúc chạy.

FROM python:3.12-slim AS runtime

# Proxy chỉ có hiệu lực trong lúc BUILD (ARG, không phải ENV) — image mang ra
# môi trường khác sẽ không kéo theo địa chỉ proxy của một mạng cụ thể.
ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ARG NO_PROXY="localhost,127.0.0.1"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Lớp phụ thuộc tách riêng để đổi mã nguồn không phải cài lại từ đầu.
COPY pyproject.toml README.md ./
COPY src ./src
RUN --mount=type=secret,id=ca_noi_bo,target=/run/secrets/ca_noi_bo,required=false \
    if [ -s /run/secrets/ca_noi_bo ]; then \
        echo "→ dùng CA nội bộ cho TLS lúc build" ; \
        cp /run/secrets/ca_noi_bo /tmp/ca-noi-bo.pem ; \
        export SSL_CERT_FILE=/tmp/ca-noi-bo.pem PIP_CERT=/tmp/ca-noi-bo.pem \
               REQUESTS_CA_BUNDLE=/tmp/ca-noi-bo.pem ; \
    fi ; \
    pip install --no-cache-dir ".[api,ui]" ; \
    rm -f /tmp/ca-noi-bo.pem

COPY config ./config
COPY ui ./ui
COPY api ./api
COPY scripts ./scripts

# Đóng dấu phiên bản (lý do 2 ở trên). Ghi ra CẢ file lẫn biến môi trường: biến
# tiện khi `docker run`, file sống sót kể cả khi ai đó ghi đè `--env`.
ARG COMMIT=unknown
ENV SIZING_COPILOT_COMMIT=${COMMIT}
RUN printf '%s' "${COMMIT}" > /app/.commit

# Đệm lời gọi model (2.12) và trạng thái công việc (3.2) ghi vào `.cache/`. Để
# trong image thì mất khi container chết — mount ra ngoài nếu muốn việc đang
# chạy sống sót qua một lần khởi động lại.
RUN mkdir -p /app/.cache \
    && useradd --create-home --uid 10001 copilot \
    && chown -R copilot:copilot /app
USER copilot

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health',timeout=4).status==200 else 1)"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
