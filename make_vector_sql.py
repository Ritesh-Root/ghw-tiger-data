"""Builds 04-vector-search.sql. Embeddings are a toy feature-hashing bag-of-words model
(64 dims, L2-normalised): enough to show pgvector + time/metadata filtering, NOT a semantic model.
Swap embed() for a real embedding API in production."""
import hashlib, math, re

DIM = 64
STOP = set("a an the of to and in on for with is are it as at by from this that be or".split())

def embed(text):
    v = [0.0] * DIM
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOP:
            continue
        h = int(hashlib.md5(w.encode()).hexdigest(), 16)
        v[h % DIM] += 1.0 if (h >> 8) & 1 else -1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]

def lit(v):
    return "'[" + ",".join(f"{x:.5f}" for x in v) + "]'"

docs = [
 ("engineering", 1, "Hypertables partition time-series data into chunks so range queries stay fast"),
 ("engineering", 2, "Continuous aggregates precompute hourly averages for fast dashboards"),
 ("engineering", 3, "Compression into the columnstore saves storage on old sensor data"),
 ("engineering", 5, "PostgreSQL indexes speed up lookups but slow down heavy inserts"),
 ("engineering", 8, "Vector search finds similar documents using embeddings and cosine distance"),
 ("engineering", 12, "Retention policies drop old chunks automatically to control disk usage"),
 ("hackathon", 1, "Global Hack Week challenges include building apps with Cursor and GitHub Copilot"),
 ("hackathon", 4, "Hacktoberfest rewards open source contributions with pull requests during October"),
 ("hackathon", 6, "Team demo day: present your project and show a working prototype"),
 ("hackathon", 9, "MLH hackathon prizes include swag and API credits from sponsors"),
 ("hackathon", 14, "Codespaces gives every contributor the same cloud development environment"),
 ("food", 2, "Slow cooked tomato pasta with garlic basil and olive oil"),
 ("food", 7, "Crispy roasted vegetables seasoned with cumin and lemon"),
 ("food", 10, "Homemade sourdough bread needs a long fermentation and a hot oven"),
 ("food", 15, "Spicy chickpea curry served with rice and fresh coriander"),
 ("space", 3, "Reusable rockets land back on Earth after delivering satellites to orbit"),
 ("space", 6, "The telescope captured distant galaxies and faint light from early stars"),
 ("space", 11, "Astronauts on the station run experiments about microgravity and plant growth"),
 ("space", 13, "Mars rovers search for signs of ancient water on the red planet"),
]

out = []
out.append("CREATE EXTENSION IF NOT EXISTS vector;")
out.append("CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE;")
out.append(f"""CREATE TABLE documents (
  time      TIMESTAMPTZ NOT NULL,
  id        BIGSERIAL,
  category  TEXT NOT NULL,
  content   TEXT NOT NULL,
  embedding vector({DIM}) NOT NULL
) WITH (tsdb.hypertable, tsdb.segmentby = 'category', tsdb.orderby = 'time DESC');""")
out.append("INSERT INTO documents (time, category, content, embedding) VALUES")
rows = []
for cat, days, text in docs:
    safe = text.replace("'", "''")
    rows.append(f"  (now() - interval '{days} days', '{cat}', '{safe}', {lit(embed(text))})")
out.append(",\n".join(rows) + ";")
out.append("CREATE INDEX documents_embedding_idx ON documents USING diskann (embedding vector_cosine_ops);")

def search(title, qtext, where):
    return f"""-- {title}
-- query text: "{qtext}"
SELECT round((embedding <=> {lit(embed(qtext))}::vector)::numeric, 3) AS distance,
       category, (now() - time)::interval(0) AS age, content
FROM documents
{where}
ORDER BY embedding <=> {lit(embed(qtext))}::vector
LIMIT 3;"""

out.append(search("1) Pure similarity search", "fast queries on time series chunks", ""))
out.append(search("2) Similarity + metadata filter (category = hackathon)", "build a project and win prizes", "WHERE category = 'hackathon'"))
out.append(search("3) Similarity + time-range filter (last 5 days)", "cloud environment and open source", "WHERE time > now() - interval '5 days'"))
out.append("SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector','vectorscale','timescaledb') ORDER BY 1;")
out.append("SELECT count(*) AS stored_vectors, vector_dims(embedding) AS dims FROM documents GROUP BY 2;")
open("04-vector-search.sql", "w").write("\n\n".join(out) + "\n")
print("wrote", len(docs), "docs")
