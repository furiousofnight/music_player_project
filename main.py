from music_player import MusicPlayer
import logging


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
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
                print("▶ Reproduzindo música...")
            elif choice == "2":
                player.stop()
                print("⏹ Música parada.")
            elif choice == "3":
                if player.current_index + 1 < len(player.music_list):
                    player.play_music(player.current_index + 1)
                    print("⏩ Próxima música.")
                else:
                    print("⚠️ Não há próxima música na playlist.")
            elif choice == "4":
                if player.current_index > 0:
                    player.play_music(player.current_index - 1)
                    print("⏪ Música anterior.")
                else:
                    print("⚠️ Não há música anterior na playlist.")
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
                    print(f"⚠️ {info['error']}")
            elif choice == "8":
                if player.music_list:
                    print("\n🎵 Playlist:")
                    for i, song in enumerate(player.music_list, start=1):
                        print(f"{i}. {song}")
                else:
                    print("⚠️ A playlist está vazia.")
            elif choice == "9":
                if player.genres:
                    print("\n🎸 Gêneros disponíveis:")
                    genres = list(player.genres.keys())
                    for i, genre in enumerate(genres, start=1):
                        print(f"{i}. {genre}")
                    genre_choice = input("Digite o número do gênero: ").strip()
                    if genre_choice.isdigit():
                        idx = int(genre_choice) - 1
                        if 0 <= idx < len(genres):
                            selected_genre = genres[idx]
                            player.select_genre(selected_genre)
                            print(f"🎸 Gênero selecionado: {selected_genre}")
                        else:
                            print("⚠️ Número de gênero inválido.")
                    else:
                        print("⚠️ Entrada inválida.")
                else:
                    print("⚠️ Nenhum gênero disponível.")
            elif choice == "10":
                player.reset_playlist()
                print("🔄 Playlist restaurada.")
            elif choice == "11":
                player.quit()
                print("❌ Saindo do player. Até logo!")
                break
            else:
                print("⚠️ Opção inválida. Tente novamente.")
        except Exception as e:
            logging.exception("Erro no menu interativo:")
            print(f"⚠️ Erro: {str(e)}")


if __name__ == "__main__":
    main()
