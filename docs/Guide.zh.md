# RAC COMPILER — 使用指南

🌍 [English](Guide.md) | 🇻🇳 [Tiếng Việt](Guide.vi.md)

---

## 1. 注释
* **语法:**
  - `# <comment>`
  - `/* <comment> */`

```assembly
# 单行注释
/* 
   多行
   注释
*/
```

## 2. 变量与寄存器
* **语法:**
  - `var <var> = <value>`
  - `reg <reg> = <value>`
  - `<reg> = <value>`
  - `<var> = <value>`
* **调用 / 取值:**
  - `<name_var>` (例如, `a`, `b`, `c`, `var`)

```assembly
var count = 10         # 声明 count 变量
reg r1 = 0x5           # 初始化寄存器 r1
r2 = 0xFF              # 直接给 r2 赋值
count = 20             # 重新赋值给变量 count
count                  # 调用/求值 count
```

## 3. 数据类型与字符串处理
* **语法:**
  - 整数 / 十六进制: `<int(hex)>` (例如, `0x02`, `10`) 或 `hex <int(hex)>`
  - 字符串:
    - `"<string>"` (使用 `~` 表示空格, 例如 `"hello~world"`)
    - `"<f-string>"` (例如 `"hello {name}"`)
    - `'<token string>'` (为数学引擎保持结构完整)
    - `str "<string>"` (编译原始字符串)
    - `str <var> "<var_string>"` (声明字符串变量)
    - `str <var>` (调用字符串变量的值)
  - 数组 / 列表:
    - `[<item>; <item>; ...]` (内联)
    - 多行块:
      ```assembly
      [
          <item>
          <item>
      ]
      ```
  - 内存量度:
    - `pr_length` / `sizeof()` (当前段的大小)
    - `sizeof(<section>)` (指定段的大小)
    - `dist.<section>` (初始地址与备份地址之间的字节距离)
    - `pr_org()` (当前段的初始原点地址)
    - `pr_org(<section>)` (指定段的初始原点地址)
    - `pr_backup()` (当前段的备份地址)
    - `pr_backup(<section>)` (指定段的备份地址)

```assembly
var ten = "World"
"Xin~chào,~{ten}!"        # 带有空格的插值: "Xin chào, World!"
'sin( 9 0 )'              # 标记字符串
str greeting "Hi"         # 字符串变量
str greeting              # 编译 "Hi"
[0x1; 0x2]                # 内联列表
[                         # 块列表
  0x3
  0x4
]
var size = sizeof(main)
var delta = dist.launcher
```

## 4. 别名 (Aliases)
* **语法:**
  - `<var/reg/gadget/label/...> as <new_name>`
  - `@section.<old_name> [at <addr_org> backup <addr_backup>] as <new_name>`
  - `@set.<old_name> [at <addr_org> backup <addr_backup>] as <new_name>`

```assembly
er0 as tmp
tmp = 0x1200                             # 编译为: er0 = 0x12

@section.init at 0x1000 backup 0x2000 as start
```

## 5. 标签与跳转
* **语法:**
  - 声明:
    - `lbl <label>`
    - `<label>:`
  - 获取地址:
    - `adr(<label>)`
    - `adr(<label>, <offset>)`
    - `adr(<label>, <offset>, <base_addr>)`
    - `adr($)` (获取本行的当前地址)
    - `adr_of <label>`
    - `adr_of [<offset>] <label>`
    - `adr_of [<offset>][<base_addr>] <label>`
  - 跳转:
    - `goto <label>` (扩展为: `er14 = adr(<label>, -2); sp = er14, pop er14`)

```assembly
lbl start
# 或:
start:
  goto end

lbl end
  var addr1 = adr(start)
  var addr2 = adr_of [-2][0x8000] end
```

## 6. 调用与代码片段 (Gadgets)
* **语法:**
  - `call <address/function_name>`
  - `def <gadget> : <address>` (将小工具定义到 command_dict 中)
  - `def {<tag>} <name_gadget>: <address>`

```assembly
def my_gadget : 0x17b34
call my_gadget
call 0x1234
def {memcpy} memcpy_auto_jmp: 0x12345
```

