# RAC COMPILER — USAGE GUIDE

🇻🇳 [Guide.vi.md](Guide.vi.md)

---

## 1. Comments
* **Syntax:**
  - `# <comment>`
  - `/* <comment> */`

```assembly
# Single-line comment
/* 
   Multi-line 
   comment 
*/
```

## 2. Variables & Registers
* **Syntax:**
  - `var <var> = <value>`
  - `reg <reg> = <value>`
  - `<reg> = <value>`
  - `<var> = <value>`
* **Call / Recall:**
  - `<name_var>` (e.g., `a`, `b`, `c`, `var`)

```assembly
var count = 10         # Declares count variable
reg r1 = 0x5           # Initializes register r1
r2 = 0xFF              # Directly assigns to r2
count = 20             # Re-assigns variable count
count                  # Recalls/evaluates count
```

## 3. Data Types & String Handling
* **Syntax:**
  - Integer / Hex: `<int(hex)>` (e.g., `0x02`, `10`) or `hex <int(hex)>`
  - Strings:
    - `"<string>"` (use `~` to represent spaces, e.g., `"hello~world"`)
    - `"<f-string>"` (e.g., `"hello {name}"`)
    - `'<token string>'` (keeps structure intact for math engines)
    - `str "<string>"` (compiles raw string)
    - `str <var> "<var_string>"` (declares string variable)
    - `str <var>` (recalls string variable value)
  - Arrays / Lists:
    - `[<item>; <item>; ...]` (inline)
    - Multi-line block:
      ```assembly
      [
          <item>
          <item>
      ]
      ```
  - Memory Metrics:
    - `pr_length` / `sizeof()` (size of current section)
    - `sizeof(<section>)` (size of specified section)
    - `dist.<section>` (byte distance between org and backup)
    - `pr_org(<section>)` (origin address of the specified section)
    - `pr_backup(<section>)` (backup address of the specified section)

```assembly
var ten = "World"
"Xin~chào,~{ten}!"        # Interpolation with spaces: "Xin chào, World!"
'sin( 9 0 )'              # Token string
str greeting "Hi"         # String variable
str greeting              # Compiles "Hi"
[0x1; 0x2]                # Inline list
[                         # Block list
  0x3
  0x4
]
var size = sizeof(main)
var delta = dist.launcher
```

## 4. Aliases
* **Syntax:**
  - `<var/reg/gadget/label/...> as <new_name>`
  - `@section.<old_name> [at <addr_org> backup <addr_backup>] as <new_name>`
  - `@set.<old_name> [at <addr_org> backup <addr_backup>] as <new_name>`

```assembly
er0 as tmp
tmp = 0x1200                             # Compiles to: er0 = 0x12

@section.init at 0x1000 backup 0x2000 as start
```

## 5. Labels & Jump
* **Syntax:**
  - Declaration:
    - `lbl <label>`
    - `<label>:`
  - Address Retrieval:
    - `adr(<label>)`
    - `adr(<label>, <offset>)`
    - `adr(<label>, <offset>, <base_addr>)`
    - `adr($)` (gets the current address of this line)
    - `adr_of <label>`
    - `adr_of [<offset>] <label>`
    - `adr_of [<offset>][<base_addr>] <label>`
  - Jump:
    - `goto <label>` (expands to: `er14 = adr(<label>, -2); sp = er14, pop er14`)

```assembly
lbl start
# or:
start:
  goto end

lbl end
  var addr1 = adr(start)
  var addr2 = adr_of [-2][0x8000] end
```

## 6. Calls & Gadgets
* **Syntax:**
  - `call <address/function_name>`
  - `def <gadget> : <address>` (defines gadget into command_dict)
  - `def {<tag>} <name_gadget>: <address>`

```assembly
def my_gadget : 0x17b34
call my_gadget
call 0x1234
def {memcpy} memcpy_auto_jmp: 0x12345
```

## 7. Compound Statements
* **Syntax:** `<statement1> ; <statement2> ; ...`

```assembly
call 0x1234 ; goto end
```

## 8. Dynamic Macros
* **Syntax:**
  - Single-line: `def <macro_name>(<args>) => <single_line_expr>`
  - Block form: `def <macro_name>(<args>) => { <block_of_code> }`

