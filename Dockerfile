FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta
EXPOSE 10000

# Comando para iniciar
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "app:app"]
