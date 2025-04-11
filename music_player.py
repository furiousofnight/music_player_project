import os
import random
import threading
from mutagen import File, MutagenError  # Para analisar duração do arquivo de áudio

# Detecta se está em ambiente Fly.io (sem pygame)
IS_RENDER = os.getenv("RENDER") == "true"

if not IS_RENDER:
    import pygame  # pygame apenas em ambiente local


def _normalize_string(string: str) -> str:
    """Normaliza strings para comparação insensível a maiúsculas, hífens e underscores."""
    return string.lower().strip().replace("-", " ").replace("_", " ")


class MusicPlayer:
    def __init__(self, music_folder: str = "songs"):
        """Inicializa o reprodutor de música com estrutura adaptável a múltiplos ambientes."""
        self.music_folder = music_folder
        self.music_list: list[str] = []
        self.current_index: int = -1
        self.playing: bool = False
        self.genres: dict[str, list[str]] = {}
        self.duration_cache: dict[str, int] = {}
        self.position: int = 0

        self.loop: bool = False
        self.shuffle_without_repeat: bool = False
        self.played_indices: list[int] = []

        self.lock = threading.Lock()

        if not IS_RENDER:
            try:
                pygame.init()
                pygame.mixer.init()
            except pygame.error as error:
                raise RuntimeError(f"Erro ao inicializar pygame: {error}")

        self._load_musics()

    def _load_musics(self) -> None:
        """Carrega e classifica as músicas por gênero, com cache de durações."""
        self.music_list.clear()
        self.genres.clear()

        if not os.path.exists(self.music_folder):
            os.makedirs(self.music_folder)

        for root, _, files in os.walk(self.music_folder):
            for file in files:
                if file.lower().endswith((".mp3", ".wav", ".flac", ".ogg")):
                    path = os.path.join(root, file)
                    genre = os.path.relpath(root, self.music_folder).split(os.sep)[0]  # Gênero é a subpasta imediata
                    self.music_list.append(path)

                    if genre not in self.genres:
                        self.genres[genre] = []
                    self.genres[genre].append(path)

        self._cache_song_durations()

    def _cache_song_durations(self) -> None:
        """Calcula e armazena a duração das músicas usando Mutagen."""
        for song in self.music_list:
            if song not in self.duration_cache:
                try:
                    audio = File(song)
                    self.duration_cache[song] = int(audio.info.length) if audio and hasattr(audio.info, "length") else 0
                except (MutagenError, AttributeError) as e:
                    print(f"Erro ao processar '{song}': {e}")
                    self.duration_cache[song] = 0

    def get_current_duration(self) -> int:
        if 0 <= self.current_index < len(self.music_list):
            return self.duration_cache.get(self.music_list[self.current_index], 0)
        return 0

    def play_music(self, query: int | str | None = None) -> None:
        with self.lock:
            if not self.music_list:
                print("Nenhuma música disponível.")
                return

            if isinstance(query, int):
                if query < 0:
                    query = len(self.music_list) - 1
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
        if not self.music_list:
            print("Nenhuma música disponível.")
            return

        remaining = [i for i in range(len(self.music_list)) if i not in self.played_indices]
        if not remaining:
            self.played_indices.clear()
            remaining = list(range(len(self.music_list)))

        self.current_index = random.choice(remaining)
        self.played_indices.append(self.current_index)
        self._play_current_music()

    def _play_current_music(self) -> None:
        if IS_RENDER:
            return

        try:
            pygame.mixer.music.load(self.music_list[self.current_index])
            pygame.mixer.music.play(-1 if self.loop else 0)
            self.position = 0
            self.playing = True
        except pygame.error as e:
            print(f"Erro ao tocar música: {e}")
            self.playing = False

    def stop(self) -> None:
        if not IS_RENDER:
            pygame.mixer.music.stop()
        self.playing = False

    def toggle_shuffle_without_repeat(self) -> bool:
        self.shuffle_without_repeat = not self.shuffle_without_repeat
        return self.shuffle_without_repeat

    def repeat_mode(self) -> bool:
        self.loop = not self.loop
        return self.loop

    def show_info(self) -> dict:
        if self.current_index < 0 or self.current_index >= len(self.music_list):
            return {"error": "Nenhuma música está tocando."}

        music = self.music_list[self.current_index]
        elapsed = 0

        if not IS_RENDER:
            elapsed = max(0, pygame.mixer.music.get_pos() // 1000)
            self.position = elapsed

            if not pygame.mixer.music.get_busy() and elapsed >= self.get_current_duration():
                with self.lock:
                    if self.loop:
                        self._play_current_music()
                    elif self.shuffle_without_repeat:
                        self._play_next_random()
                    else:
                        self.current_index = (self.current_index + 1) % len(self.music_list)
                        self._play_current_music()

        return {
            "current_song": os.path.basename(music),
            "time_played": elapsed,
            "duration": self.get_current_duration(),
            "genre": next((g for g, songs in self.genres.items() if music in songs), "Desconhecido"),
            "full_path": music,
        }

    def set_position(self, time: int) -> None:
        if not self.playing or self.current_index == -1:
            raise Exception("Nenhuma música está tocando.")
        if time < 0:
            raise ValueError("Tempo não pode ser negativo.")
        duration = self.get_current_duration()
        if time > duration:
            raise ValueError(f"Tempo excede a duração de {duration} segundos.")
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.play(loops=-1 if self.loop else 0, start=time)
            self.position = time
        except pygame.error as e:
            raise Exception(f"Erro ao ajustar posição: {str(e)}")

    def select_genre(self, genre: str) -> None:
        if genre not in self.genres:
            raise ValueError("Gênro não encontrado.")
        self.music_list = self.genres[genre]
        self.current_index = -1

    def reset_playlist(self) -> None:
        self._load_musics()

    def quit(self) -> None:
        if not IS_RENDER:
            pygame.mixer.quit()