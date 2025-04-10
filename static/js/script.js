document.addEventListener("DOMContentLoaded", () => {
    // Elementos principais
    const genreSelect = document.getElementById("genre-select");
    const loadGenreButton = document.getElementById("load-genre");
    const playlistElement = document.getElementById("playlist");
    const currentSongDisplay = document.getElementById("current-song");
    const genreDisplay = document.getElementById("genre");
    const timeDisplay = document.getElementById("time");
    const progressBar = document.getElementById("progress-bar");

    let intervalId = null; // ID do intervalo de atualização
    let userSeeking = false; // Indica se o usuário está manipulando a barra de progresso
    let currentPlayingIndex = -1; // Índice da música atual
    let isRepeatActive = false; // Estado do botão repetir (sincronizado com o backend)
    let isShuffleActive = false; // Estado do modo shuffle (sincronizado com o backend)
    let isProcessing = false; // Controle de cliques repetidos (ex.: repeat/shuffle)

    // Ativar/desativar o modo shuffle
    const toggleShuffle = () => {
        fetch("/api/shuffle", { method: "POST", headers: { "Content-Type": "application/json" } })
            .then((response) => response.json())
            .then((data) => {
                const shuffleBtn = document.getElementById("shuffle");
                shuffleBtn.classList.toggle("active", data.shuffle_status === "ativado");
                alert(`Modo shuffle ${data.shuffle_status}`);
            })
            .catch((error) => console.error("Erro ao alternar modo shuffle:", error));
    };

    // Ativar/desativar o modo repeat
    const toggleRepeat = () => {
        fetch("/api/repeat", { method: "POST", headers: { "Content-Type": "application/json" } })
            .then((response) => response.json())
            .then((data) => {
                const repeatBtn = document.getElementById("repeat");
                repeatBtn.classList.toggle("active", data.repeat_status === "ativado");
                alert(`Modo repetir ${data.repeat_status}`);
            })
            .catch((error) => console.error("Erro ao alternar modo repetir:", error));
    };

    // Carregar gêneros
    const loadGenres = () => {
        fetch("/api/genres")
            .then((response) => {
                if (!response.ok) throw new Error(`Erro ao carregar gêneros: ${response.status}`);
                return response.json();
            })
            .then((data) => {
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
            })
            .catch((error) => console.error("Erro ao carregar gêneros:", error));
    };

    // Carregar músicas do gênero selecionado
    const loadGenrePlaylist = () => {
        const selectedGenre = genreSelect.value;
        if (!selectedGenre) {
            alert("Selecione um gênero.");
            return;
        }

        fetch("/api/select_genre", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ genre: selectedGenre }),
        })
            .then((response) => {
                if (!response.ok) throw new Error(`Erro ao carregar playlist do gênero: ${response.status}`);
                return response.json();
            })
            .then((data) => updatePlaylistDisplay(data.playlist || [], selectedGenre))
            .catch((error) => console.error("Erro ao carregar a playlist do gênero:", error));
    };

    // Atualizar exibição da playlist
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

    // Reproduzir música por índice
    const playSong = (index) => {
        fetch("/api/play", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ index }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(`Erro: ${data.error}`);
                    return;
                }
                currentPlayingIndex = index; // Atualiza o índice atual
                currentSongDisplay.textContent = `🎶 Tocando agora: ${data.current_song}`;
                startTimer(); // Inicia o temporizador
            })
            .catch((err) => console.error("Erro ao iniciar a música:", err));
    };

    // Parar música
    const stopSong = () => {
        fetch("/api/stop", { method: "POST" })
            .then((response) => response.json())
            .then((data) => {
                if (data.status === "stopped") {
                    clearInterval(intervalId); // Para o temporizador
                    currentPlayingIndex = -1; // Reseta o índice atual
                    currentSongDisplay.textContent = "Nenhuma música tocando";
                    timeDisplay.textContent = "Tempo reproduzido: 00:00";
                    progressBar.value = 0; // Reseta a barra de progresso
                    alert("Música parada com sucesso.");
                }
            })
            .catch((error) => console.error("Erro ao parar a música:", error));
    };

    // Iniciar temporizador de progresso
    const startTimer = () => {
        clearInterval(intervalId);
        intervalId = setInterval(() => {
            fetch("/api/info")
                .then((response) => response.json())
                .then((data) => {
                    if (data.info.current_song === "Nenhuma música tocando") {
                        clearInterval(intervalId);
                        currentSongDisplay.textContent = "Nenhuma música tocando";
                        timeDisplay.textContent = "Tempo reproduzido: 00:00";
                        progressBar.value = 0;
                        return;
                    }

                    // Atualiza a barra de progresso
                    updateProgressBar(data.info.time_played, data.info.duration);

                    // Atualiza o nome da música se mudou
                    if (currentSongDisplay.textContent !== `🎶 Tocando agora: ${data.info.current_song}`) {
                        currentSongDisplay.textContent = `🎶 Tocando agora: ${data.info.current_song}`;
                    }
                })
                .catch((error) => console.error("Erro ao atualizar progresso:", error));
        }, 1000);
    };

    // Atualizar barra de progresso
    const updateProgressBar = (currentTime, duration) => {
        if (!userSeeking) { // Só atualizar se o usuário não estiver manipulando
            progressBar.max = duration;
            progressBar.value = currentTime;
            timeDisplay.textContent = `Tempo: ${formatTime(currentTime)} / ${formatTime(duration)}`;
        }
    };

    // Quando o usuário arrasta a barra de progresso
    progressBar.addEventListener("input", () => {
        userSeeking = true; // Indica que o usuário está manipulando
        const currentTime = Math.floor(progressBar.value); // Garante que o valor seja inteiro
        timeDisplay.textContent = `Tempo: ${formatTime(currentTime)} / ${formatTime(progressBar.max)}`;
    });

    // Quando o usuário solta a barra de progresso
    progressBar.addEventListener("change", () => {
        const time = Math.floor(progressBar.value); // Garante que o valor seja inteiro
        fetch("/api/set_position", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ time }), // Atualiza o tempo no backend
        })
            .then((response) => {
                if (!response.ok) throw new Error("Erro ao ajustar posição");
                return response.json();
            })
            .then((data) => {
                if (data.success) {
                    userSeeking = false; // Indica que o usuário terminou de ajustar
                    progressBar.value = data.current_time; // Atualiza a barra de progresso com o tempo ajustado
                    timeDisplay.textContent = `Tempo: ${formatTime(data.current_time)} / ${formatTime(data.duration)}`;
                } else {
                    console.error("Erro ao ajustar posição:", data.error);
                }
            })
            .catch((error) => {
                console.error("Erro ao ajustar posição:", error);
                userSeeking = false; // Certifica-se de que volta ao estado padrão
            });
    });

    // Funções auxiliares
    const capitalize = (str) => str.charAt(0).toUpperCase() + str.slice(1);
    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    };
    const extractSongName = (path) => path.split("/").pop().replace(/\.(mp3|wav|ogg|flac)$/i, "");

    // Event listeners
    document.getElementById("play").addEventListener("click", () => playSong(0));
    document.getElementById("stop").addEventListener("click", stopSong);
    document.getElementById("repeat").addEventListener("click", toggleRepeat);
    document.getElementById("shuffle").addEventListener("click", toggleShuffle);
    loadGenreButton.addEventListener("click", loadGenrePlaylist);
    document.getElementById("next").addEventListener("click", () => {
        fetch("/api/next", { method: "POST" })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                    return;
                }
                currentSongDisplay.textContent = `🎶 Tocando agora: ${data.current_song}`;
                startTimer(); // Reinicia o temporizador
            })
            .catch((error) => console.error("Erro ao ir para a próxima música:", error));
    });

    document.getElementById("prev").addEventListener("click", () => {
        fetch("/api/previous", { method: "POST" })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                    return;
                }
                currentSongDisplay.textContent = `🎶 Tocando agora: ${data.current_song}`;
                startTimer(); // Reinicia o temporizador
            })
            .catch((error) => console.error("Erro ao voltar para a música anterior:", error));
    });

    // Carregar gêneros ao iniciar
    loadGenres();
});