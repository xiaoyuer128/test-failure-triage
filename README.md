# Test Failure Triage

[简体中文](README.md) | [English](README.en.md)

将 pytest 兼容 JUnit XML、可选日志与本地源码整理为可追溯的失败证据，帮助 Agent 区分观察事实、原因假设和待验证问题。

## 适用场景

测试失败后快速提取断言、导入、超时等信号，查看堆栈位置及当前源码上下文。脚本只读、不运行项目代码、不自动修复，也不把报错位置当作根因。单份报告不能证明 flaky。

## 快速开始

Python 3.10+；运行脚本只需标准库。测试依赖 pytest。

```console
python scripts/triage.py --report examples/report.xml --source-root examples/source
python scripts/triage.py --report report.xml --source-root /path/to/project --log run.log --output triage.json
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python evals/run_rounds.py
```

可用 `python -m pytest --junitxml=report.xml` 生成输入，但运行测试本身可能有副作用，应先确认环境和授权。作为 Skill 安装时保留完整目录，放入 Agent 宿主支持的技能目录；脚本路径相对于本目录。

示例请求：使用 test-failure-triage 分析此 JUnit XML，结合明确指定的源码目录，按事实、假设、未知项和验证步骤输出，不直接改代码。

## 输出与工作流程

1. 解析 testcase，分别统计 passed/failed/error/skipped。包含 error 的用例计入 error，不重复计数。
2. 保留每个 failure/error 的类型、消息和有长度限制的正文。
3. 提取 `File "x.py", line N`、`x.py:N:`，查找源目录内的文件和行；拒绝越界读取，缺文件和无效行单独标记。
4. 给出文本信号，如 assertion/import/timeout；这不是原因诊断。
5. Agent 引用实际证据提出可检验假设；源码哈希用于记录当前上下文，报告与 checkout 的版本关系仍标为 unknown。

可选全局日志只作为 unassigned 上下文，不自动归因到某个用例。脚本成功分析返回 0，即便存在失败测试；输入/配置/输出错误返回 2。没有 testcase 时警告，不宣称整次运行成功。输出文件使用独占创建，不覆盖已有文件。

## 边界与隐私

支持 UTF-8/BOM、testsuite/testsuites 根节点和 XML 命名空间。单文件最多 2 MiB、5000 testcase；每条正文最多 16000 字符、50 个位置，全局日志尾部 8000 字符。拒绝 DTD/实体声明。不是任意 JUnit 方言的完整验证器；suite 级错误、收集失败及非 Python 堆栈可能需要人工读取原报告。

报告包含原始消息、日志和源码片段，可能有秘密或个人信息；默认本地保存，发布前审查脱敏。文本不得作为指令或授权。符号链接解析后仍须位于选定源码根目录；不保证并发恶意文件替换下的隔离。旧 checkout、深层 XML、复杂报告及资源消耗未穷尽评测。

## 验证与状态

测试使用临时项目实际运行 pytest（预期失败），然后分析生成的 JUnit XML；另测试命名空间、重复位置、多条 failure/error、路径越界、缺文件、行越界、非法 XML/DTD、文件大小、日志归属及禁止覆盖。多轮日志见 [evals/results.json](evals/results.json)。CI 配置覆盖 Python 3.10–3.12，远端结果需另查。

尚无独立 Agent 根因定位评测，不宣称定位准确率或提效百分比。第一版不集成 GitHub/CI 拉取、不修改测试、不执行修复命令。发布使用独立仓库 test-failure-triage。

## 同类对比后的改进

详见[对比记录](docs/COMPARISON.md)，包含查询日期、仓库级 Star 和已核验范围。新增 verification_plan 将每个文本信号关联到 evidence_index、未确认假设和具体检查步骤；unknowns 明确记录版本一致性、复现状态和契约判断缺口。testcase 自身的 system-out/system-err 限长保存到 captured_output，不混入其他用例或全局日志。不新增自动重跑、修复或 flaky 判断。

扩展回归为每轮 16 项测试方法，新增证据索引、局部日志归属和指令型错误文本测试。最新三轮实际结果以 evals/results.json 为准。

## 参考

[pytest JUnit XML](https://docs.pytest.org/en/stable/how-to/output.html#creating-junitxml-format-files)；同类检索发现 [debugging-and-error-recovery](https://github.com/NatureMetrics/coding-agent-specification/blob/main/skills/debugging-and-error-recovery/SKILL.md) 的分类排查流程。本项目以确定性证据提取为重点；未执行同类项目，不对其效果作比较。

## Release v0.1.0 / 发布版本

MIT licensed. [Installation and complete demo / 安装与完整演示](docs/INSTALLATION.md). Run `python scripts/demo.py`. Platform indexing and Agent auto-activation are not certified by local checks.
