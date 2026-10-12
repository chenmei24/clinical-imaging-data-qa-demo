# Clinical imaging data QA launch kit / 发布材料

Publication drafts for a reproducible **synthetic** portfolio example. No client outcome, patient dataset, clinical validation, or community publication is claimed. Verify the example and current script before copying.

## Positioning / 一句话定位

**EN:** A source-preserving CSV quality review with inspectable queries, documented changes, and reproducible outputs.

**中文：** 保留源文件和全部记录，用可追溯的查询日志、变更日志及复现脚本展示临床影像研究 CSV 质控交付。

Primary audience: researchers or small teams who need an agreed, traceable data-cleaning and QA workflow. This demo uses a fixed synthetic schema; a client project requires an authorized, de-identified sample, data dictionary, transformation rules, and agreed acceptance criteria.

## Reproducible tutorial / 可复现教程

From a clone of this repository, run:

```bash
python scripts/audit_csv.py --input examples/01_synthetic_source.csv --output-dir output
python -m unittest discover -s tests -v
```

Python 3.10+; the audit uses the standard library. On Windows with a legacy locale, use `python -X utf8` in place of `python` if needed.

Inspect the committed source and delivered examples:

| Artifact | What it demonstrates |
| --- | --- |
| [Synthetic source](../../examples/01_synthetic_source.csv) | 120 fictional rows, all using `SYN-*` identifiers |
| [Standardized copy](../../examples/02_standardized_with_flags.csv) | All 120 rows retained, with flags and one logged conversion |
| [Query log](../../examples/03_query_log.csv) | 8 row-level events: 7 unresolved queries and 1 documented conversion |
| [Change log](../../examples/04_change_log.csv) | Before/after trace for the single applied change |
| [Summary](../../examples/05_summary.json) | 120 input rows, 120 output rows, 0 rows dropped |
| [Delivery note](../DELIVERY_EXAMPLE.md) | Concise handoff and decisions for the source owner |

The documented example converts `2.7 cm` to `27.0 mm`. An age of `155`, repeated identifiers, an invalid date, unexpected code, and questionable measurement remain visible as queries. The script does not guess a corrected age or decide which duplicate record is valid.

**中文解读：** 120 行源数据全部保留；8 个质控事件包括 7 个待源数据负责人核对的问题和 1 个已记录的单位换算。`2.7 cm` 转为 `27.0 mm` 有前后记录；年龄 `155` 等疑问项保留原值并标记，不凭空修改。复现结果只证明这套示例规则可重复，不证明数据在临床或统计层面已经有效。

## Copy-ready launch posts / 可复制发布文案

### Chinese portfolio introduction

**标题：临床研究数据清洗，交付的不应只是一张“干净表格”**

我做了一个可复现的临床影像 CSV 质控示例，所有记录都是自建的合成数据。交付同时包含源文件、标准化副本、逐行查询日志、变更日志、汇总和复现脚本。

这个示例有 120 行、8 个质控事件：7 个问题留给源数据负责人确认，1 个单位换算有明确依据和变更记录，0 行被静默删除。比如 `2.7 cm` 转为 `27.0 mm`，但年龄 `155` 不会被程序猜改成另一个数值。

这是一份展示方法的作品集，不是客户项目或真实患者数据。实际项目先明确数据字典、检查范围和验收标准，再处理授权且去标识化的数据。

可直接查看和复现：https://github.com/chenmei24/clinical-imaging-data-qa-demo

### English portfolio introduction

**Title: Data cleaning with a review trail, not just a “clean” spreadsheet**

This reproducible clinical-imaging CSV demo preserves the source and delivers a standardized copy, row-level query log, change log, summary, and reusable audit command.

The example contains **120 synthetic records, 8 documented QA events, 1 documented unit conversion, and 0 silently dropped rows**. Seven questions remain open for the source owner. The script converts `2.7 cm` to `27.0 mm` and records the change; it does not invent an age or choose which duplicate record to keep.

Every record is fictional. This is a self-created portfolio demonstration, not a client engagement or clinical validation. A real project starts with an authorized, de-identified sample, data dictionary, agreed rules, and acceptance criteria.

Inspect the outputs and reproduce the example: https://github.com/chenmei24/clinical-imaging-data-qa-demo

### Optional service paragraph / 可选服务介绍