```assembly
def add_hex(<val1>, <val2>) => eval(<val1> + <val2>)

def my_macro(<addr>, <val>) => {
    er0 = <addr>
    er2 = <val>
}
```

## 9. Functions
* **Syntax:**
  - Multi-line block:
    ```assembly
    func <function>(<args>) {
        <code>
    }
    ```
  - Standalone call: `<function>(<args>)`
  - Single-line return (can be assigned to variables/registers):
    `func <function>(<args>) { return <expression> }`

```assembly
func greet(person) {
  "Hello,~{person}!"
}
greet("Alice")

func add(x, y) { return x + y }
r1 = add(5, 10)
```

## 10. Location & Alignment Directives
* **Syntax:**
  - `org <addr_org>` (sets mapping origin address; skip if using `@set` inline `at`)
  - `backup <addr_backup>` (sets backup storage address)

```assembly
org 0xe9e0
backup 0xd000
```

## 11. Phased Memory Blocks (Sections)
* **Syntax:**
  - `@section.<section> [at <addr_org> backup <addr_backup>]`
  - `@set.<section> [at <addr_org> backup <addr_backup>]`

```assembly
@set.main at 0xe9e0 backup 0xf000
0x1234

@section.launcher at 0xd180
r1 = 0x5
```

## 12. Build Configuration (`@build`)
* **Syntax:**
  - Block form:
    ```assembly
    @build {
        emu.inj = <true|false>
        emu.inj_file = "<file_name>"
        emu.inj_var = "<name_var>"
        emu.inj_adr[<section>] = <address>
        line.bytes = <count>
        output.file = <true|false>
        output.file_name = "<file_name>"
    }
    ```
  - Inline form: `@build <key> = <value>; ...;`

```assembly
@build {
    emu.inj = true
    emu.inj_file = "payload.txt"
    emu.inj_var = "payload"
    line.bytes = 16
    line.gadgets = 0x30300000
    output.file = true
    output.file_name = "build_output.txt"
}
```

## 13. Compile-Time Evaluation & Arithmetic
* **Syntax:**
  - `eval(<expression>)`
  - `calc(<expression>)`
  - `adr_arith <label1> <+/-> adr_arith <label2> ...`
  - `adr_arith [<offset1>] <label1> <+/-> adr_arith [<offset2>] <label2> ...`

```assembly
eval(0x1 + 0x2 * 0x3)                     # Evaluates to 0x7
calc(adr(label1) - adr(label2))
adr_arith start - adr_arith end
adr_arith [+4] start - adr_arith [-2] end
```

## 14. Compile-Time Loops & Padding
* **Loops:**
  - `loop <range> { <code> }`
  - `repeat <range> { <code> }`
* **Padding:**
  - `fill(<count>, [<value>])`: Fills `<count>` bytes with `<value>` (default 0).
  - `align(<size>, [<value>])`: Pads bytes until the address is a multiple of `<size>`.
  - `pad(<offset>, [<value>])`: Pads bytes until the section length reaches `<offset>`.
  - `pad_abs(<address>, [<value>])`: Pads bytes until the absolute address reaches `<address>`.

```assembly
loop 4 {
  0x67
}

fill(16, 0xFF)
align(4)
pad(0x100, 0x00)
```

## 15. Embedded Python Scripting
* **Syntax:** `@python { <python_code> }`
* Allows executing Python code directly during compilation. Variables can be injected into the compiler environment (`loader.vars_dict`).

```assembly
@python {
    # Complex Python logic
    loader.vars_dict["calculated_val"] = 0x1234 * 2
}
var my_val = calculated_val
```

## 16. Line Continuation & Multi-line
* **Syntax:**
  - Use `\` at the end of a line to continue a raw statement.
  - Parentheses `()`, brackets `[]`, or braces `{}` automatically support multi-line without `\`.

```assembly
hex 30 \
31

eval(
    0x01 + 0x02
)
```

## 17. Hardware Key Mapping (fx-580VN X target)
* Traverses standard scan-code labels defined in `labels.txt`.

```assembly
KEY_SHIFT
KEY_1
KEY_ADD
```

---

**Document Maintainer:** `luongvantam`