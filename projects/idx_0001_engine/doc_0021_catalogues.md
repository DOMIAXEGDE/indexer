# Catalogue maintenance and schema

The project follows the six rules in its preserved `ref_0004_sources/indexer.txt`. `x4.md` is the update contract; this file describes the callable catalogue interface.

```python
from pkg_0002_engine.mod_0013_catalogues import fn_7001_sync, fn_7002_check, fn_7003_load

# Positional arguments preserve the project's numbered parameter names.
fn_7001_sync("D:/indexer/projects/idx_0001_engine")
fn_7002_check("D:/indexer/projects/idx_0001_engine")
fn_7003_load("D:/indexer/projects/idx_0001_engine")
```

`sync` and `check` return an `ok` boolean and an `errors` list. Successful results include entity, edge and inspected-file counts; successful synchronization also returns the source and catalogue digests. `load` reads the generated x2 object and rejects unsupported schema versions.

`x0.txt` uses TOML schema version 1. Its `entities` array describes each owned declaration or filesystem object using `id`, `name`, `form`, `description`, `origin`, `active` and `locations`. A location gives the relative file, one-based line and column, and the occurrence role. Several declarations using an identical numbered spelling share an entity, while every declaration location remains recorded. Reusing an integer with a different owned spelling fails validation. New declarations receive semantic descriptions from docstrings or their named binding roles. Existing empty descriptions fail validation; synchronization does not silently repair documentation gaps.

`x1.txt` uses TOML schema version 1. Its `edges` array contains `id`, `source`, `target`, `relation`, `description`, `origin` and `locations`. Source-generated relationships include `contains`, `calls`, `reads`, `assigned_from`, `inputs`, `outputs` and `persistence`. The map is static, so computed dispatch and reflection may need explicit manual edges. Add manual edges with `origin = "manual"` and real endpoints. Maintainer descriptions and unrecognized manual edge metadata survive synchronization.

`x2.json` includes both flat arrays (`entities`, `wiring`) for querying and a `recursive` representation for browsing. Its root expands the project containment graph; disconnected or retired entities appear under `uncontained`. Containment expands each entity at most once. Shared targets, cycles, and noncontainment references use `{"$ref": "<entity-id>"}`. The SHA-256-derived documentation IDs are independent of record IDs, generator ordinals, algebra IDs and numbered source suffixes.

To register a validated report with the catalogue:

```python
fn_7001_sync("D:/indexer/projects/idx_0001_engine", [{
    "name": "report_10001_namespace_totals",
    "description": "Group persisted inventory rows by namespace.",
    "form": "report",
    "definition": {"source": "inventory", "columns": ["namespace"]},
    "wiring": [{
        "target": "idx_0001_engine",
        "relation": "reads",
        "description": "Read the project's inventory through its registered report service."
    }]
}])
```

This catalogue API stores metadata; validation and activation in the report service also update the persistent request/registry state. Use that service for ordinary report creation. Do not register an example skill by running documentation snippets against a production registry.

Normal synchronization preserves obsolete source entities with `active = false`, retaining their descriptions and reserved names. It preserves reports and manual entities with their existing identities. New source occurrences reactivate a matching entity. The source digest excludes generated catalogues, preserved reference contents and runtime state; it includes owned documentation and tests. Run synchronization after editing this file, then validate.
