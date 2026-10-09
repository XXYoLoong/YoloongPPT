# Auto PPT Engine 研究基线（P05）

## 对应任务与边界

- Requirement ID：`RES-P05-01`
- Task ID：`TASK/VERIFY-RES-P05-01`、`TASK/VERIFY-RES-P05-02`
- P05-01 固定研究版本与官方最小运行，P05-02 建立调用链；P05-03/04/05 的决策、模板与对象能力研究仍待完成。
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

P05-01/02 已按原候选研究验收收尾；页数、可编辑性、QA/视觉缺陷和许可矛盾继续作为限制，未声称产品通过。P05-03/04/05 下一步依据已有调用链提取决策、模板/布局及 30 对象/QA/修订状态，避免重复初始化和正常生成。

## 历史环境阻塞

2026-10-07 的 Docker Engine pipe 缺失与恢复失败曾阻止官方示例运行；2026-10-09 全局 WSL/Docker 已按用户授权恢复，见 `research/P04/validation/environment-recovery.json`。旧阻塞不再是当前状态。本次研究容器启动首次因继承 ENTRYPOINT sleep 与重复参数退出 1；仅重建本任务的空容器并显式 entrypoint 后恢复，记录在 environment.json。

## 固定来源

- [Auto PPT Engine 固定 commit](https://github.com/lijunliu-gh/auto-ppt-engine/tree/5ae0670747885c464aa8063329a902d80a251877)
- [固定 commit README](https://github.com/lijunliu-gh/auto-ppt-engine/blob/5ae0670747885c464aa8063329a902d80a251877/README.md)
- [固定 commit pyproject.toml](https://github.com/lijunliu-gh/auto-ppt-engine/blob/5ae0670747885c464aa8063329a902d80a251877/pyproject.toml)
- [固定 commit package.json](https://github.com/lijunliu-gh/auto-ppt-engine/blob/5ae0670747885c464aa8063329a902d80a251877/package.json)
- [固定 commit LICENSE](https://github.com/lijunliu-gh/auto-ppt-engine/blob/5ae0670747885c464aa8063329a902d80a251877/LICENSE)