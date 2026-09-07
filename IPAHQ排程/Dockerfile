# 使用輕量級 Node.js 20 官方映像檔
FROM node:20-slim

# 安裝 Python 3 與相關條碼/Excel 函式庫 (用於台積電三合一單生成)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package*.json ./
RUN npm install --production

RUN pip3 install --no-cache-dir --break-system-packages openpyxl qrcode pillow

COPY . .

ENV PORT=3000
ENV NODE_ENV=production
ENV RENDER=true

EXPOSE 3000

CMD ["node", "server.js"]
