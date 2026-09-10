from storage import (
    create_tables,
    tweet_exists,
    insert_tweet
)

from twitter_scraper import (
    TwitterScraperV2
)

from exporter import Exporter


class PipelineV2:

    def __init__(self):

        self.scraper = TwitterScraperV2()
        self.exporter = Exporter()

    # --------------------------------
    # Inicialização
    # --------------------------------

    async def initialize(self):

        print("Criando tabelas...")

        create_tables()

        print("Carregando cookies...")

        accounts = self.scraper.load_cookies(
            "cookies.txt"
        )

        print(
            f"{len(accounts)} contas carregadas."
        )

        print("Inicializando contas...")

        await self.scraper.initialize_accounts(
            accounts
        )

        print("Contas inicializadas.")

    # --------------------------------
    # Coleta
    # --------------------------------

    async def collect_all_profiles(
        self,
        date_from,
        date_to,
        selected_profile=None
    ):

        profiles = self.scraper.load_profiles()

        if selected_profile:
            profiles = [selected_profile]

        # ==================================
        # TESTE
        # ==================================
        # profiles = profiles[:1]

        total_profiles = len(profiles)

        total_inserted = 0
        total_skipped = 0
        total_errors = 0
        total_media_queued = 0

        errors_profiles = []

        # --------------------------------
        # Período da pesquisa
        # --------------------------------

        print()
        print("=" * 60)
        print("INICIANDO COLETA")
        print("=" * 60)

        print(
            f"Período: "
            f"{date_from.strftime('%d/%m/%Y')} "
            f"até "
            f"{date_to.strftime('%d/%m/%Y')}"
        )

        # --------------------------------
        # Perfis
        # --------------------------------

        for index, profile in enumerate(
            profiles,
            start=1
        ):

            print()

            print(
                f"[{index}/{total_profiles}] "
                f"@{profile['username']}"
            )

            try:

                # --------------------------------
                # Coleta
                # --------------------------------

                tweets = await self.scraper.scrape_profile(
                    profile=profile,
                    date_from=date_from,
                    date_to=date_to
                )

                # ========================================
                # VERIFICAR TWEETS NO BANCO
                # ========================================

                novos_tweets = []
                tweets_existentes = []

                for tweet in tweets:

                    tweet_id = tweet[
                        "platform_post_id"
                    ]

                    if tweet_exists(tweet_id):

                        tweets_existentes.append(
                            tweet
                        )

                    else:

                        novos_tweets.append(
                            tweet
                        )


                # ========================================
                # VERIFICAÇÃO DOS TWEETS
                # ========================================

                print()
                print("-" * 60)
                print("VERIFICAÇÃO DOS TWEETS")
                print("-" * 60)

                print()
                print(
                    f"Tweets coletados: "
                    f"{len(tweets)}"
                )

                print(
                    f"Tweets novos: "
                    f"{len(novos_tweets)}"
                )

                print(
                    f"Tweets já existentes: "
                    f"{len(tweets_existentes)}"
                )

                # --------------------------------
                # IDs NOVOS
                # --------------------------------

                if novos_tweets:
                    print()
                    print("NOVOS TWEETS:")
                    print("-" * 40)

                    for tweet in novos_tweets:
                        print(
                            f"↪ {tweet['platform_post_id']}"
                        )

                   
                # --------------------------------
                # IDs EXISTENTES
                # --------------------------------

                if tweets_existentes:

                    print()
                    print(
                        "TWEETS JÁ EXISTENTES:"
                    )

                    print("-" * 40)

                    for tweet in tweets_existentes:

                        print(
                            f"↪ "
                            f"{tweet['platform_post_id']}"
                        )

                print("-" * 60)

                # ========================================
                # CONTADORES
                # ========================================

                profile_skipped = len(
                    tweets_existentes
                )

                profile_inserted = len(
                    novos_tweets
                )

                total_skipped += (
                    profile_skipped
                )

                # ========================================
                # TODOS OS TWEETS PARA EXPORTAÇÃO
                # ========================================
                # Se rodar novamente o mesmo dia, O JSON/CSV
                # será recriado contendo TODOS os tweets encontrados.
                #
                # Porém, somente os novos serão inseridos
                # novamente no banco.
                # ========================================

                todos_os_tweets = (
                    novos_tweets +
                    tweets_existentes
                )


                # ========================================
                # EXPORTAÇÃO
                # ========================================

                media_result = {
                    "queued": 0
                }


                if todos_os_tweets:

                    print()
                    print(
                        f"Exportando "
                        f"{len(todos_os_tweets)} "
                        f"tweets..."
                    )

                    media_result = (
                        self.exporter.export_profile(
                            tweets=todos_os_tweets,
                            profile=profile,
                            date_from=date_from,
                            date_to=date_to
                        )
                    )

                    total_media_queued += (
                        media_result.get(
                            "queued",
                            0
                        )
                    )

                else:

                    print()
                    print(
                        "Nenhum tweet coletado."
                    )

                    print(
                        "JSON, CSV e mídias "
                        "não serão exportados."
                    )

                # ========================================
                # BANCO
                # ========================================

                for tweet in novos_tweets:

                    inserted = insert_tweet(tweet)

                    if inserted:
                        total_inserted += 1

                # ========================================
                # RESULTADO DO PERFIL
                # ========================================

                print()

                print(
                    f"✓ Inseridos: "
                    f"{profile_inserted}"
                )

                print(
                    f"✓ Ignorados: "
                    f"{profile_skipped}"
                )

                print(
                    f"✓ Mídias na fila: "
                    f"{media_result.get('queued', 0)}"
                )

            except Exception as e:

                total_errors += 1

                errors_profiles.append({

                    "username":
                        profile["username"],

                    "name":
                        profile.get("name"),

                    "category":
                        profile.get("category"),

                    "uf":
                        profile.get("uf"),

                    "partido":
                        profile.get("partido"),

                    "error":
                        str(e)
                })

                print()

                print(
                    f"✗ Erro em "
                    f"@{profile['username']}: "
                    f"{e}"
                )

                continue

        # ========================================
        # RESULTADO FINAL
        # ========================================

        print()

        print("=" * 60)
        print("COLETA FINALIZADA")
        print("=" * 60)

        print(
            f"Perfis processados: "
            f"{total_profiles}"
        )

        print(
            f"Tweets inseridos: "
            f"{total_inserted}"
        )

        print(
            f"Tweets ignorados: "
            f"{total_skipped}"
        )

        print(
            f"Perfis com erro: "
            f"{total_errors}"
        )

        print(
            f"Mídias adicionadas à fila: "
            f"{total_media_queued}"
        )

        # ========================================
        # PERFIS COM ERRO
        # ========================================

        if errors_profiles:

            print()
            print("PERFIS COM ERRO")
            print("-" * 50)

            for error_profile in errors_profiles:

                print(
                    f"@{error_profile['username']}"
                )

                print(
                    f"Nome: "
                    f"{error_profile['name']}"
                )

                print(
                    f"Categoria: "
                    f"{error_profile['category']}"
                )

                print(
                    f"UF: "
                    f"{error_profile['uf']}"
                )

                print(
                    f"Partido: "
                    f"{error_profile['partido']}"
                )

                print(
                    f"Erro: "
                    f"{error_profile['error']}"
                )

                print("-" * 50)

        print()
        print("=" * 60)

        return {

            "inserted":
                total_inserted,

            "skipped":
                total_skipped,

            "errors":
                total_errors,

            "error_profiles":
                errors_profiles,

            "media_queued":
                total_media_queued
        }