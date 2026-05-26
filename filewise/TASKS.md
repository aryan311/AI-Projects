# FileWise Task Decomposition

## Milestone 1: Document Upload

- Add upload endpoint
- Support PDF and TXT first
- Extract text
- Store document metadata
- Return document ID

Done when:

- uploaded document can be parsed and referenced

## Milestone 2: Chunking

- Implement chunk size and overlap
- Preserve source metadata
- Store page or section markers
- Add chunker tests

Done when:

- chunks can be traced back to source location

## Milestone 3: Embeddings and Storage

- Add embedding interface
- Add local or hosted embedding implementation
- Add vector store
- Add fake embeddings for tests

Done when:

- tests do not need paid APIs

## Milestone 4: Retrieval

- Retrieve top chunks
- Add score threshold
- Add source metadata in result
- Add fixture-based retrieval tests

Done when:

- expected chunks appear for known questions

## Milestone 5: Answering

- Generate answer from retrieved chunks
- Add citations
- Add not-enough-evidence behavior
- Add citation validator

Done when:

- answer cannot be returned without citations

## High-Level Build Estimate

- MVP: 5-7 focused days
- evaluation report: 1-2 days
- UI: 1-2 days

## Diligent Notes

- Root risk: unsupported confident answers.
- Automation: retrieval fixtures prevent silent quality regressions.
- Scope guard: skip chat memory in v1.
