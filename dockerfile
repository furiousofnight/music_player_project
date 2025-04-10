FROM python:3.13.3-slim-bullseye

EXPOSE 8080

# Ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV RENDER=true

# Instala dependências
COPY requirements.txt .
RUN apt-get update && apt-get install -y libglib2.0-0 libgl1-mesa-glx && \
    python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt

# Projeto
WORKDIR /app
COPY . /app

# Cria usuário não-root
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Comando de inicialização
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080"]
