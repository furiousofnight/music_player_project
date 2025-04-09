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
    let isRepeatActive = false; // Estado do modo repetir
    let currentPlayingIndex = 0; // Índice da música atual

    // Função para alternar o modo repetir
    const toggleRepeat = () => {
        isRepeatActive = !isRepeatActive;

        fetch("/api/repeat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        })
            .then((response) => response.json())
            .then((data) => {
                const repeatBtn = document.getElementById("repeat");
                repeatBtn.classList.toggle("active", isRepeatActive); // Atualiza estado visual
                alert(`Modo repetir ${data.repeat_status}!`);
            })
            .catch((err) => {
                console.error("Erro ao alterar o modo repetir:", err);
                alert("Não foi possível alterar o modo repetir.");
            });
    };

    // Função para extrair o nome da música do caminho
    const extractSongName = (filePath) => {
        const fileName = filePath.split("/").pop().split("\\").pop();
        return fileName.replace(/\.(mp3|wav|ogg|flac)$/i, "").replace(/-/g, " ");
    };

    // Carregar os gêneros disponíveis
    const loadGenres = () => {
        fetch("/api/genres")
            .then((response) => response.json())
            .then((data) => {
                const genres = data.genres;
                if (Object.keys(genres).length === 0) {
                    alert("Nenhum gênero encontrado!");
                    return;
                }
                genreSelect.innerHTML = "<option value='' disabled selected>Selecione um gênero</option>"; // Reseta as opções
                Object.keys(genres).forEach((genre) => {
                    const option = document.createElement("option");
                    option.value = genre;
                    option.textContent = capitalize(genre);
                    genreSelect.appendChild(option);
                });
            })
            .catch((err) => {
                console.error("Erro ao carregar gêneros:", err);
                alert("Não foi possível carregar a lista de gêneros.");
            });
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
            .then((response) => response.json())
            .then((data) => {
                const playlist = data.playlist;

                // Exibe alerta se a playlist estiver vazia
                if (!playlist || playlist.length === 0) {
                    alert("Nenhuma música disponível no gênero selecionado.");
                    genreDisplay.textContent = `Gênero: ${capitalize(selectedGenre)}`;
                    currentSongDisplay.textContent = "Nenhuma música tocando";
                    timeDisplay.textContent = "Tempo reproduzido: 00:00";
                    playlistElement.innerHTML = "";
                    progressBar.value = 0;
                    return;
                }

                // Processa normalmente caso haja músicas
                genreDisplay.textContent = `Gênero: ${capitalize(selectedGenre)}`;
                currentSongDisplay.textContent = "Nenhuma música tocando";
                timeDisplay.textContent = "Tempo reproduzido: 00:00";
                playlistElement.innerHTML = ""; // Limpa a playlist antiga

                playlist.forEach((song, index) => {
                    const li = document.createElement("li");
                    const songName = extractSongName(song);
                    li.textContent = `${index + 1}. ${capitalize(songName)}`;
                    li.dataset.index = index;
                    li.addEventListener("click", () => playSong(index));
                    playlistElement.appendChild(li);
                });
                progressBar.value = 0; // Reinicia a barra de progresso
            })
            .catch((err) => {
                console.error("Erro ao carregar a playlist:", err);
                alert("Erro ao carregar a playlist. Verifique a API.");
            });
    };

    // Tocar uma música
    const playSong = (index) => {
        currentPlayingIndex = index; // Atualiza o índice da música atual
        fetch("/api/play", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ index }),
        })
            .then((res) => res.json())
            .then((data) => {
                currentSongDisplay.textContent = `🎶 Tocando agora: ${data.current_song} 🎶`;
                progressBar.disabled = false;
                startTimer();
            })
            .catch((err) => {
                console.error("Erro ao tocar música:", err);
                alert("Não foi possível iniciar a reprodução.");
            });
    };

    // Manipular quando uma música chegar ao fim
    const handleSongEnd = () => {
        if (isRepeatActive) {
            // Repetir a música atual
            playSong(currentPlayingIndex);
        } else {
            // Ir para a próxima música
            fetch("/api/next", { method: "POST" })
                .then((res) => res.json())
                .then((data) => {
                    currentSongDisplay.textContent = `🎶 Tocando agora: ${data.current_song} 🎶`;
                    startTimer();
                })
                .catch((err) => {
                    console.error("Erro ao ir para a próxima música:", err);
                });
        }
    };

    // Parar a reprodução
    const stopSong = () => {
        clearInterval(intervalId); // Para o timer
        progressBar.value = 0; // Reseta a barra de progresso
        timeDisplay.textContent = "Tempo reproduzido: 00:00";

        fetch("/api/stop", { method: "POST" })
            .then(() => {
                currentSongDisplay.textContent = "Nenhuma música tocando";
                progressBar.disabled = true;
            })
            .catch((err) => {
                console.error("Erro ao parar música:", err);
                alert("Erro ao parar a música.");
            });
    };

    // Atualizar a barra de progresso
    const updateProgressBar = (currentTime, duration) => {
        if (!userSeeking) {
            progressBar.max = duration;
            progressBar.value = currentTime;
            timeDisplay.textContent = `Tempo: ${formatTime(currentTime)} / ${formatTime(duration)}`;
        }
    };

    // Iniciar o timer da barra de progresso
    const startTimer = () => {
        clearInterval(intervalId);
        intervalId = setInterval(() => {
            fetch("/api/info")
                .then((res) => res.json())
                .then((data) => {
                    const info = data.info;

                    if (!info || !info.time_played || !info.duration) {
                        clearInterval(intervalId);
                        return;
                    }

                    updateProgressBar(info.time_played, info.duration);

                    if (info.time_played >= info.duration) {
                        clearInterval(intervalId);
                        handleSongEnd(); // Lida com o fim da música
                    }
                })
                .catch((err) => {
                    console.error("Erro ao atualizar o tempo:", err);
                });
        }, 1000);
    };

    // Formatar o tempo para mm:ss
    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    };

    // Manipulação manual da barra de progresso
    progressBar.addEventListener("change", () => {
        userSeeking = false;
        const newTime = parseInt(progressBar.value, 10);

        fetch("/api/seek", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ time: newTime }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.status === "success") {
                    startTimer(); // Reinicia o timer no novo ponto
                }
            })
            .catch((err) => {
                console.error("Erro ao ajustar o tempo:", err);
            });
    });

    // Capitalizar texto
    const capitalize = (str) => str.charAt(0).toUpperCase() + str.slice(1);

    // Botões e Eventos
    document.getElementById("play").addEventListener("click", () => playSong(0));
    document.getElementById("stop").addEventListener("click", stopSong);
    document.getElementById("next").addEventListener("click", () => handleSongEnd());
    document.getElementById("prev").addEventListener("click", () => handleSongEnd());
    document.getElementById("repeat").addEventListener("click", toggleRepeat);
    loadGenreButton.addEventListener("click", loadGenrePlaylist);

    // Carregar os gêneros ao iniciar
    loadGenres();
});