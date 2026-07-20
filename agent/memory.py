import os
import json
import psycopg2
from psycopg2.extras import Json

def _to_vector_literal(embedding):
    return "[" + ",".join(str(x) for x in embedding) + "]"
def get_connection():
    dsn = os.environ["DATABASE_URL"]
    return psycopg2.connect(dsn)


def insert_incident(conn, namespace, resource_name, resource_kind, issue_type, description, raw_details, embedding, suggested_fix=None, fix_status="llm_suggested"):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO incidents
                (namespace, resource_name, resource_kind, issue_type,
                 description, raw_details, embedding, suggested_fix, fix_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (namespace, resource_name, resource_kind, issue_type,
             description, Json(raw_details), _to_vector_literal(embedding), suggested_fix, fix_status),
        )
        incident_id = cur.fetchone()[0]
    conn.commit()
    return incident_id


def confirm_fix(conn, incident_id):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE incidents SET fix_status = 'confirmed' WHERE id = %s",
            (incident_id,),
        )
    conn.commit()


def find_similar_incidents(conn, embedding, resource_kind, issue_type, limit=5):
    """Rank by vector distance, but only within incidents of the same
    resource_kind/issue_type so unrelated resources aren't matched purely
    on text similarity."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, namespace, resource_name, resource_kind, issue_type,
                   description, suggested_fix, fix_status, created_at,
                   embedding <-> %s AS distance
            FROM incidents
            WHERE embedding IS NOT NULL
              AND resource_kind = %s
              AND issue_type = %s
            ORDER BY fix_status = 'confirmed' DESC, distance ASC
            LIMIT %s
            """,
            (_to_vector_literal(embedding), resource_kind, issue_type, limit),
        )
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]