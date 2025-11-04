# Python 3.9 베이스 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 비root 사용자 생성 및 설정
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 필요한 파일만 명시적으로 복사 (재귀적 복사 방지)
COPY requirements.txt .
COPY main.py .
COPY templates/ templates/
COPY todo.json .

# 의존성 설치 및 소유권 변경
RUN pip install --no-cache-dir -r requirements.txt && \
    chown -R appuser:appuser /app

# 비root 사용자로 전환
USER appuser

# FastAPI 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]