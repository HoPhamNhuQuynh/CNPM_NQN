# Sử dụng Base Image Python chính thức.
FROM python:3.11-slim

# Thiết lập biến môi trường
ENV FLASK_APP=server/app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Thiết lập thư mục làm việc bên trong Container
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết cho Playwright
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libnss3 libfontconfig libicu-dev libasound2 libgtk-3-0 libnotify4 libxss1 libxtst6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 1. Sao chép và cài đặt thư viện Python
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Cài đặt trình duyệt Chromium cho Playwright
RUN playwright install chromium --with-deps

# 3. SAO CHÉP CODE VÀ TẤT CẢ FILE DỮ LIỆU
COPY server/ server/
RUN chmod -R a+r /app

# Sao chép thư mục Frontend
COPY website/ website/

# Khai báo cổng mà ứng dụng Flask sẽ lắng nghe
EXPOSE 5000

# Lệnh chạy ứng dụng bằng Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "server.app:app"]