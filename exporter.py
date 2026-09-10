"""
Exporter

Responsável por exportar tweets para:

- JSON
- CSV
- Fila de mídias

O download das mídias NÃO é realizado aqui.

Estrutura:

C:/Users/helen/twitter_scraper_exports/

└── eleicoes_2026/
    └── presidencia/
        └── Renan Santos/
            └── 16082026/
                ├── Renan_Santos_tweets_16082026.json
                └── Renan_Santos_tweets_16082026.csv
"""


import csv
import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from media_queue import add_media_to_queue


class Exporter:

    BASE_DIR = Path(
        r"C:\Users\helen\twitter_scraper_exports"
    )

    # ============================================================
    # NOME SEGURO
    # ============================================================

    def sanitize_filename(self, name):

        """
        Remove acentos e caracteres problemáticos
        para uso em nomes de arquivos/pastas.
        """

        name = unicodedata.normalize(
            "NFKD",
            name
        )

        name = "".join(
            char
            for char in name
            if not unicodedata.combining(char)
        )

        name = re.sub(
            r'[<>:"/\\|?*]',
            "-",
            name
        )

        name = re.sub(
            r"\s+",
            "_",
            name.strip()
        )

        return name

    # ============================================================
    # PASTA DO PERFIL
    # ============================================================

    def create_profile_folder(
        self,
        profile,
        collection_date
    ):

        """
        Cria:

        eleicoes_2026/
        └── categoria/
            └── perfil/
                └── data/
        """

        category = (
            profile.get("category")
            or "sem_categoria"
        )

        profile_name = (
            profile.get("name")
            or profile.get("username")
            or "perfil_desconhecido"
        )

        category = self.sanitize_filename(
            category
        )

        profile_name = self.sanitize_filename(
            profile_name
        )

        folder = (
            self.BASE_DIR
            / "eleicoes_2026"
            / category
            / profile_name
            / collection_date
        )

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        return folder

    # ============================================================
    # DATA DO TWEET
    # ============================================================

    def get_tweet_date(self, tweet):

        """
        Obtém a data de publicação do tweet.

        Retorna:

            DDMMYYYY
        """

        posted_at = tweet.get(
            "posted_at"
        )

        if isinstance(
            posted_at,
            datetime
        ):

            return posted_at.strftime(
                "%d%m%Y"
            )

        if posted_at:

            try:

                parsed_date = datetime.fromisoformat(
                    str(posted_at).replace(
                        "Z",
                        "+00:00"
                    )
                )

                return parsed_date.strftime(
                    "%d%m%Y"
                )

            except ValueError:

                pass

        raise ValueError(
            "Tweet sem posted_at válido."
        )

    # ============================================================
    # AGRUPAR TWEETS POR DATA
    # ============================================================

    def group_tweets_by_date(
        self,
        tweets
    ):

        """
        Agrupa todos os tweets pela data
        de publicação.

        Exemplo:

        16082026 -> tweets do dia 16
        17082026 -> tweets do dia 17
        18082026 -> tweets do dia 18
        """

        tweets_by_date = defaultdict(list)

        for tweet in tweets:

            collection_date = (
                self.get_tweet_date(tweet)
            )

            tweets_by_date[
                collection_date
            ].append(tweet)

        return dict(
            tweets_by_date
        )

    # ============================================================
    # JSON
    # ============================================================

    def export_json(
        self,
        tweets,
        profile,
        collection_date
    ):

        folder = self.create_profile_folder(
            profile,
            collection_date
        )

        profile_name = (
            profile.get("name")
            or profile.get("username")
            or "perfil_desconhecido"
        )

        profile_name = self.sanitize_filename(
            profile_name
        )

        output_file = (
            folder
            / (
                f"{profile_name}_tweets_"
                f"{collection_date}.json"
            )
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                tweets,
                f,
                ensure_ascii=False,
                indent=4,
                default=str
            )

        print(
            f"JSON salvo: {output_file}"
        )

    # ============================================================
    # CSV
    # ============================================================

    def export_csv(
        self,
        tweets,
        profile,
        collection_date
    ):

        if not tweets:
            return

        folder = self.create_profile_folder(
            profile,
            collection_date
        )

        profile_name = (
            profile.get("name")
            or profile.get("username")
            or "perfil_desconhecido"
        )

        profile_name = self.sanitize_filename(
            profile_name
        )

        output_file = (
            folder
            / (
                f"{profile_name}_tweets_"
                f"{collection_date}.csv"
            )
        )

        fieldnames = [
            key
            for key in tweets[0].keys()
            if key != "raw_json"
        ]

        with open(
            output_file,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as csvfile:

            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                delimiter=";",
                extrasaction="ignore"
            )

            writer.writeheader()

            for tweet in tweets:

                row = {}

                for key in fieldnames:

                    value = tweet.get(key)

                    if key == "media":

                        value = json.dumps(
                            value,
                            ensure_ascii=False
                        )

                    row[key] = value

                writer.writerow(row)

        print(
            f"CSV salvo: {output_file}"
        )

    # ============================================================
    # ADICIONAR MÍDIA À FILA
    # ============================================================

    def queue_media(
        self,
        tweets,
        profile,
        collection_date
    ):

        """
        Coloca as mídias dos tweets na fila.

        NÃO realiza download.
        """

        username = (
            profile.get("username")
            or "usuario_desconhecido"
        )

        folder = self.create_profile_folder(
            profile,
            collection_date
        )

        media_folder = (
            folder / "midia"
        )

        queued = 0
        skipped = 0

        for tweet in tweets:

            tweet_id = str(
                tweet.get(
                    "platform_post_id"
                )
            )

            media_list = tweet.get(
                "media",
                []
            )

            if not media_list:
                continue

            for media_index, media in enumerate(
                media_list,
                start=1
            ):

                media_type = media.get(
                    "type"
                )

                url = media.get(
                    "url"
                )

                if not url:
                    continue

                # ------------------------------------------------
                # Tenta adicionar na fila
                # ------------------------------------------------

                before_count = queued

                add_media_to_queue(
                    tweet_id=int(tweet_id),
                    username=username,
                    media_url=url,
                    media_type=media_type,
                    media_index=media_index,
                    destination_path=str(
                        media_folder
                    )
                )

                queued += 1

        return {
            "queued": queued,
            "skipped": skipped
        }

    # ============================================================
    # EXPORTAÇÃO COMPLETA
    # ============================================================

    def export_profile(
        self,
        tweets,
        profile,
        date_from=None,
        date_to=None
    ):

        """
        Exporta tweets separados por data.

        Para cada dia:

        perfil/
        └── DDMMYYYY/
            ├── Perfil_tweets_DDMMYYYY.json
            └── Perfil_tweets_DDMMYYYY.csv

        As mídias são apenas adicionadas à fila.
        """

        if not tweets:

            return {
                "queued": 0
            }

        # --------------------------------------------------------
        # Agrupar tweets por data
        # --------------------------------------------------------

        tweets_by_date = (
            self.group_tweets_by_date(
                tweets
            )
        )

        total_queued = 0

        # --------------------------------------------------------
        # Exportar cada dia
        # --------------------------------------------------------

        for collection_date, daily_tweets in (
            tweets_by_date.items()
        ):

            print()
            print(
                f"Exportando {collection_date}..."
            )

            # JSON
            self.export_json(
                daily_tweets,
                profile,
                collection_date
            )

            # CSV
            self.export_csv(
                daily_tweets,
                profile,
                collection_date
            )

            # Fila de mídia
            media_result = self.queue_media(
                daily_tweets,
                profile,
                collection_date
            )

            total_queued += (
                media_result["queued"]
            )

        print()
        print(
            f"Mídias adicionadas à fila: "
            f"{total_queued}"
        )

        return {
            "queued": total_queued
        }