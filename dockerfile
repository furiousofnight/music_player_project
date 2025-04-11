# Imagem base leve e segura
FROM python:3.13.3-slim-bullseye

# Expondo a porta usada pelo Gunicorn
EXPOSE 8080

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV RENDER=true

# Define diretório padrão de trabalho
WORKDIR /app

# Copia arquivos de dependências e instala pacotes
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o restante do projeto
COPY . /app

# Cria diretório para músicas com permissões adequadas
RUN mkdir -p /app/songs && chmod -R 755 /app/songs

# Cria e usa usuário não-root por segurança
RUN adduser --disabled-password --gecos "" --uid 5678 appuser && chown -R appuser /app
USER appuser

# Comando para iniciar o servidor com Gunicorn
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080"]
