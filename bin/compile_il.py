#!/usr/bin/env python3
"""Expand named routines and values into an assembly listing."""

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent
NAME = r"[A-Za-z_][A-Za-z0-9_]*(?:[ \t]+[A-Za-z_][A-Za-z0-9_]*)*"
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
SIGNATURE = re.compile(rf"({NAME})\s*\(([^()]*)\)\s*\Z")
PLACEHOLDER = re.compile(r"\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}")
DIRECTIVE = re.compile(r"@(function|end|call|const|var|let|set)\b", re.IGNORECASE)
ASSIGNMENT = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)\Z")
NUMBER = re.compile(r"[+-]?(?:\$[0-9A-Fa-f]+|0[xX][0-9A-Fa-f]+|[0-9]+)\Z")
COMMENT = re.compile(r';(?=(?:[^"]*"[^"]*")*[^"]*$)')
MAX_DEPTH = 100


class Routine(NamedTuple):
    parameters: tuple[str, ...]
    body: list[tuple[int, str]]


def parse_signature(text: str, line_number: int) -> tuple[str, list[str]]:
    match = SIGNATURE.fullmatch(text.strip())
    if not match:
        raise ValueError(f"line {line_number}: expected a name followed by parentheses")
    name = " ".join(match.group(1).split())
    arguments = [item.strip() for item in match.group(2).split(",")] if match.group(2).strip() else []
    if any(not item for item in arguments):
        raise ValueError(f"line {line_number}: empty parameter or argument")
    return name, arguments


def parse_assignment(text: str, line_number: int) -> tuple[str, str]:
    match = ASSIGNMENT.fullmatch(text.strip())
    if not match or not match.group(2).strip():
        raise ValueError(f"line {line_number}: expected a name and value separated by '='")
    return match.group(1), match.group(2).strip()


