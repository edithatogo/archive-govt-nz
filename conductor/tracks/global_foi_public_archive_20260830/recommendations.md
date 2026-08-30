# Additional recommendations incorporated at approval

The user asked for further improvements while approving the track. These make
existing acceptance criteria precise; they do not introduce a new architecture,
external provider, spending commitment or collection purpose.

| Improvement | Why it matters | Acceptance and tasks |
| --- | --- | --- |
| Rescue expiring artifacts first | Existing capture transport expires; preserved metadata is no substitute for lost raw bytes. Inventory durable copies and deadlines before recapture. | AC06/AC08; P0.3, P3.3 |
| Publish coherent global snapshots | Independent country uploads must not produce a global index with missing files or mixed revisions. Pin child revisions and promote only after verification. | AC07; P4.1–P4.4 |
| Fence ownership across repositories | Per-repository concurrency cannot stop a delayed donor job after takeover. Require shared owner generation or equivalent tested fencing. | AC08/AC10; P5.1, P6.1–P6.4 |
| Prove cold restore and outage recovery | A warm local cache can hide missing published objects. Restore in a clean environment and measure the recovery/data-loss window. | AC06/AC07/AC10; P3.3, P4.4, P6.2 |
| Isolate unsafe URLs and payloads | Public request systems can expose malicious attachments and redirects. Bound parsing/expansion, prevent private-network fetches, and quarantine unsafe exports without rewriting originals. | AC06/AC11; P3.1–P3.4, P4.1 |
| Bound growth and retry costs | Global backfills must share capacity fairly, avoid retry storms, and remain resumable as manifests grow. Use explicit budgets, sharding, queue age and storage forecasts. | AC08/AC09; P5.1–P5.5 |

Keep optional additional mirrors, paid storage and a custom frontend outside
this initialization. Revisit independent redundancy after the HF archive can
be reconstructed and the operator can assess the measured storage footprint.

The first execution priority remains the two diagnosed automation failures,
after the required baseline/contract checks. No recommendation permits skipping
source rights/privacy review or reporting incomplete countries as captured.
