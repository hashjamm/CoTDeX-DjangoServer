# 베이스 이미지를 Python으로 설정
FROM python:3.13.0-slim

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    python3-dev \
    libmysqlclient-dev \
    build-essential
    
# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사
COPY requirements.txt .

# dependencies 설치
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# 포트 설정
EXPOSE 8000

# 서버 실행 명령
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
