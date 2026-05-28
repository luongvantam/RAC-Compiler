# RAC COMPILER — USAGE GUIDE

---

## OVERVIEW
**RAC Compiler** is a specialized source code compiler and assembler designed to develop, optimize, and package machine code for embedded systems, emulation environments, or scientific calculators (such as the fx-580VN X). This document details the syntax, directives, control flow, and extension architecture of the RSC language.

🇻🇳 Nếu bạn là người Việt Nam, vui lòng chuyển sang [Guide.vi.md](Guide.vi.md) để xem hướng dẫn bằng tiếng Việt.

---

## PART I: BASIC SYNTAX & DATA STRUCTURES

### 1. Comments
Comments help annotate code algorithms or temporarily disable code blocks during debugging. RAC supports both single-line and multi-line notation:

* **Single-line Comment:** Starts with `#`. The compiler ignores all subsequent text on that line.
* **Multi-line Comment:** Starts with `/*` and ends with `*/`. Useful for block descriptions or documentation.

```assembly
# This is a single-line comment for quick notes
/*
   This is a multi-line comment block.
   The RAC compiler will ignore everything enclosed 
   until the closing token is reached.
*/

```

### 2. Variables & Registers

RAC distinguishes between compile-time variables and runtime hardware or structural registers.

* **`var`:** Declares a variable supporting Integers, Hexadecimals, and Strings. Reference the variable directly by its name.
* **`reg`:** Allocates or modifies physical/virtual destination architecture registers.

```assembly
var count = 10         # Decimal integer variable
var hexval = 0x1A2B    # Hexadecimal variable
var message = "Test"   # String variable

reg r1 = 0x5           # Initialize register r1 with 0x5
r2 = 0xFF              # Direct assignment to register r2

```

### 3. String Handling

RAC supports string literals with **String Interpolation** using the `{variable_name}` syntax.

* **Special Rule:** Due to the internal tokenizer structure, spaces (` `) inside strings must be replaced with a tilde (`~`). During compilation, `~` is automatically evaluated back into a standard space character (`0x20`).

```assembly
var ten = "World"
"Xin~chào,~{ten}!"  # Compiled output string: "Xin chào, World!"

```

### 4. Arrays / Lists

Data collections can be represented using multi-line blocks or condensed into single-line statements.

```assembly
# Method 1: Multi-line array declaration
[
  0x1
  0x2
]

# Method 2: Inline array declaration (elements separated by semicolons `;`)
[0x1; 0x2]

```

### 5. Token Sequence (Token Strings)

Enclosing an expression in single quotes `'...'` defines a raw token sequence. The RAC parser preserves this structure intact for evaluation by specific macro processors or math expression engines.

```assembly
'sin( 9 0 )' # Token sequence for custom arithmetic parsing

```

---

## PART II: CONTROL FLOW & FUNCTION DEFINITIONS

### 6. Labels

Labels mark absolute or relative positions within the source file, allowing branches, jumps, and calls to reference memory locations without manual byte offset calculations.

* **Syntax:** `lbl <label_name>`

```assembly
lbl start
  call 0x1234  # Invoke subroutine at absolute address 0x1234
  goto end     # Unconditional jump to 'end'

lbl end        # Execution target destination

```

### 7. Calls & Jumps

Primary control flow commands redirect execution context to concrete locations, API hooks, or internal subroutines.

* **`call <address / function_name>`:** Diverts execution to an address or a built-in macro block. Execution resumes at the next line once finished.
* **`goto <label_name>`:** Jumps immediately to the specified label inside the file.

```assembly
call 0x5678        # Calls subroutine at static target 0x5678
call line_print    # Calls a built-in routine named 'line_print'
goto start         # Infinite loop constraint back to 'start'

```

### 8. Compound Statements

Multiple statements can be written sequentially on a single line to keep source files compact. Statements are separated using a semicolon `;`.

```assembly
call 0x1234 ; goto end  # Executes call first, followed immediately by goto

```

### 9. Built-in Functions (RAC Functions)

Functions allow code modularity and parameterization. Functions accept parameters and parse string expansions or machine data blocks within curly braces `{}`.

```assembly
# Define function 'greet' with one parameter 'person'
func greet(person) {
  "Hello,~{person}!"
}

# Invoke the function with different arguments
greet("Alice")
greet("Bob")

```

---

## PART III: MEMORY MANAGEMENT & COMPILER DIRECTIVES

### 10. Origin Directive (`org`)

The `org` (Origin) directive defines the absolute memory base address where the generated binary blob is mapped and executed. This is critical for fixed-mapped firmware hooks or shellcode layout.

* **Syntax:** `org <Hex_Address>`

```assembly
org 0xe9e0  # Anchors the program execution entry point to memory location 0xE9E0

```

### 11. Raw Data Insertion

RAC allows developers to embed arbitrary binary contents or hexadecimal raw buffers directly into the compiled output. It supports Big-Endian and Little-Endian conventions.

* **Direct Hex (Big-Endian structural order):** Direct literal prefixing using `0x`.
* **Byte Array Stream (Little-Endian / Multi-byte strings):** Using the `hex` keyword followed by whitespace-separated byte groups.

