FROM python:3.12

WORKDIR /app

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

RUN playwright install chromium && playwright install-deps

EXPOSE ${PORT}

CMD ["python3", "main.py"]