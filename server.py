from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from music_player import MusicPlayer
import logging
import os
from threading import Lock

# Configuração do Flask
app = Flask(__name__)
CORS(app)

# Configuração do logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Inicialização do player e lock
MUSIC_FOLDER = "songs"
player = MusicPlayer(music_folder=MUSIC_FOLDER)
lock = Lock()  # Lock para operações thread-safe no player


@app.route("/")
def index():
    """Renderiza a página principal."""
    return render_template("index.html")


@app.route("/api/musics", methods=["GET"])
def get_playlist():
    """Retorna a lista de músicas disponíveis."""
    try:
        logging.info("Solicitação para listar a playlist recebida.")
        if not player.music_list:
            return jsonify({"playlist": [], "message": "Nenhuma música encontrada."})
        return jsonify({"playlist": player.music_list})
    except Exception as e:
        logging.exception("Erro ao obter a playlist.")
        return jsonify({"error": "Erro ao obter a playlist", "details": str(e)}), 500


@app.route("/api/play", methods=["POST"])
def play_music():
    """Reproduz a música no índice fornecido."""
    try:
        data = request.get_json()
        if not data or "index" not in data:
            return jsonify({"error": "O parâmetro 'index' é obrigatório"}), 400

        song_index = data.get("index")
        if not isinstance(song_index, int) or song_index < 0 or song_index >= len(player.music_list):
            return jsonify({"error": "Índice inválido ou fora dos limites."}), 400

        with lock:
            player.play_music(song_index)
        song_name = os.path.basename(player.music_list[player.current_index])
        logging.info(f"Música reproduzida: {song_name}")
        return jsonify({"status": "playing", "current_song": song_name})
    except Exception as e:
        logging.exception("Erro ao tentar reproduzir música.")
        return jsonify({"error": "Não foi possível reproduzir música.", "details": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
def stop_music():
    """Interrompe a reprodução da música."""
    try:
        with lock:
            player.stop()
        logging.info("Música parada.")
        return jsonify({"status": "stopped"})
    except Exception as e:
        logging.exception("Erro ao parar música.")
        return jsonify({"error": "Não foi possível parar música.", "details": str(e)}), 500


@app.route("/api/next", methods=["POST"])
def next_music():
    """Reproduz a próxima música."""
    try:
        with lock:
            if player.current_index + 1 >= len(player.music_list):
                player.current_index = 0  # Volta para a primeira música
            else:
                player.play_music(player.current_index + 1)
        song_name = os.path.basename(player.music_list[player.current_index])
        logging.info(f"Próxima música reproduzida: {song_name}")
        return jsonify({"status": "playing", "current_song": song_name})
    except Exception as e:
        logging.exception("Erro ao reproduzir próxima música.")
        return jsonify({"error": "Erro ao reproduzir próxima música.", "details": str(e)}), 500


@app.route("/api/previous", methods=["POST"])
def previous_music():
    """Reproduz a música anterior."""
    try:
        with lock:
            if player.current_index <= 0:
                player.current_index = len(player.music_list) - 1  # Vai para a última música
            else:
                player.play_music(player.current_index - 1)
        song_name = os.path.basename(player.music_list[player.current_index])
        logging.info(f"Música anterior reproduzida: {song_name}")
        return jsonify({"status": "playing", "current_song": song_name})
    except Exception as e:
        logging.exception("Erro ao reproduzir música anterior.")
        return jsonify({"error": "Erro ao reproduzir música anterior.", "details": str(e)}), 500


@app.route("/api/shuffle", methods=["POST"])
def shuffle_music():
    """Ativa ou desativa o modo shuffle."""
    try:
        with lock:
            shuffle_status = player.toggle_shuffle_without_repeat()
        status_text = "ativado" if shuffle_status else "desativado"
        logging.info(f"Modo shuffle {status_text}.")
        return jsonify({"status": "success", "shuffle_status": status_text})
    except Exception as e:
        logging.exception("Erro ao alternar shuffle.")
        return jsonify({"error": "Não foi possível alterar shuffle.", "details": str(e)}), 500


@app.route("/api/repeat", methods=["POST"])
def repeat_mode():
    """Ativa ou desativa o modo repeat."""
    try:
        with lock:
            repeat_status = player.repeat_mode()
        status_text = "ativado" if repeat_status else "desativado"
        logging.info(f"Modo repeat {status_text}.")
        return jsonify({"status": "success", "repeat_status": status_text})
    except Exception as e:
        logging.exception("Erro ao alternar repeat.")
        return jsonify({"error": "Não foi possível alterar repeat.", "details": str(e)}), 500


@app.route("/api/info", methods=["GET"])
def get_info():
    """Retorna informações sobre a música atual."""
    try:
        if player.current_index == -1 or not player.playing:
            logging.info("Nenhuma música em reprodução no momento.")
            return jsonify({
                "info": {
                    "current_song": "Nenhuma música tocando",
                    "time_played": 0,
                    "duration": 0,
                    "genre": "N/A",
                    "full_path": ""
                }
            }), 200

        with lock:
            info = player.show_info()
        logging.info(f"Informações retornadas: {info}")
        return jsonify({"info": info})
    except Exception as e:
        logging.exception("Erro ao obter informações da música.")
        return jsonify({"error": "Erro ao obter informações da música.", "details": str(e)}), 500


@app.route("/api/genres", methods=["GET"])
def get_genres():
    """Retorna a lista de gêneros disponíveis."""
    try:
        with lock:
            genres = player.genres
        logging.info(f"Gêneros disponíveis retornados: {list(genres.keys())}")
        return jsonify({"genres": genres})
    except Exception as e:
        logging.exception("Erro ao obter gêneros.")
        return jsonify({"error": "Não foi possível obter gêneros.", "details": str(e)}), 500


@app.route("/api/select_genre", methods=["POST"])
def select_genre():
    """Define um gênero específico na playlist atual."""
    try:
        data = request.get_json()
        if not data or "genre" not in data:
            return jsonify({"error": "O parâmetro 'genre' é obrigatório"}), 400

        genre = data.get("genre")
        if genre not in player.genres:
            return jsonify({"error": f"Gênero '{genre}' não encontrado."}), 400

        with lock:
            player.select_genre(genre)
        logging.info(f"Gênero selecionado: {genre}")
        return jsonify({"status": "ok", "playlist": player.music_list})
    except Exception as e:
        logging.exception("Erro ao selecionar gênero.")
        return jsonify({"error": "Erro ao definir gênero.", "details": str(e)}), 500


@app.route("/api/reset_playlist", methods=["POST"])
def reset_playlist():
    """Restaura a playlist original."""
    try:
        with lock:
            player.reset_playlist()
        logging.info("Playlist restaurada com sucesso.")
        return jsonify({"status": "success", "playlist": player.music_list})
    except Exception as e:
        logging.exception("Erro ao restaurar playlist.")
        return jsonify({"error": "Erro ao restaurar playlist.", "details": str(e)}), 500


@app.route("/api/set_position", methods=["POST"])
def set_position():
    """Rota para definir a posição do tempo da música atual"""
    try:
        data = request.get_json()
        new_time = data.get("time")

        if new_time is None or not isinstance(new_time, int):
            return jsonify({"success": False, "error": "Tempo inválido."}), 400

        if not player.playing or player.current_index == -1:
            return jsonify({"success": False, "error": "Nenhuma música está tocando no momento."}), 400

        duration = player.get_current_duration()  # Usando o método público
        if new_time < 0 or new_time > duration:
            return jsonify({"success": False, "error": "Tempo fora dos limites da duração da música."}), 400

        with lock:
            player.set_position(new_time)
        return jsonify({
            "success": True,
            "current_time": int(player.position),  # Garante que o valor seja inteiro
            "duration": int(duration)  # Garante que o valor seja inteiro
        })
    except Exception as e:
        logging.exception("Erro ao tentar ajustar posição:")
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
