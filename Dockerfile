#1. Chọn base image Python chính thức
FROM python:3.11-slim 
#2. Cài đặt các thư viện cần thiết 
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*
#3. Đặt folder vào trong container 
WORKDIR /app
#4.Copy file requirements.txt vào trong container 
COPY requirements.txt .
#5. Cài đặt các thư viện Python 
RUN pip install --no-cache-dir -r requirements.txt 
#6. Copy toàn bộ Source code vào trong container
COPY . .
#7. Khai báo cổng Flash chạy 
EXPOSE 5000
#8. Chạy container 
CMD [ "python", "UI/app.py" ]