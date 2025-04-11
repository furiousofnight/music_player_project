import os
import random
from mutagen import File, MutagenError  # Para analisar duração do arquivo de áudio


def _normalize_string(string: str) -> str:
    """Normaliza strings para comparação insensível a maiúsculas, hífens e underscores."""
    return string.lower().strip().replace("-", " ").replace("_", " ")


class MusicPlayer:
    def __init__(self, music_folder: str = "songs"):
        self.music_folder = music_folder
        self.music_list: list[str] = []
        self.current_index: int = -1
        self.genres: dict[str, list[str]] = {}
        self.duration_cache: dict[str, int] = {}
        self.position: int = 0
        self.loop: bool = False
        self.shuffle_without_repeat: bool = False
        self.played_indices: list[int] = []

        self._load_musics()

    def _load_musics(self) -> None:
        self.music_list.clear()
        self.genres.clear()

        if not os.path.exists(self.music_folder):
            os.makedirs(self.music_folder)

        for root, _, files in os.walk(self.music_folder):
            for file in files:
                if file.lower().endswith((".mp3", ".wav", ".flac", ".ogg")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.music_folder)
                    genre = rel_path.split(os.sep)[0]  # Subpasta principal = gênero
                    self.music_list.append(rel_path)

                    if genre not in self.genres:
                        self.genres[genre] = []
                    self.genres[genre].append(rel_path)

        self._cache_song_durations()

    def _cache_song_durations(self) -> None:
        for song in self.music_list:
            abs_path = os.path.join(self.music_folder, song)
            if song not in self.duration_cache:
                try:
                    audio = File(abs_path)
                    self.duration_cache[song] = int(audio.info.length) if audio and hasattr(audio.info, "length") else 0
                except (MutagenError, AttributeError) as e:
                    print(f"Erro ao processar '{song}': {e}")
                    self.duration_cache[song] = 0

    def get_current_duration(self) -> int:
        if 0 <= self.current_index < len(self.music_list):
            return self.duration_cache.get(self.music_list[self.current_index], 0)
        return 0

    def play_music(self, query: int | str | None = None) -> None:
        if not self.music_list:
            return

        if isinstance(query, int):
            if 0 <= query < len(self.music_list):
                self.current_index = query
        elif isinstance(query, str):
            for index, song in enumerate(self.music_list):
                if _normalize_string(query) in _normalize_string(song):
                    self.current_index = index
                    break
        elif self.shuffle_without_repeat:
            self._play_next_random()
            return
        else:
            self.current_index = (self.current_index + 1) % len(self.music_list)

        self.position = 0  # Resetar a posição ao tocar nova música

    def _play_next_random(self) -> None:
        if not self.music_list:
            return
        remaining = [i for i in range(len(self.music_list)) if i not in self.played_indices]
        if not remaining:
            self.played_indices.clear()
            remaining = list(range(len(self.music_list)))
        self.current_index = random.choice(remaining)
        self.played_indices.append(self.current_index)

    def stop(self) -> None:
        self.current_index = -1
        self.position = 0

    def toggle_shuffle_without_repeat(self) -> bool:
        self.shuffle_without_repeat = not self.shuffle_without_repeat
        return self.shuffle_without_repeat

    def repeat_mode(self) -> bool:
        self.loop = not self.loop
        return self.loop

    def show_info(self) -> dict:
        if self.current_index == -1 or self.current_index >= len(self.music_list):
            return {
                "current_song": "Nenhuma música tocando",
                "time_played": 0,
                "duration": 0,
                "genre": "N/A",
                "full_path": ""
            }

        song = self.music_list[self.current_index]
        return {
            "current_song": os.path.basename(song),
            "time_played": self.position,
            "duration": self.get_current_duration(),
            "genre": next((g for g, songs in self.genres.items() if song in songs), "Desconhecido"),
            "full_path": song,
        }

    def set_position(self, time: int) -> None:
        self.position = max(0, min(time, self.get_current_duration()))

    def select_genre(self, genre: str) -> None:
        if genre not in self.genres:
            raise ValueError("Gênero não encontrado.")
        self.music_list = self.genres[genre]
        self.current_index = -1

    def reset_playlist(self) -> None:
        self._load_musics()

    def next_music(self) -> None:
        if not self.music_list:
            return
        if self.shuffle_without_repeat:
            self._play_next_random()
        else:
            self.current_index = (self.current_index + 1) % len(self.music_list)
        self.position = 0

    def previous_music(self) -> None:
        if not self.music_list:
            return
        self.current_index = (self.current_index - 1) % len(self.music_list)
        self.position = 0