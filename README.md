# microshell

将一部分常用 Unix 命令静态翻译为 PowerShell / CMD 命令行并执行。

## 已支持

- 单命令：`ls` `rm` `cp` `mv` `cat` `mkdir` `grep`
- 连接符：`;` `&&` `||`（PowerShell 5.1 下 `&&`/`||` 降级为 `if ($?)` 形式）
- 管道：`|`
- 重定向：`>` `>>` `2>` `2>>` `2>&1`
- 不展开 glob、`~`、`$VAR`、`$(...)`
- 不支持输入重定向 `<`（会报错并提示改用管道）

## 使用

```powershell
pip install -e ".[dev]"

microshell --dry-run "ls -la | grep foo"
microshell --shell pwsh --dry-run "ls && echo done"
microshell --shell cmd --dry-run "rm -rf .\build"
```

`--shell` 取值：
- `powershell`（默认）：Windows PowerShell 5.1
- `pwsh`：PowerShell 7+
- `cmd`：CMD

环境变量 `MICROSHELL_SHELL` 可覆盖默认值。