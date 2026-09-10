print("MAIN EXECUTOU")

import storage
import twitter_scraper

print("=" * 60)
print("ARQUIVOS REALMENTE CARREGADOS PELO PYTHON")
print("=" * 60)
print("storage:", storage.__file__)
print("twitter_scraperV2:", twitter_scraper.__file__)
print("=" * 60)



import asyncio

from datetime import datetime, timezone

from pipeline import PipelineV2


async def main():

    pipeline = PipelineV2()

    await pipeline.initialize()

    # ================================================
    # DATA DA COLETA
    # ================================================

    date_from = input(
        "Data inicial (AAAA-MM-DD): "
    ).strip()

    date_to = input(
        "Data final (AAAA-MM-DD): "
    ).strip()

    date_from = datetime.strptime(
        date_from,
        "%Y-%m-%d"
    ).replace(
        tzinfo=timezone.utc
    )

    date_to = datetime.strptime(
        date_to,
        "%Y-%m-%d"
    ).replace(
        hour=23,
        minute=59,
        second=59,
        tzinfo=timezone.utc
    )

    # ================================================
    # SELEÇÃO DE PERFIS
    # ================================================

    profiles = pipeline.scraper.load_profiles()

    print()
    print("=" * 60)
    print("SELEÇÃO DE PERFIS")
    print("=" * 60)
    print()

    print(
        f"Perfis encontrados: {len(profiles)}"
    )

    print()
    print("1 - Todos os perfis")
    print("2 - Escolher um perfil")

    print()

    option = input(
        "Digite a opção: "
    ).strip()

    # ================================================
    # TODOS OS PERFIS
    # ================================================

    if option == "1":

        selected_profile = None

        print()
        print(
            f"Todos os {len(profiles)} perfis "
            "serão coletados."
        )

    # ================================================
    # UM PERFIL
    # ================================================

    elif option == "2":

        while True:

            username = input(
                "\nDigite o username: @"
            ).strip()

            # Remove @ caso o usuário digite
            # @LulaOficial
            username = username.lstrip("@")

            selected_profile = None

            for profile in profiles:

                if (
                    profile["username"].lower()
                    == username.lower()
                ):
                    selected_profile = profile
                    break

            # ========================================
            # PERFIL NÃO ENCONTRADO
            # ========================================

            if selected_profile is None:

                print()
                print(
                    f"✗ Perfil @{username} "
                    "não encontrado no profiles.json."
                )

                continue

            # ========================================
            # PERFIL ENCONTRADO
            # ========================================

            print()
            print("Perfil selecionado:")
            print(
                f"Nome: "
                f"{selected_profile.get('name') or '-'}"
            )
            print(
                f"Username: "
                f"@{selected_profile.get('username') or '-'}"
            )
            print(
                f"Categoria: "
                f"{selected_profile.get('category') or '-'}"
            )
            print(
                f"UF: "
                f"{selected_profile.get('uf') or '-'}"
            )
            print(
                f"Partido: "
                f"{selected_profile.get('partido') or '-'}"
            )

            break

    # ================================================
    # OPÇÃO INVÁLIDA
    # ================================================

    else:

        print()
        print("✗ Opção inválida.")
        return

    # ================================================
    # CONFIRMAÇÃO
    # ================================================

    print()

    confirmation = input(
        "Deseja iniciar a coleta? (S/N): "
    ).strip().lower()

    if confirmation != "s":

        print()
        print("Coleta cancelada.")
        return

    # ================================================
    # INICIAR COLETA
    # ================================================

    print()

    await pipeline.collect_all_profiles(
        date_from=date_from,
        date_to=date_to,
        selected_profile=selected_profile
    )


if __name__ == "__main__":

    asyncio.run(main())