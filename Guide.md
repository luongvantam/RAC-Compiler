# RAC Compiler — Usage Guide

🇻🇳 Nếu bạn là người Việt Nam, vui lòng chuyển sang [Guide.vi.md](Guide.vi.md) để xem hướng dẫn bằng tiếng Việt.

---

## 1. Comments

Use comments to annotate your code. RAC supports both single-line and multi-line comments.

```rsc
# This is a single-line comment
/*
   This is a multi-line
   comment block
*/
```

---

## 2. Directives

### org

Set the base address for code mapping.

```rsc
org 0xe9e0
```

---

## 3. Labels

Define a label for jumps or references.

```rsc
lbl start
  call 0x1234
  goto end
lbl end
```

---

## 4. Data Insertion

Insert raw hexadecimal data or reversed hex data.

```rsc
0x1234ABCD
hex CD AB 34 12
```

---

## 5. Calls & Jumps

Call an address or built-in function, or jump to a label.

```rsc
call 0x5678
call line_print
goto label
```

---

## 6. Address Of

Get the address of a label (optionally with offset).

```rsc
adr(main)
eval(adr(loop) + 0x4)
```

---

## 7. Program Length

Insert the current program length at this point.

```rsc
pr_length
```

---

## 8. String Handling

Insert strings with variable expansion using curly braces `{}`.

```rsc
var ten = "World"
"Xin~chào,~{ten}!"
```

**Note:** Use `~` to replace ` ` in strings.

---

## 9. Functions

Define reusable code blocks and call them with arguments.

```rsc
func greet(person) {
  "Hello,~{person}!"
}

greet("Alice")
greet("Bob")
```

---

## 10. Eval (Expression Evaluation)

Evaluate math or address expressions at compile time.

```rsc
eval(0x1 + 0x2 * 0x3)
eval(adr(label1) - adr(label2))
# We can use calc() instead of eval() because they have the same function.
```

---

## 11. Variables & Registers

Define variables (int, hex, string) and assign values to registers.

```rsc
var count = 10
var hexval = 0x1A2B
var message = "Test"
reg r1 = 0x5
r2 = 0xFF
```

The way to call a variable is `varname`, and the same applies to strings.

---

## 12. Compound Statements

Combine multiple statements in one line using `;`.

```rsc
call 0x1234 ; goto end
```

---

## 13. Key Mapping

Use key constants for fx580vnx (see key_map.txt for full list).

```rsc
KEY_SHIFT
KEY_1
KEY_ADD
```

---

## 14. Functions Python

Define a Python function, then call and use it.

```rsc
org 0xe9e0

def check_even_odd(n) {
  if n%2==0{
    return 0x1      # Even
  } else {
    return 0x0      # Odd
  }
}

py.check_even_odd(0x2)
py.check_even_odd(0x3)
```

---

## 15. Repeat

Repeat a block of code a fixed number of times at compile time.

```rsc
loop 4 {
  0x67
}
hex 00 00
```

---

## 16. Find_gadgets

Search for suitable gadgets.

```rsc
find_gadgets {
  mov er{a[1]}, er{b[1]}
  pop pc
}
```
Use {var} to specify a hypothetical variable with a value from 0 to 15, {var[1]} to specify a hypothetical variable from 0 to 9.

---

## 17. Section

Sections allow you to divide a file into multiple independent areas.

```rsc
@set.main
org 0xe9e0
hex 30 30 30 30

@set.launcher
org 0xd180
xr0 = hex 30 30 30 30
```

---

## 18. Extension System

You can define new syntax and macros via `extensions.txt`.

**Example extension syntax:**

```txt
---syntax---
print {msg}
---logic---
print(msg)
---output---
call print
```

---

## 19. Full Example

```rsc
org 0xe9e0
var name = "Nick"
lbl main
  "Hello,~{name}!"
```

---

Written by: luongvantam
