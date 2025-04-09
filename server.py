from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import logging
from threading import Lock
from music_player import MusicPlayer

app = Flask(__name__)
CORS(app)
MUSIC_FOLDER = "songs"
player = MusicPlayer(music_folder=MUSIC_FOLDER)
lock = Lock()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/media/<path:filename>")
def serve_song(filename):
    """Serve a song file for playback in the browser."""
    try:
        return send_from_directory(MUSIC_FOLDER, filename)
    except FileNotFoundError:
        logging.error("Arquivo de música não encontrado: %s", filename)
        return jsonify({"error": "Arquivo de música não encontrado."}), 404


@app.route("/api/musics", methods=["GET"])
def get_playlist():
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
    try:
        data = request.get_json()
        if not data or "index" not in data:
            return jsonify({"error": "O parâmetro 'index' é obrigatório"}), 400

        song_index = data.get("index")
        if not isinstance(song_index, int) or song_index < 0 or song_index >= len(player.music_list):
            return jsonify({"error": "Índice inválido ou fora dos limites."}), 400

        with lock:
            player.play_music(song_index)

        song_path = player.music_list[song_index]
        song_name = os.path.basename(song_path)
        relative_path = os.path.relpath(song_path, MUSIC_FOLDER).replace("\\", "/")
        song_url = f"/media/{relative_path}"

        logging.info("Música selecionada: %s", song_name)
        return jsonify({"status": "playing", "current_song": song_name, "song_url": song_url})
    except ValueError:
        logging.error("Índice inválido fornecido.")
        return jsonify({"error": "Índice inválido."}), 400
    except Exception as e:
        logging.exception("Erro ao tentar preparar música.")
        return jsonify({"error": "Não foi possível preparar música.", "details": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
def stop_music():
    try:
        with lock:
            player.stop()
            player.current_index = -1  # Reseta o índice da música
        logging.info("Música parada.")
        return jsonify({"status": "stopped"})
    except Exception as e:
        logging.exception("Erro ao parar a música.")
        return jsonify({"error": "Não foi possível parar a música.", "details": str(e)}), 500


@app.route("/api/next", methods=["POST"])
def next_music():
    try:
        with lock:
            player.play_music(player.current_index + 1)
        song_path = player.music_list[player.current_index]
        song_name = os.path.basename(song_path)
        relative_path = os.path.relpath(song_path, MUSIC_FOLDER).replace("\\", "/")
        song_url = f"/media/{relative_path}"
        logging.info("Próxima música: %s", song_name)
        return jsonify({"status": "ready", "current_song": song_name, "song_url": song_url})
    except IndexError:
        logging.warning("Nenhuma próxima música disponível.")
        return jsonify({"error": "Não há próxima música."}), 400
    except Exception as e:
        logging.exception("Erro ao mudar para próxima música.")
        return jsonify({"error": "Erro ao avançar música.", "details": str(e)}), 500


@app.route("/api/previous", methods=["POST"])
def previous_music():
    try:
        with lock:
            player.play_music(player.current_index - 1)
        song_path = player.music_list[player.current_index]
        song_name = os.path.basename(song_path)
        relative_path = os.path.relpath(song_path, MUSIC_FOLDER).replace("\\", "/")
        song_url = f"/media/{relative_path}"
        logging.info("Música anterior: %s", song_name)
        return jsonify({"status": "ready", "current_song": song_name, "song_url": song_url})
    except IndexError:
        logging.warning("Nenhuma música anterior disponível.")
        return jsonify({"error": "Não há música anterior."}), 400
    except Exception as e:
        logging.exception("Erro ao voltar música.")
        return jsonify({"error": "Erro ao voltar música.", "details": str(e)}), 500


@app.route("/api/shuffle", methods=["POST"])
def shuffle_music():
    try:
        with lock:
            shuffle_status = player.toggle_shuffle_without_repeat()
        status_text = "ativado" if shuffle_status else "desativado"
        logging.info("Modo shuffle %s.", status_text)
        return jsonify({"status": "success", "shuffle_status": status_text})
    except Exception as e:
        logging.exception("Erro ao alternar shuffle.")
        return jsonify({"error": "Não foi possível alterar shuffle.", "details": str(e)}), 500


@app.route("/api/repeat", methods=["POST"])
def repeat_mode():
    try:
        with lock:
            repeat_status = player.repeat_mode()
        status_text = "ativado" if repeat_status else "desativado"
        logging.info("Modo repeat %s.", status_text)
        return jsonify({"status": "success", "repeat_status": status_text})
    except Exception as e:
        logging.exception("Erro ao alternar repeat.")
        return jsonify({"error": "Não foi possível alterar repeat.", "details": str(e)}), 500


@app.route("/api/info", methods=["GET"])
def get_info():
    try:
        if player.current_index == -1:
            logging.info("Nenhuma música em reprodução no momento.")
            return jsonify({"error": "Nenhuma música em reprodução."}), 400

        with lock:
            info = player.show_info()
        logging.info("Informações retornadas: %s", info)
        return jsonify({"info": info})
    except Exception as e:
        logging.exception("Erro ao obter informações da música.")
        return jsonify({"error": "Erro ao obter informações.", "details": str(e)}), 500


@app.route("/api/genres", methods=["GET"])
def get_genres():
    try:
        with lock:
            genres = player.genres
        logging.info("Gêneros disponíveis retornados: %s", list(genres.keys()))
        return jsonify({"genres": genres})
    except Exception as e:
        logging.exception("Erro ao obter gêneros.")
        return jsonify({"error": "Erro ao obter gêneros.", "details": str(e)}), 500


@app.route("/api/select_genre", methods=["POST"])
def select_genre():
    try:
        data = request.get_json()
        if not data or "genre" not in data:
            return jsonify({"error": "O parâmetro 'genre' é obrigatório"}), 400

        genre = data.get("genre")
        if genre not in player.genres:
            return jsonify({"error": f"Gênero '{genre}' não encontrado."}), 400

        with lock:
            player.select_genre(genre)
        logging.info("Gênero selecionado: %s", genre)
        return jsonify({"status": "ok", "playlist": player.music_list})
    except Exception as e:
        logging.exception("Erro ao selecionar gênero.")
        return jsonify({"error": "Erro ao definir gênero.", "details": str(e)}), 500


@app.route("/api/reset_playlist", methods=["POST"])
def reset_playlist():
    try:
        with lock:
            player.reset_playlist()
        logging.info("Playlist restaurada com sucesso.")
        return jsonify({"status": "success", "playlist": player.music_list})
    except Exception as e:
        logging.exception("Erro ao restaurar playlist.")
        return jsonify({"error": "Erro ao restaurar playlist.", "details": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
