# MicroPy Compiler

A compiler for **MicroPy** — a simplified subset of Python designed for teaching and demonstrating core compiler construction concepts.

> ⚠️ **Current Status: Phase 1 Complete — Lexical Analysis (Scanner)**
> The parser, semantic analyser and code generator are under active development.

---

## What is MicroPy?

MicroPy is a mini programming language based on Python syntax. It was designed with a deliberate scope — powerful enough to demonstrate real compiler concepts, simple enough to implement fully within a semester.

A valid MicroPy program looks like this:

```mpy
num1 = int(input('enter first number'))
num2 = int(input('enter second number'))

if num1 == num2:
    print("the numbers are equal")
else:
    print(f"num1 is {num1} and num2 is {num2}")

while num1 < 10:
    num1 = num1 + 1

boolean_value = num1 == num2
print(boolean_value)
```

---

## File Extension

MicroPy uses its own file extension — **`.mpy`**

This clearly identifies MicroPy source files and distinguishes them from standard Python (`.py`) files. Example:

```
calculator.mpy
myprogram.mpy
```

---

## VS Code Syntax Highlighting

We have built and published a **dedicated VS Code syntax highlighter** for `.mpy` files — available for free on the Open VSX marketplace.

**Install it:**
1. Open VS Code or Windsurf
2. Go to Extensions `Ctrl+Shift+X`
3. Search **MicroPy**
4. Click **Install**

You will get full syntax highlighting for all MicroPy token types including keywords, strings, f-strings, numbers, booleans, operators and comments.

Or find it directly at:
```
open-vsx.org/extension/john-otieno-okello/micropy-syntax
```

---

## Language Features

### Token Types
| Token | Description | Examples |
|---|---|---|
| `KEYWORD` | Reserved words | `if`, `else`, `while`, `print`, `input`, `int` |
| `IDENTIFIER` | Variable names | `x`, `count`, `boolean_value` |
| `NUMBER` | Integer | `42` |
| `STRING` | Text in quotes | `"hello"`, `'world'` |
| `FSTRING` | Formatted strings | `f"value is {x}"` |
| `BOOLEAN` | Logical truth values | `True`, `False` |
| `OPERATOR` | Arithmetic symbols | `+`, `-`, `*`, `/` |
| `COMPARE_OP` | Comparison symbols | `==`, `!=`, `<`, `>`, `<=`, `>=` |
| `LOGICAL_OP` | Logical connectors | `and`, `or` |
| `ASSIGNMENT` | Assignment symbol | `=` |
| `DELIMITER` | Punctuation | `(`, `)`, `:`, `,` |

### Control Structures
- `if / else` — conditional branching
- `while` — loop repetition

### Expression Types
- **Arithmetic expressions** — e.g. `x + y * 2`
- **Logical/Boolean expressions** — e.g. `flag and count == 5`

### Built-in Functions
- `print()` — output to console
- `input()` — read user input
- `int()` — convert to integer
---

## Project Structure

```
micropy/
├── main.py                  ← entry point — run this
├── lexer/
│   ├── __init__.py
│   ├── token.py             ← Token class, TokenType enum, reserved words
│   └── lexer.py             ← Lexer/Scanner — full lexical analysis
├── parser/                  ← coming in subsequent phases
│   └── __init__.py
├── semantic/                ← coming in subsequent phases
│   └── __init__.py
├── codegen/                 ← coming in subsequent phases
│   └── __init__.py
├── utils/
│   ├── __init__.py
│   └── error_handler.py     ← centralised error reporting
└── samples/
    └── calculator.mpy       ← default sample MicroPy program for testing
```

---

## Phase 1 — Lexical Analysis (Scanner) 

The scanner is the first phase of the compiler. It reads raw MicroPy source code character by character and converts it into a stream of classified tokens.

### How it works

```
Raw Source Code  →  Lexer  →  Token Stream
"x = 42 + y"         ↓
                IDENTIFIER  x
                ASSIGNMENT  =
                NUMBER      42
                OPERATOR    +
                IDENTIFIER  y
```

### Features of the Scanner
- ✅ Recognises all 11 token types
- ✅ Handles both single `'` and double `"` quoted strings
- ✅ Handles f-strings with `{variable}` expressions inside
- ✅ Handles single and multi-character operators (`=` vs `==`, `<` vs `<=`)
- ✅ Tracks line numbers for every token — used in error messages
- ✅ Handles indentation — emits `INDENT` and `DEDENT` tokens for block tracking
- ✅ Skips comments — everything after `#` is ignored
- ✅ Centralised error reporting — unknown characters are reported with line numbers
- ✅ Handles decimal numbers — `3.14`, `0.5`

### Indentation Handling
Unlike most languages that use `{ }` for blocks, MicroPy follows Python's indentation style. The scanner automatically generates `INDENT` and `DEDENT` tokens when indentation increases or decreases:

```mpy
if x > 5:
    print(x)    ← INDENT token generated here
print("done")   ← DEDENT token generated here
```

---

## Installation and Usage

### Requirements
- Python 3.8 or higher
- No external libraries needed — uses only the Python standard library

### Running the compiler

```bash
# Clone the repository
git clone git clone git@github.com:John-hack321/micropy.git
cd micropy

# Run on the default sample program
python main.py

# Run on your own .mpy file
python main.py samples/calculator.mpy

# Run on any custom file
python main.py path/to/yourprogram.mpy
```

### Sample Output

```

  TOKEN TYPE     | VALUE                               | LINE
  ────────────────────────────────────────────────────────────
  IDENTIFIER     | 'num1'                              | 1
  ASSIGNMENT     | '='                                 | 1
  KEYWORD        | 'int'                               | 1
  DELIMITER      | '('                                 | 1
  KEYWORD        | 'input'                             | 1
  ...


```

---

## Roadmap

| Phase | Description | Status |
|---|---|---|
| **Phase 1** | Lexical Analysis — Scanner |  Complete |
| **Phase 2** | Syntax Analysis — Parser |  Coming soon |
| **Phase 3** | Semantic Analysis | Coming soon |
| **Phase 4** | Code Generation |  Coming soon |

---

## Authors

Built by **Group 22** as part of a Compiler Construction course project.

| Name | Admission Number |
|---|---|
| John Otieno Okello | SCS3/2286/2023 |
| Marxeem Nyambura | SCS3/2607/2022 |
| Taha Karimjee | SCS3/146721/2023 |
| Collins Upendo | P15/136859/2019 |

---