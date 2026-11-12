# Agent guidance for rc2tools

Repository conventions for anyone (human or agent) changing this project.

## Testing

- Run the full suite with `python3 -m unittest discover -s tests` (about 40 seconds).
- Run only the smallest set that covers a change, for example `python3 -m unittest tests.test_rc2t_hack tests.test_rom_io tests.test_rom_stats`.
- Run tests from the repository root. Test modules import `tests.support`, so running a file directly with `python3 tests/x.py` fails.
- Documentation-only changes need no test run.
- If a command fails in this environment, don't rerun it unchanged later in the same session. Report your best assessment of the root cause to the user. Then either wait for them to fix the environment or continue without rerunning it, as they direct.

## Test helpers

- Shared helpers live in `tests/support.py`. Use them instead of local copies:
  - `load_bin_module(name)` loads `bin/<name>.py` without touching `sys.modules`.
  - `blank_rom(fill=0x00, header=False)` returns a `ROM_SIZE` bytearray. Pass `header=True` to add the title and the header bytes that `read_rom` validates.
  - `copy_tool_tree(root)` copies `rc2t`, `rc2h`, and all `bin/*.py` into a temp directory for the CLI tests. New `bin/` modules need no copy-list edits.

## Code conventions

- Use `bin/rom_io.py` for ROM reads (`read_rom`), hex/offset parsing (`parse_hex_dump`, `parse_offset`), and the `ROM_SIZE`/`BANK_SIZE` constants. Use `bin/tiles.py` for the 2bpp tile codec. Don't reimplement either in a tool.
- To add a new art set for `dump-art` and `inject-art`, register a `(render, apply)` pair in `ART_HANDLERS` in `bin/hack_rom.py`. Don't add new name checks to `dump_art` or `read_art`.
- Keep `render-graphics --highlight-known` ranges in sync with the documented graphics, glyphs, and tables in `docs/rom-map.md`.
- Comment code only where it needs clarification.

## Dependencies and legal

- Prefer the standard library and in-repo code. Before adding an external dependency, check whether the needed functionality can be reimplemented in the repo without excessive effort or complexity. If it can, reimplement it.
- Pillow is the accepted image dependency. It provides JPEG output and the default label font, so don't remove it without asking the user.
- Any new dependency, external reference, or third-party material must be added to the "Third-party tools and references" section of [LEGAL.md](LEGAL.md) in the same change. Update the "Requirements and dependencies" section of [README.md](README.md) when a runtime requirement changes.
- Don't commit raw long-form game content: no dialogue, story text, long strings, large sections of disassembled code, or graphics dumped from the ROM. Short strings such as character names, menu labels, and place names are fine.
- For content that isn't committed, document how to re-derive it with `rc2t` from a legally acquired copy of the ROM. Generated output belongs in the gitignored `output/` or `working/` folders.

## Repository hygiene

- Put throwaway ROM trace and analysis scripts in the gitignored `scratch/` folder (for example `scratch/rom-trace/`), not in `/tmp` or tracked paths.
- `working/` and `output/` are gitignored generated output. Don't commit them.
- Use `git --no-pager` in commands. Plain `grep -r` also searches `__pycache__`, so prefer `git --no-pager grep` for tracked files.
- Do not commit unless the user explicitly asks you to.

## Documentation

- The README is a high-level overview of functionality. Don't document layout details that users can see by running a command (such as the exact sprite grid or stat array format). Do not update it to include references to changes to tools between versions, or internal implementation details.
- Keep `docs/rom-map.md` current when ROM addresses, tables, or graphics change.

