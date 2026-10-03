# Engine API reference

All interfaces use the dispatcher in `pkg_0002_engine/mod_0016_commands.py`. Native Python inputs use Python integers and bytes. CLI, REPL and PHP inputs use JSON; their responses apply the lossless wire encoding below. The root response is `{"status":"ok","result":...}` on success. Operational errors have a specific `status`, an `error` message, optional `details`, and `outcome: null`. Mathematical undefined or empty answers remain successful operations inside `result`.

## CLI, bridge and wire types

Choose exactly one CLI mode: a positional command with optional `--data '<JSON fields>'`, `--request <UTF-8 JSON file>`, `--json-stdin`, or `--repl`. `--database <path>` selects SQLite storage. Exit status is 0 for a successful root status and 2 for an operational error. The REPL accepts one complete JSON object per line, plus `:help` and `:quit`.

JSON requests have a `command` field. Database paths and project paths are host settings; browser requests cannot change them. PHP sends JSON through the fixed Python stdin bridge. Use `INDEXER_PYTHON`, `INDEXER_DATABASE` and `INDEXER_PROJECT` for host configuration. The PHP launcher and endpoint are intended for loopback access only.

| Native value | JSON transport |
|---|---|
| Integer | `{"type":"integer","value":"12345678901234567890"}` |
| Bytes | `{"type":"bytes","encoding":"base64","value":"AAEC"}` |
| Ordinary string | A JSON string; numeric text remains text |
| Literal dictionary matching a reserved tag | `{"type":"object","entries":[["key", value], ...]}` |

Plain JSON integer inputs are also accepted. Prefer tagged decimal strings whenever another client could round a number. Decimal tags use canonical spelling: zero is `"0"`, positive values have no leading zero or plus sign, and negative values use `-` followed by a nonzero leading digit. Negative transport values do not make negative pointer IDs or negative algebra multiplicities valid.

The three exact reserved dictionary shapes are `{type,value}` with `type="integer"`, `{type,encoding,value}` with `type="bytes"`, and `{type,entries}` with `type="object"`. To store the literal payload `{"type":"integer","value":"23"}` rather than integer 23, send:

```json
{"command":"register","payload":{"type":"object","entries":[["type","integer"],["value","23"]]}}
```

The Python helpers `fn_0121_wire(value)` and `fn_0125_unwire(value)` apply this escaping recursively. Ordinary dictionaries with additional keys are not reserved tags. Response integers, including IDs, counts and schema versions, are tagged recursively. Typed report cells deliberately include `role:"cell"`; an integer cell's `value` is a decimal string.

Requests are limited to 16 MiB. Generator `generate`/`export` transport requests also use a conservative 64 MiB estimated-output preflight; an oversized request returns `resource_limit` instead of allocating its proposed response. Split larger exports into windows or use native `fn_5005_generate` to stream records.

## Commands

Fields marked optional have the defaults shown. All examples use small ordinary JSON integers for readability; wire tags are accepted in their place.

