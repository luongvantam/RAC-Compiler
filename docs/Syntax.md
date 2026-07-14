# Notation

```
<...> : value to be replaced
[...] : optional
... : placeholder for something else
```

# alias

```
<var/reg/gadget/label/...> as <new_name>
<new_name>

@section.<old_name> [at ... backup ...] as <new_name>
# if using sizeof(<new_name>) it will automatically map to sizeof(<old_name>)
```

# define gadget

```
def {tag} <name_gadget>: <address>

example:
def {memcpy} memcpy_auto_jmp: 0x12345
```

# build (test)

```
@build {
    emu.inj = <true|false>
    emu.inj_file = "<file_name>"
    emu.inj_var = "<name_var>"
    emu.inj_adr[<section>] = <address>

    line.bytes = <hex_bytes_per_line>
    line.gadgets = <>

    output.file = <true|false>
    output.file_name = "<file_name>"

    # these lines can be optionally declared
}

# it can also be declared in a single line
@build ...; ...; ...;
```

# section

```
@section.<section> [at <addr_org> backup <addr_backup>]
@set.<section> [at <addr_org> backup <addr_backup>]
```

# set program location

```
org <addr_org>              # if you use `@set.<section> at <addr_org>` or `@section.<section> at <addr_org>`, then do not use this command.
backup <addr_backup>
```

# variable and register declaration

```
var <var> = <value>
reg <reg> = <value>
<reg> = <value>
<var> = <value>
```

# call variable

```
<name_var>      # like `a`, `b`, `c`, `var`, ...
```

# data type

```
<int(hex) like 0x02>
hex <int(hex)>

"<string>"
"<f-string (ex : "hello {name}")>"
'<token string>'

[
    <list>
    ...
    ...
]
[<list>;...;...]

pr_length               # length of section

dist.<section>          # distance backup to src
sizeof(<section>)       # like pr_length
```

# function

```
func <function>(<args>) {
    <code>
}
<function>(<args>)
```

```
# like `lambda <name>: <args> => <expression>`
func <function>(<args>) {
    return <expression>
}

# can be used to assign to a variable or register
# however, it must be on a single line
```

# repeat & padding

```
repeat <range> {
    <code>
}
loop <range> {
    <code>
}

fill(<count>, [<value>])        # fill <count> bytes with <value> (default 0)
align(<size>, [<value>])        # pad bytes until address is multiple of <size>
pad(<offset>, [<value>])        # pad bytes until section length reaches <offset>
pad_abs(<address>, [<value>])   # pad bytes until absolute address reaches <address>
```

# label

```
# label declaration
lbl <label>
lbl <label> at <address>
<label>:

# get the label address
adr(<label>)
adr(<label>, <offset>)
adr(<label>, <offset>, <base_addr>)
adr($)      # current address of this line

# jump to label
goto <label>            # it's `er14 = adr(<label>, -2); sp = er14, pop er14`
```

# call gadget

```
def <gadget> : <address>            # define a new gadget into command_dict
call <address/function_name>        # like `call 0x17b34`
```

# calculate

```
eval(<expression>)
calc(<expression>)          # function like `eval`
```

# Comment

```
# <comment>
/*
    <big comment>
*/
```

---

# New Updates (Draft)

### Line Continuation

```
# Use \ at the end of the line to continue the statement
hex 30 \
31

# Write parentheses expressions on multiple lines
eval(
    0x01 + 0x02
)
```

### Dynamic macro

```
# Single-line format
def add_hex(<val1>, <val2>) => eval(<val1> + <val2>)

# Block format
def my_macro(<addr>, <val>) => {
    er0 = <addr>
    er2 = <val>
}
```

### Legacy Syntax (HD Compiler)

These are syntaxes from the HD compiler. They are still supported for backward compatibility, but it is not recommended to use them together with the new eval() expressions as they can cause parsing errors.

```
str "<string>"
str <var> "<var_string>"        # variable declaration
str <var>                       # it's `str "<var_string>"`

adr_of <label>
adr_of [<offset>] <label>
adr_of [<offset>][<base_addr>] <label>

adr_arith <label1> <+/-> adr_arith <label2> <+/-> ...
adr_arith [<offset1>] <label1> <+/-> adr_arith [<offset2>] <label2> <+/-> ...
```
