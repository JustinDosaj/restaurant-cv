# Python Standards

Authoritative rules for Python **language** usage (3.11+, fully type-hinted). Each rule has a stable `PY.*` ID cited by the review skills (`/audit`, `/doc-drift`); this file owns them.

> One directive + a tiny good/bad. Ruff owns formatting — line length, quotes, indentation, import sorting, trailing commas — never a rule here.

---

## Typing & `Any`

- **PY.TYPE-HINTS** — Every function signature is fully annotated: all params and the return type (`-> None` included). Locals only when inference fails or a hint aids the reader.
- **PY.STRICT** — The type checker runs strict; never loosen its config or per-file settings to make code pass.
- **PY.NO-ANY** — Never `Any`. Take `object` and narrow with `isinstance`, or define a real type. `Any` disables checking silently everywhere the value flows.
  ```py
  def parse_conf(value: object) -> float:
      if not isinstance(value, (int, float)):
          raise TypeError(f"confidence must be numeric, got {type(value).__name__}")
      return float(value)
  ```
- **PY.NO-TYPE-IGNORE** — Never bare `# type: ignore`. If a suppression is unavoidable, scope it to the error code + a one-line reason: `# type: ignore[arg-type]  # ultralytics stubs lag the runtime API`.
- **PY.MODERN-HINTS** — Modern hint syntax only: builtin generics and `|` unions; never `typing.List`, `Optional`, `Union`, `Dict`.
  ```py
  def load_zones(path: Path) -> dict[str, Zone] | None: ...   # Good
  def load_zones(path: Path) -> Optional[Dict[str, Zone]]: ...  # Bad
  ```
- **PY.EXPLICIT-NONE** — A param defaulting to `None` says so in its hint (`limit: int | None = None`); no implicit-Optional.
- **PY.PREFER-NARROW** — Prefer `isinstance`/`TypeGuard` narrowing over `cast()`: a cast asserts, a check verifies. `cast()` only at a validated boundary, with the check adjacent.

## Data shapes

- **PY.DATACLASS** — Structured data crossing a function boundary is a frozen `@dataclass` (or pydantic model where validation is needed), never a bare dict or positional tuple.
  ```py
  @dataclass(frozen=True, slots=True)
  class Zone:
      table_id: str
      polygon: list[tuple[float, float]]
      capacity: int
  ```
- **PY.TYPED-BOUNDARY** — Raw external data (JSON config, API payloads) is parsed into a typed shape (`TypedDict`, dataclass, pydantic) at the boundary; `dict[str, Any]` never travels past it.
- **PY.ENUM** — Closed sets of values are a `StrEnum` (serializes as its string, so it doubles as data), not bare string literals scattered through the code. Members are UPPER_CASE.
  ```py
  class TableState(StrEnum):
      EMPTY = "empty"
      SEATED = "seated"
  ```
- **PY.SINGLE-SOURCE** — Never hand-write a second shape that mirrors an existing model/schema; derive it or reuse it so it can't drift.

## Naming

- **PY.NAME-CASE** — snake_case for functions, variables, params, modules; PascalCase for classes and enums; SCREAMING_SNAKE_CASE for module-level constants (`FOOT_POINT_OFFSET`).
- **PY.BOOL-NAME** — Prefix booleans (vars and returns) with `is_`/`has_`/`can_`/`should_`.
- **PY.PRIVATE-UNDERSCORE** — One leading underscore marks module/class internals (`_clamp_box`); no double-underscore name mangling for privacy.
- **PY.NO-SHADOW** — Never shadow builtins (`id`, `type`, `list`, `input`, `filter`); pick a real name (`track_id`, not `id`).
- **PY.DESCRIPTIVE-NAME** — Names reveal intent and scale with scope — `p` is fine inside a 2-line comprehension, exports get full words; no cryptic abbreviations.

## Idioms & control flow

- **PY.IS-NONE** — Compare to `None` (and `True`/`False`, when you must) with `is`/`is not`, never `==`.
- **PY.TRUTHINESS** — Test emptiness by truthiness (`if detections:`), but write `is None` explicitly whenever `None` means something different from empty/`0`.
  ```py
  if not detections: return          # Good — empty check
  if capacity is None: ...           # Good — 0 is a valid capacity
  ```
- **PY.FSTRING** — f-strings for all interpolation, never `%` or `.format()`. One exception: `logging` calls pass lazy args (`logger.info("table %s at %d", tid, n)`) so formatting is skipped when the level is off.
- **PY.LOGGING** — `logging` module in pipeline/library code, never `print()`; `print` is fine only in one-off scripts and CLI output.
- **PY.PATHLIB** — `pathlib.Path` for all path work; no `os.path` string surgery, and path-taking functions accept `Path`.
- **PY.WITH-RESOURCES** — Every resource with a lifetime (files, `cv2.VideoCapture`, connections, locks) is acquired via `with`/a context manager — never left to the garbage collector to release.
- **PY.COMPREHENSION** — Prefer comprehensions/generator expressions over `map`/`filter`/accumulator loops — until nesting hurts readability; a nested comprehension becomes a `for` loop.
- **PY.NO-UNUSED** — No unused variables or imports. Name an intentionally-unused value `_` (`for _ in range(3)`).