| Command | Required fields | Optional fields and result |
|---|---|---|
| `health` | None | Returns database schema version, default record namespace and supported command names. |
| `namespace` | `kind` | `specification={}`, `namespace`. Registers immutable namespace semantics and returns them. |
| `register` | `payload` | `namespace=default record namespace`, `reference=false`. Appends a record and returns `{kind,namespace,id}`. |
| `alias` | `name`, `target` | `expected_revision=0`, `namespace=default alias namespace`. Appends a checked alias revision. |
| `history` | `name` | `namespace=default alias namespace`. Returns all revisions in ascending order. |
| `resolve` | `pointer` | `namespace`, `kind`, `max_hops=64`. Returns terminal `pointer`, `target`, `target_type` and `trace`. |
| `encode` | `configuration` and algebra context | Returns configuration and canonical pointer. |
| `decode` | `id` and algebra context | Returns namespace, ID and multiplicity vector. |
| `evaluate` | `operation`, `left`, `right` and algebra context | `composition`, `max_steps=500000`, `max_solutions=10000`. Returns exact outcome or budget exhaustion. |
| `laws` | `composition` and algebra context | `max_steps=500000`. Checks tensor laws and identity. |
| `generate` | `specification` | `start=0`, `limit=10000`. Returns namespace, total, requested window and generated records. |
| `export` | `specification` | `start=0`, `limit=10000`. Returns namespace, total, requested window and `data` as tagged bytes containing one C++ record block. |
| `import` | `data` as tagged bytes | `specification` when needed. Validates one C++ block, registers its generator and stores an immutable archive; returns archive pointer, namespace, emitted count and start. |
| `inventory` | None | `limit=1000`, allowed 0–100000. Returns stored records in deterministic namespace/ID order. |
| `catalogue` | None | Returns x2 metadata. |
| `catalogue_check` | None | Returns current validation result; root status is `catalogue_invalid` on failed checks. |
| `catalogue_sync` | None | Synchronizes x0/x1/x2 under the project publication lock. |
| `report` | None | `name="inventory"`, `evidence`, `limit=1000` (1–100000). Returns typed rows, provenance and coverage. |
| `report_request` | `definition` | Stores a request with `request_id`, validation `status` and `diagnostic`, including invalid definitions. |
| `report_activate` | `request_id` | Activates a validated request after catalogue publication; returns active name, request ID, catalogue entity and digest. |

Algebra context is either `alphabet`, an ordered nonempty list of unique nonempty strings, or `namespace`, an already registered configuration namespace. If both are supplied they must agree. Encoding, decoding and evaluation register the canonical configuration namespace. Its fingerprint includes the alphabet order and ranking convention, independently of composition rules.

For `namespace`, use `kind="record"` with an optional explicit namespace; its specification is empty. Use `kind="configuration"` with `specification={"alphabet":[...]}` or `kind="generator"` with a generator specification. Configuration and generator namespaces are derived from the immutable normalized specification; use the returned namespace in subsequent pointers.

## Records, references and aliases

A structured pointer has exactly `{"kind":"record|generator|configuration","namespace":"...","id":<integer>}`. Its text spelling is `idx:<kind>:<namespace>:<nonnegative decimal id>`. Namespaces contain only letters, digits, `.`, `_` and `-`. Bare integer resolution requires an explicit namespace and kind; booleans are not IDs.

Record IDs begin at 1 and remain bound permanently. JSON records are terminal even if their payload resembles a pointer. Set `reference:true` to create a traversable reference. Its payload must be a structured/full-text pointer or `{"alias":"exact name","namespace":"alias namespace"}`. Referenced records can be appended before their targets exist; unresolved targets fail when resolved.

Aliases are nonempty exact text outside the reserved `idx:` prefix. They point to an existing explicit pointer, including a reference record. `expected_revision=0` creates a new alias. Updating it requires the latest observed revision; stale writers receive `revision_conflict` with the actual revision. Prior revisions remain unchanged. Alias lookup uses the supplied alias namespace or the database's default record namespace.

`resolve.pointer` also accepts `{"alias":"exact name","namespace":"alias namespace"}`. A string such as `"001"` is an alias, whereas JSON integer `1` is an integer pointer. Neither strings nor ordinary record payloads undergo implicit integer conversion. Reference following retains every traversed pointer and alias revision in one consistent SQLite snapshot. The default maximum is 64 reference hops; accepted explicit values are 1–10000.

Principal resolution errors are `missing_target`, `namespace_mismatch`, `malformed_pointer`, `cycle` and `resource_limit`. Invalid input, alias revision conflict, unsupported schema, database and I/O failures have separate operational statuses. Explicit namespace/kind context must agree with an explicit starting pointer.

## Canonical algebra

Multiplicity vectors contain one nonnegative integer per ordered alphabet symbol. ID order is increasing total cardinality, then ascending lexicographic vector order. For `["neutral","toggle"]`, IDs 0–5 decode as `[0,0]`, `[0,1]`, `[1,0]`, `[0,2]`, `[1,1]`, `[2,0]`. Rank/unrank uses binomial counting and binary searches; it does not enumerate earlier configurations.

