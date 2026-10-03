# Indexer pointer-resolution engine

A local Python engine for permanent JSON records, exact text aliases, integer pointers, byte-exact C/C++ generator ports, and canonical Object Counting Algebra. Every pointer identifies its address kind and namespace. A Python library, CLI, JSON REPL and PHP interface share the same engine.

## Start on Windows

Use Python 3.12 or later. The runtime uses only the Python standard library. Keep this source checkout as the full deployment; PHP on PATH is needed for the browser interface and catalogue validation.

```powershell
Set-Location D:\indexer\projects\idx_0001_engine
py -3.12 -m pkg_0002_engine health
py -3.12 -m pkg_0002_engine --repl
py -3.12 -m pkg_0002_engine --request example_0005_requests/request_0027_algebra.json
```

In the REPL, submit one JSON object per line. `:help` lists commands and `:quit` exits. For example:

```json
{"command":"register","payload":{"label":"first record"}}
{"command":"encode","alphabet":["neutral","toggle"],"configuration":[1,1]}
```

The first call appends a persistent record. The second returns configuration ID 4 in the namespace determined by that ordered alphabet. JSON results encode integers as `{"type":"integer","value":"4"}` to preserve their precision through PHP and browser clients.

To run the local browser interface:

```powershell
.\tool_0006_scripts\run_0023_web.ps1
```

Open [http://127.0.0.1:8765/x3.php](http://127.0.0.1:8765/x3.php). The page provides a JSON command editor, result viewer, catalogue and inventory links, and report examples. The same endpoint accepts JSON POST requests. Ctrl+C stops the server. The launcher selects Python 3.12; a manually launched PHP process can select a Python executable through `INDEXER_PYTHON`.

Optional editable installation adds the `idx_0001_engine` console command:

```powershell
py -3.12 -m pip install -e .
idx_0001_engine health
```

A noneditable package installation provides the Python library. For CLI/report use from such an installation, set `INDEXER_PROJECT` to this checkout so it can find the catalogues, PHP interface and examples. `--database` or `INDEXER_DATABASE` selects another SQLite database. The default is `runtime_0007_state/data_0022_store.sqlite3`.

## Demonstration and checks

```powershell
py -3.12 example_0005_requests/demo_0026_end_to_end.py
py -3.12 -m unittest discover -s tests_0003_suite -p "test_*.py" -v
py -3.12 -m pkg_0002_engine catalogue_check
```

The demonstration registers a record, assigns and resolves an alias, computes the manuscript's neutral–toggle example, and exports a typed report to `runtime_0007_state/demo_0028_report.json`. Its sample database is `runtime_0007_state/demo_0029_store.sqlite3`.

For a four-line poem demonstrating addition, exact subtraction, multiplication and complete division, run `py -3.12 example_0005_requests/demo_0051_poem.py`. Its editable configuration is [config_0050_poem.json](example_0005_requests/config_0050_poem.json); [the poem walkthrough](doc_0052_poem.md) explains its line-count model, operation chain, dedicated example database and evidence report.

Tests cover canonical indexing, exact algebra outcomes, pointer persistence and reference chains, lossless JSON, generator compatibility, catalogue coverage and report behavior. C/C++ compiler-dependent checks require a suitable compiler on PATH; the tests report skipped checks explicitly when tools are unavailable.

## Three different integer address spaces

| Kind | Meaning | Origin |
|---|---|---|
| `record` | An immutable stored record in a database namespace | Allocated from 1 |
| `generator` | A source ordinal computed from a fixed specification | Starts at 0 |
| `configuration` | A nonnegative multiplicity vector ranked by cardinality, then ascending lexicographic order | Empty vector has ID 0 |

A full text pointer is `idx:<kind>:<namespace>:<id>`. Resolving a bare integer requires explicit `kind` and `namespace`. Text `"123"` resolves the exact alias named `123`; it is never silently converted into integer 123. Changed records receive new IDs, while aliases move through explicitly checked revisions and retain their history. Reference chains return a trace and use one SQLite snapshot.

The algebra uses the complete natural multiplicity domain over an explicitly ordered alphabet. Multiplication and division require an explicit complete composition tensor. Valid zero, impossible division, a unique zero quotient and undefined subtraction remain distinct. A resource limit returns no mathematical conclusion. Signed and restricted domains are outside this release.

Generators preserve source ordinals, byte lengths, escaping, leading zeroes, FNV-1a checksums and record metadata. Exports are bounded by default; use the native iterator for larger streamed work. The originals are preserved under [ref_0004_sources](ref_0004_sources), with hashes and original paths in [provenance_0030_sources.json](ref_0004_sources/provenance_0030_sources.json). This includes all six C/C++ files, the manuscript and `indexer.txt`. Their contents are reference data.

See [the API reference](doc_0025_api.md) for exact commands, transport tags and limits; [catalogue maintenance](doc_0021_catalogues.md) for x0/x1/x2; and [the update contract](x4.md) for code changes, report activation and migrations. After an intentional code or documentation edit, run `catalogue_sync`, review the generated changes and run `catalogue_check` before release.
