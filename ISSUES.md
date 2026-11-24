# 框架问题：复现、原因和缓解

本文件是 [README.md](README.md) 的一部分，记录实验中在 OpenCollab上找到的两个问题：现象、原因、证据，以及本项目的修复或缓解和前后对比。框架扩展（双层经验记忆、Team 预算共享）见 [IMPROVEMENTS.md](IMPROVEMENTS.md)。

## 一览

| 问题 | 类型 | 影响 | 本项目做了什么 | 前后对比 |
|---|---|---|---|---|
| [问题一：成员被重新唤醒后停下，事件流不记录](#1-问题一成员被重新唤醒后停下事件流不记录) | 确定的 bug | 统计时共 171 次 Team 运行，其中 90 个席位的“预算用完”被记成了“完成” | 修复：改 4 行代码，加 31 行测试 | 新增的 2 条测试从失败变为通过，原有 8912 条测试仍全部通过 |
| [问题二：Duo 的候选可以用 bash 越过隔离](#2-问题二duo-的候选可以用-bash-越过隔离) | 有文档记载的限制，但后果没写清楚 | ClassEval 上 Duo 有 6 次运行被框架中止；其中 4 次交付的代码绕过了 Duo 的选择流程 | 缓解：给候选的 bash 加一个拦截器（guard） | 开发题上越界命令 136 条 → 0 条；ClassEval 上 Duo 被中止 6 次 → 0 次，做对 41 → 45 次 |

> [!NOTE]
> **几个名词。**
> - **事件流**：每次运行留下的记录文件 `trajectory.jsonl`，按时间顺序记下每个成员开始、结束、调用工具等事件。论文和本项目都靠它统计“谁怎么结束的”。
> - **席位**：Team 里的一个智能体（成员）。本项目的 Team 有 3 个席位。
> - **done / stopped**：成员的两种结束状态。done 是自己完成了工作；stopped 是被框架停下，比如预算用完。
> - **Duo**：框架自带的工作流，让两个**候选**（两个 Coder）各自独立写一份代码，再由框架比较、选出一份写回。
> - **worktree**：给每个候选单独准备的代码副本目录。候选本来只应该改自己的那一份。
> - **源工作区**：存放最终代码的原始目录（`/tmp/ws/repo`）。按设计，只有框架选出候选之后，才把选中的代码写进这里。
>
> **怎么读这些数字。** “解决”指一次运行通过了全部隐藏测试。“配对”是把同一道题、同一次重复的两种做法放在一起比；p 越小越不像运气，一般以 0.05 为界。详细说明见 [README](README.md) 第 3.3 节。

**目录**

- [1. 问题一：成员被重新唤醒后停下，事件流不记录](#1-问题一成员被重新唤醒后停下事件流不记录)
  - [1.1 现象](#11-现象) · [1.2 为什么是 bug](#12-为什么是-bug) · [1.3 原因](#13-原因) · [1.4 证据](#14-证据) · [1.5 修复和前后对比](#15-修复和前后对比)
- [2. 问题二：Duo 的候选可以用 bash 越过隔离](#2-问题二duo-的候选可以用-bash-越过隔离)
  - [2.1 现象](#21-现象) · [2.2 后果](#22-后果) · [2.3 根本原因](#23-根本原因) · [2.4 建议的根本修复](#24-建议的根本修复) · [2.5 本项目的缓解：guard](#25-本项目的缓解guard) · [2.6 guard 前后对比](#26-guard-前后对比) · [2.7 guard 的局限](#27-guard-的局限)
- [3. 如何复现](#3-如何复现)
- [4. Issue 和 PR](#4-issue-和-pr)

---

## 1. 问题一：成员被重新唤醒后停下，事件流不记录

> [!IMPORTANT]
> Team 里的成员完成工作后，可能被队友的消息叫醒、接着干活，最后因为预算用完被停下。这次“停下”不会写进事件流，记录里留着的仍是第一次的“完成”。统计时共有 171 次 Team 运行，其中 90 个席位是这种情况。本项目改了 4 行代码修好，并补了测试。

### 1.1 现象

一个席位的经过是这样的：

1. 它做完了自己的工作，状态是 **done**，事件流里记下一条“done”；
2. 队友给它发消息，它被重新唤醒，接着干活；
3. 这一轮干到一半，预算用完，被框架停下，状态变成 **stopped**；
4. 但事件流里**不会**再记这次 stopped，留着的仍是第 1 步的“done”。

结果是，看事件流会以为这个席位顺利完成了，实际上它是被预算截断的。

这个 bug **不影响做题结果**：代码照常交、照常评分。它影响的是用事件流做的统计。比如要数“有多少运行被预算截断”，这些席位会被算成“完成”而漏掉。

### 1.2 为什么是 bug

论文附录 C.6 的 Table 15 写明，会话结束事件的用途之一，就是识别 "runs cut off by the allowance after delegation began"，也就是开始分工之后被预算截断的运行。被漏记的恰好就是这种情况，所以这不是设计上的取舍，而是和论文说明不符的 bug。

### 1.3 原因

[session_run.py](https://github.com/RISE-X-Lab/OpenCollab/blob/78ca8e37/opencollab/application/session_run.py) 用一个标志 `_session_terminal_traced` 保证每个会话只写一条结束事件 `session_terminal`。代码注释说明了本意：有时框架只是“只读地”重新进入一个已经完成的会话、取一下它的答案，这时不应该再记一次结束。

问题是这个标志一旦置位，就再也不会重置。成员被真正唤醒、开始新一轮工作之后，新的结束状态也被当成“已经记过了”而丢掉。

### 1.4 证据

- **离线复现**：不调用模型，在原版 `78ca8e37` 上运行 [scripts/repro_terminal_trace.py](scripts/repro_terminal_trace.py)，输出见 [results/evidence/repro_terminal_trace_upstream.txt](results/evidence/repro_terminal_trace_upstream.txt)。第 1 轮 done，第 2 轮因预算 stopped，事件流里只有一条 done。
- **真实数据**：统计时共有 171 次 Team 运行（之后又跑了更多 Team 运行，所以 [IMPROVEMENTS.md](IMPROVEMENTS.md) 第 2.1 节用的是 273 次），其中有 540 个席位实际工作过，其中 90 个席位（分布在 82 次运行里）的最终状态是预算用完，事件流里却只有 done。

### 1.5 修复和前后对比

**修复**：开始一轮新的真实工作时，重置这个标志；只读重进时保持不变。改了 4 行代码，加了 31 行测试，补丁见 [results/evidence/fix_session_terminal.patch](results/evidence/fix_session_terminal.patch)。

| | 原版 `78ca8e37` | 修复后 |
|---|---:|---:|
| 新增测试（两种唤醒路径） | 2 条都失败 | 2 条都通过 |
| 原有“只读重进不重复记录”测试 | 通过 | 通过 |
| 框架测试（agents、runtime、workflows、interfaces） | 8912 通过，0 失败 | 8914 通过，0 失败 |

修复后多出的 2 条通过的测试，就是新增的那 2 条；原有的测试一条都没有被改坏。

---

## 2. 问题二：Duo 的候选可以用 bash 越过隔离

> [!IMPORTANT]
> Duo 的两个候选本应各自在自己的 worktree 里干活，但用 bash 就能读写源工作区和另一个候选的目录。在 ClassEval 上，这让 Duo 60 次运行里有 6 次被框架中止，其中 4 次交付的代码是候选直接写进源工作区的，绕过了 Duo 的选择流程。根本原因是框架的候选会话不支持进程级隔离。本项目加了一个拦截器（guard）作为缓解：在开发题上，候选在源工作区执行成功的越界命令从 136 条降到 0 条；在 ClassEval 上，Duo 的中止从 6 次降到 0 次。

### 2.1 现象

框架文档写 "Duo V8 produces two isolated solutions"（两个相互隔离的解），论文写 "Each works in its own candidate environment … The code, not an agent, applies the selected candidate"（每个候选在自己的环境里工作，由代码而不是智能体把选中的候选写回去）。

但官方的 Duo 示例要求打开 `allow_unisolated_shell` 才能让候选运行命令。打开后会出现两种不一致的行为：

| 操作 | 用文件工具（`file_read` / `file_write`） | 用 bash（如 `cat`、重定向写文件） |
|---|---|---|
| 读另一个候选的 worktree | 被拒绝 | **成功** |
| 写源工作区 | 被拒绝 | **成功** |

文件工具会检查路径，bash 不会。所以候选只要用 bash，就能越过隔离。

### 2.2 后果

**越界很常见。** 在 8 道开发题上（每题 8 次，共 64 次运行），不加 guard 的 Duo 有 30 次运行的候选在源工作区执行了命令，共 136 条。

**越界会让运行直接失败。** 在 ClassEval 测试集上，Duo（原版框架）60 次运行里有 **6 次被框架中止**，报错 "source worktree changed during candidate"（候选运行期间源工作区被改动了）。逐条检查后，这 6 次都是候选用 bash 在源工作区（`/tmp/ws/repo`）里执行了命令，比如 `cd /tmp/ws/repo && git show ...`，或者在源工作区里运行脚本。框架发现源工作区被改动，于是中止了整个运行。

**越界还会改变最终交付的代码。** 这 6 次都是在候选阶段被中止的：Duo 还没有选出候选，也没有把任何候选写回去。可是导出的最终工作区里都有新代码（`final.diff` 新增 7 到 37 行）。这些代码是候选用 bash 直接写进源工作区的，例如 `cd /tmp/ws/repo && python3 - <<EOF ... open('solution.py') ...`，每次运行有 1 到 9 条这样的写入。

其中 4 次的代码通过了全部隐藏测试。按统一的评分规则（运行结束时工作区里是什么代码，就拿什么去评分），这 4 次记为解决。也就是说，这 4 次的交付绕过了 Duo 的选择流程，论文说的 "The code, not an agent, applies the selected candidate" 在这几次里并不成立。

> [!NOTE]
> 如果按“被中止的运行不交付任何代码”的严格标准，Duo 在 ClassEval 上是 37 次解决，而不是 41 次。[README](README.md) 第 4 节的主结果仍按统一规则记为 41 次，不单独为 Duo 改规则。

### 2.3 根本原因

`candidate_agent`（创建候选的接口）不支持进程级隔离，候选只能是同一个环境里的 worktree：它从父环境里取一个 worktree 作为候选的工作目录，并在创建会话时写死了 `isolation=False`（[workflow_candidates.py:347-367](https://github.com/RISE-X-Lab/OpenCollab/blob/78ca8e37/opencollab/application/workflow_candidates.py#L347-L367)）。

所以即使整个运行放在容器里，所有候选也只是同一个容器里的几个目录，彼此之间、以及和源工作区之间都没有进程隔离。文档原文是："A container-backed parent keeps its children inside that container."

而框架里的其他会话（`ctx.agent`、Team 成员）可以用 `docker-session` 做到“一个会话一个容器”（[docs/session-isolation.md](https://github.com/RISE-X-Lab/OpenCollab/blob/78ca8e37/docs/session-isolation.md)），只有候选做不到。以上结论来自阅读代码和文档，没有实际用 `docker-session` 运行 Duo 来验证。

### 2.4 建议的根本修复

让 `candidate_agent` 也遵守隔离设置。比如在 `docker-session` 下，给每个候选分配自己的容器，只挂载它自己的 worktree。框架已有的 `docker-session` 能为普通会话复制工作区、导出改动，可以复用。

但这要改动候选会话的整个生命周期（初始化、导出、写回、清理、取消），应由框架维护者决定和实现。本项目只在 issue 里提出，没有自己改。

### 2.5 本项目的缓解：guard

在框架补上候选隔离之前，本项目加了一个低成本的缓解措施，用来拦住智能体无意中的越界：

- **做法**：给候选会话的 bash 加一个拦截器。命令文本里如果出现指向源工作区或另一个候选 worktree 的**绝对路径**，就拒绝执行。
- **开关**：默认打开，设环境变量 `OPENCOLLAB_CANDIDATE_PATH_GUARD=0` 可以关闭。
- **改动**：`opencollab/adapters/safety.py` 和 `opencollab/bootstrap/_workflow_runtime_session.py`，另加 5 条测试。

### 2.6 guard 前后对比

**① 开发题上的对比**（8 道开发题，每题 8 次，共 64 对，详细数据见 [results/guard_pairs.md](results/guard_pairs.md)）：

| | 不加 guard | 加 guard | 配对检验 |
|---|---:|---:|---|
| 在源工作区执行成功的命令 | 136 条（30/64 次运行） | **0 条** | — |
| 解决 | 48/64（75%） | 51/64（80%） | 4 : 1，p = 0.375，不显著 |
| 平均 token | 34.8 万 | **25.5 万（−27%）** | 64 对中 40 对更少，Wilcoxon p = 0.005 |
| 耗时中位数 | 87 s | 86 s | p = 0.53，没有差别 |

- **token 的节省主要来自 4 道较难的题**，占总节省的 96%，4 道简单题基本不变。节省最多的 5 对占了总节省的 56%：这 5 对里，不加 guard 的运行把 80 万预算花到约 79 万，加 guard 的只用了 11.5 万到 15.5 万。去掉这 5 对，平均仍少 14%。

**② ClassEval 全部运行的对比。** Duo 和 v7 在 ClassEval 上各用 guard 跑了 60 次，和原版按同一题、同一次重复配对：

| | 不加 guard | 加 guard | 配对 |
|---|---:|---:|---|
| Duo 做对 | 41 | **45** | 5 : 1，p = 0.22 |
| Duo 因 "source worktree changed" 被中止 | 6 | **0** | — |
| v7 做对 | 41 | 39 | 1 : 3，p = 0.63 |

- **对 Duo**：guard 消除了越界造成的中止，多做对 4 次。
- **对 v7**：没有实际作用。v7 的候选几乎不越界，60 次里 guard 只拦下 2 条命令；做对的次数少了 2 次是重跑的随机波动，guard 在这几次里没有拦截任何命令。
- **其他测试集**：Duo 几乎不受影响。新 IO2CodeBench 上没有被中止过；BigCodeBench-Hard 上被中止的 2 次（b_771、b_988）是所有方法都没做对的题。
- 两者都加 guard 后对 v7 结论的影响，见 [README](README.md) 第 4.6 节。CrossCheck 和基线的主要比较（README 第 4 节）全部在原版框架上进行，Duo 的这 6 次失败照常计入。

<details>
<summary><b>③ 6 次被中止的运行，加 guard 后各重跑 3 次</b>（共 18 次，点开查看）</summary>

对上面 6 次被中止的 Duo 运行，在同一道题、同一次重复上，用加了 guard 的框架各重跑 3 次。表里 `c_` 开头的是 ClassEval 的题目编号，“第几次”指第几次重复：

| 情况 | 不加 guard（原来） | 加 guard 的 3 次重跑 | 3 次里做对几次 |
|---|---|---|---:|
| c_1 第 3 次 | 被中止（代码 26/26，算解决） | 完成 / 报错\* / 完成，都是 26/26 | 3 |
| c_30 第 3 次 | 被中止（0/31） | 完成 / 报错\* / 完成，都是 31/31 | 3 |
| c_37 第 3 次 | 被中止（代码 18/18，算解决） | 3 次都完成，18/18 | 3 |
| c_79 第 2 次 | 被中止（代码 32/32，算解决） | 3 次都完成，32/32 | 3 |
| c_97 第 1 次 | 被中止（5/13） | 3 次都完成：10/13、11/13、8/13 | 0 |
| c_97 第 2 次 | 被中止（代码 13/13，算解决） | 3 次都完成：13/13、7/13、12/13 | 1 |

\* 另一种框架错误（"workflow runtime failed without finalized execution evidence"），v7 也遇到过，与越界无关，交上来的代码仍是对的。

- 18 次重跑中，候选共尝试在源工作区执行命令 20 次，**全部被 guard 拦下**；“source worktree changed”的中止**一次都没有再出现**。
- 对正确率影响很小：原来 6 次里有 4 次代码本来就是对的，真正被救回来的只有 c_30 这一次；c_97 本身较难，加 guard 后大多仍做不对。所以 guard 的主要作用是**让运行不再因越界而被中止**，而不是提高正确率。
- 这不是公平的对照实验：这 6 次是因为失败才被挑出来的，不加 guard 原样重跑，其中一些也可能碰巧不再越界。所以这组数据只能说明“guard 拦住了越界，也消除了这类中止”，公平的对比要看上面 ② 的 60 次全部运行。

</details>

### 2.7 guard 的局限

- **只是缓解，不是根本修复。** guard 只检查命令文本里的绝对路径，拦不住相对路径（如 `cd ../ws/repo`）、用变量拼出的路径、先写脚本再执行等方式。这一点是根据代码分析得出的，没有实际测试。
- 实验中观察到的越界，都是智能体无意中用绝对路径造成的，guard 能全部拦下。
- 要彻底解决，仍然需要第 2.4 节说的进程级隔离。

---

## 3. 如何复现

两个问题都可以离线复现，不需要模型 API。命令在 Git Bash 里、从项目目录运行：

```bash
K=/d/VMWareMachine2/mywork/kaohe      # 换成你的 kaohe 目录
cd "$K/oc-crosscheck"

# 问题一：在原版框架上复现事件流漏记
MSYS_NO_PATHCONV=1 docker run --rm -v "$K/vendor/OpenCollab-upstream:/kaohe/vendor/OpenCollab:ro" \
  -v "$K/oc-crosscheck/scripts:/kaohe/oc-crosscheck/scripts:ro" -v oc-venv:/venv:ro \
  -w /kaohe/vendor/OpenCollab oc-crosscheck:dev /venv/bin/python /kaohe/oc-crosscheck/scripts/repro_terminal_trace.py

# 问题二：候选越界（加 --bash 测试 bash 路径）。dk.sh 挂载的是带 guard 的框架副本：
# 关闭 guard 时等同原版行为（bash 越界成功），打开 guard 时越界被拒绝
# dk.sh 默认使用 D:/VMWareMachine2/mywork/kaohe；在别的电脑上先 export KAOHE=<你的 kaohe 目录>
scripts/dk.sh sh -c "OPENCOLLAB_CANDIDATE_PATH_GUARD=0 python -I scripts/repro_candidate_escape.py --bash"
scripts/dk.sh python -I scripts/repro_candidate_escape.py --bash
```

预期输出分别和 [results/evidence/repro_terminal_trace_upstream.txt](results/evidence/repro_terminal_trace_upstream.txt)、[results/evidence/repro_candidate_escape.txt](results/evidence/repro_candidate_escape.txt) 一致。

---

## 4. Issue 和 PR

| 内容 | 代码位置 | 状态 |
|---|---|---|
| 问题一 issue | — | 待提交 |
| 问题二 issue | — | 待提交 |
| 问题一的修复 | 分支 `fix/session-terminal-after-resume` | PR 待提交 |
| 问题二的 guard | 分支 `fix/candidate-shell-path-guard` | PR 待提交 |
| 双层经验记忆（[IMPROVEMENTS.md](IMPROVEMENTS.md) 第 1 节） | `vendor/OpenCollab-skills2` | PR 待提交 |
| Team 预算共享（[IMPROVEMENTS.md](IMPROVEMENTS.md) 第 2 节） | `vendor/OpenCollab-fix-budget` 的 `feat/team-seat-budget` 分支 | PR 待提交 |