`left` and `right` accept multiplicity lists, integer configuration IDs, or explicit configuration pointers. Pointer namespaces must match the algebra context. `operation` is one of `add`, `subtract`, `multiply`, `divide_right` or `divide_left`. Addition aggregates counts. Subtraction removes counts exactly and reports coordinate deficits when removal is undefined.

Multiplication and both divisions require the complete tensor `composition[i][j][k]`, giving the number of output symbol `k` produced by primitive pair `(i,j)`. Every entry is nonnegative and every dimension equals the alphabet length. No multiplication rule is inferred from names or ID arithmetic.

`divide_right(x,y)` solves `q*y=x`; `divide_left(x,y)` solves `y*q=x`. Division enumerates all bounded-coordinate solutions. Zero columns produce exact symbolic free coordinates, not truncated samples. Default solver limits are 500000 steps and 10000 finite solutions/base solutions. These are computation budgets, not domain restrictions.

| Result | Native inner result |
|---|---|
| Single value, including valid zero | `{"status":"ok","outcome":{"kind":"value","id":0,"configuration":[0,0]}}` |
| No quotient exists | `{"status":"ok","outcome":{"kind":"solutions","finite":true,"ids":[],"configurations":[]}}` |
| Unique zero quotient | `{"status":"ok","outcome":{"kind":"solutions","finite":true,"ids":[0],"configurations":[[0,0]]}}` |
| Undefined subtraction | `{"status":"ok","outcome":{"kind":"undefined","deficits":[...]}}` |

Other finite divisions return every quotient ID and configuration. Infinite divisions return `finite:false`, `bases`, `base_ids`, `free_coordinates`, `parameterization` and `namespace`. Each quotient is a listed base plus arbitrary nonnegative multiples of the listed coordinate unit vectors; its ID is obtained through canonical encoding. Exhausted budgets return `{"status":"resource_limit","outcome":null}` without claiming impossibility or presenting an incomplete family as complete.

The `laws` command reports verified associativity, commutativity, a two-sided identity (possibly composite), primitive identity, finite-monoid conditions, cardinality behavior and classification. If its budget expires it returns `laws:null`. Signed and restricted multiplicity domains are not implemented.

The manuscript's neutral–toggle model is an explicit fixture:

```json
{"command":"evaluate","alphabet":["neutral","toggle"],"operation":"divide_right","left":4,"right":4,"composition":[[[1,0],[0,1]],[[0,1],[1,0]]]}
```

Its quotient IDs are `[1,2]`. With this tensor, ID operations also give `1+2 -> 4`, `4-1 -> 2`, and `1*1 -> 2`. These are configuration operations transported through IDs, not ordinary arithmetic on the integers naming them.

## Generator specifications and imports

Generators address UTF-8 bytes with direct zero-based ordinals. `start` selects the first ordinal; `limit` is a count. The command transport accepts 0–1000000 records per explicit window, subject to the estimated-output budget. Native iteration accepts a larger explicit count and remains lazy. Window/output-path controls do not change the namespace.

| `source_kind` | Specification and defaults | Source limits |
|---|---|---|
| `configure_1` | `width=4`, `alphabet_name="original"` | Width 1–16; alphabets `original`, `safe`, `digits`, `lower`. |
| `configure_2` | `width=7`, `alphabet_name="decimal_digits"` | Width 1–18; `digits` normalizes to `decimal_digits`. Leading zeroes remain part of payloads. |
| `configure_3` | Fields below | Cartesian width at most 64; repeat count at most 1000000. |

The default source kind is `configure_1`. Its `original` alphabet is lowercase letters, uppercase letters, digits, space and newline; `safe` substitutes underscore for the final whitespace symbols. `digits` contains decimal digits and `lower` contains lowercase letters.

