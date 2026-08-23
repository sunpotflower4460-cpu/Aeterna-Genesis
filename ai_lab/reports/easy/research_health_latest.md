# Research Infrastructure Health

✅ burst `dream-20260823-0404` — strict errors: 0, warnings: 1

これは研究インフラの整合性監査です。科学的な負の結果・未再現・低gainを失敗扱いしません。

- ✅ `easy-current-burst-present` — easy/latest.json must identify the current completed burst
- ✅ `frontier-alias-current-burst` — frontier_latest must belong to the same burst as easy/latest
- ✅ `frontier-budget-nonnegative` — frontier budget fields must be non-negative
- ✅ `frontier-allocation-within-request` — allocated frontier compute must not exceed the requested bounded budget
- ✅ `frontier-execution-within-allocation` — executed frontier experiments must not exceed allocated compute
- ✅ `frontier-unallocated-accounting` — unallocated_due_to_capacity must close the requested-vs-allocated accounting identity
- ✅ `frontier-execution-gap-accounting` — allocated_but_not_executed must close the allocation-vs-execution identity
- ✅ `frontier-current-question-keys-unique` — a current burst must not count the same progress question twice
- ✅ `frontier-x-context-identity-migration` — current X progress keys should carry start-context identity; legacy keys remain valid history but are not safe as cross-context coverage
- ✅ `research-memory-keys-unique` — Research Memory entry keys must be unique
- ✅ `research-memory-schema-durable` — progress_question entries require durable Research Memory schema version >=2
- ✅ `research-memory-progress-count` — counts.progress_questions must equal the actual durable progress_question entries
- ✅ `research-memory-ratchet-policy` — durable progress memory contract must survive later reporting layers
- ✅ `research-memory-total-count` — counts.total must match the number of Research Memory entries
- ⚠️ `research-memory-legacy-x-context-debt` — legacy contextless X progress entries are migration debt only; they must remain preserved but must not suppress a new context-aware question
- ✅ `crossworld-shadow-current-burst` — embedded Cross-World replication shadow must belong to the current easy-report burst
- ✅ `crossworld-replication-current-burst` — replication_latest must never silently point at a previous burst
- ✅ `crossworld-replication-completion-labelled` — an incomplete Cross-World replication is allowed only when explicitly labelled incomplete/skipped
- ✅ `crossworld-shadow-cannot-promote-science` — Cross-World shadow must not promote Rooms/Levels/confidence or equate matching fingerprints with physics
- ✅ `crossworld-replication-cannot-promote-science` — independent replication is a shadow and must not mutate scientific promotion/confidence state
- ✅ `strict-nothing-current-burst` — NØ control report must belong to the current easy-report burst
- ✅ `strict-nothing-remains-null-control` — NØ must remain a single declarative null-control, not a seeded dynamical or emergence success arm

科学的主張、物理方程式、初期条件、Room/公式Levelはこの監査では変更しません。
