# Architecture Decisions

## ADR-01: Bounded workflow instead of autonomous multi-agent system

**Decision:** Use one LangGraph workflow coordinating normal application tools.

**Why:** The reimbursement process is predictable and financially sensitive.
A bounded graph is easier to audit, test, and govern than open-ended autonomous
planning. Multi-agent coordination would add latency, cost, failure modes, and
explanation complexity without a clear business benefit in this scope.

## ADR-02: Deterministic financial decisioning

**Decision:** Policy limits, amount calculation, duplicate checks, approval
thresholds, and final routing are deterministic Python/application logic.

**Why:** Financial controls require repeatability, testability, and auditability.
The LLM cannot override these results.

## ADR-03: Retrieval-augmented generation, not fine-tuning

**Decision:** Retrieve policy sections at runtime and provide the retrieved
evidence to the LLM explanation step.

**Why:** Policies change and decisions need traceable sources. Fine-tuning would
make policy updates and provenance harder.

## ADR-04: Lightweight lexical RAG for the one-day prototype

**Decision:** Parse the Markdown policy into section-level chunks and use a
small lexical retriever.

**Why:** There are only five policy sections. A vector database is unnecessary
for demonstrating the retrieval contract and would increase setup risk.
Production can replace this implementation with hybrid/vector enterprise search
without changing the workflow or policy-tool interface.

## ADR-05: LLM only for grounded explanation

**Decision:** The LLM receives an already-computed decision, amounts, receipt
status, and retrieved policy evidence. It generates only the user-facing
explanation.

**Fallback:** If no LLM is configured or the call fails, the deterministic
explanation is returned. Financial processing therefore does not depend on LLM
availability.
