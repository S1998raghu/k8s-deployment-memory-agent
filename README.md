# k8s-deployment-memory-agent

An agent that scans a Kubernetes namespace for pod issues (CrashLoopBackOff,
ImagePullBackOff, OOMKilled), embeds each incident, looks up similar past
incidents in CockroachDB (pgvector), and asks a Bedrock-hosted Claude model
to suggest a diagnosis/fix. Incidents and their fixes are persisted so the
agent gets better at diagnosing recurring problems over time.

## Architecture

- `agent/scanner.py` — watches a namespace via the Kubernetes API and detects
  known failure patterns on pods.
- `agent/embeddings.py` — turns an incident description into a vector
  embedding (Bedrock).
- `agent/memory.py` — stores incidents in CockroachDB and retrieves similar
  past incidents by vector distance, scoped to the same `resource_kind` and
  `issue_type` so unrelated resources don't get matched purely on text
  similarity.
- `agent/reasoner.py` — prompts Claude (via Bedrock) with the current
  incident plus retrieved history, preferring fixes that were previously
  confirmed as correct.
- `db/schema.sql` — CockroachDB schema for the `incidents` table.
- `infra/` — Terraform for the EKS cluster this agent watches.
- `k8s/manifests` — sample manifests used to exercise the scanner.

## Retrieval design

Incident retrieval is **not** plain top-k vector search over free text. Pure
embedding similarity can match incidents that read alike but belong to
different resources or issue classes (e.g. matching an OOMKilled Redis pod
in `staging` to an unrelated CPU-throttled pod in `prod`, just because the
descriptions are semantically close). To avoid that, `find_similar_incidents`
first scopes candidates by `resource_kind` and `issue_type` (structural/
business identity) and only uses vector distance to rank *within* that
scoped set. Stored fixes also carry a `fix_status` (`llm_suggested` /
`confirmed`) so the reasoner can prefer fixes that were actually verified to
work over its own past guesses, instead of letting unverified suggestions
compound silently over time.

This design is informed by:
[AI Agents Need Data Product Context, Not More RAG](https://blog.opendataproducts.org/ai-agents-need-data-product-context-not-more-rag-99fa4690f4c8)
— the core idea being that agents need governed, entity-scoped context with
provenance/trust signals, not just raw semantic retrieval.

## Usage

```bash
pip install -r requirements.txt
python -m agent.main --namespace default
```

Requires `DATABASE_URL` (CockroachDB DSN) and AWS credentials for Bedrock in
the environment (see `.env`).
