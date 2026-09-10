"""
Twitter/X Scraper V2 — Pesquisa Acadêmica

Versão automatizada do scraper.

Os perfis são carregados automaticamente a partir do arquivo
profiles.json. Apenas perfis com "active": true são processados.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict

from twscrape import API

from storage import (
    create_tables,
    tweet_exists,
    insert_tweet
)


# --------------------------------
# Erros
# --------------------------------

class ScrapeError(Exception):
    """Erro geral durante a coleta."""
    pass


class AuthError(ScrapeError):
    """Erro relacionado à autenticação da conta."""
    pass


# --------------------------------
# Constantes
# --------------------------------

PROFILES_FILE = "profiles.json"


# --------------------------------
# Twitter Scraper V2
# --------------------------------

class TwitterScraperV2:

    def __init__(self):
        self.api = API()

    # --------------------------------
    # Contas
    # --------------------------------

    async def initialize_accounts(self, accounts):
        """
        Carrega as contas do X utilizando cookies.
        """

        for account in accounts:
            await self.api.pool.add_account_cookies(
                account["account_name"],
                account["cookie_string"]
            )

        print(
            f"{len(accounts)} contas carregadas via cookies."
        )

    def load_cookies(self, cookies_file):
        """
        Carrega as contas a partir do arquivo de cookies.
        """

        if not os.path.exists(cookies_file):
            raise AuthError(
                f"Arquivo não encontrado: {cookies_file}"
            )

        accounts = []

        with open(
            cookies_file,
            "r",
            encoding="utf-8"
        ) as file:

            for line_number, line in enumerate(
                file,
                start=1
            ):

                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                try:
                    account_name, cookie_string = (
                        line.split("|", 1)
                    )

                except ValueError:
                    raise AuthError(
                        f"Formato inválido na linha "
                        f"{line_number}"
                    )

                accounts.append({
                    "account_name": account_name.strip(),
                    "cookie_string": cookie_string.strip()
                })

        return accounts

    # --------------------------------
    # Profiles
    # --------------------------------

    def load_profiles(
        self,
        profiles_file=PROFILES_FILE
    ):
        """
        Carrega os perfis a partir do profiles.json.

        Apenas perfis com active=True são retornados.
        """

        if not os.path.exists(profiles_file):
            raise ScrapeError(
                f"Arquivo de perfis não encontrado: "
                f"{profiles_file}"
            )

        try:

            with open(
                profiles_file,
                "r",
                encoding="utf-8"
            ) as file:

                profiles = json.load(file)

        except json.JSONDecodeError as e:

            raise ScrapeError(
                f"Erro ao ler {profiles_file}: {e}"
            )

        if not isinstance(profiles, list):

            raise ScrapeError(
                "O profiles.json deve conter "
                "uma lista de perfis."
            )

        active_profiles = [
            profile
            for profile in profiles
            if profile.get("active") is True
        ]

        for profile in active_profiles:

            if "profile_id" not in profile:
                raise ScrapeError(
                    f"Perfil @{profile.get('username', '-')} "
                    f"não possui profile_id."
                )

        print(
            f"\nPerfis encontrados: {len(profiles)}"
        )

        print(
            f"Perfis ativos: {len(active_profiles)}"
        )

        return active_profiles

    # --------------------------------
    # Twitter
    # --------------------------------

    async def fetch_user(
        self,
        username: str
    ):
        """
        Busca as informações de um perfil do X
        a partir do username.
        """

        try:

            user = await self.api.user_by_login(
                username
            )

        except Exception as e:

            raise ScrapeError(
                f"Erro ao buscar o perfil "
                f"@{username}: {e}"
            )

        if user is None:

            raise ScrapeError(
                f"Perfil @{username} não encontrado."
            )

        return user

    
    async def fetch_tweets(
        self,
        user_id: int,
        date_from: datetime,
        date_to: datetime
    ):
        tweets = []

        async for tweet in self.api.user_tweets(
            user_id,
            limit=100
        ):
            # ============================================================
            # GARANTE QUE O TWEET PERTENCE AO PERFIL COLETADO
            # ============================================================

            if tweet.user.id != user_id:
                continue

            # ============================================================
            # FILTRO DE DATA
            # ============================================================

            if tweet.date > date_to:
                continue

            if tweet.date < date_from:
                continue

            tweets.append(tweet)

        print(f"Total filtrado: {len(tweets)}")

        return tweets


    
    # --------------------------------
    # Parse do tweet
    # --------------------------------

   
    def parse_tweet(
        self,
        tweet,
        profile: Dict[str, Any]
    ):
        """
        Converte um tweet do twscrape para o formato
        utilizado pelo projeto.

        Também identifica relacionamentos:

        - tweet normal
        - quote
        - reply
        - retweet

        Importante:
        O profile_id representa o perfil que estamos coletando.
        O author_username/author_name representam o autor real
        do tweet retornado.
        """

        partido = (
            profile.get("partido")
            or profile.get("sigla")
        )

        media = self.parse_media(
            tweet.media
        )

        # ============================================================
        # IDENTIFICAÇÃO DO TIPO DE TWEET
        # ============================================================

        tweet_type = "tweet"

        quoted_tweet_id = None
        reply_to_tweet_id = None
        retweeted_tweet_id = None

        # ------------------------------------------------------------
        # RETWEET
        # ------------------------------------------------------------

        retweeted_tweet = getattr(
            tweet,
            "retweetedTweet",
            None
        )

        if retweeted_tweet is not None:
            tweet_type = "retweet"

            retweeted_tweet_id = str(
                retweeted_tweet.id
            )

        # ------------------------------------------------------------
        # QUOTE
        # ------------------------------------------------------------

        quoted_tweet = getattr(
            tweet,
            "quotedTweet",
            None
        )

        if quoted_tweet is not None:
            tweet_type = "quote"

            quoted_tweet_id = str(
                quoted_tweet.id
            )

        # ------------------------------------------------------------
        # REPLY
        # ------------------------------------------------------------

        in_reply_to = getattr(
            tweet,
            "inReplyToTweetId",
            None
        )

        if in_reply_to is not None:
            tweet_type = "reply"

            reply_to_tweet_id = str(
                in_reply_to
            )
        

        # ============================================================
        # RESULTADO
        # ============================================================

        return {

            # --------------------------------------------------------
            # Perfil que está sendo coletado
            # --------------------------------------------------------

            "profile_id": profile["profile_id"],

            "profile_category": profile.get(
                "category"
            ),

            "profile_uf": profile.get(
                "uf"
            ),

            "profile_partido": partido,

            # --------------------------------------------------------
            # Autor REAL do tweet
            # --------------------------------------------------------

            "author_username": (
                tweet.user.username
            ),

            "author_name": (
                tweet.user.displayname
            ),

            # --------------------------------------------------------
            # Tweet
            # --------------------------------------------------------

            "platform_post_id": str(
                tweet.id
            ),

            "posted_at": tweet.date,

            "text": tweet.rawContent,

            "likes": tweet.likeCount,

            "comments_count": tweet.replyCount,

            "reposts": tweet.retweetCount,

            "quotes": tweet.quoteCount,

            "views": tweet.viewCount,

            "lang": tweet.lang,

            "tweet_url": tweet.url,

            # --------------------------------------------------------
            # TIPO E RELACIONAMENTOS
            # --------------------------------------------------------

            "tweet_type": tweet_type,

            "quoted_tweet_id": quoted_tweet_id,

            "reply_to_tweet_id": reply_to_tweet_id,

            "retweeted_tweet_id": retweeted_tweet_id,

            # --------------------------------------------------------
            # Mídia
            # --------------------------------------------------------

            "media": media,

            # --------------------------------------------------------
            # JSON original
            # --------------------------------------------------------

            "raw_json": json.loads(
                json.dumps(
                    tweet.dict(),
                    default=str
                )
            )
        }

    # --------------------------------
    # Mídia
    # --------------------------------

    def parse_media(self, media):
        """
        Converte as mídias do twscrape para
        um formato simples de dicionário.

        Fotos:
            mantém a URL original.

        Vídeos:
            seleciona a versão 1920x1080 quando disponível.
            Caso não exista, seleciona a maior qualidade disponível.

        GIFs/animações:
            mantém a URL disponível.
        """

        if not media:
            return []

        result = []

        # --------------------------------
        # Fotos
        # --------------------------------

        for photo in getattr(
            media,
            "photos",
            []
        ):

            result.append({
                "type": "photo",
                "url": photo.url
            })

        # --------------------------------
        # Vídeos
        # --------------------------------

        for video in getattr(
            media,
            "videos",
            []
        ):

            variants = getattr(
                video,
                "variants",
                []
            )

            mp4_variants = [
                variant
                for variant in variants
                if getattr(
                    variant,
                    "contentType",
                    ""
                ) == "video/mp4"
            ]

            if not mp4_variants:
                continue

            # Procura especificamente 1920x1080
            selected = None

            for variant in mp4_variants:

                url = getattr(
                    variant,
                    "url",
                    ""
                )

                if "1920x1080" in url:
                    selected = variant
                    break

            # Se não existir 1920x1080,
            # pega a maior qualidade disponível
            if selected is None:

                selected = max(
                    mp4_variants,
                    key=lambda variant: (
                        getattr(
                            variant,
                            "bitrate",
                            0
                        ) or 0
                    )
                )

            result.append({
                "type": "video",
                "url": selected.url,
                "bitrate": getattr(
                    selected,
                    "bitrate",
                    None
                )
            })

        # --------------------------------
        # Animações / GIFs
        # --------------------------------

        for animated in getattr(
            media,
            "animated",
            []
        ):

            result.append({
                "type": "animated",
                "url": getattr(
                    animated,
                    "url",
                    None
                )
            })

        return result

    # --------------------------------
    # Armazenamento
    # --------------------------------

    def save_tweets(self, tweets):
        """
        Salva os tweets coletados no PostgreSQL.

        Tweets que já existem no banco não são inseridos novamente.
        """

        inserted = 0
        duplicated = 0
        errors = 0

        for tweet_data in tweets:

            try:

                if tweet_exists(
                    tweet_data["platform_post_id"]
                ):

                    duplicated += 1

                    continue

                insert_tweet(tweet_data)

                inserted += 1

            except Exception as e:

                errors += 1

                print(
                    f"✗ Erro ao salvar tweet "
                    f"{tweet_data.get('platform_post_id')}: {e}"
                )

        print("\n" + "-" * 20)
        print("RESULTADO DO ARMAZENAMENTO")
        print("-" * 20)

        print(
            f"Tweets inseridos: {inserted}"
        )

        print(
            f"Tweets já existentes: {duplicated}"
        )

        print(
            f"Erros: {errors}"
        )

        return {
            "inserted": inserted,
            "duplicated": duplicated,
            "errors": errors
        }


    # --------------------------------
    # Filtro de data
    # --------------------------------

    def filter_tweets_by_date(
        self,
        tweets,
        date_from: datetime,
        date_to: datetime
    ):
        """
        Mantém somente tweets dentro do intervalo
        informado.
        """

        filtered = []

        for tweet in tweets:

            tweet_date = tweet.date

            if tweet_date < date_from:
                continue

            if tweet_date > date_to:
                continue

            filtered.append(tweet)

        return filtered

    # --------------------------------
    # Coleta de um perfil
    # --------------------------------

    async def scrape_profile(
        self,
        profile: Dict[str, Any],
        date_from: datetime,
        date_to: datetime
    ):
        """
        Coleta tweets de um perfil definido
        no profiles.json.
        """

        username = profile["username"]

        print("\n" + "=" * 60)

        print(
            f"Perfil: {profile.get('name', '-')}"
        )

        print(
            f"Username: @{username}"
        )

        print(
            f"Categoria: "
            f"{profile.get('category', '-')}"
        )

        print(
            f"UF: "
            f"{profile.get('uf', '-')}"
        )

        print(
            f"Partido: "
            f"{profile.get('partido') or profile.get('sigla', '-')}"
        )

        print("=" * 60)

        # Busca o perfil no X
        user = await self.fetch_user(
            username
        )

        print(
            f"Usuário encontrado: "
            f"@{user.username}"
        )

        print(
            f"ID: {user.id}"
        )

        # Coleta tweets
        print("\nColetando tweets...")

        tweets = await self.fetch_tweets(
            user.id,
            date_from,
            date_to
        )


        print(
            f"Tweets no intervalo: "
            f"{len(tweets)}"
        )

        # Conversão para o formato do banco
        parsed_tweets = [
            self.parse_tweet(
                tweet,
                profile
            )
            for tweet in tweets
        ]

        return parsed_tweets

    # --------------------------------
    # Coleta automática
    # --------------------------------

    async def scrape_all(
        self,
        date_from: datetime,
        date_to: datetime
    ):
        """
        Percorre automaticamente todos os perfis
        ativos presentes no profiles.json.

        Os tweets coletados são salvos diretamente
        no PostgreSQL.
        """

        # Garante que a tabela existe
        create_tables()

        profiles = self.load_profiles()

        total_collected = 0
        total_inserted = 0
        total_duplicated = 0
        total_errors = 0

        print("\n" + "=" * 20)
        print("INICIANDO COLETA AUTOMÁTICA")
        print("=" * 20)

        for index, profile in enumerate(
            profiles,
            start=1
        ):

            print(
                f"\n[{index}/{len(profiles)}]"
            )

            try:

                tweets = await self.scrape_profile(
                    profile,
                    date_from,
                    date_to
                )

                total_collected += len(tweets)

                # -----------------------------
                # Salva no banco
                # -----------------------------

                result = self.save_tweets(
                    tweets
                )

                total_inserted += result["inserted"]

                total_duplicated += result["duplicated"]

                total_errors += result["errors"]

                print(
                    f"✓ Perfil "
                    f"@{profile['username']} "
                    f"finalizado."
                )

            except Exception as e:

                print(
                    f"✗ Erro no perfil "
                    f"@{profile['username']}: {e}"
                )

                # Não interrompe a coleta
                continue

        print("\n" + "=" * 20)
        print("COLETA AUTOMÁTICA FINALIZADA")
        print("=" * 20)

        print(
            f"Tweets coletados: "
            f"{total_collected}"
        )

        print(
            f"Tweets inseridos no banco: "
            f"{total_inserted}"
        )

        print(
            f"Tweets já existentes: "
            f"{total_duplicated}"
        )

        print(
            f"Erros de armazenamento: "
            f"{total_errors}"
        )

        print("=" * 20)

        return {
            "collected": total_collected,
            "inserted": total_inserted,
            "duplicated": total_duplicated,
            "errors": total_errors
        }