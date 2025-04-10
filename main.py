from music_player import MusicPlayer


def main():
    player = MusicPlayer(music_folder="songs")
    while True:
        print("\n🎵 MENU DO PLAYER 🎵")
        print("[1] ▶ Reproduzir música")
        print("[2] ⏹ Parar música")
        print("[3] ⏩ Próxima música")
        print("[4] ⏪ Música anterior")
        print("[5] 🔀 Ativar/desativar modo shuffle")
        print("[6] 🔁 Ativar/desativar modo repetir")
        print("[7] ℹ️ Informações da música atual")
        print("[8] 📃 Mostrar playlist")
        print("[9] 🎸 Selecionar gênero")
        print("[10] 🔄 Restaurar playlist")
        print("[11] ❌ Sair")
        choice = input("Escolha uma opção: ").strip()

        try:
            if choice == "1":
                query = input("Digite o índice ou parte do nome da música: ").strip()
                if query.isdigit():
                    player.play_music(int(query) - 1)
                else:
                    player.play_music(query)
            elif choice == "2":
                player.stop()
                print("⏹ Música parada.")
            elif choice == "3":
                player.play_music(player.current_index + 1)
                print("⏩ Próxima música.")
            elif choice == "4":
                player.play_music(player.current_index - 1)
                print("⏪ Música anterior.")
            elif choice == "5":
                status = player.toggle_shuffle_without_repeat()
                print(f"🔀 Modo shuffle {'ativado' if status else 'desativado'}.")
            elif choice == "6":
                status = player.repeat_mode()
                print(f"🔁 Modo repetir {'ativado' if status else 'desativado'}.")
            elif choice == "7":
                info = player.show_info()
                if "error" not in info:
                    print(f"🎶 Tocando: {info['current_song']}")
                    print(f"📂 Gênero: {info['genre']}")
                    print(f"⏱ Tempo reproduzido: {info['time_played']} / {info['duration']} segundos")
                else:
                    print(info["error"])
            elif choice == "8":
                print("\n🎵 Playlist:")
                for i, song in enumerate(player.music_list, start=1):
                    print(f"{i}. {song}")
            elif choice == "9":
                print("\n🎸 Gêneros disponíveis:")
                for i, genre in enumerate(player.genres.keys(), start=1):
                    print(f"{i}. {genre}")
                genre_choice = input("Digite o número do gênero: ").strip()
                if genre_choice.isdigit():
                    selected_genre = list(player.genres.keys())[int(genre_choice) - 1]
                    player.select_genre(selected_genre)
                    print(f"🎸 Gênero selecionado: {selected_genre}")
            elif choice == "10":
                player.reset_playlist()
                print("Playlist restaurada.")
            elif choice == "11":
                player.quit()
                print("Saindo do player.")
                break
            else:
                print("Opção inválida. Tente novamente.")
        except Exception as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    main()
