# 🎵 Music Player 🎵

## Descrição
Um reprodutor de músicas completo e interativo, desenvolvido em Python e Flask, que permite reproduzir músicas armazenadas localmente, organizadas por gêneros musicais. Possui um frontend responsivo e rico em funcionalidades, utilizando HTML, CSS e JavaScript.

## Funcionalidades Principais
- ✅ Reprodução de músicas locais organizadas por gêneros
- ✅ Controles básicos de reprodução: play, pause, parar, próxima e música anterior
- ✅ Modos de reprodução aleatório (shuffle) e repetir (repeat)
- ✅ Interface moderna e responsiva
- ✅ Barra de progresso interativa
- ✅ Exibição das informações da música atual: nome, duração e tempo reproduzido
- ✅ Seleção de gênero musical para playlist personalizada
- ✅ Interface terminal amigável através de menu interativo (opcional via `main.py`)
- ✅ Pronto para deploy com Docker e compatível com plataformas como Fly.io
- ✅ Suporte para ambientes sem dispositivo de áudio (ex: servidores cloud)

## 📁 Estrutura do Projeto
```plaintext
.
├── songs/
│   └── (suas músicas organizadas por gênero)
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
├── templates/
│   └── index.html
├── music_player.py
├── server.py
├── main.py (uso via terminal)
├── requirements.txt
├── Dockerfile
├── Procfile
└── README.md
```

## 🔧 Instalação e Configuração

Certifique-se de ter o Python instalado (3.8 ou superior recomendado).

**1. Clone o repositório**
```bash
git clone <url-do-seu-repositorio>
cd music_player_project
```

**2. Crie e ative um ambiente virtual**
```bash
python -m venv venv
# Ativar ambiente virtual
# Windows
venv\Scripts\activate
# Linux / MacOS
source venv/bin/activate
```

**3. Instale as dependências**
```bash
pip install -r requirements.txt
```

**4. Organize suas músicas**
- Coloque suas músicas preferidas dentro da pasta `songs` e organize-as em subdiretórios por gênero (por exemplo, `songs/Rock`, `songs/Pop`).

## 🚀 Execução

### Opção A - Servidor Web com Frontend
Inicie o servidor web usando Flask e Gunicorn:
```bash
gunicorn server:app --bind 0.0.0.0:8080
```
Acesse a aplicação em seu navegador através de:
[http://localhost:8080](http://localhost:8080)

### Opção B - Terminal Interativo
Para uma interface textual interativa, execute no terminal:
```bash
python main.py
```

## 📸 Demonstração Visual
*(Aqui você pode adicionar imagens ou GIFs demonstrativos do funcionamento visual da aplicação no momento oportuno.)*

## 🛠️ Tecnologias Utilizadas
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Bibliotecas Adicionais:** pygame (áudio), mutagen (metadados de áudio), PyQt5
- **Deploy:** Docker, Gunicorn, Fly.io

## 👤 Autor
Desenvolvido por **FURIOUSOFNIGHT**.

---

🎧 Aproveite sua experiência musical! 🎶

