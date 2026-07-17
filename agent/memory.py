import os
import json
import psycopg2
from psycopg2.extras import Json

def _to_vector_literal(embedding):
    return "[" + ",".join(str(x) for x in embedding) + "]"
def get_connection():
    dsn = os.environ["DATABASE_URL"]
    return psycopg2.connect(dsn)


def insert_incident(conn, namespace, resource_name, resource_kind, issue_type, description, raw_details, embedding, suggested_fix=None):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO incidents
                (namespace, resource_name, resource_kind, issue_type,
                 description, raw_details, embedding, suggested_fix)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (namespace, resource_name, resource_kind, issue_type,
             description, Json(raw_details),  _to_vector_literal(embedding), suggested_fix),
        )
        incident_id = cur.fetchone()[0]
    conn.commit()
    return incident_id


def find_similar_incidents(conn, embedding, limit=5):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, namespace, resource_name, resource_kind, issue_type,
                   description, suggested_fix, created_at,
                   embedding <-> %s AS distance
            FROM incidents
            WHERE embedding IS NOT NULL
            ORDER BY distance ASC
            LIMIT %s
            """,
            (_to_vector_literal(embedding), limit),
        )
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]