## Functions

- **PY.KWONLY** — For 3+ params, and for **every** boolean flag, force keywords with `*` so call sites stay readable; never a bare `True, False` positional pair.
  ```py
  def render(frame: Frame, *, draw_boxes: bool = True, draw_zones: bool = False): ...
  render(frame, draw_boxes=False)   # Good
  render(frame, False, True)        # Bad — illegal under this signature, by design
  ```
- **PY.NO-MUTABLE-DEFAULT** — Never a mutable default arg (`[]`, `{}`, `set()`); default to `None` and create inside, or use `field(default_factory=...)` in dataclasses.
  ```py
  def collect(records: list[Record] | None = None) -> list[Record]:
      records = records if records is not None else []
  ```
- **PY.RETURN-SHAPE** — A function returns one shape; if a no-result case exists, it's `| None` (or raises) per the hint — never `False`/`-1`/`""` sentinels.
- **PY.GENERATOR-STREAM** — Yield from frame/record streams instead of accumulating whole lists in memory; return a list only when the caller genuinely needs one materialized.

## Errors & exceptions

- **PY.NARROW-EXCEPT** — Catch the narrowest exception that can occur; never bare `except:`, and `except Exception:` only at a top-level loop boundary that logs and continues (e.g., keep the pipeline alive across a bad frame).
- **PY.NO-SILENT-PASS** — Never `except ...: pass`. Swallowing must be a decision the reader can see: log it, or comment why ignoring is correct.
- **PY.EXC-CHAIN** — When translating an exception, chain it: `raise ZoneConfigError(f"bad polygon for {table_id}") from err` — never lose the original traceback.
- **PY.CUSTOM-EXC** — Domain failures raise project exceptions (subclassing one project base), so callers can catch ours without catching the world's.
- **PY.EAFP** — For races and I/O, act and catch (`try: path.read_text() except FileNotFoundError:`) rather than check-then-act; check-first (`if path.exists():`) is a TOCTOU bug waiting.

## Modules & imports

- **PY.IMPORT-TOP** — All imports at the top of the module. Exceptions (heavy optional deps, circular-import breaks) sit inside the function with a one-line why.
- **PY.NO-STAR** — Never `from module import *`; it hides provenance and breaks tooling.
- **PY.ABSOLUTE-IMPORT** — Absolute imports from the package root (`from restaurant_cv.zones import Zone`); relative imports only between siblings inside one subpackage.
- **PY.IMPORT-ORDER** — stdlib → third-party → local, blank line between groups (Ruff/isort enforces; don't fight it).
- **PY.MAIN-GUARD** — Every runnable script defines `main()` and calls it under `if __name__ == "__main__":` — importing a module must never execute work.
- **PY.NO-MUTABLE-GLOBALS** — No mutable module-level state (caches, counters, loaded models) mutated from functions; pass state explicitly or own it in a class.

## Comments & docs

Canonical policy: CLAUDE.md → **Comments policy** (docstring = the caller's contract; `#` = the maintainer's why). These are its citable PY-side enforcement.

- **PY.DOCSTRING-PUBLIC** — Every public function/class/module gets a docstring whose default is a **single summary line** — what it does, imperative mood. Types live in the signature; never restate them.
  ```py
  def foot_point(box: Box) -> tuple[float, float]:
      """Return the bottom-center of a bounding box, used for zone tests."""
  ```
- **PY.DOCSTRING-BUDGET** — Escalate past the summary only for a contract the signature can't express, one line each (Google style): `Args:` (semantics not evident from name + hint), `Returns:` (units, coordinate space, None cases), `Raises:`, one `Side effect:` line, one named cross-file invariant. Ceiling: summary + one line per item, never longer than the body. **Banned:** caller enumerations, design rationale, restating hints, re-explaining a canonical doc.
  ```py
  """Assign each detection to the zone containing its foot point.

  Returns:
      Mapping of table_id to detections; people outside every zone are dropped.
  """
  ```
- **PY.COMMENT-WHY** — Inline `#` (inside bodies, above module constants) explains **why** — a non-obvious constraint, workaround, or invariant — at the exact line, one sentence. A why lives in exactly one place, never duplicated into the docstring.
  ```py
  # Box centers drift into neighboring zones when people stand near tables (CLAUDE.md)
  point = foot_point(det.box)
  ```
- **PY.NO-DEAD-COMMENT** — Delete commented-out code and obsolete comments; git is the history. A stale comment that contradicts the code is worse than none.
