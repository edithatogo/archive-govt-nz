# Mermaid Diagram Style Guide

This document outlines standards for creating diagrams using Mermaid syntax in
documentation and specifications.

## When to use Mermaid

Use Mermaid diagrams for:

- Architecture diagrams.
- Flowcharts and decision trees.
- Sequence diagrams.
- Class diagrams.
- ER diagrams.
- Gantt charts.
- State diagrams.

## Diagram types

### Flowcharts

Use for process visualization and decision trees.

```mermaid
flowchart TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process A]
    B -->|No| D[Process B]
    C --> E[End]
    D --> E
```

### Sequence diagrams

Use for showing interactions between actors or components over time.

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Database

    Client->>API: Request data
    API->>Database: Query
    Database-->>API: Return results
    API-->>Client: Response
```

### Class diagrams

Use for object-oriented design documentation.

```mermaid
classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
    }

    class Dog {
        +fetch()
    }

    Animal <|-- Dog
```

### ER diagrams

Use for database schema documentation.

```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    CUSTOMER {
        string id PK
        string name
    }
    ORDER {
        string id PK
        string customer_id FK
    }
```