**中文：** 如果你的研究团队需要类似交付，可通过我的 Upwork 页面讨论范围：数据字典核对、单位标准化、重复/缺失/范围检查、查询与变更日志，以及约定范围内的批处理脚本。请先提供授权且去标识化的样例，不在公开 Issue 上传患者数据。工作量与交付范围确定后再报价。

**EN:** If your team needs a similar handoff, contact me through Upwork to scope a data-dictionary review, unit standardization, duplicate/missing/range checks, query and change logs, and an agreed batch workflow. Start with an authorized, de-identified sample; do not upload patient data to a public issue. Pricing follows the agreed scope.

Existing profile: https://www.upwork.com/freelancers/~0149df5417ad7e0bcf

This paragraph is for an explicitly chosen portfolio/service context, not a footer to repeat in every technical reply.

## Assets / 展示图

- [Vector social card](../../assets/launch/social-preview.svg), 1280 × 640.
- [PNG social card](../../assets/launch/social-preview.png), rendered from the SVG.
- The card uses counts from the committed [summary](../../examples/05_summary.json). It labels the dataset as synthetic and is not a fabricated client result or screenshot.
- Existing [portfolio preview](../../assets/portfolio_preview.png) and [case study PDF](../../assets/portfolio_case_study.pdf) remain available for detailed review.

## 30-day execution calendar / 30天执行日历

Day 1 begins when the updated, verified portfolio is public. Use this project for qualified service interest while dicleak remains the main technical launch. The kit does not send messages, submit proposals, or publish posts.

| Days | Action / 行动 | Evidence to record / 留存证据 |
| --- | --- | --- |
| 1–3 | Verify source protection, decimal precision, reproducibility, and artifact links | Command, checks, actual output counts |
| 4–6 | Confirm license and social image; ensure the synthetic label appears prominently | Repository page and readable preview |
| 7–10 | Prepare a portfolio entry showing source → queries → documented change → delivery | Entry draft/link and actual artifact links |
| 11–14 | Publish one permitted educational post about retaining doubtful values | Post URL, useful questions, traffic snapshot |
| 15–17 | Prepare a short scope questionnaire: keys, valid codes/ranges, units, permitted changes, acceptance criteria | Reviewable questionnaire; no private dataset |
| 18–21 | Demonstrate one documented conversion and one unresolved query side by side | Source row, log entry, synthetic output |
| 22–24 | Refine the delivery note from real reader questions; cross-link related tools only where relevant | Revised note and feedback trail |
| 25–27 | If authorized opportunities exist, use a project-specific portfolio excerpt in proposals | Proposal/portfolio record; no claimed client results |
| 28–30 | Review which channels yielded scoped inquiries; revise the scope and examples | 30-day review and next action |

## Measurement / 衡量方式

| Metric | How to record | Interpretation |
| --- | --- | --- |
| Repository visitors / unique visitors | Dated weekly GitHub Traffic snapshots | Readers reached, separate from clients |
| Clones / unique cloners | Same windows as visitor data | Exploration of reproducibility |
| Artifact feedback | Comments/questions on the source, query/change logs, or delivery note | Whether the handoff is clear |
| Qualified inquiries | Unique requests describing a dataset, intended use, and deliverable | Potential scope discussion, not booked work |
| Scope discussions | Record whether rules and acceptance criteria were defined | Whether interest fits the service |
| Agreed projects | Record only actually agreed engagements | Commercial outcome, separate from inquiries |
| Common blockers | Note missing dictionary, unclear keys, authorization, or unavailable source answers | How to improve intake and documentation |

Use a baseline and dated weekly snapshots. Do not sum overlapping unique-visitor windows as a 30-day unique-user count, equate clones with clients, or imply synthetic QA counts are paid project results. No star, revenue, or project-count outcome is promised.

Suggested private tracking fields: date, channel/post URL, release, traffic window, visitors, unique visitors, clones, unique cloners, artifact feedback, qualified inquiries, scope discussion, agreed work, blocker/next step. No patient-identifiable data belongs in this tracker.

## Publication check / 发布前核对

- [ ] The current run reproduces the stated 120 / 8 / 1 / 0 counts.
- [ ] All samples are labeled synthetic; no real client or clinical conclusion is implied.
- [ ] Source preservation and transformation precision match the updated code.
- [ ] Artifact links work, and licensing accurately permits the intended reuse.
- [ ] Service scope is specific; data authorization and acceptance rules are established per engagement.
