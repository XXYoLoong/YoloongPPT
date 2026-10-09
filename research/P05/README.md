# Auto PPT Engine 研究基线（P05）

## 对应任务与边界

- Requirement ID：`RES-P05-01–05`
- Task ID：`TASK/VERIFY-RES-P05-01–05`
- P05-01/02 固定研究版本、官方最小运行与调用链；P05-03/04/05 已交付决策、模板与对象能力映射及实际边界/失败证据。
- 2026-10-09 已按官方无密钥 mock Quick Start 生成并修订 JSON/PPTX，再核对源码调用链。P05-01/02 及其 TASK/VERIFY 已完成候选研究；不代表产品质量或真实 AI 生成验收。

## 固定源码快照

2026-10-07 查询官方 refs：`refs/heads/main` 指向 `5ae0670747885c464aa8063329a902d80a251877`；上游 `v0.8.0` annotated tag object 为 `923300ac557b0c09ec73f4a1f681233be2940452`，peeled commit 也指向 `5ae0670747885c464aa8063329a902d80a251877`。仓库外研究 clone `F:\YoloongPPT-Research\P05` 为 detached HEAD，工作树干净。

固定 checkout：

```powershell
git clone --filter=blob:none --depth=1 --no-checkout https://github.com/lijunliu-gh/auto-ppt-engine.git F:\YoloongPPT-Research\P05
git -C F:\YoloongPPT-Research\P05 checkout --detach 5ae0670747885c464aa8063329a902d80a251877
git -C F:\YoloongPPT-Research\P05 rev-parse HEAD
```

最后一条命令应输出 `5ae0670747885c464aa8063329a902d80a251877`。上游 main 和 tag refs 是研究来源，不等于 YoloongPPT 的产品依赖或后端选型。

## 上游锁文件与运行条件

| 文件 / 范围 | 固定信息 | SHA-256 |
|---|---|---|
| `pyproject.toml` | Python 包 `auto-ppt-engine==0.7.8`；`requires-python >=3.10`；声明 Python 3.10、3.11、3.12 分类器 | `b2f5a3bf0dee49b81f884bef8f3968cbb1647f9f9e75bcf824860fd1e293813a` |
| `requirements.txt` | 仅最低版本约束（如 `openai>=1.68.2`、`jsonschema>=4.23.0`），不是完整锁文件 | `f9f546fd5ac93c242f006ce5560a2b618cfd35e6d48284c2f53016b2626e3370` |
| `package.json` | npm 包版本 `0.8.0`；声明 Node.js `>=18` | — |
| `package-lock.json` | npm `lockfileVersion: 3`；根包版本 `0.7.8`，与 `package.json` 的 `0.8.0` 不同 | `596b9c9236cdf4868bbe7198a389e05a9a4b486ca489d32415639b681da5edcf` |
| `Dockerfile` | 上游镜像声明 `python:3.12-slim`，并通过 NodeSource `20.x` 安装 Node.js | — |
| `LICENSE` | 文件标题为 GNU Affero General Public License Version 3 | `0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0` |

README 的 Quick Start 声明 Python 3.10+ 和 Node.js 18+。未发现根目录 `.python-version`、`.node-version`、`.nvmrc`、`.tool-versions`、`uv.lock` 或 `Pipfile.lock`；Python 依赖没有精确锁定。上表全部是该候选上游在固定 commit 中的声明，不是 YoloongPPT 的运行时决定。**YoloongPPT 当前架构与语言仍未选定；Python 3.11.2 不是本项目已确认的要求。**

## 许可证差异（未解决）

同一固定快照的声明相互矛盾：根 `LICENSE` 是 AGPL v3；`package.json` 声明 `AGPL-3.0-only`；`pyproject.toml` 与 `package-lock.json` 根包元数据声明 `Apache-2.0`；需求矩阵登记为 `AGPL-3.0`。本任务不替上游解释或裁定该冲突。版本清单将 P05 许可证标为 `not_assessed`，依赖复用与分发前需先取得可追溯的上游/法律确认。