`configure_3` fields are `object_name="x33"`, `input_name="x1"`, `input_value="0123456789"`, `input_width=7`, `flow_name="x15"`, `flow_type="cartesian"`, `output_name="x31"`, `separator="\n"`, `prefix=""` and `suffix=""`. Names must be nonempty text; width must be a positive integer. `input_value`, `separator`, `prefix` and `suffix` each have a 4096-byte UTF-8 bound. Flow names are `cartesian`, `literal`, `repeat` and `reverse`; aliases `product`/`combinations` normalize to `cartesian`, and `echo` to `literal`.

Cartesian flow selects bytes with repetition, literal emits one input payload, repeat emits `input_width` distinct ordinal records carrying that same payload, and reverse reverses the input bytes once. Prefix and suffix wrap each payload. The original separator is preserved as metadata. The supplied JSON text is already decoded; JSON `"\n"` supplies an actual newline, while `"\\n"` supplies the two literal characters backslash and n.

Each generated record includes source kind/namespace/ordinal, authoritative `payload_bytes` and `rendered_bytes`, hex equivalents, preview text, payload `byte_length` and lowercase 64-bit FNV-1a checksum of rendered bytes. Byte-level reversal or selection can produce invalid UTF-8; preview strings use replacement characters while bytes/hex remain exact. Duplicate payloads retain distinct ordinals.

`export` emits one newline-terminated `# cppdb-configure-source v1` block with original headers, escaped fields, record ordinals, byte lengths and checksums. `import` accepts exactly one complete block, validating metadata, source identity, lengths, checksums, ordering, escaping, truncation and reconstructed records. LF and CRLF framing are accepted. Split concatenated C++ object blocks at their magic headers before importing individually. `configure_1` and `configure_2` can reconstruct specifications from complete headers. `configure_3` requires an explicit specification including `input_value`, which its header omits.

## Typed reports and activation

The built-in sources are:

| Source | Columns and declared types |
|---|---|
| `inventory` | `namespace:string`, `id:integer`, `record_type:string`, `payload:json` |
| `dependency` | `relation:string`, `source:string`, `target:string`, `description:string` |
| `resolution` | `step:integer`, `evidence:json` |
| `algebra` | `status:string`, `outcome:json` |

Inventory reads stored rows; dependency reads x2 wiring. Resolution requires `evidence` containing a `trace` list. Algebra requires `evidence` containing `status` and `outcome`. Those evidence objects are supplied by the caller, and provenance explicitly says `evidence_origin:"caller_supplied"`; displaying them does not certify that the engine originally produced them. Inventory and dependency provenance says `"engine"`.

A report definition contains exactly `name`, `source`, optional `columns`, optional `filters` and optional `group_by`. Names have 1–64 ASCII letters/digits/underscores and begin with a letter. Columns default to every source column; selections and grouping lists use unique valid source columns. At most 32 filters are allowed. Every filter has exactly `field`, `op`, `value`, with `op` equal to `eq`, `ne` or `contains`. Equality is type-sensitive; `contains` requires actual and expected values to be strings.

```json
{"command":"report_request","definition":{"name":"records_by_namespace","source":"inventory","columns":["namespace","id"],"filters":[{"field":"record_type","op":"eq","value":"json"}],"group_by":["namespace"]}}
{"command":"report_activate","request_id":1}
{"command":"report","name":"records_by_namespace","limit":1000}
```

Use the actual returned request ID. Request IDs belong to their SQLite database. Catalogue report entities receive project-wide numbered identities so databases sharing a project cannot reuse a documentation number. Activation serializes catalogue publication, updates x0/x1/x2 and the database registry, and can be retried for an active request. Invalid requests remain stored with diagnostics and cannot activate.

Output has `type:"list"`, an `element_type` describing list column types, `items` as lists of typed cells, `provenance` and `coverage`. Filters operate on the selected source window. With `group_by`, output columns become the grouping fields followed by integer `count`; aggregation counts only that filtered window. `coverage.source_total`, `source_complete`, `limit` and `filter_scope:"selected_source_window"` state its extent. A limited report must not be interpreted as a whole-database aggregate.