## 7. 复合语句
* **语法:** `<statement1> ; <statement2> ; ...`

```assembly
call 0x1234 ; goto end
```

## 8. 动态宏 (Dynamic Macros)
* **语法:**
  - 单行: `def <macro_name>(<args>) => <single_line_expr>`
  - 块形式: `def <macro_name>(<args>) => { <block_of_code> }`

```assembly
def add_hex(<val1>, <val2>) => eval(<val1> + <val2>)

def my_macro(<addr>, <val>) => {
    er0 = <addr>
    er2 = <val>
}
```

## 9. 函数
* **语法:**
  - 多行块:
    ```assembly
    func <function>(<args>) {
        <code>
    }
    ```
  - 独立调用: `<function>(<args>)`
  - 单行返回 (可赋值给变量/寄存器):
    `func <function>(<args>) { return <expression> }`

```assembly
func greet(person) {
  "Hello,~{person}!"
}
greet("Alice")

func add(x, y) { return x + y }
r1 = add(5, 10)
```

## 10. 定位与对齐指令
* **语法:**
  - `org <addr_org>` (设置映射原点地址；如果使用 `@set` 内联 `at` 则跳过)
  - `backup <addr_backup>` (设置备份存储地址)

```assembly
org 0xe9e0
backup 0xd000
```

## 11. 阶段内存块 (Sections)
* **语法:**
  - `@section.<section> [at <addr_org> backup <addr_backup>]`
  - `@set.<section> [at <addr_org> backup <addr_backup>]`

```assembly
@set.main at 0xe9e0 backup 0xf000
0x1234

@section.launcher at 0xd180
r1 = 0x5
```

## 12. 构建配置 (`@build`)
* **语法:**
  - 块形式:
    ```assembly
    @build {
        emu.inj = <true|false>
        emu.inj_file = "<file_name>"
        emu.inj_var = "<name_var>"
        emu.inj_adr[<section>] = <address>
        line.bytes = <count>
        line.gadgets = <address>
        output.file = <true|false>
        output.file_name = "<file_name>"
    }
    ```
  - 内联形式: `@build <key> = <value>; ...;`

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

## 13. 编译时求值与算术
* **语法:**
  - `eval(<expression>)`
  - `calc(<expression>)`
  - `adr_arith <label1> <+/-> adr_arith <label2> ...`
  - `adr_arith [<offset1>] <label1> <+/-> adr_arith [<offset2>] <label2> ...`

```assembly
eval(0x1 + 0x2 * 0x3)                     # 求值为 0x7
calc(adr(label1) - adr(label2))
adr_arith start - adr_arith end
adr_arith [+4] start - adr_arith [-2] end
```

## 14. 编译时循环与填充
* **循环:**
  - `loop <range> { <code> }`
  - `repeat <range> { <code> }`
* **填充:**
  - `fill(<count>, [<value>])`: 用 `<value>`（默认0）填充 `<count>` 个字节。
  - `align(<size>, [<value>])`: 填充字节直到地址成为 `<size>` 的倍数。
  - `pad(<offset>, [<value>])`: 填充字节直到段长度达到 `<offset>`。
  - `pad_abs(<address>, [<value>])`: 填充字节直到绝对地址达到 `<address>`。

```assembly
loop 4 {
  0x67
}

fill(16, 0xFF)
align(4)
pad(0x100, 0x00)
```

## 15. 嵌入式 Python 脚本
* **语法:** `@python { <python_code> }`
* 允许在编译期间直接执行 Python 代码。变量可以注入到编译器环境 (`loader.vars_dict`) 中。

```assembly
@python {
    # 复杂的 Python 逻辑
    loader.vars_dict["calculated_val"] = 0x1234 * 2
}
var my_val = calculated_val
```

## 16. 行连续与多行
* **语法:**
  - 在行末使用 `\` 以继续一条原始语句。
  - 圆括号 `()`、方括号 `[]` 或大括号 `{}` 自动支持多行，无需 `\`。

```assembly
hex 30 \
31

eval(
    0x01 + 0x02
)
```

---

**文档维护者:** `luongvantam`
