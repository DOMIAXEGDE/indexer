# A short poem using all four Object Counting Algebra operations

The executable example is configured in [config_0050_poem.json](example_0005_requests/config_0050_poem.json).
Its four operations run through the existing `fn_1408_dispatch` workflow.

**After the Rain**

> Rain leaves silver on the street.  
> Lamplight gathers at my feet.  
> Clouds unfold; the stars appear.  
> Night grows quiet. You are here.

## Declared model

This is an example formalization proposed for this poem. The alphabet consists
of the four exact whole lines above, in that order. A vector `[a,b,c,d]` counts
occurrences of those lines. The domain is the complete `N0^4`, with coordinatewise
equality and canonical indexing by cardinality, then ascending lexicographic order.
The final poem is `[1,1,1,1]`, with canonical configuration ID **55**.

The JSON stores reading order separately as `[0,1,2,3]`. Rendering prints copies
of each line adjacently in that order. Thus `[1,1,1,2]` has the last line twice;
the multiset itself does not encode sequence, rhyme, meter or literary meaning.

For this example, matching line types reproduce the same type, and unlike types
produce the empty configuration. The complete tensor is in the JSON:

```text
T[i][j][k] = 1 when i=j=k, otherwise 0
(x*y)[i] = x[i]*y[i]
```

This is a declared line-count composition rule, not inferred sentence semantics.
The engine verifies associativity, commutativity, distributivity, zero absorption
and the composite identity `[1,1,1,1]`. It classifies this model as a commutative
unital semiring. It is not the singleton-product finite-monoid specialization:
unlike pairs produce zero, and total cardinality is not generally multiplicative.
For example, the two operands with counts 4 and 8 below have product count 8.

## The connected operation chain

Every result supplies the next row's left operand. All vectors use the same alphabet.

| Operation | Configuration calculation | Canonical result |
|---|---|---|
| Addition | `[1,1,0,0] + [0,0,1,2] = [1,1,1,2]` | ID 97: join two drafts, retaining an extra last line |
| Exact subtraction | `[1,1,1,2] - [0,0,0,1] = [1,1,1,1]` | ID 55: remove that extra line |
| Multiplication | `[1,1,1,1] * [2,2,2,2] = [2,2,2,2]` | ID 426: repeat each line twice |
| Right division | `{q : q*[2,2,2,2] = [2,2,2,2]} = {[1,1,1,1]}` | Complete solution set `{55}`: recover the poem |

Subtraction is defined because the removed vector fits componentwise, and its
result plus the removed line reconstructs the draft. In alpha/phi/tau notation,
alpha is `[1,1,1,2]`, phi is `[0,0,0,1]`, and tau is `[1,1,1,1]`.

Division solves `2*q[i]=2` at every coordinate. Each count must therefore be 1;
there are no free coordinates or additional quotients. The runner retains the
engine's complete solution object and verifies quotient-times-divisor reconstruction.
IDs are addresses: these results do not come from ordinary arithmetic on IDs.

## Run and inspect

```powershell
Set-Location D:\indexer\projects\idx_0001_engine
py -3.12 example_0005_requests/demo_0051_poem.py
```

The configuration JSON is an example bundle read by the runner, not a single
CLI request. It declares the domain, line interpretation, tensor, four steps,
expected results and worded requirements. The runner sends ordinary `laws`,
`evaluate`, `encode`, `decode`, `report`, `register`, `history`, `alias` and
`resolve` requests. It checks the operation chain, expected configurations,
exact reconstructions, complete quotient set, indexing round trips and saved
record resolution. A failed check stops execution with an error.

Generated outputs are:

| File | Purpose |
|---|---|
| `runtime_0007_state/poem_0055_text.txt` | The final four-line poem |
| `runtime_0007_state/poem_0053_report.json` | Configuration, law results, all step outcomes, rendered intermediate drafts, typed algebra reports, full dispatcher requests/responses and verification scope |
| `runtime_0007_state/poem_0054_store.sqlite3` | Dedicated example database containing the immutable poem record and alias history |

The evidence report uses the engine's lossless JSON wire encoding: integers are
tagged decimal strings. `fn_0125_unwire` converts these into native Python integers.
The configuration file uses plain JSON integers so it is easy to edit. Typed
algebra reports identify their evidence as caller-supplied; the full dispatcher
responses are also retained so the arithmetic can be inspected directly.

Each rerun appends a new record and advances the alias through a checked revision.
The latest poem resolves with:

```powershell
py -3.12 -m pkg_0002_engine --database runtime_0007_state/poem_0054_store.sqlite3 resolve --data '{"pointer":"poem_after_the_rain"}'
```

Persistent record IDs, alias revisions and configuration ID 55 remain separate
address spaces. The stored record binds the exact configuration, tensor,
rendering rule, poem text and final configuration pointer together.

To use an individual operation in the CLI, REPL or x3 JSON editor, copy its
complete `request` object from the evidence report. For example, the final
division can be requested with:

```json
{
  "command": "evaluate",
  "alphabet": [
    "Rain leaves silver on the street.",
    "Lamplight gathers at my feet.",
    "Clouds unfold; the stars appear.",
    "Night grows quiet. You are here."
  ],
  "operation": "divide_right",
  "left": [2, 2, 2, 2],
  "right": [2, 2, 2, 2],
  "composition": [
    [[1,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
    [[0,0,0,0],[0,1,0,0],[0,0,0,0],[0,0,0,0]],
    [[0,0,0,0],[0,0,0,0],[0,0,1,0],[0,0,0,0]],
    [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,1]]
  ]
}
```
