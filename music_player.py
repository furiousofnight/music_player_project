from mutagen import File, MutagenError  # Para analisar duração do arquivo de áudio
import os
import threading
import random
import pygame
import logging

# Detecta se está em ambiente de produção (Render, CI/CD, etc)
IS_RENDER = os.environ.get("RENDER", "false").lower() == "true"

# Inicialização segura do pygame
if not IS_RENDER:
    try:
        import pygame
        pygame.init()
        pygame.mixer.init()
    except ImportError:
        logging.warning("pygame não está disponível. Ignorando inicialização.")
    except pygame.error as error:
        raise RuntimeError(f"Erro ao inicializar o pygame: {error}")
else:
    logging.warning("Modo servidor detectado — pygame não será inicializado.")


def _normalize_string(string: str) -> str:
    """Normaliza uma string para facilitar comparações."""
    return string.lower().strip().replace("-", " ").replace("_", " ")


class MusicPlayer:
    def __init__(self, music_folder: str = "songs"):
        self.music_folder = music_folder
        self.music_list: list[str] = []
        self.current_index: int = -1
        self.playing: bool = False
        self.loop: bool = False
        self.shuffle_without_repeat: bool = False
        self.played_indices: list[int] = []
        self.lock = threading.Lock()
        self.genres: dict[str, list[str]] = {}
        self.duration_cache: dict[str, int] = {}
        self.position: int = 0
        self._load_musics()

    def _load_musics(self) -> None:
        """Carrega as músicas do diretório especificado."""
        self.music_list.clear()
        if not os.path.exists(self.music_folder):
            os.makedirs(self.music_folder)

        for root, _, files in os.walk(self.music_folder):
            for file in files:
                if file.lower().endswith((".mp3", ".wav", ".flac", ".ogg")):
                    path = os.path.join(root, file)
                    genre = os.path.relpath(root, self.music_folder)
                    self.music_list.append(path)

                    if genre not in self.genres:
                        self.genres[genre] = []
                    self.genres[genre].append(path)

        self._cache_song_durations()

    def _cache_song_durations(self) -> None:
        """Cacheia a duração das músicas para evitar cálculos repetidos."""
        for song in self.music_list:
            if song not in self.duration_cache:
                try:
                    audio = File(song)
                    if audio and hasattr(audio.info, 'length'):
                        self.duration_cache[song] = int(audio.info.length)
                    else:
                        self.duration_cache[song] = 0
                except (MutagenError, AttributeError) as e:
                    logging.warning("Erro ao processar duração de '%s': %s", song, e)
                    self.duration_cache[song] = 0

    def get_current_duration(self) -> int:
        """Retorna a duração da música atual."""
        if 0 <= self.current_index < len(self.music_list):
            return self.duration_cache.get(self.music_list[self.current_index], 0)
        return 0

    def play_music(self, query: int | str | None = None) -> None:
        """Reproduz uma música com base no índice ou nome."""
        if IS_RENDER:
            logging.warning("Reprodução de áudio desativada no ambiente Render.")
            return

        with self.lock:
            if not self.music_list:
                logging.warning("Nenhuma música disponível.")
                return

            if isinstance(query, int):
                if 0 <= query < len(self.music_list):
                    self.current_index = query
                else:
                    raise ValueError("Índice fora dos limites.")
            elif isinstance(query, str):
                for index, song in enumerate(self.music_list):
                    if _normalize_string(query) in _normalize_string(song):
                        self.current_index = index
                        break
                else:
                    raise ValueError(f"Música '{query}' não encontrada.")
            elif self.shuffle_without_repeat:
                self._play_next_random()
                return
            else:
                self.current_index = (self.current_index + 1) % len(self.music_list)

            self._play_current_music()

    def _play_next_random(self) -> None:
        """Reproduz uma música aleatória sem repetir até que todas sejam tocadas."""
        if IS_RENDER:
            logging.warning("Reprodução de áudio desativada no ambiente Render.")
            return

        if not self.music_list:
            logging.warning("Nenhuma música disponível para reprodução.")
            return

        remaining = [i for i in range(len(self.music_list)) if i not in self.played_indices]
        if not remaining:
            self.played_indices.clear()
            remaining = list(range(len(self.music_list)))

        self.current_index = random.choice(remaining)
        self.played_indices.append(self.current_index)
        self._play_current_music()

    def _play_current_music(self) -> None:
        """Reproduz a música atual."""
        if IS_RENDER:
            return
        try:
            logging.info("Carregando música: %s", self.music_list[self.current_index])
            pygame.mixer.music.load(self.music_list[self.current_index])
            pygame.mixer.music.play(-1 if self.loop else 0)
            self.position = 0
            self.playing = True
        except pygame.error as e:
            logging.error("Erro ao carregar a música: %s", e)
            self.playing = False

    def stop(self) -> None:
        """Para a reprodução da música."""
        if not IS_RENDER:
            pygame.mixer.music.stop()
        self.playing = False

    def toggle_shuffle_without_repeat(self) -> bool:
        """Ativa ou desativa o modo shuffle sem repetição."""
        self.shuffle_without_repeat = not self.shuffle_without_repeat
        return self.shuffle_without_repeat

    def repeat_mode(self) -> bool:
        """Ativa ou desativa o modo repetir."""
        self.loop = not self.loop
        return self.loop

    def show_info(self) -> dict:
        """Retorna informações sobre a música atual."""
        if self.current_index < 0 or self.current_index >= len(self.music_list):
            return {"error": "Nenhuma música está tocando."}

        music = self.music_list[self.current_index]
        elapsed = self.position if IS_RENDER else max(0, pygame.mixer.music.get_pos() // 1000)
        self.position = elapsed
        return {
            "current_song": os.path.basename(music),
            "time_played": elapsed,
            "duration": self.get_current_duration(),
            "genre": next((g for g, songs in self.genres.items() if music in songs), "Desconhecido"),
            "full_path": music,
        }

    def set_position(self, time: int) -> None:
        """Define a posição de reprodução da música."""
        if IS_RENDER:
            logging.warning("Setar posição desativado no ambiente Render.")
            return

        if not self.playing or self.current_index == -1:
            raise Exception("Nenhuma música está tocando.")

        if time < 0:
            raise ValueError("Tempo não pode ser negativo.")

        duration = self.get_current_duration()
        if time > duration:
            raise ValueError(f"Tempo excede a duração ({duration} segundos).")

        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.play(loops=-1 if self.loop else 0, start=time)
            self.position = time
        except pygame.error as e:
            raise Exception(f"Erro ao ajustar posição: {e}") from e

    def select_genre(self, genre: str) -> None:
        """Seleciona um gênero e atualiza a playlist."""
        if genre not in self.genres:
            raise ValueError("Gênero não encontrado.")
        self.music_list = self.genres[genre]
        self.current_index = -1

    def reset_playlist(self) -> None:
        """Restaura a playlist original."""
        self._load_musics()

    def quit(self) -> None:
        """Finaliza o player."""
        if not IS_RENDER:
            pygame.mixer.quit()

    def clear_duration_cache(self) -> None:
        """Limpa o cache de durações para recálculo."""
        self.duration_cache.clear()
        self._cache_song_durations()

    def update_duration_cache(self, song_path: str) -> None:
        """Atualiza a duração de uma música específica."""
        self._cache_song_durations()
        if song_path in self.duration_cache:
            return self.duration_cache[song_path]
        else:
            return 0
