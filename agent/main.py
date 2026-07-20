import argparse

from dotenv import load_dotenv
load_dotenv()

from agent.scanner import scan_namespace
from agent.embeddings import embed_text
from agent.memory import get_connection, insert_incident, find_similar_incidents
from agent.reasoner import suggest_fix


def run(namespace):
    incidents = scan_namespace(namespace)

    if not incidents:
        print(f"No issues detected in namespace '{namespace}'.")
        return

    conn = get_connection()

    for incident in incidents:
        print(f"\n=== Detected: {incident['issue_type']} on {incident['resource_name']} ===")
        print(incident["description"])

        embedding = embed_text(incident["description"])

        similar = find_similar_incidents(
            conn, embedding,
            resource_kind=incident["resource_kind"],
            issue_type=incident["issue_type"],
            limit=3,
        )
        print(f"Found {len(similar)} similar past incident(s).")

        fix = suggest_fix(incident["description"], similar)
        print(f"\nSuggested diagnosis/fix:\n{fix}")

        incident_id = insert_incident(
            conn,
            namespace=incident["namespace"],
            resource_name=incident["resource_name"],
            resource_kind=incident["resource_kind"],
            issue_type=incident["issue_type"],
            description=incident["description"],
            raw_details=incident["raw_details"],
            embedding=embedding,
            suggested_fix=fix,
        )
        print(f"Saved incident to memory: {incident_id}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="K8s Deployment Memory Agent")
    parser.add_argument("--namespace", default="default", help="Kubernetes namespace to scan")
    args = parser.parse_args()
    run(args.namespace)


if __name__ == "__main__":
    main()