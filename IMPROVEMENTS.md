# 框架扩展：双层经验记忆和 Team 预算共享

本文件是 [README.md](README.md) 的一部分，记录给 OpenCollab加的两个扩展：改了什么、怎么做的实验、前后对比的结果。框架问题（bug 和隔离缺陷）见 [ISSUES.md](ISSUES.md)。

两个扩展都**只加参数、不删原有代码**；不传新参数时，框架行为和原版完全一样。

## 一览

| 扩展 | 加了什么 | 在哪里测 | 主要结果 | 代价 |
|---|---|---|---|---|
| [双层经验记忆](#1-双层经验记忆)，用于 single-sh | `agent(memory=...)`：做题前读入训练题上的例题和教训 | BigCodeBench-Hard 20 题 × 3 次 | 只加例题：Pass@1 40% → **50%**（6 胜 0 负，p = 0.031） | token +13% |
| [双层经验记忆](#1-双层经验记忆)，用于 v7 的 Test Designer | 同一功能；记忆里放以前写过的测试，标明哪些在参考答案上成立、哪些不成立以及报错 | 同上 | 写错的测试显著减少：Test Designer 写的用例在参考答案上成立的比例 62.0% → **68.3%**（p = 0.002）；Pass@1 不变 | token **−21%**，耗时 **−25%** |
| [Team 预算共享](#2-team-预算共享) | `team(seat_budget="shared")`：取消每个席位只能用三分之一预算的限制 | 三个测试集，219 对 | Pass@1 48% → **53%**（22 胜 12 负，p = 0.12）；“因预算停下”的运行 53 → 13 次 | token +17% |

> [!NOTE]
> **几个名词。**
> - **v7**：本项目设计的多智能体工作流 CrossCheck 的第 7 版，也是最终方案（[README](README.md) 第 2 节）。
> - **Test Designer**：v7 里的一个角色。它只看题目、不看任何人写的代码，独立写一套测试，后面的环节用这套测试检查 Coder 的代码。它写的测试如果本身是错的（在参考答案上都通不过），就会误判，这是 v7 的主要瓶颈（[README](README.md) 第 1 节第 3 条）。
> - **single-sh**：框架自带的单智能体 Single2，开启了运行代码的能力（[README](README.md) 第 3.1 节）。
> - **席位**：Team 里的一个智能体。本项目的 Team 有 3 个席位，各自独立调用模型，各有一份预算。
> - **因预算停下**：一次 Team 运行没有正常交卷，而是以 `budget exhausted before model call`（“调用模型前预算已用完”）结束。原版里这通常是某个席位用完了自己那三分之一的份额，即使团队总预算还有剩，也不能继续调用模型。按运行计数，219 次里有几次这样结束就记几次。详见第 2.1 节和第 2.5 节第 1 条。
>
> **怎么读这些数字。** “解决”指一次运行通过了全部隐藏测试；“隐藏测试通过率”把部分通过也算上。“配对”是把同一道题、同一次重复的两种做法放在一起比，“6 胜 0 负”指 6 对里只有新做法做对、0 对里只有原做法做对。p 越小越不像运气，一般以 0.05 为界。详细说明见 [README](README.md) 第 3.3 节。

**目录**

- [1. 双层经验记忆](#1-双层经验记忆)
  - [1.1 要解决的问题](#11-要解决的问题)
  - [1.2 框架改了什么](#12-框架改了什么)
  - [1.3 两个记忆库](#13-两个记忆库)
  - [1.4 实验一：给 single-sh 加记忆](#14-实验一给-single-sh-加记忆)
  - [1.5 实验二：给 v7 的 Test Designer 加测试记忆](#15-实验二给-v7-的-test-designer-加测试记忆)
  - [1.6 两个实验合起来看：收益与不足](#16-两个实验合起来看收益与不足)
  - [1.7 如何运行](#17-如何运行)
- [2. Team 预算共享](#2-team-预算共享)
  - [2.1 要解决的问题](#21-要解决的问题)
  - [2.2 框架改了什么](#22-框架改了什么)
  - [2.3 实验设计](#23-实验设计)
  - [2.4 结果](#24-结果)
  - [2.5 分析](#25-分析)
  - [2.6 如何运行](#26-如何运行)

---

## 1. 双层经验记忆

> [!IMPORTANT]
> - **single-sh 上**：只加相似例题，Pass@1 从 40%（24/60）提高到 50%（30/60），6 胜 0 负（p = 0.031），token 只多 13%。抽象经验没有效果。
> - **v7 的 Test Designer 上**：给它看以前写过的测试，哪些在参考答案上成立、哪些不成立、不成立时报了什么错，再加上从中总结的几条写测试的注意事项。它写错的测试显著减少（p = 0.002），v7 的 token 少 21%，Pass@1 不变。
> - **观察**（只基于这 20 道题，原因是推测）：写代码的 single-sh 从例题得到帮助，写测试的 Test Designer 从经验得到帮助。

### 1.1 要解决的问题

OpenCollab 每次运行都从零开始：同一个智能体做完一道题，学到的东西不会带到下一道题。框架里和“记忆”有关的只有会话内的上下文压缩，以及只读的 skill 目录，没有跨任务积累经验的机制。

### 1.2 框架改了什么

代码在官方仓库的一个干净 clone 里：`vendor/OpenCollab-skills2`，基于 `78ca8e37`。

| 文件 | 改动 |
|---|---|
| `opencollab/adapters/memory/experience.py`（新） | `ExperienceMemory`：读取 `insights.json`（抽象经验）和 `examples.jsonl`（例题）；按 TF-IDF 余弦相似度找最像当前题的 2 道例题；把选中的内容拼成一段 “Memory from earlier tasks” 文本。例题可带一个可选字段 `label`，说明例题里放的是什么（默认“通过了测试的代码”） |
| `opencollab/sdk/client.py` | `agent(..., memory=None, memory_layers=("insights", "examples"))`。不传 `memory` 时行为和原版一样；传了就把记忆文本追加到系统提示词后面，目录不存在时报错 |
| `tests/tools/test_experience_memory.py`（新） | 5 个单元测试；`tests/interfaces/test_sdk_api.py` 里 `agent()` 的参数清单也更新了。相关测试 19 个全部通过 |

**v7 怎么用上记忆。** 上面的 `memory` 参数加在 `agent()` 上，single-sh 就是用 `agent()` 启动的，可以直接用。v7 的每个角色也是一个智能体，但它们不是用 `oc.agent()` 启动的：v7 是一个工作流（workflow），角色由工作流内部的接口创建（Test Designer 和两个 Coder 用 `ctx.candidate_agent()`，在各自独立的 worktree 里干活），所以 `oc.agent()` 上加的 `memory` 参数传不到它们那里。为此，在 v7 的代码 [workflows/crosscheck.py](workflows/crosscheck.py) 里补了两个可选参数：

- `td_memory`：记忆文件夹；`td_memory_layers`：用哪几层。
- 设置后，v7 调用同一套记忆代码（`ExperienceMemory`）生成记忆文本，交给 Test Designer。`candidate_agent()` 不能单独设置系统提示词，所以记忆接在 Test Designer 的任务描述后面，模型开工前就能看到。
- 只有 Test Designer 拿到记忆，其他角色、预算和规则都不变；不设这两个参数时，v7 和原来完全一样。

两层记忆分别是：

| 层 | 存在哪个文件 | 内容 | 怎么用 |
|---|---|---|---|
| 第一层：经验（insights） | 记忆文件夹里的 `insights.json` | 几条通用的教训，每条记下来自哪些训练题 | 只展示被至少 2 道不同训练题支持的，按支持的题数排序，最多 8 条 |
| 第二层：例题（examples） | 记忆文件夹里的 `examples.jsonl`，一行一道题 | 训练题的题目原文，加上一段参考内容 | 按和当前题的相似度取前 2 道 |

本项目有两个记忆文件夹：`memory/lib2/`（实验一）和 `memory/lib_tests/`（实验二），见第 1.3 节。

### 1.3 两个记忆库

本项目建了两个记忆库：一个给写代码的 single-sh 用，一个给写测试的 Test Designer 用。两个库都只用**训练题**建出来，建好后就不再改动。

**训练题和测试题分开。** BigCodeBench-Hard 的题按一个固定的随机顺序排好（[README](README.md) 第 3.2 节），本节说的“第几题”都是指这个顺序。测试用的是第 14–33 题，这 20 道题从来没有进过任何记忆。

#### 记忆一：`memory/lib2/`，给 single-sh 用

**原料**：33 道训练题（第 1–13 题和第 54–73 题）以前所有方法的运行记录。每次运行只看一个结果：交上去的代码有没有通过这道题的全部隐藏测试。隐藏测试的报错内容不给任何模型看。

**怎么建**（脚本 [memory/build_memory.py](memory/build_memory.py)）：

1. **例题**：33 道训练题里，有 18 道以前至少被做对过一次。每道存下“题目原文 + 第一份做对的代码”，一共 18 道例题。
2. **经验**：有 12 道训练题既有做对的运行、也有做错的运行。每道题挑一份做对的代码和一份做错的代码交给模型，只告诉它哪份通过了，让它总结“做这类题要注意什么”，最多 3 条，一共得到 36 条。
3. **合并**：再调用一次模型，把意思相同的教训合并，并记下每条来自哪几道题，最后得到 8 条。

<details>
<summary><b>这 8 条经验是什么</b></summary>

1. 输入为空或不正常时，也要返回题目要求类型的对象（列、结构都要对），不要报错或返回 None。
2. 每条代码路径（包括出错时的兜底）都要返回题目承诺的类型和结构。
3. 输出格式、列名、标签、字符串严格照题目写，不要换成意思相近的写法。
4. 只在题目写明的情况下抛题目写明的异常，不要大范围 catch，也不要一出错就抛。
5. 实现保持最小、忠于题目，不加多余的假设、过滤、重新编号或等待逻辑。
6. 数量、范围、是否包含端点等有歧义时，按题目原文和例子确定。
7. 输出的形状按实际数据决定，不假设固定宽度或某列一定存在。
8. 题目给了骨架或要求更新已有数据时，要真的写出函数体、保留原有结构。

</details>

#### 记忆二：`memory/lib_tests/`，给 v7 的 Test Designer 用

**原料**：v7 以前在 13 道训练题（第 1–13 题）上跑过 38 次，每次 Test Designer 都写了一套测试，一共 432 条测试用例。第 54–73 题没有 v7 的运行记录，所以只有 13 道题。

**怎么建**（脚本 [memory/build_test_memory.py](memory/build_test_memory.py)）：

1. **检查每条测试写得对不对，不用模型。** 每道题都有一份标准的正确代码（参考答案）。把每条测试拿到参考答案上跑：
   - 通过了，说明这条测试写对了；
   - 没通过，说明这条测试本身写错了，同时记下参考答案报的错。

   结果是 432 条里 283 条写对、149 条写错。
2. **例题**：每道训练题存下“题目原文 + 最多 3 条写错的测试（附报错）+ 最多 3 条写对的测试”，一共 13 道。测试里用到的辅助函数也一起保存，方便看出错在哪里。
3. **经验**：11 道题有写错的测试。每道题把这些测试和报错交给模型，让它总结“写测试时要注意什么”，最多 3 条，一共 33 条；再合并一次。最后有 5 条至少有 2 道题支持，实际展示的就是这 5 条。

<details>
<summary><b>这 5 条经验是什么，以及一条例题</b></summary>

1. 题目没写明格式、列名、路径约定时，不要自己编；只测题目明确保证的行为。
2. 只断言题目明确保证的性质（类型、是否存在、数量），不要断言题目没要求的副作用或精确数值类型。
3. 测异常时只断言题目点名的异常类型；构造的输入只触发一种错误，不要假设哪项检查先执行。
4. 不要自己假设边界情况的语义（空结果、NaN、什么算数值、随机数是否每次不同）。
5. 题目写了特殊情况的行为，就测那个行为，不要假设它会报错或返回空。

**例题里一条写错的测试（b_917）**：这道题要用股票收盘价做预测。测试自己造了一份数据，把收盘价那一列叫做 `Close`，但参考答案读的是 `closing_price` 这一列，所以在参考答案上报错 `KeyError: 'closing_price'`。例题里会同时给出这条测试、它用来造数据的辅助函数 `_make_df`，以及这条报错。Test Designer 看到后就知道：题目没写明列名时，不要自己编一个。

</details>

> [!NOTE]
> **有没有泄题。** 第 1 步用到了训练题的参考答案，这和记忆一用到的“通过 / 没通过”一样，都来自训练题，属于训练数据。测试题的参考答案和隐藏测试完全没有碰过。另外，第 1 步得到的 283 条写对，和原来判分时记录的数字完全一致。

### 1.4 实验一：给 single-sh 加记忆

- **执行者**：single-sh（能运行代码的 Single2，见 [README](README.md) 第 3.1 节）。
- **数据**：测试题 20 道，每题 3 次独立重复。
- **四组**：不带记忆（已有运行）、只加经验、只加例题、两层都加。记忆库是 `lib2`。
- **比较**：和不带记忆按（题目，重复）配对。

**结果**（各 60 对；v7、Team、Duo 取自 [README](README.md) 第 4 节同一批题的运行，作参照）：

| 方法 | Pass@1 | 对 single-sh 配对 | 隐藏测试通过率 | 平均 token | 平均时间 | 三次重复各做对 |
|---|---:|---|---:|---:|---:|:---:|
| v7 | 32（53%） | | 71.2% | 218,000 | 106 s | |
| Team | 28（47%） | | 70.0% | 394,000 | 103 s | |
| Duo | 26（43%） | | 70.1% | 125,000 | 64 s | |
| single-sh（不带记忆） | 24（40%） | — | 68.7% | 19,700 | 13.3 s | 9 / 8 / 7 |
| + 只加经验 | 25（42%） | 3 胜 2 负，p = 1.0 | 67.9% | 30,300 | 15.7 s | 8 / 9 / 8 |
| **+ 只加例题** | **30（50%）** | **6 胜 0 负，p = 0.031** | 68.7% | 22,300 | 13.7 s | **10 / 10 / 10** |
| + 两层都加 | 28（47%） | 6 胜 2 负，p = 0.29 | 67.8% | 21,300 | 12.3 s | 9 / 10 / 9 |

只加例题时，single-sh 追平了 Team、超过了 Duo，比 v7 少 2 次（和 v7 配对 1 胜 3 负，p = 0.63）。它的 token 约为 v7 的 1/10，时间约为 1/8。

<details>
<summary><b>Pass@1 有变化的配对</b>（60 对里其余结果相同）</summary>

| 方法 | 胜（带记忆做对、不带没做对） | 负（反过来） |
|---|---|---|
| 只加经验 | b_458 第 1、2、3 次（4/5 → 5/5） | b_199 第 1 次、b_854 第 1 次（5/5 → 4/5） |
| 只加例题 | b_971 第 1、2、3 次（9/10 → 10/10）、b_854 第 2、3 次（4/5 → 5/5）、b_530 第 3 次（3/7 → 7/7） | 无 |
| 两层都加 | 和只加例题相同的 6 次 | b_199 第 3 次（5/5 → 4/5）、b_530 第 1 次（7/7 → 3/7） |

</details>

**分析：**

1. **例题有效，而且效果稳定。** 加了例题后，没有一道原来做对的题变错，三次重复每次都比不带记忆多做对 1–3 道。但提升只集中在 3 道题上，换一批题，幅度可能不同。
2. **例题帮的是“写法”，不是“同类知识”。** 检索出的例题和当前题内容往往并不相近，比如“列目录文件”检索到的是“时间戳差值”。所以例题起作用，更可能是因为它示范了一份能通过隐藏测试的完整代码长什么样：严格按函数签名写、返回格式照题目、异常照题目抛。这一点是推测，没有单独验证。
3. **例题让“差一点就全对”的题补全了，但整体质量没变。** 变成做对的那几次，每次都只多过了 1 条测试；同时也有少数运行反而错得更多，两边抵消，所以隐藏测试通过率没变。准确的说法是“例题让快做对的题更容易补全”，而不是“代码整体写得更好”。
4. **抽象经验没有用。** 这些通用建议在一道题上有帮助，换一道题可能起反作用，有赢有输，最后打平。从别的题总结出来的通用建议，很难迁移到新题上。
5. **两层都加不如只加例题。** 例题带来的提升都保留了，但加上经验后又多输了 2 次，说明经验在这里是干扰。

### 1.5 实验二：给 v7 的 Test Designer 加测试记忆

**为什么做：** v7 的瓶颈是 Test Designer 写错测试：BigCodeBench-Hard 上它写的用例只有约 66% 能在参考答案上通过（[README](README.md) 第 1 节第 3 条）。实验一先在便宜的 single-sh 上证明了记忆有效，这里再把记忆用到 Test Designer 上。它的任务是写测试，所以记忆里直接放以前写过的测试（`lib_tests`，第 1.3 节）。

同样 20 题 × 3 次 × 3 种记忆（只加经验、只加例题、两层都加），共 180 次，和原来的 v7 按（题目，重复）配对。中途服务商余额用完一次，受影响的 3 次运行已排除并在充值后重跑，记录在 `results/evidence/excluded_runs.jsonl`。

表里有两列需要先说明：

- **用例成立比例**：衡量 Test Designer 写的测试有多少是对的。它写的每个测试函数算一条用例；把每条用例拿到这道题的参考答案（标准的正确代码）上跑，通过了就是“成立”，说明这条用例写对了；没通过就是用例本身写错了（连正确代码都过不了）。一次运行的比例 = 成立的用例数 ÷ 用例总数，表里是对所有运行取平均。“62.0% → 68.3%”的意思是：不带记忆时，Test Designer 写 100 条用例平均有 62 条是对的；加了记忆后有 68 条是对的。“24 升 6 降”是把同一道题、同一次重复的两次运行放在一起比，两边都写了测试的 53 对里，24 对加记忆后比例更高，6 对更低，其余持平。
- **三次重复各做对**：每道题独立做 3 次，相当于把这 20 道题完整考了 3 遍。这一列是 3 遍里每一遍各做对几道（每遍满分 20）。比如“10 / 11 / 11”表示第 1 遍做对 10 道，第 2、3 遍各做对 11 道。用来看效果是不是只出现在某一遍，也就是是不是运气。

| 方法 | Pass@1 | 对 v7 配对 | 隐藏测试通过率 | 用例成立比例（配对） | 每次用例数 | 平均 token | 中位 token | 平均时间 | 三次重复各做对 |
|---|---:|---|---:|---|---:|---:|---:|---:|:---:|
| v7（不带记忆） | 32 | — | 71.2% | — | 13.4 | 218,000 | 129,100 | 106 s | 10 / 10 / 12 |
| + 测试经验 | 34 | 5 胜 3 负，p = 0.73 | 72.4% | 62.1% → 67.6%，19 升 11 降，p = 0.054 | 9.2 | 167,500 | 110,100 | 80 s | 12 / 12 / 10 |
| + 测试例题 | 29 | 1 胜 4 负，p = 0.38 | 66.6%（变差，p = 0.024） | 58.1% → 62.4%，19 升 13 降，p = 0.12 | 12.8 | 237,700 | 112,200 | 111 s | 8 / 11 / 10 |
| **+ 两层都加** | 32 | 3 胜 3 负，p = 1.0 | 72.4% | **62.0% → 68.3%，24 升 6 降，p = 0.002** | 9.9 | **171,500** | **96,400** | **80 s** | 10 / 11 / 11 |

**分析：**

1. **测试记忆解决了写错测试的问题。** 两层都加时，用例成立比例显著提高（p = 0.002）。在比例有变化的 13 道题里，11 道变好、2 道变差，不是一两道题撑起来的。
2. **测试变准了，但 Pass@1 没有变，收益体现在成本上。** v7 本来就有几层兜底（见 [README](README.md) 第 2 节）：Coder 的代码没通过测试时，审核员 Auditor 会先判断是不是测试本身写错了，写错的用例就不再使用；还解决不了，就让另一个程序员 Coder B 从头独立重写一份，再比较选出更好的（这一层叫 L4）。所以测试写错了，原来也常常能被后面的环节纠正，只是要多花 token。测试变准后，两层都加时平均 token 少 21%，中位 token 少 25%，耗时少 25%，Pass@1 和隐藏测试通过率保持不变。
3. **经验比例题有用。** 效果来自那 5 条简短的教训。只加例题时测试只变准了一点，token 反而多了 9%，隐藏测试通过率还显著变差。可能的原因见第 1.6 节“观察”。

### 1.6 两个实验合起来看：收益与不足

> [!IMPORTANT]
> 同样 20 道题 × 3 次，和不带记忆的同一方法配对：
>
> | 实验 | 加记忆的角色 | 记忆里放什么 | 最好的一组 | Pass@1 | 用例成立比例 | token |
> |---|---|---|---|---|---|---|
> | 一 | single-sh | 做对过的题和代码 | 只加例题 | 24 → **30**（6 胜 0 负） | — | +13% |
> | 二 | v7 的 Test Designer | 以前写过的测试及其对错 | 两层都加 | 32 → 32 | 62.0% → **68.3%**（p = 0.002） | **−21%** |

#### 收益

1. **single-sh 做对的题变多了，成本几乎不变。** 只加例题，Pass@1 从 40% 提高到 50%，token 只多 13%，约为 v7 的 1/10。同一批题上，single-sh 加例题做对 30 次，v7 加测试记忆做对 32–34 次，v7 的 token 约是前者的 7.5 倍。
2. **Test Designer 写错的测试变少了，v7 变便宜了。** 两层都加时，它写的用例里写对的比例从 62.0% 提高到 68.3%（p = 0.002），v7 的平均 token 少 21%，耗时少 25%，Pass@1 和隐藏测试通过率保持不变。
3. **框架改动小。** 只给 `agent()` 加了一个可选参数，v7 里另加了一个开关；不传参数时，行为和原版完全一样。

#### 不足

1. **测试范围小。** 只在 BigCodeBench-Hard 的 20 道测试题上测过。新 IO2CodeBench 和 ClassEval 没有可用来建记忆的训练题，没有测。
2. **训练题少。** 写代码的记忆来自 33 道训练题，测试记忆只来自 13 道。记忆里能检索到的相似题很少，检索出来的例题和当前题内容往往并不相近。
3. **single-sh 的提升只集中在少数题上。** 6 次胜利只来自 3 道题，换一批题，提升幅度可能不同。
4. **Test Designer 的测试变准了，但 v7 做对的题没有变多。** 这次的收益只体现在成本上。
5. **有的组合反而变差。** 只给 Test Designer 测试例题、不给经验时，v7 的隐藏测试通过率显著下降（71.2% → 66.6%，p = 0.024），token 还多了 9%。
6. **测试记忆依赖参考答案。** 建测试记忆时，要用训练题的正确代码来判断每条测试写得对不对。真实项目里不一定有这样的正确代码。
7. **记忆是一次性建好的。** 建好后就冻结，做新题时不会继续积累经验。原本计划在此基础上加入自我进化机制：做新题时把做对的题加入例题，让记忆越用越大，缓解训练题少、检索不准的问题。难点在于做新题时没有隐藏测试，无法确知是否真的做对，误判的代码进入记忆会污染后续结果；同时记忆随做题顺序变化，评估需要固定顺序并多次重复。受算力限制，这一步没有实现。

#### 观察

两个角色从不同的记忆层得到了帮助：single-sh 写代码时，例题有效、经验没有效果；Test Designer 写测试时，经验有效，只给例题效果不明显。可能的原因是，写代码时一份通过的完整代码可以直接参照；而对 Test Designer 来说，经验提醒它哪些事不能乱假设，它就少写那些没把握的用例：每次的用例从 13.4 条降到 9–10 条，写对的比例明显提高。只给例题时，用例数和原来差不多（12.8 条），写对的比例也没有明显提高，例题没有改变它写测试的方式。

### 1.7 如何运行

下面的命令都在 Git Bash 里、从项目目录运行。先设置路径：

```bash
K=/d/VMWareMachine2/mywork/kaohe      # 换成你的 kaohe 目录
P=$K/oc-crosscheck
cd "$P"
```

准备工作（Docker 镜像 `oc-crosscheck:dev`、虚拟环境卷 `oc-venv`、各题的依赖环境卷、模型配置 `vendor/OpenCollab/configs/.env`）见 [README](README.md) 第 6.1 节。

#### 复现文档里的两张结果表（不需要模型，不花钱）

两个实验的全部运行都已记录在 `results/runs.jsonl` 里，直接统计即可：

```bash
python scripts/memory_pairs.py           # 两个实验都输出
python scripts/memory_pairs.py --exp 1   # 只看实验一（single-sh）
python scripts/memory_pairs.py --exp 2   # 只看实验二（v7 的 Test Designer）
```

输出的 Pass@1、胜负、p 值、隐藏测试通过率、用例成立比例、用例数、token 和每次重复做对的题数，就是第 1.4 节和第 1.5 节表里的数字。

#### 运行框架的单元测试（不需要模型）

```bash
MSYS_NO_PATHCONV=1 docker run --rm -v "$K/vendor/OpenCollab-skills2:/kaohe/vendor/OpenCollab" \
  --tmpfs /kaohe/vendor/OpenCollab/configs -v oc-venv:/venv:ro -w /kaohe/vendor/OpenCollab oc-crosscheck:dev \
  /venv/bin/python -m pytest -q -p no:cacheprovider tests/tools/test_experience_memory.py tests/interfaces/test_sdk_api.py
```

#### 重新建记忆库（可选，会调用模型）

> [!WARNING]
> 实验用的是已经冻结的 `memory/lib2/` 和 `memory/lib_tests/`。模型每次输出不同，重新建出来的记忆和原来不一样，所以**请输出到新的文件夹**，不要覆盖这两个。

```bash
# 记忆一：写代码的记忆。模型配置从 stdin 传进容器
MSYS_NO_PATHCONV=1 docker run --rm -i --memory 1500m -v "$K:/kaohe" \
  -v "$K/vendor/OpenCollab-skills2:/kaohe/vendor/OpenCollab:ro" --tmpfs /kaohe/vendor/OpenCollab/configs \
  -v oc-venv:/venv:ro -e PYTHONDONTWRITEBYTECODE=1 -w /kaohe/oc-crosscheck oc-crosscheck:dev \
  /venv/bin/python memory/build_memory.py --out memory/lib2_rebuild < "$K/vendor/OpenCollab/configs/.env"

# 记忆二第 1 步：在 13 道训练题的参考答案上检查每条测试（不需要模型，结果写到 memory/test_labels/）
for t in $(python -c "import sys; sys.path.insert(0,'evolve'); from driver import ORDER; print(' '.join(ORDER[:13]))"); do
  VOL=$(python -c "import json,sys; print(json.load(open(sys.argv[1]))['env_volume'])" tasks_bcb/$t/meta.json)
  MSYS_NO_PATHCONV=1 docker run --rm --network none --memory 4g -v "$P:/kaohe/oc-crosscheck" -v oc-venv:/venv:ro \
    -v "$VOL:/env:ro" -v oc-pythons:/pythons:ro -v oc-hf-cache:/hf -e HF_HOME=/hf -e MPLBACKEND=Agg \
    -e XC_TEST_PYTHON=/env/venv/bin/python -e PYTHONDONTWRITEBYTECODE=1 -w /kaohe/oc-crosscheck oc-crosscheck:dev \
    /venv/bin/python memory/build_test_memory.py label --task $t
done

# 记忆二第 2 步：生成例题和经验（会调用模型）
MSYS_NO_PATHCONV=1 docker run --rm -i --memory 4g -v "$K:/kaohe" \
  -v "$K/vendor/OpenCollab-skills2:/kaohe/vendor/OpenCollab:ro" --tmpfs /kaohe/vendor/OpenCollab/configs \
  -v oc-venv:/venv:ro -e PYTHONDONTWRITEBYTECODE=1 -w /kaohe/oc-crosscheck oc-crosscheck:dev \
  /venv/bin/python memory/build_test_memory.py build --out memory/lib_tests_rebuild < "$K/vendor/OpenCollab/configs/.env"
```

#### 重新跑实验（会调用模型）

每次运行在独立的容器里进行，结果追加到 `results/runs.jsonl`。`batch_mem.sh` 会**跳过已经有记录的（题目，方法，重复）**，所以：
- 中途断了，再执行一次同样的命令就能从断点继续；
- 想从头重跑，要先把 `results/runs.jsonl` 里对应方法的记录移到别处（先备份），否则什么都不会跑。

```bash
# 实验一：single-sh 加三种记忆，20 题 × 3 次 × 3 种 = 180 次，1 个并行
scripts/batch_mem.sh plans/memory_test.txt 1
# 实验二：v7 的 Test Designer 加三种测试记忆，180 次，3 个并行
scripts/batch_mem.sh plans/v7_tmem_test.txt 3

# 用重建的记忆库跑：设置 MEMORY_LIB（实验一默认 memory/lib2，实验二默认 memory/lib_tests）
MEMORY_LIB="$P/memory/lib2_rebuild" scripts/batch_mem.sh plans/memory_test.txt 1

# 统计
python scripts/memory_pairs.py
```

两个实验的对照组不在上面的计划里：实验一的对照是不带记忆的 `single-sh`（`plans/single_sh_test.txt`），实验二的对照是 [README](README.md) 第 4 节主实验里的 `crosscheck:v7@s2` 运行。它们已经有记录，统计时会自动配对。

#### 在自己的代码里使用

```python
# 单智能体：做题前读入记忆
await oc.agent(prompt, memory="memory/lib2", memory_layers=("examples",))

# v7：只给 Test Designer 加记忆（workflows/crosscheck.py 的可选参数）
await oc.workflow("crosscheck", {"goal": prompt, "variant": "v7", "allow_unisolated_shell": True,
                                 "td_memory": "memory/lib_tests",
                                 "td_memory_layers": ["insights", "examples"]},
                  agent_profile="single2")
```

---

## 2. Team 预算共享

> [!IMPORTANT]
> 默认 `"equal"` 和原版完全一样；设成 `"shared"` 后，每个席位可以用团队还没用完的全部预算。三个测试集合计 219 对：
> - Pass@1 105（48%）→ **115（53%）**，22 胜 12 负（p = 0.12）；隐藏测试通过率 68.3% → **72.5%**（p = 0.075）。
> - 因预算停下的运行 53 → **13** 次；平均 token 多 17%。
> - 提升在新 IO2CodeBench 和 ClassEval 上，BigCodeBench-Hard 上没有变化。改后的 Team 和 v7 做对的题一样多（115 对 115），v7 便宜约 43%。

### 2.1 要解决的问题

**每个席位只能花三分之一的预算。** Team 由 3 个席位（3 个智能体）组成，团队总预算是 80 万 token。框架把总预算平均分给每个席位：每个席位最多用 80 万 ÷ 3 ≈ 26.7 万，只有 Single2 单独做题时的三分之一。这个比例写死在框架代码里（`opencollab/domain/scheduler.py` 的常量 `PER_AGENT_BUDGET_SHARE = 1.0`），用户没法通过参数修改。

**席位用完自己那份就会被停下，即使团队还有预算。** 打个比方：三个人一起出差，公司给 80 万经费，但规定每人最多花 26.7 万。一个人花到上限后就不能再花钱，哪怕另外两个人的钱还没怎么用。已有记录里，2 个开发集和 3 个测试集上有 75 次 Team 运行因为“调用模型前预算已用完”而结束，其中 28 次团队总预算还剩至少 20 万。

**运行记录还看不出是这个原因。** 框架文档说，席位到上限时会记一条 `agent_cap_reached` 事件。但 273 次 Team 运行里，这条记录一次都没出现过。原因是：每次调用模型前，框架会先估算这次要用多少 token；如果剩下的额度不够，就直接停下。比如某个席位还剩 1.6 万，下一次调用要 3 万，它就会停下，这时额度还没有用到零，所以“到上限”的记录永远不会写出来。结果，运行记录里只写着笼统的“预算已用完”，看起来像是团队总预算花光了，实际却是席位自己的那一份不够了。

### 2.2 框架改了什么

代码在官方仓库的另一个干净 clone 里：`vendor/OpenCollab-fix-budget`，分支 `feat/team-seat-budget`，基于 `78ca8e37`。

| 文件 | 改动 |
|---|---|
| `opencollab/domain/scheduler.py` | 新增 `SEAT_BUDGET_MODES = ("equal", "shared")` 和 `seat_budget_share(mode, 席位数)`：`"equal"` 返回 1.0（原版），`"shared"` 返回席位数，即每个席位的上限等于总预算 |
| `opencollab/application/scheduler.py` | `Scheduler(..., seat_budget="equal")`，检查取值；和按角色分配预算（`role_budgets`）同时使用时报错 |
| `opencollab/application/_scheduler_persistence.py` | 每席位上限按 `seat_budget` 计算；trace 里记录的 share 也随之改变 |
| `scheduler_factory.build_scheduler`、两个 `run_team`、`sdk/client.py` 的 `team()` | 逐层传递 `seat_budget`，默认 `"equal"` |
| `tests/tools/test_seat_budget_modes.py`（新） | 6 个单元测试；`tests/interfaces/test_sdk_api.py` 的参数清单加了 `seat_budget` |

团队总预算仍然受 80 万的上限约束，`"shared"` 只取消每个席位的份额限制。改完后跑了一遍全量测试：10315 个通过，只有 1 个失败，是检查 `team()` 参数清单的测试，因为清单里还没有新加的 `seat_budget`。把它加进清单后，重跑了相关的 20 个测试，全部通过。

### 2.3 实验设计

- **数据**：三个测试集（BigCodeBench-Hard 33 题、新 IO2CodeBench 20 题、ClassEval 20 题），每题 3 次，共 219 次。
- **对照**：[README](README.md) 第 4 节的 `team-collab@s2` 就是 `"equal"` 组；`team-collab@s2+shared` 的模型、总预算、提示词、team 文件和运行脚本都和它相同。
- **比较**：按（题目，重复）配对。

### 2.4 结果

| 测试集 | 方法 | Pass@1 | 隐藏测试通过率 | 因预算停下 | 平均 token | 中位 token | 三次重复各做对 |
|---|---|---:|---:|---:|---:|---:|:---:|
| BigCodeBench-Hard（99） | equal（原版） | 38（38%） | 67.5% | 16 | 426,500 | 381,700 | 14 / 11 / 13 |
| | shared | 39（39%） | 66.9% | 4 | 515,300 | 447,200 | 12 / 13 / 14 |
| 新 IO2CodeBench（60） | equal（原版） | 26（43%） | 52.6% | 29 | 373,900 | 256,900 | 9 / 8 / 9 |
| | shared | 33（55%） | 64.0% | 7 | 459,000 | 404,000 | 10 / 11 / 12 |
| ClassEval（60） | equal（原版） | 41（68%） | 85.3% | 8 | 476,200 | 442,000 | 12 / 15 / 14 |
| | shared | 43（72%） | 90.2% | 2 | 508,600 | 457,700 | 15 / 14 / 14 |
| **合计（219）** | equal（原版） | 105（48%） | 68.3% | 53 | 425,700 | 393,700 | 35 / 34 / 36 |
| | **shared** | **115（53%）** | **72.5%** | **13** | 498,000 | 444,400 | 37 / 38 / 40 |

配对比较（shared 对 equal）：

| 测试集 | Pass@1 胜 : 负 | p | 隐藏测试通过率 升 / 降 | p |
|---|:---:|---:|:---:|---:|
| BigCodeBench-Hard | 9 : 8 | 1.0 | 13 / 16 | 0.83 |
| 新 IO2CodeBench | 10 : 3 | 0.092 | 13 / 6 | 0.044 |
| ClassEval | 3 : 1 | 0.63 | 10 / 1 | 0.006 |
| **合计** | **22 : 12** | 0.12 | **36 / 23** | 0.075 |

### 2.5 分析

1. **机制按设计起了作用：因预算停下的运行从 53 次降到 13 次。**
   - **53 次是什么**：原版（equal）的 219 次运行里，有 53 次以 `budget exhausted before model call` 结束，也就是约四分之一的运行没能正常交卷，而是某个席位的份额用完后被框架停下。剩下的预算还在，但这个席位不能再用。
   - **13 次是什么**：改成 shared 后，同样 219 次里只有 13 次这样结束。这 13 次用掉的 token 都在 75.6 万到 83.8 万之间，也就是团队 80 万的**总预算**真的用完了，不再是某个席位的份额限制。
   - **少掉的 40 次去哪了**：这些运行的席位接着用团队剩下的预算干活，最后正常交卷。
   - **这些运行有没有变好**：在 equal 组因预算停下的那 53 对里，shared 做对了 18 次，equal 只做对 13 次；其中新 IO2CodeBench 上是 8 对 2。也就是说，被份额卡住的运行，放开后有一部分能做对。
2. **效果取决于数据集。**
   - **新 IO2CodeBench 最明显**：Pass@1 43% → 55%，通过率高 11 个百分点。这里 equal 组有 29 次因预算停下，几乎每两次就有一次，席位份额是实际的瓶颈。
   - **ClassEval**：Pass@1 只多 2 次，但通过率 85.3% → 90.2%（p = 0.006）。多出的预算让席位把更多方法写完。
   - **BigCodeBench-Hard 没有变化**（9 胜 8 负）。这里 equal 组只有 16 次因预算停下，失败主要是猜错了题目没写明的约定（[README](README.md) 第 1 节第 3 条），多给预算也解决不了。
3. **成本。** 平均 token 多 17%（42.6 万 → 49.8 万），因为席位能继续用团队剩下的预算。平均耗时反而少了（104 s → 89 s），但两组在不同时间段跑，服务商响应速度不同，耗时不能直接比。
4. **对 v7 结论的影响。** 合计 219 对上，v7 和 shared Team 都做对 115 次，配对 11 胜 11 负（p = 1.0）；隐藏测试通过率 v7 74.6%、shared Team 72.5%（p = 0.25）；v7 的平均 token 28.5 万，比 shared Team 少 43%。分数据集看，BigCodeBench-Hard 上 v7 仍领先（43 对 39，8 胜 4 负），新 IO2CodeBench 和 ClassEval 上 shared Team 略高。所以：**在原版框架上 v7 好于 Team；改了预算规则之后，两者做对的题一样多，v7 便宜约 43%。** 和 [README](README.md) 第 4.6 节的 guard 一样，第 4 节的主结果仍以原版框架为准，因为那里所有方法在同一个运行环境下比较。

### 2.6 如何运行

下面的命令都在 Git Bash 里、从项目目录运行。先设置路径：

```bash
K=/d/VMWareMachine2/mywork/kaohe      # 换成你的 kaohe 目录
cd "$K/oc-crosscheck"
```

准备工作（Docker 镜像 `oc-crosscheck:dev`、虚拟环境卷 `oc-venv`、各题的依赖环境卷、模型配置 `vendor/OpenCollab/configs/.env`）见 [README](README.md) 第 6.1 节。

#### 复现文档里的结果表（不需要模型，不花钱）

两组的全部运行都已记录在 `results/runs.jsonl` 里，直接统计即可：

```bash
python scripts/seat_budget_pairs.py
```

它按测试集分别输出 equal 组和 shared 组的 Pass@1、隐藏测试通过率、因预算停下的次数、平均 / 中位 token、每次重复做对的题数，以及配对胜负和 p 值，就是第 2.4 节两张表里的数字；还会输出第 2.5 节用到的两组数：equal 组因预算停下的那些配对里两边各做对几次，以及 v7 和 shared Team 的对比。

#### 运行框架的单元测试（不需要模型）

```bash
MSYS_NO_PATHCONV=1 docker run --rm --memory 1500m -v "$K/vendor/OpenCollab-fix-budget:/src:ro" -v oc-venv:/venv:ro \
  -e PYTHONDONTWRITEBYTECODE=1 oc-crosscheck:dev sh -c "git config --global --add safe.directory '*'; \
  mkdir -p /kaohe/vendor && cp -r /src /kaohe/vendor/OpenCollab && cd /kaohe/vendor/OpenCollab && \
  /venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/tools/test_seat_budget_modes.py tests/interfaces/test_sdk_api.py"
```

框架以只读方式挂进容器，再拷贝一份来跑测试，不会改动 `vendor/OpenCollab-fix-budget` 里的任何文件。

#### 重新跑实验（会调用模型）

```bash
# 方法名加 +shared：脚本改用 vendor/OpenCollab-fix-budget，并传 seat_budget="shared"。219 次，3 个并行
scripts/batch.sh plans/team_shared_test.txt 3
python scripts/seat_budget_pairs.py
```

每次运行在独立的容器里进行，结果追加到 `results/runs.jsonl`。`batch.sh` 会**跳过已经有记录的（题目，方法，重复）**：中途断了，再执行一次同样的命令就能从断点继续；想从头重跑，要先把 `results/runs.jsonl` 里 `team-collab@s2+shared` 的记录移到别处（先备份），否则什么都不会跑。

对照组 equal 不在这个计划里，它就是 [README](README.md) 第 4 节主实验里的 `team-collab@s2` 运行，已经有记录，统计时会自动配对。

#### 在自己的代码里使用

```python
await oc.team(prompt, seat_budget="shared")
```
