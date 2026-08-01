# Specification

## Objective

Build a reproducible, evidence-first inventory of health and healthcare-related
datasets discoverable through the official data.govt.nz CKAN catalogue, using
the supplied text-search and health-group views plus organisation facets.

## Boundary

The track discovers and preserves CKAN metadata, query receipts, pagination,
deduplication, classification, and source-resolution outcomes. It must not
download resource payloads or publish data. Payload capture is a separate,
rights- and policy-gated follow-up track.

## Required outcomes

Every result is classified as discovered, duplicate, metadata-fetched,
metadata-failed, candidate, excluded, or decision-required. Search coverage,
query parameters, timestamps, catalogue version, and raw responses are retained
with redaction and bounded response limits.

## Safety

Use HTTPS only, bounded pagination/concurrency/time/response size, a descriptive
User-Agent, retry classification, and fail-closed handling. Never infer that a
health label means personal or sensitive data is safe to publish.
