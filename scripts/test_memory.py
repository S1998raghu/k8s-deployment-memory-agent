import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from agent.memory import get_connection, insert_incident, find_similar_incidents

def random_embedding(dim=1024):
    return [random.uniform(-1, 1) for _ in range(dim)]

conn = get_connection()

incident_id = insert_incident(
    conn,
    namespace="default",
    resource_name="test-app",
    resource_kind="Deployment",
    issue_type="crashloop",
    description="Pod test-app is crash looping due to bad config",
    raw_details={"restarts": 5, "reason": "CrashLoopBackOff"},
    embedding=random_embedding(),
    suggested_fix=None,
)
print(f"Inserted incident: {incident_id}")

query_embedding = random_embedding()
results = find_similar_incidents(conn, query_embedding, limit=3)
print(f"Found {len(results)} similar incidents:")
for r in results:
    print(f"  - {r['id']} | {r['issue_type']} | distance={r['distance']:.4f}")

conn.close()
