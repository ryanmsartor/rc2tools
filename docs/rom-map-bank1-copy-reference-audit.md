# Bank-1 Hero Sprite-Copy Reference Audit

This addendum records the static reference analysis for the copied Hero graphics at physical ROM offsets `0x5286-0x5585`. It focuses on whether the interior copied bytes are used from physical bank 1, rather than treating every CPU address in the switchable window as a physical offset.

## Addressing model

The ROM uses 16 KiB banks. CPU addresses `0x4000-0x7FFF` map to the currently selected ROM bank:

| Selected bank | CPU address `0x5382` maps to physical ROM offset |
|---|---:|
| 1 | `0x5382` |
| 5 | `0x15382` |

Consequently, a pointer value such as `0x5382` is not evidence that physical offset `0x5382` was read. The selected bank at the actual dereference must also be known. In the fixed window (`0x0000-0x3FFF`), CPU addresses correspond directly to physical offsets.

The bank-selection helpers relevant to this audit are:

| Helper | Effect |
|---|---|
| `CALL 0x0CD4` | Selects bank 1 while preserving the previous bank for the wrapper's restore path |
| `CALL 0x0D04` | Selects bank 5 |
| `CALL 0x0D3F` | Selects the bank number in `A`; used by some paths to restore the prior bank |
| `JP 0x0CCB` | Returns through the bank-restore path used by banked-call wrappers |

The copied data in physical bank 1 is aligned with the Hero graphics in bank 2, at a `0x4000` offset. See the parent section in [the ROM map](./rom-map.md#bank-1-copy-and-code-overlays) for the segment-by-segment sprite assignments and code overlays.

## Candidate data references resolved to bank 5

Instruction-shaped and pointer-shaped byte scans found many CPU values in the `0x52xx-0x55xx` range. The following code paths were traced far enough to resolve their reads to bank 5, not to the bank-1 copy:

| Fixed-bank code location | Pointer or address | Bank-state evidence |
|---|---:|---|
| `0x025F` and `0x0568` | `0x5382` | `0x025F` stores the pointer for later use. The reader at `0x0559` selects bank 5 before dereferencing it; the direct `0x0568` access is also after that selection. |
| `0x1D5C` | `0x5449` | The routine preserves the pointer, selects bank 5 at `0x1D77`, then consumes the pointed-to data. |
| `0x1EBD` | `0x53E1` | The helper is called at `0x1D90` while bank 5 is selected; the caller restores the previous bank afterward. |
| `0x1EE1`, `0x1EF4`, `0x1EFD` | `0x5459`, `0x5489`, `0x549B` | The path selects bank 5 at `0x1EDD`; the conditional path to the latter pointers remains in that bank. |
| `0x1FA5` | `0x53E1` | This is in a helper reached by callers that select bank 5 first. Call sites include `0x1EF1`, `0x1FF6`, `0x2024`, `0x25DC`, `0x2601`, `0x283C`, and `0x28C8`; each is in a bank-5-selected path. |
| `0x1FEE`, `0x1FF9` | `0x54AD`, `0x54CD` | The enclosing path selects bank 5 at `0x1FEB`. |
| `0x2018`, `0x2027` | `0x54DF`, `0x54FF` | The enclosing path selects bank 5 at `0x2015`. |
| `0x20A9` | `0x5511` | The enclosing path selects bank 5 at `0x20A6`. |
| `0x2166`, `0x2171` | `0x5541` | The enclosing path selects bank 5 at `0x2161`. |
| `0x300A`, `0x300F` | `0x5308`, `0x533F` | The enclosing path selected bank 5 at `0x2FD9`. |

A pointer table at physical bank-1 offset `0x4ACB` contains values including `0x5449`, `0x545B`, `0x54AE`, `0x54E0`, and `0x5512`. The fixed-bank table reader near `0x17FE` switches to bank 5 before dereferencing the values. These table entries therefore do not establish reads from the similarly addressed bank-1 sprite bytes.

The analysis also encountered byte sequences that decode as instructions if interpreted at arbitrary offsets. For example, an apparent `CALL NZ,0x539D` at bank-1 offset `0x460F` is part of data, not a confirmed executable call. Scanning raw little-endian words or opcode-shaped bytes alone produces false positives in graphics and other tables.

## Apparent call to `0x54EA` disproved

The bank-1 routine at `0x519D` is called from fixed-bank code at `0x0299E` after selecting bank 1. It calls the fixed-bank handler at `0x03DD`, which can call `0x14F9` at fixed-bank offset `0x0444`. This appeared to lead to a possible call into the copied sword-arc data, but instruction boundaries disprove that interpretation.

The bytes around the suspected call are:

```text
0x194A: 3E 19 CD 11 05 F0 CD EA 54 C1 C9
```

Decoding from the instruction boundary at `0x194A` gives:

```text
0x194A  LD A,0x19
0x194C  CALL 0x0511
0x194F  LDH A,(0xFFCD)   ; 0xCD is the immediate byte
0x1951  LD (0xC154),A
0x1954  RET
```

Thus `0x1950` is an operand byte, not an instruction boundary, and `0xCD` there is not a `CALL` opcode. The apparent `CALL 0x54EA` is a false positive from scanning for opcode bytes without decoding instruction boundaries. The bank-1 handler path therefore does not establish a control-flow reference to `0x54EA`.

## Conclusion and limits

- The traced data-pointer candidates resolve to bank 5. They are not evidence that the bank-1 copy is loaded as graphics.
- No confirmed graphics-loading path targeting the copied bank-1 sprites was found in this audit.
- The suspected call to CPU address `0x54EA` is not a real call. The traced references provide no evidence that the interior copy is read from physical bank 1.
- The code overlays at `0x5286-0x5290` and `0x5580-0x5585` are distinct from the interior copied graphics. The latter contains the two jump stubs to `0x55C0` and `0x55AA`; fixed-bank code calls `0x5580` and `0x5583`.
- Startup also selects bank 1 before calling `0x5586`, immediately after the analyzed interval.

The static evidence supports treating the copied interior sprite data (`0x5291-0x557F`) as unused by the game as graphics. This is a static-analysis conclusion, not proof against every possible indirect or data-driven access; a runtime trace would be needed for that stronger claim.