```assembly
0x1234ABCD      # Injects a 4-byte raw double-word sequentially
hex CD AB 34 12 # Swapped layout stream injection (typical for architecture mapping)

```

### 12. Address Of Operation

Extract label address assignments and modify pointer targets programmatically using the `adr()` operator combined with static offset calculations via `eval()`.

* **`adr(label)`:** Returns the resolved location of `label`.
* **`eval(expression)`:** Performs compile-time evaluation on mathematical and pointer expressions.

```assembly
adr(main)               # Grabs static address representation of 'main'
eval(adr(loop) + 0x4)   # Extracts location pointer for 'loop' offset by +4 bytes

```

### 13. Phased Memory Blocks (Sections)

Memory can be chunked into isolated blocks using `@section` or `@set` scopes. This enables deploying detached initialization sections (like Launchers) alongside main applications in a single compilation pass.

```assembly
@set.main              # Context switch to the main program segment
org 0xe9e0             # Mapping origin point for main
hex 30 30 30 30

@set.launcher          # Defines and targets an independent launcher area
org 0xd180             # Static layout mapping for launcher segment at 0xD180
xr0 = hex 30 30 30 30  # Register assignment distinct to the launcher environment

```

### 14. Program Length Verification (`pr_length`)

The `pr_length` compiler constant evaluates the complete binary footprint size (in bytes) of the file and reflects that value directly onto the token's position.

```assembly
pr_length  # Replaced at compile-time by total generated binary byte-length size

```

---

## PART IV: OPTIMIZATION & EXTENSION SCHEMES

### 15. Compile-time Evaluation

Mathematical operations, bitwise actions, or pointer differences can be resolved during compilation using `eval()` or `calc()`. This removes processing overhead from the calculator runtime.

> 💡 **Note:** `eval()` and `calc()` are functional duplicates. You can use either keyword interchangeably based on style preference.

```assembly
eval(0x1 + 0x2 * 0x3)           # Returns 0x7 directly (honors operator precedence)
calc(adr(label1) - adr(label2)) # Measures byte-distance delta between two markers

```

### 16. Compile-time Loops (Repeat)

The `loop` sequence tells the compiler to replicate a block of commands or raw bytes multiple times during compilation, removing the need for manual copy-pasting.

* **Syntax:** `loop <count> { <data_or_statements> }`

```assembly
loop 4 {
  0x67  # Generates four repeating 0x67 bytes sequentially
}
hex 00 00  # appends padding array trailing the loop execution

```

### 17. Hardware Key Mapping (fx-580VN X target)

RAC integrates keycode layout mappings. Refer to `labels.txt` to access the full scan-code registry database.

```assembly
KEY_SHIFT   # Keycode constant mapping for the calculator SHIFT key
KEY_1       # Keycode constant mapping for number key 1
KEY_ADD     # Keycode constant mapping for addition operational key (+)

```

### 18. Custom Syntax Extensions

RAC provides an open interface to define high-level abstractions, macros, and customized statement translations through an external `extensions.txt` file. Every layout definition follows a strict blocks map:

* `---syntax---`: Defines the keywords, parameters, and structural signature (enclosed in `{}`).
* `---output---`: Dictates the matching machine directives or RAC statements generated by the compiler core.

**Configuration Example (`extensions.txt`):**

```text
---syntax---
render_bitmap({x},{y},{w},{h},{addr_bitmap})
---output---
xr0 = {x}, {y}, {w}, {h}
render_bitmap
er0 = {addr_bitmap}
---

```

---

## PART V: DEPRECATION ARCHIVE & SAMPLES

### 19. Inline Python Integration (`def`) — [DEPRECATED / REMOVED]

> ⚠️ **SYNTAX WARNING:** The inline Python evaluation execution blocks previously supported within RAC source scripts **have been completely removed** in current versions. This segment remains for structural history tracking only.

```assembly
# Legacy invalid syntax structure:
def check_even_odd(n) {
  if n % 2 == 0:
    return 0x1
  else:
    return 0x0
}
py.check_even_odd(0x2)

```

### 20. Gadget Discovery Engine (`find_gadgets`) — [DEPRECATED / REMOVED]

> ⚠️ **SYNTAX WARNING:** The ROP (Return-Oriented Programming) gadget engine `find_gadgets` block **has been completely removed** from active RAC tooling releases. This segment remains for reference purposes only.

```assembly
# Legacy invalid syntax structure:
find_gadgets {
  mov er{a[1]}, er{b[1]}
  pop pc
}
# Legacy rule matching:
# {var}    : Matches registers ranging from index 0 to 15.
# {var[1]} : Matches registers ranging from index 0 to 9.

```

### 21. Full Compilation Example

Below is a standard program sample combining configuration rules, data definitions, string transformations, and macro calling constraints.

```assembly
org 0xe9e0                     # 1. Direct compilation base to address 0xE9E0

var name = "Nick"              # 2. String allocation (replaces whitespace with '~')

lbl main                       # 3. Code entry layout definition
  "Hello,~{name}!"             # 4. Evaluates variables using string interpolation
  call line_print              # 5. Direct program invocation to print the string data

```

> 💡 *For real-world proof-of-concept setups, explore advanced ROP implementations under the `rsc_ropchain/` directory.*

---

**Document Maintainer:** `luongvantam`