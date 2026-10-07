# Auto PPT Engine 研究基线（P05）

## 对应任务与边界

- Requirement ID：`RES-P05-01`
- Task ID：`TASK-RES-P05-01`
- 本记录只处理固定研究版本、锁文件、上游运行条件和许可证；P05-02 至 P05-05 的调用链、决策节点、模板/中间表示与写入/QA/修订边界仍是独立任务。
- 矩阵要求先运行官方最小示例，再做静态阅读。本次先尝试项目隔离容器启动；Docker Engine 不可用后才登记静态元数据。官方示例未执行，因此本任务保持进行中，`VERIFY-RES-P05-01` 保持未开始。

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

## 官方最小流程与容器阻塞

固定快照 README 的无 API key Quick Start 为：安装 `npm install && pip install .`，然后运行 `./auto-ppt generate --mock --prompt ... --source examples/inputs/sample-source-brief.md`。本任务未在宿主机安装这些依赖。

项目隔离容器命令 `scripts/project.ps1 start` 实际执行失败：Docker Desktop Linux Engine 管道 `//./pipe/dockerDesktopLinuxEngine` 不存在，`docker desktop status` 为 `stopped`。Docker CLI 为 `27.4.0`、Docker Desktop 为 `4.37.1`、desktop CLI 插件为 `v0.1.0`、WSL 为 `2.7.14.0`，均只是当次环境观测。Linux 引擎已选中；默认与 `desktop-linux` 两个 context 都无法连接。WSL 内部 `docker-desktop` 发行版可启动并执行 `/bin/echo`，但未发现 `dockerd`，Engine 仍不可用。WSL 输出 `Unknown key 'automount.crossDistro' in /etc/wsl.conf:3`；探针仍能执行，当前没有证据证明这条警告是 Engine 阻塞根因。Docker Desktop CLI 启动、重启、停止、重新选择 Linux 引擎及 WSL 重置后，`docker info` 仍未返回 Server 版本；启动辅助 Windows 服务也因当前权限被拒绝。没有运行上游 npm/pip 安装、测试、构建或生成 PPTX。

因此，refs、锁文件摘要、上游运行声明和许可证差异已静态登记；`ProjectBaseline` 验收未通过。Docker Engine 恢复后，应先在项目隔离容器按官方 Quick Start 执行 mock 生成，保留实际日志与 JSON/PPTX，再完成 VERIFY；本记录不把上游 README 截图或声明当作本项目验证结果。

## 固定来源

- [Auto PPT Engine 固定 commit](https://github.com/lijunliu-gh/auto-ppt-engine/tree/5ae0670747885c464aa8063329a902d80a251877)
- [固定 commit README](https://github.com/lijunliu-gh/auto-ppt-engine/blob/5ae0670747885c464aa8063329a902d80a251877/README.md)
- [固定 commit pyproject.toml](https://github.com/lijunliu-gh/auto-ppt-engine/blob/5ae0670747885c464aa8063329a902d80a251877/pyproject.toml)
- [固定 commit package.json](https://github.com/lijunliu-gh/auto-ppt-engine/blob/5ae0670747885c464aa8063329a902d80a251877/package.json)
- [固定 commit LICENSE](https://github.com/lijunliu-gh/auto-ppt-engine/blob/5ae0670747885c464aa8063329a902d80a251877/LICENSE)