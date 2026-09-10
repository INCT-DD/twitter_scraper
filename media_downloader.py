
import time
import requests
from pathlib import Path

from media_queue import (
    get_next_media,
    mark_downloaded,
    mark_error
)


class MediaDownloader:

    RETRY_DELAYS = {
        1: 5,
        2: 15,
        3: 30
    }

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/151.0.0.0 "
                "Safari/537.36"
            )
        })

    # --------------------------------
    # Download
    # --------------------------------

    def download_media(
        self,
        queue_item
    ):

        queue_id = queue_item[0]
        status = queue_item[1]
        tweet_id = queue_item[2]
        username = queue_item[3]
        media_url = queue_item[4]
        media_type = queue_item[5]
        media_index = queue_item[6]
        destination_path = queue_item[7]
        attempts = queue_item[8]

        print()
        print("-" * 60)

        print(
            f"Fila ID: {queue_id}"
        )

        print(
            f"Tweet: {tweet_id}"
        )

        print(
            f"Usuário: @{username}"
        )

        print(
            f"Tipo: {media_type}"
        )

        current_attempt = attempts + 1

        print(
            f"Tentativa: "
            f"{current_attempt}/3"
        )

        # --------------------------------
        # Pasta
        # --------------------------------

        destination = Path(
            destination_path
        )

        destination.mkdir(
            parents=True,
            exist_ok=True
        )

        # --------------------------------
        # Nome do arquivo
        # --------------------------------

        filename = (
            f"{tweet_id}_"
            f"{media_index}"
        )

        if media_type == "photo":
            extension = ".jpg"

        elif media_type == "video":
            extension = ".mp4"

        elif media_type == "animated":
            extension = ".gif"

        else:
            extension = ".bin"

        output_file = (
            destination
            / f"{filename}{extension}"
        )

        temp_file = Path(
            f"{output_file}.part"
        )

        print(
            f"Destino: {output_file}"
        )

        # --------------------------------
        # Arquivo já existe
        # --------------------------------

        if output_file.exists():

            print(
                "✓ Arquivo já existe."
            )

            mark_downloaded(
                queue_id
            )

            return True


        # --------------------------------
        # Download
        # --------------------------------

        try:

            print(
                "Baixando..."
            )

            response = self.session.get(
                media_url,
                timeout=120,
                stream=True
            )

            response.raise_for_status()

            # --------------------------------
            # Salvar arquivo
            # --------------------------------

            with open(
                temp_file,
                "wb"
            ) as file:

                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):

                    if chunk:

                        file.write(
                            chunk
                        )

            # --------------------------------
            # Validar arquivo temporário
            # --------------------------------

            if not temp_file.exists():

                raise Exception(
                    "Arquivo temporário não foi criado."
                )

            file_size = temp_file.stat().st_size

            if file_size == 0:

                raise Exception(
                    "Arquivo baixado está vazio."
                )


            # --------------------------------
            # Transformar .part em definitivo
            # --------------------------------

            temp_file.replace(
                output_file
            )


            # --------------------------------
            # Sucesso
            # --------------------------------

            mark_downloaded(
                queue_id
            )

            print(
                f"✓ Download concluído: "
                f"{output_file.name}"
            )

            return True

        except Exception as e:

            # --------------------------------
            # Remover arquivo temporário
            # --------------------------------

            if temp_file.exists():

                temp_file.unlink()

            # --------------------------------
            # Erro
            # --------------------------------

            error_message = str(e)

            mark_error(
                queue_id,
                error_message
            )

            print(
            f"Erro na tentativa "
            f"{current_attempt}/3: "
            f"{error_message}"
        )

            return False

    # --------------------------------
    # Processar fila
    # --------------------------------

    def process_queue(self):

        print()
        print("=" * 60)
        print("DOWNLOAD DE MÍDIAS")
        print("=" * 60)

        downloaded = 0
        errors = 0
        processed = 0

        while True:

            queue_item = get_next_media()

            if not queue_item:
                break

            processed += 1

            success = self.download_media(
                queue_item
            )

            if success:

                downloaded += 1

            else:

                errors += 1

        # --------------------------------
        # Resultado
        # --------------------------------

        print()

        print("=" * 60)
        print("DOWNLOAD FINALIZADO")
        print("=" * 60)

        print(
            f"Processadas: "
            f"{processed}"
        )

        print(
            f"Baixadas: "
            f"{downloaded}"
        )

        print(
            f"Erros: "
            f"{errors}"
        )

        print("=" * 60)