import psycopg2
import psycopg2.extras

from config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD
)


def get_connection():

     return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def create_tables():

    conn = get_connection()
    cur = conn.cursor()

    # ==========================================
    # TABELA DE TWEETS
    # ==========================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tweets (

            id SERIAL PRIMARY KEY,

            profile_id INTEGER,

            profile_category TEXT,

            profile_uf VARCHAR(2),

            profile_partido TEXT,

            author_username TEXT,

            author_name TEXT,

            platform_post_id VARCHAR(50) UNIQUE NOT NULL,

            posted_at TIMESTAMP NOT NULL,

            collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

            text TEXT,

            likes INTEGER,

            comments_count INTEGER,

            reposts INTEGER,

            quotes INTEGER,

            views INTEGER,

            lang VARCHAR(10),

            tweet_url TEXT,

            raw_json JSONB

        );
    """)

    # ==========================================
    # RELACIONAMENTOS DOS TWEETS
    # ==========================================

    cur.execute("""
        ALTER TABLE tweets
        ADD COLUMN IF NOT EXISTS tweet_type TEXT NOT NULL DEFAULT 'tweet'
    """)

    cur.execute("""
        ALTER TABLE tweets
        ADD COLUMN IF NOT EXISTS quoted_tweet_id VARCHAR(50)
    """)

    cur.execute("""
        ALTER TABLE tweets
        ADD COLUMN IF NOT EXISTS reply_to_tweet_id VARCHAR(50)
    """)

    cur.execute("""
        ALTER TABLE tweets
        ADD COLUMN IF NOT EXISTS retweeted_tweet_id VARCHAR(50)
    """)


    # ==========================================
    # FILA DE MÍDIAS
    # ==========================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS media_queue (

            id SERIAL PRIMARY KEY,

            status TEXT NOT NULL DEFAULT 'pending',

            tweet_id BIGINT NOT NULL,

            username TEXT NOT NULL,

            media_url TEXT NOT NULL,

            media_type TEXT,

            destination_path TEXT NOT NULL,

            attempts INTEGER NOT NULL DEFAULT 0,

            error TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            downloaded_at TIMESTAMP,

            UNIQUE (tweet_id, media_url)

        );
    """)

    # ==========================================
    # COMMIT
    # ==========================================

    conn.commit()

    cur.close()
    conn.close()

def tweet_exists(tweet_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 1
        FROM tweets
        WHERE platform_post_id = %s
        """,
        (str(tweet_id),)
    )

    exists = cur.fetchone() is not None

    cur.close()
    conn.close()

    return exists



def insert_tweet(tweet_data):

    conn = get_connection()
    cur = conn.cursor()

    query = """
        INSERT INTO tweets (
            profile_id,
            profile_category,
            profile_uf,
            profile_partido,
            author_username,
            author_name,
            platform_post_id,
            posted_at,
            text,
            likes,
            comments_count,
            reposts,
            quotes,
            views,
            lang,
            tweet_url,
            tweet_type,
            quoted_tweet_id,
            reply_to_tweet_id,
            retweeted_tweet_id,
            raw_json
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        ON CONFLICT (platform_post_id)
        DO NOTHING
    """

    values = (
        tweet_data["profile_id"],
        tweet_data["profile_category"],
        tweet_data["profile_uf"],
        tweet_data["profile_partido"],
        tweet_data["author_username"],
        tweet_data["author_name"],
        tweet_data["platform_post_id"],
        tweet_data["posted_at"],
        tweet_data["text"],
        tweet_data["likes"],
        tweet_data["comments_count"],
        tweet_data["reposts"],
        tweet_data["quotes"],
        tweet_data["views"],
        tweet_data["lang"],
        tweet_data["tweet_url"],
        tweet_data["tweet_type"],
        tweet_data["quoted_tweet_id"],
        tweet_data["reply_to_tweet_id"],
        tweet_data["retweeted_tweet_id"],
        psycopg2.extras.Json(
            tweet_data["raw_json"]
        )
    )


    if len(values) != query.count("%s"):
        raise ValueError(
            f"INSERT inválido: "
            f"{query.count('%s')} placeholders "
            f"para {len(values)} valores."
        )

    try:

        cur.execute(query, values)

        inserted = cur.rowcount

        conn.commit()

        return inserted > 0

    except Exception: 
        conn.rollback() 
        raise

    finally:

        cur.close()
        conn.close()