# Use uma imagem oficial do Python como base
FROM python:3.9-slim

# Instalar dependências do OpenCV e ZBar
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    zbar-tools \
    libzbar0

# Defina o diretório de trabalho dentro do container
WORKDIR /app

# Copie o arquivo requirements.txt para o diretório de trabalho
COPY app/requirements.txt .

# Instale as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Copie o restante do código da aplicação para o diretório de trabalho
COPY app/ .

# Exponha a porta padrão do Streamlit
EXPOSE 8501

# Comando para iniciar o Streamlit no container
CMD ["streamlit", "run", "index.py", "--server.port=8501", "--server.address=0.0.0.0"]