## 官方最小流程与实际结果

固定快照 README 的无 API key Quick Start 为 `npm install && pip install .` 后运行 `./auto-ppt generate --mock --prompt ... --source examples/inputs/sample-source-brief.md`。独立研究容器 `yoloongppt-p05-research` 复用已有系统工具，源码工作副本、依赖、缓存、临时文件与产物均在 F 盘；Python 包安装到独立 venv，Windows 未安装项目依赖。安装后断开 bridge 网络，运行 [run-baseline.py](run-baseline.py)。实际命令与返回码见 [baseline-run.json](validation/baseline-run.json)。

| 探针 | 实际结果 |
|---|---|
| 官方正常 8 页 + sample source | JSON/PPTX 生成成功、8 页；ZIP 与 python-pptx 读取通过 |
| 请求 1 页 | 返回成功但实际 5 页；源码钳制改变请求 |
| 缺少来源文件 | CLI 1，明确文件不存在；未生成失败用例 PPTX |
| mock 修订压缩至 6 页 | 8→6 页 JSON 与新 PPTX；不是已有 PPTX 原位编辑 |
| `qa-visual --strict` | 8 张图导出；27 告警；CLI 1，严格 QA 未通过 |

8 页 contact sheets 逐页查看，并复核图表/末页原图。末页正文与副标题对比度过低，QA 没有标为 high-risk；图表是图片而非可编辑原生 chart。保留实际产物及失败结论，不修补固定上游来伪造研究通过。

正常 [PPTX](outputs/normal/py-generated-deck.pptx) SHA-256 `34de9862e65ba032f74d1d1c64bd813102245e8b53bcab43e8b506cb03899ceb`；修订 [PPTX](outputs/revision/py-revised-deck.pptx) 为 `e6554ebf18e3fc3e8fa91fac28c056925ce0f5d9294a328bd671e15fb4e2f897`。完整产物清单及哈希见 [verify-res-p05-01-02.json](validation/verify-res-p05-01-02.json)。

安装观测：Python 3.11.2、Node 18.20.4、npm 9.2.0；43 个 Python 发行包、113 个 npm 包；只描述候选实验。官方 npm install 更新工作副本 lock 的根包元数据 0.7.8→0.8.0，固定 clone 保持原样，前后 hash、实际 lock 和依赖清单均保存。安装报告 7 个漏洞提示（3 moderate、4 high），未自动修复或认证安全。详细复现配置见 [environment.json](validation/environment.json) 与 [install-research.sh](install-research.sh)；产品架构/语言/运行时仍未选定。

## 调用链与研究状态

[call_graph.md](call_graph.md) 和 [source_index.json](source_index.json) 覆盖 41 个节点、40 条边、13 个固定源码文件及 Prompt/Schema/theme 资源。每个节点定位文件/函数/行号并区分实际 CLI、源码分支和外部黑盒。QA 是显式独立调用，生成不自动严格 QA；模板路线删除旧 slides 再新建；HTTP/MCP、template、真实模型与 Tavily 本轮未运行。

P05-01/02 的运行记录保留其当时覆盖范围。P05-03/04/05 已按下述候选研究验收收尾；页数、可编辑性、QA/视觉缺陷和许可矛盾继续作为限制，未声称产品通过。

## 决策、模板与能力边界（2026-10-09 收尾）