def compile_source(source: str) -> str:
    """Expand directives; leave all other assembly text unchanged."""
    routines: dict[str, Routine] = {}
    program: list[tuple[int, str]] = []
    current_name = None
    parameters: tuple[str, ...] = ()
    body: list[tuple[int, str]] = []
    definition_line = 0
    declared_names: set[str] = set()

    for line_number, line in enumerate(source.splitlines(keepends=True), 1):
        code = line.split(";", 1)[0].strip()
        directive = DIRECTIVE.match(code)
        keyword = directive.group(1).lower() if directive else ""
        if keyword == "function":
            if current_name is not None:
                raise ValueError(f"line {line_number}: nested function definition")
            name, args = parse_signature(code[directive.end():], line_number)
            if name in routines:
                raise ValueError(f"line {line_number}: duplicate function {name!r}")
            if any(not IDENTIFIER.fullmatch(arg) for arg in args) or len(set(args)) != len(args):
                raise ValueError(f"line {line_number}: invalid or duplicate parameter")
            current_name, parameters, body, definition_line = name, tuple(args), [], line_number
        elif keyword == "end":
            if code[directive.end():].strip() or current_name is None:
                raise ValueError(f"line {line_number}: unexpected or malformed @end")
            routines[current_name] = Routine(parameters, body)
            current_name = None
        elif current_name is not None:
            if keyword in ("const", "var", "let"):
                raise ValueError(f"line {line_number}: declarations must be outside functions")
            body.append((line_number, line))
        else:
            if keyword in ("const", "var", "let"):
                name, _ = parse_assignment(code[directive.end():], line_number)
                declared_names.add(name)
            program.append((line_number, line))

    if current_name is not None:
        raise ValueError(f"line {definition_line}: function {current_name!r} has no @end")

    for routine in routines.values():
        for line_number, line in routine.body:
            for placeholder in PLACEHOLDER.findall(line):
                if placeholder not in routine.parameters and placeholder not in declared_names:
                    raise ValueError(f"line {line_number}: unknown parameter or name {placeholder!r}")

    symbols: dict[str, tuple[str, str]] = {}

    def substitute(text: str, values: dict[str, str], line_number: int) -> str:
        def replace(match: re.Match) -> str:
            name = match.group(1)
            if name in values:
                return values[name]
            if name in symbols:
                return symbols[name][1]
            raise ValueError(f"line {line_number}: undefined name {name!r}")

        return PLACEHOLDER.sub(replace, text)

    def expand(lines: list[tuple[int, str]], values: dict[str, str], stack: tuple[str, ...]) -> list[str]:
        output = []
        for line_number, original in lines:
            if stack:
                line = substitute(original, values, line_number)
            else:
                parts = COMMENT.split(original, maxsplit=1)
                line = substitute(parts[0], values, line_number)
                if len(parts) == 2:
                    line += ";" + parts[1]
            code, separator, comment = line.partition(";")
            directive = DIRECTIVE.match(code.strip())
            keyword = directive.group(1).lower() if directive else ""
            if keyword in ("const", "var", "let", "set"):
                name, value = parse_assignment(code.strip()[directive.end():], line_number)
                if keyword == "set":
                    if name not in symbols:
                        raise ValueError(f"line {line_number}: undefined name {name!r}")
                    if symbols[name][0] != "let":
                        raise ValueError(f"line {line_number}: {name!r} is not a compile-time variable")
                elif name in symbols:
                    raise ValueError(f"line {line_number}: duplicate name {name!r}")
                if keyword in ("const", "var") and not NUMBER.fullmatch(value):
                    raise ValueError(f"line {line_number}: {keyword} requires a numeric value")
                if keyword == "var":
                    if value.startswith("-"):
                        raise ValueError(f"line {line_number}: variable address must be in 0..$FFFF")
                    unsigned = value.lstrip("+")
                    try:
                        address = int(unsigned[1:], 16) if unsigned.startswith("$") else (
                            int(unsigned, 16) if unsigned.lower().startswith("0x") else int(unsigned)
                        )
                    except ValueError as error:
                        raise ValueError(f"line {line_number}: invalid variable address") from error
                    if not 0 <= address <= 0xFFFF:
                        raise ValueError(f"line {line_number}: variable address must be in 0..$FFFF")
                    value = unsigned
                symbols[name] = ("let" if keyword == "set" else keyword, value)
                continue
            if keyword != "call":
                output.append(line)
                continue
            name, args = parse_signature(code.strip()[directive.end():], line_number)
            if name not in routines:
                raise ValueError(f"line {line_number}: unknown function {name!r}")
            routine = routines[name]
            if len(args) != len(routine.parameters):
                raise ValueError(
                    f"line {line_number}: {name!r} expects {len(routine.parameters)} "
                    f"arguments, got {len(args)}"
                )
            if name in stack:
                raise ValueError(f"line {line_number}: recursive function call: {' -> '.join((*stack, name))}")
            if len(stack) >= MAX_DEPTH:
                raise ValueError(f"line {line_number}: function nesting exceeds {MAX_DEPTH}")
            if separator:
                output.append(f";{comment}" if comment.endswith(("\n", "\r")) else f";{comment}\n")
            output.extend(expand(routine.body, dict(zip(routine.parameters, args)), (*stack, name)))
        return output

    return "".join(expand(program, {}, ()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="intermediate-language source file")
    parser.add_argument("output", nargs="?", type=Path, help="assembly output path")
    args = parser.parse_args(argv)
    output = args.output or ROOT / "output" / f"{args.input.stem}.asm"
    try:
        if args.input.resolve() == output.resolve():
            raise ValueError("input and output must be different files")
        with args.input.open(encoding="utf-8", newline="") as source:
            assembly = compile_source(source.read())
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".rc2t-compile-", dir=output.parent) as directory:
            temporary_output = Path(directory) / "output.asm"
            with temporary_output.open("w", encoding="utf-8", newline="") as target:
                target.write(assembly)
            os.replace(temporary_output, output)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
