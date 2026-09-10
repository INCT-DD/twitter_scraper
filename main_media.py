from media_downloader import (
    MediaDownloader
)

from media_queue import (
    reset_downloading,
    retry_failed_media
)


def main():

    # ============================================
    # RECUPERAR DOWNLOADS INTERROMPIDOS
    # ============================================

    recovered_downloading = reset_downloading()

    if recovered_downloading > 0:

        print()

        print(
            f"Downloads interrompidos recuperados: "
            f"{recovered_downloading}"
        )

    # ============================================
    # RECUPERAR DOWNLOADS COM ERRO
    # ============================================

    recovered_errors = retry_failed_media()

    if recovered_errors > 0:

        print()

        print(
            f"Downloads com erro recuperados para "
            f"nova tentativa: {recovered_errors}"
        )

    # ============================================
    # INICIAR DOWNLOADER
    # ============================================

    downloader = MediaDownloader()

    downloader.process_queue()


if __name__ == "__main__":

    main()