- [ProjectDecisionMap](ProjectDecisionMap.json)：14 组结构/视觉决策，40 个统一 DEC 对照。模型规划明确标为 source-only 黑盒，未发现内容关系图或候选评分算法；输入、候选、机制、输出、fallback、源码逐组列出。
- [ProjectTemplateMap](ProjectTemplateMap.json)：17 个 JS layout key / 15 个渲染函数、6 套完整主题 token、IR schema、几何/样式表达式、裁剪规则与继承限制；实测模板解析得到 11 布局 / 58 placeholder，保留 EMU 几何。Python 映射支持 13 schema key（另外含 blank）；4 个扩展布局未映射。
- [ProjectCapabilityMap](ProjectCapabilityMap.json)：PPT-001–030 及写入、渲染、QA、JSON 修订、已有 PPTX 编辑逐项状态。原生对象写出只代表局部操作，没有把全类能力标为 Native。
- [实际探针](validation/maps-probes.json)：显式 `--native-charts` 生成两页原生 chart/table/notes；零页面模板直接写出三页原生对象。ZIP、chart part 与 embedded workbook、table 和 notes 内容检查通过；本轮未做这些新页的视觉或 PowerPoint 打开验收。
- 边界：mock 请求 12 页实际 9 页；中文 prompt 语言仍 en-US；clarify 8 项各 101 字裁为 6 项各 80 字，未新增裁剪说明；修订 tech-modern 不存在，warn 后使用 business-clean。
- 模板失败：带 2 页的正常 PPTX 在删除旧页时使用未展开 namespace 的 `r:id`，触发 `KeyError: None`；官方 CLI 退出 1，只显示 `auto-ppt: error: None`。独立主题关系中的 accent1/heading 漏读，回到默认色/字体。无页面模板可绕开删除路径，但 KPI 回落 Title Slide + bullet，KPI 字段未写出。
- 数据风险：直接 Python renderer 输入 3 个 category / 单值 `[7]`，实际写成 `[7,0,0]`；规划层则会把短 series 降级为 bullet。两个调用边界分别记录，不能概括为“从不补零”。
- [核验](validation/verify-res-p05-03-05.json)：198 个源码引用及 16 文件 hash、完整 ID/资产清单与 4 个 PPTX hash 通过；正常/边界/失败与已有 QA 结果关联。没有修改固定上游来掩盖失败，没有完成产品 DEC/PPT/AC 验收。

复现：在既有 F: 数据盘的 `yoloongppt-p05-research` 内运行 `/scratch/venv/bin/python /evidence/probe-boundaries.py`；主机仅使用已安装 stdlib 执行 `build-maps.py` 和 `verify-maps.py` 读取/核验材料。`build-maps.py` 读取 F: 临时目录导出的需求原行，导出程序见 `baseline-rows.py`；输出用途为 RES-031 及后续选型，非新产品契约。

下一主工作包为 P02 官方模型生成与审查；P05 研究不再因负面发现反复扩展。许可证冲突留给 RES-032，真实模型/HTTP/MCP/全对象能力未验证，不影响如实完成本次研究映射。

## 历史环境阻塞

2026-10-07 的 Docker Engine pipe 缺失与恢复失败曾阻止官方示例运行；2026-10-09 全局 WSL/Docker 已按用户授权恢复，见 `research/P04/validation/environment-recovery.json`。旧阻塞不再是当前状态。本次研究容器启动首次因继承 ENTRYPOINT sleep 与重复参数退出 1；仅重建本任务的空容器并显式 entrypoint 后恢复，记录在 environment.json。

## 固定来源

- [Auto PPT Engine 固定 commit](https://github.com/lijunliu-gh/auto-ppt-engine/tree/5ae0670747885c464aa8063329a902d80a251877)
- [固定 commit README](https://github.com/lijunliu-gh/auto-ppt-engine/blob/5ae0670747885c464aa8063329a902d80a251877/README.md)
- [固定 commit pyproject.toml](https://github.com/lijunliu-gh/auto-ppt-engine/blob/5ae0670747885c464aa8063329a902d80a251877/pyproject.toml)
- [固定 commit package.json](https://github.com/lijunliu-gh/auto-ppt-engine/blob/5ae0670747885c464aa8063329a902d80a251877/package.json)
- [固定 commit LICENSE](https://github.com/lijunliu-gh/auto-ppt-engine/blob/5ae0670747885c464aa8063329a902d80a251877/LICENSE)
