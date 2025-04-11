// script.js atualizado para integração com API RESTful estruturada

document.addEventListener("DOMContentLoaded", () => {
    const genreSelect = document.getElementById("genre-select");
    const loadGenreButton = document.getElementById("load-genre");
    const playlistElement = document.getElementById("playlist");
    const currentSongDisplay = document.getElementById("current-song");
    const genreDisplay = document.getElementById("genre");
    const timeDisplay = document.getElementById("time");
    const progressBar = document.getElementById("progress-bar");
    const audioPlayer = new Audio();

    let intervalId = null;
    let userSeeking = false;

    const toggleShuffle = () => {
        fetch("/api/shuffle", { method: "POST", headers: { "Content-Type": "application/json" } })
            .then(res => res.json())
            .then(({ data }) => {
                const shuffleBtn = document.getElementById("shuffle");
                shuffleBtn.classList.toggle("active", data.shuffle_status);
                alert(`Modo shuffle ${data.shuffle_status ? "ativado" : "desativado"}`);
            });
    };

    const toggleRepeat = () => {
        fetch("/api/repeat", { method: "POST", headers: { "Content-Type": "application/json" } })
            .then(res => res.json())
            .then(({ data }) => {
                const repeatBtn = document.getElementById("repeat");
                repeatBtn.classList.toggle("active", data.repeat_status);
                alert(`Modo repetir ${data.repeat_status ? "ativado" : "desativado"}`);
            });
    };

    const loadGenres = () => {
        fetch("/api/genres")
            .then(res => res.json())
            .then(({ data }) => {
                genreSelect.innerHTML = "<option value='' disabled selected>Selecione um gênero</option>";
                if (!data || Object.keys(data).length === 0) return alert("Nenhum gênero disponível!");

                Object.keys(data).forEach((genre) => {
                    const option = document.createElement("option");
                    option.value = genre;
                    option.textContent = capitalize(genre);
                    genreSelect.appendChild(option);
                });
            });
    };

    const loadGenrePlaylist = () => {
        const selectedGenre = genreSelect.value;
        if (!selectedGenre) return alert("Selecione um gênero.");

        fetch("/api/select_genre", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ genre: selectedGenre }),
        })
            .then(res => res.json())
            .then(({ data }) => updatePlaylistDisplay(data.playlist, selectedGenre));
    };

    const updatePlaylistDisplay = (playlist, genre) => {
        genreDisplay.textContent = `Gênero: ${capitalize(genre)}`;
        playlistElement.innerHTML = "";

        if (!playlist.length) {
            alert("Nenhuma música disponível neste gênero.");
            currentSongDisplay.textContent = "Nenhuma música tocando.";
            timeDisplay.textContent = "Tempo reproduzido: 00:00";
            progressBar.value = 0;
            return;
        }

        playlist.forEach((song, index) => {
            const li = document.createElement("li");
            li.textContent = `${index + 1}. ${extractSongName(song)}`;
            li.addEventListener("click", () => playSong(index));
            playlistElement.appendChild(li);
        });

        currentSongDisplay.textContent = "Nenhuma música tocando.";
        progressBar.value = 0;
    };

    const playSong = (index) => {
        fetch("/api/play", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ index }),
        })
            .then(res => res.json())
            .then(({ data }) => {
                const url = `/api/music/${encodeURIComponent(data.current_song)}`;
                audioPlayer.src = url;
                audioPlayer.play();
                currentSongDisplay.textContent = `🎶 Tocando agora: ${data.current_song}`;
                startTimer();
            });
    };

    const stopSong = () => {
        fetch("/api/stop", { method: "POST" })
            .then(res => res.json())
            .then(() => {
                audioPlayer.pause();
                audioPlayer.currentTime = 0;
                currentSongDisplay.textContent = "Nenhuma música tocando.";
                timeDisplay.textContent = "Tempo reproduzido: 00:00";
                progressBar.value = 0;
                clearInterval(intervalId);
            });
    };

    const startTimer = () => {
        clearInterval(intervalId);
        intervalId = setInterval(() => {
            fetch("/api/info")
                .then(res => res.json())
                .then(({ data }) => {
                    if (data.current_song === "Nenhuma música tocando") {
                        clearInterval(intervalId);
                        currentSongDisplay.textContent = data.current_song;
                        timeDisplay.textContent = "Tempo reproduzido: 00:00";
                        progressBar.value = 0;
                        return;
                    }
                    updateProgressBar(data.time_played, data.duration);
                    currentSongDisplay.textContent = `🎶 Tocando agora: ${data.current_song}`;
                });
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
        const currentTime = Math.floor(progressBar.value);
        timeDisplay.textContent = `Tempo: ${formatTime(currentTime)} / ${formatTime(progressBar.max)}`;
    });

    progressBar.addEventListener("change", () => {
        const time = Math.floor(progressBar.value);
        fetch("/api/set_position", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ time }),
        })
            .then(res => res.json())
            .then(({ data }) => {
                userSeeking = false;
                progressBar.value = data.current_time;
                timeDisplay.textContent = `Tempo: ${formatTime(data.current_time)} / ${formatTime(data.duration)}`;
            });
    });

    const capitalize = str => str.charAt(0).toUpperCase() + str.slice(1);
    const formatTime = seconds => `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
    const extractSongName = path => path.split("/").pop().replace(/\.(mp3|wav|ogg|flac)$/i, "");

    document.getElementById("play").addEventListener("click", () => playSong(0));
    document.getElementById("stop").addEventListener("click", stopSong);
    document.getElementById("repeat").addEventListener("click", toggleRepeat);
    document.getElementById("shuffle").addEventListener("click", toggleShuffle);
    document.getElementById("next").addEventListener("click", () => fetch("/api/next", { method: "POST" }).then(res => res.json()).then(({ data }) => {
        currentSongDisplay.textContent = `🎶 Tocando agora: ${data.current_song}`;
        startTimer();
    }));
    document.getElementById("prev").addEventListener("click", () => fetch("/api/previous", { method: "POST" }).then(res => res.json()).then(({ data }) => {
        currentSongDisplay.textContent = `🎶 Tocando agora: ${data.current_song}`;
        startTimer();
    }));

    loadGenreButton.addEventListener("click", loadGenrePlaylist);
    loadGenres();
});
