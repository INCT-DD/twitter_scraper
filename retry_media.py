import time #só seria necessário caso tivesse,
#colocado uma espera entre tentativas. 
#analisar isso depois

from media_queue import (
    retry_failed_media
)

from media_downloader import (
    MediaDownloader
)


def main():

    print()
    print("=" * 60)
    print("RETRY DE MÍDIAS")
    print("=" * 60)

    recovered = retry_failed_media()

    print(
        f"Mídias recuperadas: {recovered}"
    )

    if recovered == 0:

        print()
        print(
            "Nenhuma mídia disponível para retry."
        )

        print("=" * 60)

        return

    downloader = MediaDownloader()

    downloader.process_queue()


if __name__ == "__main__":

    main()