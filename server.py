from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from music_player import MusicPlayer
import logging
import os
from threading import Lock
from mimetypes import guess_type

# Ambiente
IS_RENDER = os.getenv("RENDER") == "true"

# Configuração do Flask
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Inicialização
MUSIC_FOLDER = "songs"
player = MusicPlayer(music_folder=MUSIC_FOLDER)
lock = Lock()

logging.info("Modo RENDER ativado. Reprodução no navegador." if IS_RENDER else "Modo local com pygame.")

# Headers de segurança
@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/musics", methods=["GET"])
def get_playlist():
    try:
        logging.info("Listando músicas.")
        return jsonify({
            "success": True,
            "data": {"playlist": player.music_list},
            "message": "Playlist carregada com sucesso.",
            "error": None
        })
    except Exception as e:
        logging.exception("Erro ao obter playlist.")
        return jsonify({"success": False, "error": str(e), "message": "Erro ao obter playlist", "data": None}), 500

@app.route("/api/play", methods=["POST"])
def play_music():
    try:
        data = request.get_json()
        index = int(data.get("index", -1))

        if index < 0 or index >= len(player.music_list):
            return jsonify({"success": False, "message": "Índice inválido.", "error": None, "data": None}), 400

        with lock:
            player.play_music(index)

        song_name = os.path.basename(player.music_list[player.current_index])
        logging.info(f"Reproduzindo: {song_name}")
        return jsonify({
            "success": True,
            "data": {"current_song": song_name},
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

@app.route("/api/next", methods=["POST"])
def next_music():
    try:
        with lock:
            if player.current_index + 1 >= len(player.music_list):
                player.current_index = 0
            else:
                player.play_music(player.current_index + 1)

        song_name = os.path.basename(player.music_list[player.current_index])
        return jsonify({
            "success": True,
            "message": "Próxima música reproduzida.",
            "data": {"current_song": song_name},
            "error": None
        })
    except Exception as e:
        logging.exception("Erro ao avançar música.")
        return jsonify({"success": False, "message": "Erro ao avançar música.", "error": str(e), "data": None}), 500

@app.route("/api/previous", methods=["POST"])
def previous_music():
    try:
        with lock:
            if player.current_index <= 0:
                player.current_index = len(player.music_list) - 1
            else:
                player.play_music(player.current_index - 1)

        song_name = os.path.basename(player.music_list[player.current_index])
        return jsonify({
            "success": True,
            "message": "Música anterior reproduzida.",
            "data": {"current_song": song_name},
            "error": None
        })
    except Exception as e:
        logging.exception("Erro ao voltar música.")
        return jsonify({"success": False, "message": "Erro ao voltar música.", "error": str(e), "data": None}), 500

@app.route("/api/shuffle", methods=["POST"])
def shuffle_music():
    try:
        with lock:
            shuffle_status = player.toggle_shuffle_without_repeat()
        return jsonify({
            "success": True,
            "message": f"Modo shuffle {'ativado' if shuffle_status else 'desativado' }.",
            "data": {"shuffle_status": shuffle_status},
            "error": None
        })
    except Exception as e:
        logging.exception("Erro ao alternar shuffle.")
        return jsonify({"success": False, "message": "Erro no shuffle.", "error": str(e), "data": None}), 500

@app.route("/api/repeat", methods=["POST"])
def repeat_mode():
    try:
        with lock:
            repeat_status = player.repeat_mode()
        return jsonify({
            "success": True,
            "message": f"Modo repeat {'ativado' if repeat_status else 'desativado' }.",
            "data": {"repeat_status": repeat_status},
            "error": None
        })
    except Exception as e:
        logging.exception("Erro ao alternar repeat.")
        return jsonify({"success": False, "message": "Erro no repeat.", "error": str(e), "data": None}), 500

@app.route("/api/info", methods=["GET"])
def get_info():
    try:
        if player.current_index == -1 or not player.playing:
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

        return jsonify({"success": True, "data": info, "message": "Informações da música atual.", "error": None})
    except Exception as e:
        logging.exception("Erro ao obter info.")
        return jsonify({"success": False, "message": "Erro ao obter info.", "error": str(e), "data": None}), 500

@app.route("/api/genres", methods=["GET"])
def get_genres():
    try:
        with lock:
            genres = player.genres
        return jsonify({"success": True, "data": genres, "message": "Gênros retornados com sucesso.", "error": None})
    except Exception as e:
        logging.exception("Erro ao obter gênros.")
        return jsonify({"success": False, "message": "Erro ao obter gênros.", "error": str(e), "data": None}), 500

@app.route("/api/select_genre", methods=["POST"])
def select_genre():
    try:
        data = request.get_json()
        genre = data.get("genre")

        if genre not in player.genres:
            return jsonify({"success": False, "message": "Gênro inválido.", "error": None, "data": None}), 400

        with lock:
            player.select_genre(genre)
        return jsonify({
            "success": True,
            "message": f"Gênro '{genre}' selecionado.",
            "data": {"playlist": player.music_list},
            "error": None
        })
    except Exception as e:
        logging.exception("Erro ao selecionar gênro.")
        return jsonify({"success": False, "message": "Erro ao selecionar gênro.", "error": str(e), "data": None}), 500

@app.route("/api/reset_playlist", methods=["POST"])
def reset_playlist():
    try:
        with lock:
            player.reset_playlist()
        return jsonify({
            "success": True,
            "message": "Playlist restaurada.",
            "data": {"playlist": player.music_list},
            "error": None
        })
    except Exception as e:
        logging.exception("Erro ao restaurar playlist.")
        return jsonify({"success": False, "message": "Erro ao restaurar playlist.", "error": str(e), "data": None}), 500

@app.route("/api/set_position", methods=["POST"])
def set_position():
    try:
        data = request.get_json()
        new_time = data.get("time")

        if not isinstance(new_time, int):
            return jsonify({"success": False, "message": "Tempo inválido.", "error": None, "data": None}), 400

        if not player.playing or player.current_index == -1:
            return jsonify({"success": False, "message": "Nenhuma música tocando.", "error": None, "data": None}), 400

        duration = player.get_current_duration()
        if new_time < 0 or new_time > duration:
            return jsonify({"success": False, "message": "Tempo fora dos limites.", "error": None, "data": None}), 400

        with lock:
            player.set_position(new_time)
        return jsonify({
            "success": True,
            "message": "Posição atualizada.",
            "data": {"current_time": int(player.position), "duration": int(duration)},
            "error": None
        })
    except Exception as e:
        logging.exception("Erro ao ajustar posição.")
        return jsonify({"success": False, "message": "Erro interno.", "error": str(e), "data": None}), 500

@app.route("/api/music/<path:filename>", methods=["GET"])
def serve_music(filename):
    try:
        file_path = os.path.join(MUSIC_FOLDER, filename)
        mime_type, _ = guess_type(file_path)
        return send_from_directory(MUSIC_FOLDER, filename, mimetype=mime_type, as_attachment=False)
    except FileNotFoundError:
        logging.error(f"Arquivo não encontrado: {filename}")
        return jsonify({"success": False, "message": "Arquivo não encontrado.", "error": None, "data": None}), 404

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
