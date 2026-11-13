# Assembly intermediate language

The intermediate language passes ordinary assembly through unchanged and adds
named values and parameterized inline routines. For example:

```asm
@const starting_health = $42
@var player_health = $C000
@let current_value = {{starting_health}}

@function write health(value)
    LD A,{{value}}
    LD [{{player_health}}],A
@end

SECTION "example", ROM0[$0000]
    @call write health({{current_value}})
    @set current_value = $20
    @call write health({{current_value}})
```

Save this as `working/example.rc2asm`, then run:

```sh
./rc2t compile-il working/example.rc2asm
./rc2t recompile output/example.asm
```

`compile-il` writes `output/<source-basename>.asm` by default. Supply a second
path to choose another output. The input and output must be different files.
Compilation errors leave an existing output unchanged.

## Syntax and behavior

### Named values

- `@const name = value` defines an immutable numeric constant. Values may be
  decimal, `$`-prefixed hexadecimal, or `0x`-prefixed hexadecimal, with an
  optional sign. References to previously declared names are allowed if the
  result is numeric.
- `@var name = address` names an explicit 16-bit Game Boy address. It is an
  immutable address alias, not an allocated memory slot or an initial value.
  Use normal assembly instructions such as `LD A,[{{name}}]` or
  `LD [{{name}}],A` to read or write memory at runtime. The programmer must
  choose an appropriate, available address and handle memory banking.
- `@let name = value` defines a mutable compile-time substitution.
  `@set name = value` changes it for subsequent lines and calls; it does not
  emit runtime instructions or change Game Boy memory. Values are nonempty
  assembly text, resolved when the declaration or assignment is encountered.
- Names are case-sensitive identifiers made of letters, digits and underscores,
  starting with a letter or underscore. Use `{{name}}` to substitute a name
  into assembly, another value, or a call argument. Constants, address aliases,
  and compile-time variables share one namespace and must be declared before
  use. Values are inserted as written; the assembler checks whether they are
  valid for the instruction and operand. A leading `+` on an address alias
  is removed.
- Declarations must be outside functions. An `@set` inside a function changes
  the same global compile-time variable for subsequent expansions. A function
  parameter shadows a named value of the same name when substituted, but
  `@set` always modifies the global compile-time variable.
- References in ordinary top-level comments are left unchanged. References in
  function bodies, including comments, are substituted during expansion.
  An undeclared name is an error when used as a substitution.

### Routines

- Define routines with `@function name(parameters)` and `@end`. Names consist
  of one or more space-separated words; each word starts with a letter or
  underscore and continues with letters, digits or underscores. Names and
  parameters are case-sensitive. Parentheses are required even when empty.
- Parameters are comma-separated identifiers. Use `{{parameter}}` in a
  routine body to substitute the corresponding argument. Arguments are
  comma-separated, nonempty pieces of assembly text; they cannot contain
  commas, parentheses, semicolons or newlines.
- Invoke routines with `@call name(arguments)` on a line of its own. Calls may
  precede definitions and may occur inside other routines. Recursion and
  nested definitions are errors. Definitions are removed from the output;
  each call inserts a copy of the body, not a Game Boy `CALL` instruction.
  Comments following a call are retained. Calls in unused routines are not
  checked until those routines are expanded.
- Directive keywords are case-insensitive. An assembly semicolon starts a
  comment on a directive line. Normal assembly lines, including comments and
  `@+2` relative operands, are passed through except for substitutions.

Expansion does not adjust addresses, fix jumps, allocate free space, or update
ROM checksums. Replacing instructions with different-sized expansions may
shift code and break numeric targets or bank boundaries. Inspect the result
before reassembling. The compiler does not validate assembly syntax; the
existing `recompile` command checks its supported instructions and sections.
Other assembly dialects pass through but are not necessarily accepted by
`recompile`. Converting assembly back into routines is not supported.
