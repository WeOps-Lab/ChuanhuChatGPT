FROM python:3.9-slim-buster as builder
RUN sed -i 's/http:\/\/deb.debian.org\/debian/http:\/\/mirrors.cloud.tencent.com\/debian/g' /etc/apt/sources.list
RUN sed -i 's/http:\/\/security.debian.org\/debian-security/http:\/\/mirrors.cloud.tencent.com\/debian-security/g' /etc/apt/sources.list

RUN apt-get update \
    && apt-get install -y build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
COPY requirements_advanced.txt .
RUN pip install --user --no-cache-dir -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple
# RUN pip install --user --no-cache-dir -r requirements_advanced.txt

FROM python:3.9-slim-buster
LABEL maintainer="iskoldt"
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . /app
WORKDIR /app
ENV dockerrun=yes
CMD ["python3", "-u", "ChuanhuChatbot.py","2>&1", "|", "tee", "/var/log/application.log"]
