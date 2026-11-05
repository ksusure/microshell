# microshell

将一部分常用 Unix 命令静态翻译为 PowerShell / CMD 命令行并执行。

## 阶段一范围

- 仅处理**单条命令**：命令名 → 标志位 → 参数
- 不处理 `|`、`&&`、`||`、`;`、`>`、`>>`、`2>&1`
- 不展开 glob、`~`、`$VAR`、`$(...)`

## 使用

```powershell
pip install -e ".[dev]"

microshell --dry-run ls -la /tmp
microshell cat .\README.md
microshell --shell cmd rm -rf .\build
```

环境变量 `MICROSHELL_SHELL=cmd` 可切换默认方言。