# Imagem base leve e segura
FROM python:3.13.3-slim-bullseye

# Porta exposta para o Gunicorn
EXPOSE 8080

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV RENDER=true

# Define diretório padrão
WORKDIR /app

# Copia as dependências primeiro para cache de build
COPY requirements.txt .

# Instala as dependências (inclui gunicorn)
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia todo o projeto (inclusive a pasta songs)
COPY . .

# Garante permissões corretas na pasta de músicas
RUN chmod -R 755 /app/songs

# Cria usuário não-root por segurança
RUN adduser --disabled-password --gecos "" --uid 5678 appuser && chown -R appuser /app
USER appuser

# Comando de execução com Gunicorn
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080"]
