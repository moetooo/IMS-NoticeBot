FROM python:3.12

WORKDIR /app

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

RUN playwright install --with-deps chromium 

EXPOSE ${PORT}

CMD ["python3", "main.py"]
