FROM python:3.9-slim

WORKDIR /app

# copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy your code
COPY main.py .

# expose port 8000
EXPOSE 8000

# run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
