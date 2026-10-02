FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY gateway ./gateway
COPY recon ./recon

# 2.0: 流式 3D 重建感知层权重 (可选；不存在则降级为 mock backbone)
COPY recon/weights ./recon/weights

EXPOSE 8000 8001

# 默认同时启动 1.0 gateway (8000) 和 2.0 recon (8001)
# docker-compose.yml 会按 service 分别启动；这里给单镜像用户提供便利
CMD ["sh", "-c", "uvicorn gateway.app:app --host 0.0.0.0 --port 8000 & uvicorn recon.service:app --host 0.0.0.0 --port 8001 & wait"]
