from storage import get_connection


# ============================================================
# ADICIONAR MÍDIA À FILA
# ============================================================

def add_media_to_queue(
    tweet_id,
    username,
    media_url,
    media_type,
    media_index,
    destination_path
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO media_queue (
            status,
            tweet_id,
            username,
            media_url,
            media_type,
            media_index,
            destination_path
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        ON CONFLICT (tweet_id, media_url)
        DO NOTHING
        """,
        (
            "pending",
            tweet_id,
            username,
            media_url,
            media_type,
            media_index,
            destination_path
        )
    )

    conn.commit()

    cur.close()
    conn.close()


# ============================================================
# BUSCAR MÍDIAS PENDENTES
# ============================================================

def get_pending_media():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            status,
            tweet_id,
            username,
            media_url,
            media_type,
            media_index,
            destination_path,
            attempts
        FROM media_queue
        WHERE status = 'pending'
        FOR UPDATE SKIP LOCKED
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


# ============================================================
# MARCAR COMO DOWNLOADING
# ============================================================

def mark_downloading(queue_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE media_queue
        SET status = 'downloading'
        WHERE id = %s
    """, (queue_id,))

    conn.commit()

    cur.close()
    conn.close()


# ============================================================
# MARCAR COMO BAIXADA
# ============================================================

def mark_downloaded(queue_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE media_queue
        SET
            status = 'downloaded',
            downloaded_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (queue_id,))

    conn.commit()

    cur.close()
    conn.close()


# ============================================================
# MARCAR COMO ERRO
# ============================================================

def mark_error(queue_id, error_message):

    conn = get_connection()
    cur = conn.cursor()

    try:

        # --------------------------------
        # Buscar dados da mídia
        # --------------------------------

        cur.execute("""
            SELECT
                tweet_id,
                username,
                media_url,
                media_type,
                attempts
            FROM media_queue
            WHERE id = %s
        """, (
            queue_id,
        ))

        row = cur.fetchone()

        if not row:
            raise Exception(
                f"Mídia da fila {queue_id} não encontrada."
            )

        tweet_id = row[0]
        username = row[1]
        media_url = row[2]
        media_type = row[3]
        attempts = row[4]

        # --------------------------------
        # Nova tentativa
        # --------------------------------

        new_attempts = attempts + 1

        # --------------------------------
        # Atualizar banco
        # --------------------------------

        cur.execute("""
            UPDATE media_queue
            SET
                status = 'error',
                attempts = %s,
                error = %s
            WHERE id = %s
        """, (
            new_attempts,
            error_message,
            queue_id
        ))

        conn.commit()

        # --------------------------------
        # Atingiu 3 tentativas
        # --------------------------------

        if new_attempts >= 3:

            print()
            print("!" * 70)
            print("!!! MÍDIA NÃO BAIXADA APÓS 3 TENTATIVAS!")
            print("!" * 70)

            print(
                f"Tweet ID: {tweet_id}"
            )

            print(
                f"Usuário: @{username}"
            )

            print(
                f"Tipo: {media_type}"
            )

            print(
                f"URL da mídia: {media_url}"
            )

            print(
                f"Erro: {error_message}"
            )

            print(
                "Essa mídia deverá ser baixada manualmente."
            )

            print("!" * 70)

    except Exception:

        conn.rollback()
        raise

    finally:

        cur.close()
        conn.close()
# ============================================================
# RECUPERAR DOWNLOADS INTERROMPIDOS
# ============================================================

def reset_downloading():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE media_queue
        SET status = 'pending'
        WHERE status = 'downloading'
    """)

    recovered = cur.rowcount

    conn.commit()

    cur.close()
    conn.close()

    return recovered


# ============================================================
# BUSCAR E RESERVAR PRÓXIMA MÍDIA
# ============================================================

def get_next_media():

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                id,
                status,
                tweet_id,
                username,
                media_url,
                media_type,
                media_index,
                destination_path,
                attempts
            FROM media_queue

            WHERE status = 'pending'

            ORDER BY id
            FOR UPDATE SKIP LOCKED
            LIMIT 1
        """)

        row = cur.fetchone()

        if not row:

            conn.commit()

            return None

        queue_id = row[0]

        cur.execute("""
            UPDATE media_queue
            SET status = 'downloading'
            WHERE id = %s
        """, (
            queue_id,
        ))

        conn.commit()

        return row

    except Exception:

        conn.rollback()

        raise

    finally:

        cur.close()
        conn.close()

def retry_failed_media():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE media_queue
        SET status = 'pending'
        WHERE status = 'error'
          AND attempts < 3
    """)

    recovered = cur.rowcount

    conn.commit()

    cur.close()
    conn.close()

    return recovered

