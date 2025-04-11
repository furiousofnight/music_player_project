document.addEventListener("DOMContentLoaded", () => {
    const genreSelect = document.getElementById("genre-select");
    const loadGenreButton = document.getElementById("load-genre");
    const playlistElement = document.getElementById("playlist");
    const currentSongDisplay = document.getElementById("current-song");
    const genreDisplay = document.getElementById("genre");
    const timeDisplay = document.getElementById("time");
    const progressBar = document.getElementById("progress-bar");
    const audioPlayer = new Audio();

    audioPlayer.preload = "auto";
    audioPlayer.volume = 1.0;

    let userSeeking = false;
    let currentDuration = 0;
    let currentIndex = 0;

    const toggleShuffle = () => {
        fetch("/api/shuffle", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        })
            .then(res => res.json())
            .then(({ success, data }) => {
                if (success) {
                    const shuffleBtn = document.getElementById("shuffle");
                    shuffleBtn.classList.toggle("active", data.shuffle_status);
                    alert(`🔀 Shuffle ${data.shuffle_status ? "ativado" : "desativado"}!`);
                }
            });
    };

    const toggleRepeat = () => {
        fetch("/api/repeat", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        })
            .then(res => res.json())
            .then(({ success, data }) => {
                if (success) {
                    const repeatBtn = document.getElementById("repeat");
                    repeatBtn.classList.toggle("active", data.repeat_status);
                    audioPlayer.loop = data.repeat_status;
                    alert(`🔁 Repeat ${data.repeat_status ? "ativado" : "desativado"}!`);
                }
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
            .then(({ data }) => {
                updatePlaylistDisplay(data.playlist, selectedGenre);
                currentIndex = 0;
            });
    };

    const updatePlaylistDisplay = (playlist, genre) => {
        genreDisplay.textContent = `Gênero: ${capitalize(genre)}`;
        playlistElement.innerHTML = "";

        if (!playlist.length) {
            alert("Nenhuma música disponível neste gênero.");
            currentSongDisplay.textContent = "Nenhuma música tocando.";
            timeDisplay.textContent = "Tempo: 00:00 / 00:00";
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
        currentIndex = index;
        fetch("/api/play", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ index }),
        })
            .then(res => res.json())
            .then(({ data }) => {
                const url = `/api/music/${encodeURIComponent(data.full_path)}`;
                audioPlayer.src = url;
                audioPlayer.play();
                currentSongDisplay.textContent = `🎶 Tocando agora: ${data.current_song}`;
            });
    };

    const stopSong = () => {
        fetch("/api/stop", { method: "POST" })
            .then(() => {
                audioPlayer.pause();
                audioPlayer.currentTime = 0;
                currentSongDisplay.textContent = "Nenhuma música tocando.";
                timeDisplay.textContent = "Tempo: 00:00 / 00:00";
                progressBar.value = 0;
            });
    };

    audioPlayer.addEventListener("loadedmetadata", () => {
        currentDuration = audioPlayer.duration;
        progressBar.max = currentDuration;
        updateProgressBar();
    });

    audioPlayer.addEventListener("timeupdate", () => {
        if (!userSeeking) updateProgressBar();
    });

    audioPlayer.addEventListener("ended", () => {
        const repeatActive = document.getElementById("repeat").classList.contains("active");
        const shuffleActive = document.getElementById("shuffle").classList.contains("active");

        if (repeatActive) {
            audioPlayer.currentTime = 0;
            audioPlayer.play();
        } else if (shuffleActive) {
            fetch("/api/next", { method: "POST" })
                .then(res => res.json())
                .then(({ data }) => {
                    const url = `/api/music/${encodeURIComponent(data.full_path)}`;
                    audioPlayer.src = url;
                    audioPlayer.play();
                    currentSongDisplay.textContent = `🎶 Tocando agora: ${data.current_song}`;
                });
        } else {
            document.getElementById("next").click();
        }
    });

    const updateProgressBar = () => {
        const currentTime = audioPlayer.currentTime;
        progressBar.value = currentTime;
        timeDisplay.textContent = `Tempo: ${formatTime(currentTime)} / ${formatTime(currentDuration)}`;
    };

    progressBar.addEventListener("input", () => {
        userSeeking = true;
        const time = Math.floor(progressBar.value);
        timeDisplay.textContent = `Tempo: ${formatTime(time)} / ${formatTime(currentDuration)}`;
    });

    progressBar.addEventListener("change", () => {
        const time = Math.floor(progressBar.value);
        audioPlayer.currentTime = time;
        userSeeking = false;
    });

    const capitalize = str => str.charAt(0).toUpperCase() + str.slice(1);
    const formatTime = seconds => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    };
    const extractSongName = path => path.split("/").pop().replace(/\.(mp3|wav|ogg|flac)$/i, "");

    document.getElementById("play").addEventListener("click", () => playSong(currentIndex));
    document.getElementById("stop").addEventListener("click", stopSong);
    document.getElementById("repeat").addEventListener("click", toggleRepeat);
    document.getElementById("shuffle").addEventListener("click", toggleShuffle);
    document.getElementById("next").addEventListener("click", () =>
        fetch("/api/next", { method: "POST" })
            .then(res => res.json())
            .then(({ data }) => {
                const url = `/api/music/${encodeURIComponent(data.full_path)}`;
                audioPlayer.src = url;
                audioPlayer.play();
                currentSongDisplay.textContent = `🎶 Tocando agora: ${data.current_song}`;
            })
    );
    document.getElementById("prev").addEventListener("click", () =>
        fetch("/api/previous", { method: "POST" })
            .then(res => res.json())
            .then(({ data }) => {
                const url = `/api/music/${encodeURIComponent(data.full_path)}`;
                audioPlayer.src = url;
                audioPlayer.play();
                currentSongDisplay.textContent = `🎶 Tocando agora: ${data.current_song}`;
            })
    );

    loadGenreButton.addEventListener("click", loadGenrePlaylist);
    loadGenres();
});