## Native Python entry points

Import the core numbered interfaces from `pkg_0002_engine`; the dispatcher, reports and catalogue helpers reside in their numbered modules. The signatures below use explanatory parameter labels. Actual implementation parameter names are numbered; pass positional arguments unless deliberately using those names.

| Interface | Purpose |
|---|---|
| `type_0112_pointer(kind, namespace, id)`; `.fn_0117_dict()` | Immutable typed pointer and ordinary-key dictionary representation. |
| `fn_0118_pointer(value)` | Parse a pointer object, exact structured dictionary or full text pointer. |
| `type_1010_engine(database_path)` | Context-managed SQLite engine. |
| `engine.fn_1028_namespace(kind, specification, namespace=None)` | Register immutable namespace semantics. |
| `engine.fn_1038_register(payload, namespace=None, reference=False)` | Append a record and return its typed pointer. |
| `engine.fn_1046_alias(name, target, expected_revision=0, namespace=None)` | Append an alias revision. |
| `engine.fn_1059_resolve(value, namespace=None, kind=None, max_hops=64)` | Resolve with a snapshot and trace. |
| `engine.fn_1074_history(name, namespace=None)` | Read alias history. |
| `engine.fn_1078_inventory(limit=1000)` | Read bounded stored records. |
| `type_3000_domain(alphabet)` | Construct an immutable natural indexing domain. |
| `fn_3002_encode(domain, configuration)`; `fn_3003_decode(domain, id)` | Exact rank/unrank. |
| `fn_3004_evaluate(domain, operation, left, right, composition=None, max_steps=500000, max_solutions=10000)` | Exact arithmetic/family evaluation. |
| `fn_3005_laws(domain, composition, max_steps=500000)` | Verify tensor laws. |
| `fn_5001_spec(spec)`; `fn_5002_namespace(spec)`; `fn_5003_total(spec)` | Normalize and inspect a generator without enumeration. |
| `fn_5004_record(spec, ordinal)`; `fn_5005_generate(spec, start=0, limit=10000)` | Direct record access and lazy window iteration. |
| `fn_5006_export(spec, start=0, limit=10000)`; `fn_5007_import(bytes, spec=None)` | Exact source-block export/import. |
| `fn_1408_dispatch(request, database=None, root=None)` | Dispatch one native request. |
| `fn_1432_json(text, database=None)` | Process one wire JSON request and return JSON text. |
| `fn_1215_request(engine, definition)`; `fn_1222_activate(engine, root_path, request_id)` | Store and activate a declarative report. |
| `fn_1231_render(engine, root_path, name="inventory", evidence=None, limit=1000)` | Produce typed report rows. |
| `fn_7001_sync(root, additions=None)`; `fn_7002_check(root)`; `fn_7003_load(root)` | Synchronize, validate and load catalogue metadata. |

Use `pathlib.Path` for native report `root_path` arguments. Operational engine exceptions are `type_0105_error` with `attr_0110_code` and `attr_0111_details`. Low-level algebra/generator validation can raise `ValueError`; the dispatcher maps invalid input to structured responses.

```python
from pkg_0002_engine import type_1010_engine, type_3000_domain, fn_3002_encode

with type_1010_engine(":memory:") as var_1950_engine:
    var_1951_pointer = var_1950_engine.fn_1038_register({"label": "example"})
    var_1950_engine.fn_1046_alias("example", var_1951_pointer, 0)
    var_1952_result = var_1950_engine.fn_1059_resolve("example")
    assert var_1952_result["target"] == {"label": "example"}

var_1953_domain = type_3000_domain(["neutral", "toggle"])
assert fn_3002_encode(var_1953_domain, [1, 1]) == 4
```

The catalogues use their own schema version and content-derived IDs. Read [doc_0021_catalogues.md](doc_0021_catalogues.md) for their format and [x4.md](x4.md) before editing source, activating report skills or migrating databases. Unsupported database/catalogue schema versions are rejected rather than guessed.
