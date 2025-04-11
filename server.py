from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from music_player import MusicPlayer
import logging
import os
from threading import Lock
from mimetypes import guess_type

# Ambiente Fly.io (sem pygame)
IS_RENDER = os.getenv("RENDER") == "true"

# Configuração do Flask
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Inicialização do player
MUSIC_FOLDER = "songs"
player = MusicPlayer(music_folder=MUSIC_FOLDER)
lock = Lock()

logging.info("Modo RENDER ativado. Reprodução no navegador." if IS_RENDER else "Modo local com pygame.")

@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/genres", methods=["GET"])
def get_genres():
    try:
        with lock:
            genres = player.genres
        return jsonify({"success": True, "data": genres, "message": "Gêneros disponíveis.", "error": None})
    except Exception as e:
        logging.exception("Erro ao obter gêneros.")
        return jsonify({"success": False, "message": "Erro ao obter gêneros.", "error": str(e), "data": None}), 500

@app.route("/api/select_genre", methods=["POST"])
def select_genre():
    try:
        data = request.get_json()
        genre = data.get("genre")

        if genre not in player.genres:
            return jsonify({"success": False, "message": "Gênero inválido.", "error": None, "data": None}), 400

        with lock:
            player.select_genre(genre)

        return jsonify({
            "success": True,
            "message": f"Gênero '{genre}' selecionado.",
            "data": {"playlist": player.music_list},
            "error": None
        })
    except Exception as e:
        logging.exception("Erro ao selecionar gênero.")
        return jsonify({"success": False, "message": "Erro ao selecionar gênero.", "error": str(e), "data": None}), 500

@app.route("/api/play", methods=["POST"])
def play_music():
    try:
        data = request.get_json()
        index = int(data.get("index", -1))

        if index < 0 or index >= len(player.music_list):
            return jsonify({"success": False, "message": "Índice inválido.", "error": None, "data": None}), 400

        with lock:
            player.play_music(index)

        abs_path = player.music_list[player.current_index]
        rel_path = abs_path.replace(f"{MUSIC_FOLDER}{os.sep}", "").replace("\\", "/")

        logging.info(f"Reproduzindo: {rel_path}")

        return jsonify({
            "success": True,
            "data": {"current_song": os.path.basename(abs_path), "full_path": rel_path},
            "message": "Música reproduzida com sucesso.",
            "error": None
        })
    except Exception as e:
        logging.exception("Erro ao reproduzir música.")
        return jsonify({"success": False, "message": "Erro ao reproduzir música", "error": str(e), "data": None}), 500

@app.route("/api/stop", methods=["POST"])
def stop_music():
    try:
        with lock:
            player.stop()
        return jsonify({"success": True, "message": "Música parada.", "data": None, "error": None})
    except Exception as e:
        logging.exception("Erro ao parar música.")
        return jsonify({"success": False, "message": "Erro ao parar música.", "error": str(e), "data": None}), 500

@app.route("/api/info", methods=["GET"])
def get_info():
    try:
        if player.current_index == -1 or not player.music_list:
            return jsonify({
                "success": True,
                "data": {
                    "current_song": "Nenhuma música tocando",
                    "time_played": 0,
                    "duration": 0,
                    "genre": "N/A",
                    "full_path": ""
                },
                "message": "Nenhuma música em execução.",
                "error": None
            })

        with lock:
            info = player.show_info()

        info["full_path"] = info["full_path"].replace(f"{MUSIC_FOLDER}{os.sep}", "").replace("\\", "/")

        return jsonify({"success": True, "data": info, "message": "Informações da música atual.", "error": None})
    except Exception as e:
        logging.exception("Erro ao obter info.")
        return jsonify({"success": False, "message": "Erro ao obter info.", "error": str(e), "data": None}), 500

@app.route("/api/next", methods=["POST"])
def next_music():
    try:
        with lock:
            player.play_music(player.current_index + 1)
        song = player.music_list[player.current_index]
        rel_path = song.replace(f"{MUSIC_FOLDER}{os.sep}", "").replace("\\", "/")
        return jsonify({
            "success": True,
            "message": "Próxima música reproduzida.",
            "data": {"current_song": os.path.basename(song), "full_path": rel_path},
            "error": None
        })
    except Exception as e:
        logging.exception("Erro ao avançar música.")
        return jsonify({"success": False, "message": "Erro ao avançar música.", "error": str(e), "data": None}), 500

@app.route("/api/previous", methods=["POST"])
def previous_music():
    try:
        with lock:
            previous_index = player.current_index - 1 if player.current_index > 0 else len(player.music_list) - 1
            player.play_music(previous_index)
        song = player.music_list[player.current_index]
        rel_path = song.replace(f"{MUSIC_FOLDER}{os.sep}", "").replace("\\", "/")
        return jsonify({
            "success": True,
            "message": "Música anterior reproduzida.",
            "data": {"current_song": os.path.basename(song), "full_path": rel_path},
            "error": None
        })
    except Exception as e:
        logging.exception("Erro ao voltar música.")
        return jsonify({"success": False, "message": "Erro ao voltar música.", "error": str(e), "data": None}), 500

@app.route("/api/shuffle", methods=["POST"])
def toggle_shuffle():
    try:
        with lock:
            status = player.toggle_shuffle_without_repeat()
        logging.info(f"Modo shuffle {'ativado' if status else 'desativado'}.")
        return jsonify({
            "success": True,
            "message": f"Modo shuffle {'ativado' if status else 'desativado'}.",
            "data": {"shuffle_status": status},
            "error": None
        })
    except Exception as e:
        logging.exception("Erro ao alternar shuffle.")
        return jsonify({"success": False, "message": "Erro ao alternar shuffle.", "error": str(e), "data": None}), 500

@app.route("/api/repeat", methods=["POST"])
def toggle_repeat():
    try:
        with lock:
            status = player.repeat_mode()
        logging.info(f"Modo repeat {'ativado' if status else 'desativado'}.")
        return jsonify({
            "success": True,
            "message": f"Modo repeat {'ativado' if status else 'desativado'}.",
            "data": {"repeat_status": status},
            "error": None
        })
    except Exception as e:
        logging.exception("Erro ao alternar repeat.")
        return jsonify({"success": False, "message": "Erro ao alternar repeat.", "error": str(e), "data": None}), 500

@app.route("/api/music/<path:filename>", methods=["GET"])
def serve_music(filename: str):
    try:
        safe_path = str(os.path.normpath(str(filename)).replace("\\", "/").lstrip("/"))
        full_path = os.path.join(MUSIC_FOLDER, safe_path)
        if not os.path.isfile(full_path):
            logging.error(f"Arquivo não encontrado: {full_path}")
            return jsonify({"success": False, "message": "Arquivo não encontrado.", "error": None, "data": None}), 404

        mime_type, _ = guess_type(full_path)
        return send_from_directory(MUSIC_FOLDER, safe_path, mimetype=str(mime_type or "audio/mpeg"), as_attachment=False)
    except Exception as e:
        logging.exception("Erro ao servir música.")
        return jsonify({"success": False, "message": "Erro ao servir música.", "error": str(e), "data": None}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)