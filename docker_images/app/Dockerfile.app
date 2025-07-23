# Dockerfile.testing

FROM python:3.12-slim


# Establecer directorio de trabajo
WORKDIR /app

# Instalar herramientas necesarias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry oficialmente
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Copiar archivos de dependencias para aprovechar la cache de Docker
COPY pyproject.toml poetry.lock* /tmp/

# Instalar dependencias del proyecto
RUN cd /tmp && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-root --with dev

# Copia el resto del proyecto
COPY pyproject.toml poetry.lock* ./ 
COPY src/ ./src/


# Establecer PYTHONPATH para imports
ENV PYTHONPATH=/app/src

EXPOSE 9000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000", "--workers", "1"]