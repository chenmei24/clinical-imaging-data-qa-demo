# 临床影像研究数据 QA：可复现的合成数据示例

[![复现合成数据 QA 示例](https://github.com/chenmei24/clinical-imaging-data-qa-demo/actions/workflows/qa.yml/badge.svg)](https://github.com/chenmei24/clinical-imaging-data-qa-demo/actions/workflows/qa.yml)
[![MIT 许可证](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[English](README.md) · 简体中文

**120 条合成记录 · 8 个 QA 事件 · 7 个待确认问题 · 1 项有记录的单位转换 · 0 条静默删除**

将一份存在质量问题的研究 CSV 整理成可追溯的交付包：保留全部记录，单独列出疑问，记录每项实际修改。本项目中的 `SYN-*` 记录全部为虚构数据，是作者自行制作的作品示例，不是客户项目、患者数据、诊断工具或研究结果。

**Python 3.10 及以上，无需安装第三方库。** 在仓库根目录运行：

```bash
python scripts/audit_csv.py --input examples/01_synthetic_source.csv --output-dir output
```

需要针对自己的授权、去标识化数据设计 QA 流程，可通过[现有 Upwork 主页联系](https://www.upwork.com/freelancers/~0149df5417ad7e0bcf)。

![合成数据质量审计示例预览](assets/portfolio_preview.png)

## 实际处理前后

| 源记录位置 | 处理前 | 处理后 | 可追溯记录 |
| --- | --- | --- | --- |
| 81 · `SYN-080` | `lesion_value=2.7`、`lesion_unit=cm` | `lesion_value=27.0`、`lesion_unit=mm` | 记录转换前后值和原因，源文件不变 |
| 11 · `SYN-010` | `age_years=155` | 仍保留 `155` | 提交数据负责人核对，不猜测正确年龄 |
| 120 · `SYN-001` | ID 重复 | 两条记录均保留 | 标记重复，不自动合并或删除 |

查看[一页案例 PDF](assets/portfolio_case_study.pdf)、[合成源文件](examples/01_synthetic_source.csv)、[标准化副本](examples/02_standardized_with_flags.csv)、[问题日志](examples/03_query_log.csv)、[变更日志](examples/04_change_log.csv)及[汇总 JSON](examples/05_summary.json)，可以直接核对交付内容。

## 本示例检查什么

| 检查项 | 示例 | 处理方式 |
| --- | --- | --- |
| 重复 ID | 2 次重复事件 | 保留并提出核对问题 |
| 缺失或不合理年龄 | 空白、`155` | 保留，不填补、不猜测 |
| 非预期分类 | `sex_code=X` | 与数据字典核对 |
| 非正测量值 | `lesion_value=-2` | 保留并标记 |
| 无效日期 | `2025/04/31` | 保留原值并核对 |
| 单位不一致 | 以毫米为主，出现 `2.7 cm` | 转为 `27.0 mm`，记录原值和原因 |

这 8 个事件由 **7 个未解决问题和 1 项已记录的转换**组成。`qa_events` 是事件数，不是存在问题的记录数；同一记录可以对应多个事件。转换不计入未解决问题。

## 运行和验证

```bash
python scripts/audit_csv.py --input examples/01_synthetic_source.csv --output-dir output
python -m unittest discover -s tests -v
```

命令在 `output/` 中生成：

| 文件 | 用途 |
| --- | --- |
| `02_standardized_with_flags.csv` | 保留全部源记录的标准化副本；疑问值仍在原字段中，标记见问题日志 |
| `03_query_log.csv` | 每个事件的源记录位置、ID、字段、问题与处理说明 |
| `04_change_log.csv` | 实际修改的前值、后值及原因 |
| `05_summary.json` | 输入/输出行数、事件数、待确认问题数与变更数 |

成功再次运行会替换这四个输出文件。测试核对已提交的 120 条示例，并覆盖小数精度、异常值、表头与记录结构、路径别名、输出失败与回滚。CI 配置为 Linux、Windows × Python 3.10、3.13。

Windows 使用旧版区域设置或中文路径时，可将命令中的 `python` 改为 `python -X utf8`。

交付说明示例见 [Sample delivery note](docs/DELIVERY_EXAMPLE.md)。

## 输入格式与数据保留

输入为 UTF-8 CSV，列名必须与下表完全一致，区分大小写。**列的排列顺序可以不同**，输出统一采用下表顺序。缺失、多余或重复的列名会给出明确错误。

| 列名 | 本示例固定规则 |
| --- | --- |
| `record_id` | 非空且唯一；缺失或重复 ID 保留并标记 |
| `age_years` | 0–120 的整数字符串；空白及不符合规则的值保留并标记 |
| `sex_code` | `F` 或 `M` |
| `modality` | `CT` 或 `MRI` |
| `lesion_value` | 有限、正的小数测量值 |
| `lesion_unit` | `mm`；有限正值的 `cm` 可按规则转换并记录 |
| `scan_date` | 合法日历日期，格式为 `YYYY-MM-DD` |

[机器可读数据字典](schemas/data_dictionary.json)说明固定演示规则，**不是可直接修改后生效的配置文件**。这些范围和分类是演示约定，不能作为通用临床标准。

- 每条记录必须具有与表头一致的字段数量。结构完整但值为空时保留并检查；少了字段、多了字段或 CSV 结构损坏时停止。
- `cm` 到 `mm` 采用精确十进制转换：`2.7 cm → 27.0 mm`，`0.004 cm → 0.04 mm`。不四舍五入丢失小数；非常大或小的值可以保留为科学计数法。
- 负值、零、非有限值、无法解析或超出 Decimal 转换表示范围的测量值保留原文，不转换，交由数据负责人核对。
- 源文件只读。程序拦截源文件与四个输出路径的碰撞，包括解析后的路径、符号链接和硬链接；输出文件也不能是符号链接或互为别名。
- 先完成检查和四个文件的临时生成，再替换正式输出。普通替换错误会触发回滚；若回滚也失败，程序报告并保留恢复文件路径。每个输出目录同一时间只运行一个进程；不提供多进程写入或断电恢复保证。
- 日志中的 `source_row` 按 CSV 逻辑记录位置计数，表头为 1；当引号字段内含换行或空文本行被跳过时，它不等于物理文本行号。
- 空输入、结构错误或不可用输出路径返回退出码 2，并给出错误信息。

## 实际委托如何开展

1. 查看已授权、去标识化的小样本、列定义和使用目的。
2. 约定记录键、范围与分类、单位、允许转换及问题处理标准。
3. 交付保留源文件的数据副本、逐记录问题日志、变更记录和简明汇总；按约定提供可复用脚本。
4. 收到数据负责人回复后重新检查；需要持续维护时再约定批次处理流程。

若需要定制数据清理或自动 QA，可在 [Upwork](https://www.upwork.com/freelancers/~0149df5417ad7e0bcf) 提供授权、去标识化样本及数据字典。公开 GitHub Issue 仅使用虚构数据，不上传患者身份信息。

## 仓库内容

| 目录或文件 | 内容 |
| --- | --- |
| `assets/` | 预览图片和一页案例 PDF |
| `examples/` | 合成源文件与可核对交付样例 |
| `scripts/` | CSV 审计命令 |
| `tests/` | 复现与数据保留测试 |
| `schemas/` | 固定演示数据字典 |
| [CHANGELOG.md](CHANGELOG.md) | 更新记录 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献和验证说明 |
| [LICENSE](LICENSE) | MIT 许可证 |

欢迎在 [GitHub Issues](https://github.com/chenmei24/clinical-imaging-data-qa-demo/issues) 提交带有最小虚构样本的错误报告。模糊记录由授权数据负责人确认；程序不推断临床结论。

## Related tools / 相关工具

- [Medical-imaging manifest audits](https://github.com/chenmei24/dicleak)
- [Manuscript rule checks](https://github.com/chenmei24/manulint)

[Launch tutorials and share images / 推广教程与展示图](docs/launch/README.md)
