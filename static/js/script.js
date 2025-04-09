document.addEventListener("DOMContentLoaded", () => {
    const genreSelect = document.getElementById("genre-select");
    const loadGenreButton = document.getElementById("load-genre");
    const playlistElement = document.getElementById("playlist");
    const currentSongDisplay = document.getElementById("current-song");
    const genreDisplay = document.getElementById("genre");
    const timeDisplay = document.getElementById("time");
    const progressBar = document.getElementById("progress-bar");

    let intervalId = null;
    let userSeeking = false;
    let currentPlayingIndex = -1;
    let isRepeatActive = false;
    let isShuffleActive = false;
    let isProcessing = false;

    const toggleRepeat = async () => {
        if (isProcessing) return;
        isProcessing = true;
        const repeatBtn = document.getElementById("repeat");
        try {
            const response = await fetch("/api/repeat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
            });
            if (!response.ok) throw new Error(`Erro no backend (Repeat): ${response.status}`);
            const data = await response.json();
            isRepeatActive = data.repeat_status === "ativado";
            repeatBtn.classList.toggle("active", isRepeatActive);
            alert(`Modo repetir ${isRepeatActive ? "ativado" : "desativado"}`);
        } catch (error) {
            console.error("Erro ao alternar modo repetir:", error);
        } finally {
            isProcessing = false;
        }
    };

    const toggleShuffle = async () => {
        if (isProcessing) return;
        isProcessing = true;
        const shuffleBtn = document.getElementById("shuffle");
        try {
            const response = await fetch("/api/shuffle", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
            });
            if (!response.ok) throw new Error(`Erro no backend (Shuffle): ${response.status}`);
            const data = await response.json();
            isShuffleActive = data.shuffle_status === "ativado";
            shuffleBtn.classList.toggle("active", isShuffleActive);
            alert(`Modo shuffle ${isShuffleActive ? "ativado" : "desativado"}`);
        } catch (error) {
            console.error("Erro ao alternar modo shuffle:", error);
        } finally {
            isProcessing = false;
        }
    };

    const loadGenres = async () => {
        try {
            const response = await fetch("/api/genres");
            if (!response.ok) throw new Error(`Erro ao carregar gêneros: ${response.status}`);
            const data = await response.json();
            const genres = data.genres || {};
            genreSelect.innerHTML = "<option value='' disabled selected>Selecione um gênero</option>";

            if (!Object.keys(genres).length) {
                alert("Nenhum gênero disponível!");
                return;
            }

            Object.keys(genres).forEach((genre) => {
                const option = document.createElement("option");
                option.value = genre;
                option.textContent = capitalize(genre);
                genreSelect.appendChild(option);
            });
        } catch (error) {
            console.error("Erro ao carregar gêneros:", error);
        }
    };

    const loadGenrePlaylist = async () => {
        const selectedGenre = genreSelect.value;
        if (!selectedGenre) {
            alert("Selecione um gênero.");
            return;
        }

        try {
            const response = await fetch("/api/select_genre", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ genre: selectedGenre }),
            });
            if (!response.ok) throw new Error(`Erro ao carregar playlist do gênero: ${response.status}`);
            const data = await response.json();
            updatePlaylistDisplay(data.playlist || [], selectedGenre);
        } catch (error) {
            console.error("Erro ao carregar a playlist do gênero:", error);
        }
    };

    const updatePlaylistDisplay = (playlist, genre) => {
        genreDisplay.textContent = `Gênero: ${capitalize(genre) || "Desconhecido"}`;
        playlistElement.innerHTML = "";

        if (!playlist.length) {
            alert("Nenhuma música disponível no gênero selecionado.");
            currentSongDisplay.textContent = "Nenhuma música tocando no momento.";
            timeDisplay.textContent = "Tempo reproduzido: 00:00";
            progressBar.value = 0;
            return;
        }

        playlist.forEach((song, index) => {
            const li = document.createElement("li");
            li.textContent = `${index + 1}. ${extractSongName(song)}`;
            li.dataset.index = index;
            li.addEventListener("click", () => playSong(index));
            playlistElement.appendChild(li);
        });

        currentSongDisplay.textContent = "Nenhuma música tocando";
        progressBar.value = 0;
    };

    const playSong = async (index) => {
        try {
            const response = await fetch("/api/play", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ index }),
            });
            const data = await response.json();
            if (data.error) {
                alert(`Erro: ${data.error}`);
                return;
            }

            // Atualiza o elemento de áudio com a URL da música
            const audioPlayer = document.getElementById("audio-player");
            audioPlayer.src = data.song_url;
            audioPlayer.play();

            currentSongDisplay.textContent = `🎶 Tocando agora: ${data.current_song}`;
        } catch (err) {
            console.error("Erro ao iniciar a música:", err);
        }
    };

    const stopSong = async () => {
        try {
            await fetch("/api/stop", { method: "POST" });
            clearInterval(intervalId); // Limpa o temporizador
            currentPlayingIndex = -1;
            currentSongDisplay.textContent = "Nenhuma música tocando";
            timeDisplay.textContent = "Tempo reproduzido: 00:00";
            progressBar.value = 0;
        } catch (error) {
            console.error("Erro ao parar a música:", error);
        }
    };

    const startTimer = () => {
        console.log("Iniciando temporizador...");
        clearInterval(intervalId); // Limpa intervalos anteriores
        intervalId = setInterval(async () => {
            try {
                const response = await fetch("/api/info");
                const data = await response.json();
                if (data.error) {
                    clearInterval(intervalId);
                    currentSongDisplay.textContent = "Nenhuma música tocando";
                    console.error(data.error);
                    return;
                }
                updateProgressBar(data.info.time_played, data.info.duration);
            } catch (error) {
                console.error("Erro ao atualizar progresso:", error);
            }
        }, 1000);
    };

    const updateProgressBar = (currentTime, duration) => {
        if (!userSeeking) {
            progressBar.max = duration;
            progressBar.value = currentTime;
            timeDisplay.textContent = `Tempo: ${formatTime(currentTime)} / ${formatTime(duration)}`;
        }
    };

    progressBar.addEventListener("input", () => {
        userSeeking = true;
        timeDisplay.textContent = `Tempo: ${formatTime(progressBar.value)} / ${formatTime(progressBar.max)}`;
    });

    progressBar.addEventListener("change", async () => {
        const time = parseInt(progressBar.value, 10);
        try {
            const response = await fetch("/api/set_position", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ time }),
            });
            if (!response.ok) throw new Error("Erro ao ajustar posição");
            await response.json();
            userSeeking = false;
            startTimer(); // Reinicia o temporizador
        } catch (error) {
            console.error("Erro ao ajustar posição:", error);
            userSeeking = false;
        }
    });

    const capitalize = (str) => str.charAt(0).toUpperCase() + str.slice(1);
    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    };
    const extractSongName = (path) => path.split("/").pop().replace(/\.(mp3|wav|ogg|flac)$/i, "");

    // Eventos dos botões
    document.getElementById("play").addEventListener("click", () => playSong(0));
    document.getElementById("stop").addEventListener("click", stopSong);
    document.getElementById("repeat").addEventListener("click", toggleRepeat);
    document.getElementById("shuffle").addEventListener("click", toggleShuffle);
    loadGenreButton.addEventListener("click", loadGenrePlaylist);

    loadGenres();
});
