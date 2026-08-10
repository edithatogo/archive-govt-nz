---
name: "Quality frontier"
title: "[Quality frontier] "
labels: []
assignees: []
body:
  - type: markdown
    attributes:
      value: |
        ## Summary
  - type: input
    id: issue
    attributes:
      label: Issue reference
      description: Parent issue number or ticket reference
      placeholder: "#15"
      required: true
  - type: textarea
    id: context
    attributes:
      label: Applicability and exclusions
      description: What applies to this track and what is excluded
      required: true
  - type: textarea
    id: gaps
    attributes:
      label: Evidence-backed gap
      description: Confirm the gap, expected threshold, and proof artifact path
      required: true
  - type: textarea
    id: gates
    attributes:
      label: Required gates
      description: Which local/hosted gates must pass
      placeholder: "locks, formats, lint, tests, mutation..."
      required: true
