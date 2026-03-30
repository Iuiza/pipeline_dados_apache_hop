import os
import psycopg
from dotenv import load_dotenv

# --------------------------------------------------
# 1. Carregar variáveis de ambiente (.env)
# --------------------------------------------------
load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    raise ValueError("Defina DATABASE_URL no .env")

# --------------------------------------------------
# 2. Conexão com PostgreSQL
# --------------------------------------------------
conn = psycopg.connect(DB_URL)
conn.autocommit = True

# --------------------------------------------------
# 3. Criar extensões necessárias (se não existirem)
# --------------------------------------------------
with conn.cursor() as cur:
    # Remove acentos
    cur.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
    
    # Busca fuzzy (erros de digitação)
    cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

# --------------------------------------------------
# 4. Criar MATERIALIZED VIEW com o "documento"
# --------------------------------------------------
# Aplicando o conceito de "documento" para a busca textual:
# Documento = concatenação de múltiplos campos
# - nome do pesquisador
# - nome do artigo
# - issn
# - ano
#
# Definindo os pesos:
#   A → mais importante (nome do artigo)
#   B → médio (nome do pesquisador)
#   C → menor (issn + ano)
# --------------------------------------------------

with conn.cursor() as cur:
    cur.execute("""
    DROP MATERIALIZED VIEW IF EXISTS documentos_fts;
    
    CREATE MATERIALIZED VIEW documentos_fts AS
    SELECT 
        p.producoes_id,
        pe.nome AS pesquisador,
        p.nomeartigo,
        p.issn,
        p.anoartigo,
        
        -- Construção do tsvector com pesos
        (
            setweight(to_tsvector('portuguese', coalesce(p.nomeartigo, '')), 'A') ||
            setweight(to_tsvector('simple', coalesce(pe.nome, '')), 'B') ||
            setweight(to_tsvector('simple', coalesce(p.issn, '')), 'C') ||
            setweight(to_tsvector('simple', coalesce(p.anoartigo::text, '')), 'C')
        ) AS document
        
    FROM producoes p
    JOIN pesquisadores pe 
        ON p.pesquisadores_id = pe.pesquisadores_id;
    """)

# --------------------------------------------------
# 5. Criar índice GIN
# --------------------------------------------------
with conn.cursor() as cur:
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_fts_document 
    ON documentos_fts USING GIN(document);
    """)

# --------------------------------------------------
# 6. Função de busca com plainto_tsquery
# (busca simples)
# --------------------------------------------------
def search_simple(search_text: str):
    print(f"\nBusca simples: {search_text}\n")

    with conn.cursor() as cur:
        cur.execute("""
        SELECT 
            pesquisador,
            nomeartigo,
            ts_rank(document, plainto_tsquery('portuguese', %s)) AS rank
        FROM documentos_fts
        WHERE document @@ plainto_tsquery('portuguese', %s)
        ORDER BY rank DESC
        LIMIT 10;
        """, (search_text, search_text))

        for row in cur.fetchall():
            print(f"[{row[2]:.4f}] {row[0]} -> {row[1]}")


# --------------------------------------------------
# 7. Função com to_tsquery
# (busca booleana)
# --------------------------------------------------
def search_boolean(tsquery: str):
    print(f"\nBusca booleana: {tsquery}\n")

    with conn.cursor() as cur:
        cur.execute("""
        SELECT 
            pesquisador,
            nomeartigo,
            ts_rank(document, to_tsquery('portuguese', %s)) AS rank
        FROM documentos_fts
        WHERE document @@ to_tsquery('portuguese', %s)
        ORDER BY rank DESC
        LIMIT 10;
        """, (tsquery, tsquery))

        for row in cur.fetchall():
            print(f"[{row[2]:.4f}] {row[0]} -> {row[1]}")


# --------------------------------------------------
# 8. Sugestão de correção (pg_trgm)
# Para palavras com erro de digitação
# --------------------------------------------------
def suggest(term: str):
    print(f"\nSugestões para: {term}\n")

    with conn.cursor() as cur:
        cur.execute("""
        WITH palavras AS (
            SELECT DISTINCT unnest(regexp_split_to_array(lower(nomeartigo), '\s+')) AS palavra
            FROM producoes
        )
        SELECT palavra, similarity(palavra, %s) AS sim
        FROM palavras
        WHERE length(palavra) > 3
        ORDER BY palavra <-> %s
        LIMIT 2;
        """, (term, term))

        rows = cur.fetchall()

        if not rows:
            print("Nenhuma sugestão encontrada.")
            return

        for row in rows:
            print(f"[{row[1]:.4f}] {row[0]}")


# --------------------------------------------------
# 9. Execução de exemplos
# --------------------------------------------------
if __name__ == "__main__":
    
    # Busca simples
    search_simple("dengue bahia")
    
    # Busca booleana
    search_boolean("covid & bahia")
    
    # Sugestão
    suggest("denge")
    