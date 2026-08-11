# Specification

## Overview

Evaluate ArchiveBox as a secondary web-page preservation method without making
it an authoritative source, an always-on service, or a dependency of the
Python 3.14 application. Publish a reusable explanation of the archive system
and carry that explanation into rolling Hugging Face metadata and future
checksum-pinned Zenodo packages.

## Functional requirements

- Provide a manual-only Linux GitHub Actions pilot for three to five selected
  HTTPS government publisher pages.
- Pin the ArchiveBox container by immutable digest and record its identity.
- Validate candidate URLs against an explicit HTTPS host allowlist before the
  container runs.
- Produce paired machine-readable and human-readable receipts containing input
  identity, capture results, output hashes, output roles, storage amplification,
  and limitations.
- Admit pilot outputs only through existing content hashing and verification;
  never classify them as original source payloads.
- Add a canonical Mermaid architecture document to the repository.
- Include the architecture document in publication metadata and future release
  candidates, while avoiding a new Zenodo DOI solely for documentation.

## Non-functional requirements

- Keep the workflow manual, least-privilege, bounded, deterministic at its
  validation boundaries, and safe for untrusted captured content.
- Do not install Docker, WSL, ArchiveBox, or an additional service locally.
- Do not add ArchiveBox to `pyproject.toml` or `uv.lock`.
- Keep GitHub Actions artefacts operational; durable payload publication remains
  Hugging Face/Zenodo gated and independently verified.
- Preserve existing dirty work and secrets.

## Acceptance criteria

- The complete repository harness passes.
- The workflow contract proves immutable action and container references,
  explicit time/URL/count/storage bounds, and no scheduled trigger.
- Pilot receipt logic has unit, property, metamorphic, contract, and deterministic
  simulation coverage where applicable.
- The architecture appears in repository documentation, generated Hugging Face
  card material, and the input set for future Zenodo packages.
- A hosted manual pilot is attempted and its actual state is recorded without
  unsupported success claims.

## Out of scope

- Always-on ArchiveBox scheduling or UI.
- Automatic promotion of captures to originals.
- Authenticated browser sessions, proxies, or anti-bot bypass.
- Automatic Hugging Face payload publication or a new Zenodo DOI.
- Adoption of Browser Use, Apify, Firecrawl, or OpenHands as runtime dependencies.
