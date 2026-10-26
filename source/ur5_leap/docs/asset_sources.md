# 资产来源与获取记录

获取日期：2026-10-26。全部文件限制在 `source/ur5_leap/`。未修改 IsaacLab 官方任务/资产源码。

| 来源 ID | 仓库 | 分支 | 固定 commit | 本地入口 | 许可 |
|---|---|---|---|---|---|
| ur | [UniversalRobots/Universal_Robots_ROS2_Description](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description) | rolling | `81f7c9fe003c2f0e02eec5a7253f1b262ad38b61` | `assets/official/ur5/` | BSD-3-Clause |
| sim | [leap-hand/LEAP_Hand_Sim](https://github.com/leap-hand/LEAP_Hand_Sim) | master | `150bc3d4b61fd6619193ba5a8ef209f3609ced89` | `assets/official/leap_hand_v1_right/sim_reference/` | 仓库 MIT；CAD 声明另存 |
| lab | [leap-hand/LEAP_Hand_Isaac_Lab](https://github.com/leap-hand/LEAP_Hand_Isaac_Lab) | main | `c576e6a83183ba504aef8f57015f2899b799db1a` | `assets/official/leap_hand_v1_right/isaac_lab_reference/` | README 声明 MIT，无独立根 LICENSE |
| cord | [xuanxuanzzzii/cordvip](https://github.com/xuanxuanzzzii/cordvip) | main | `ad6d441abe7b0480cf79b0311db266965c1313b6` | `assets/references/cordvip/ur5_leaphand/` | 根 MIT，上游资产条款保留 |
| bodex | [JYChen18/BODex](https://github.com/JYChen18/BODex) | main | `06b9a3c90870d33bde9d6c665d4ed2819471407e` | `assets/references/bodex/ur5_leap/` | NVIDIA 非商业研究/评估，含 LICENSE_ASSETS |
| website | [LEAP v1 官方 CAD](https://v1.leaphand.com/leap_cad) | 无 | 无公开下载 commit，按 URL、日期、SHA-256 固定 | `assets/official/leap_hand_v1_right/cad/`、`urdf/website_right/` | 页面 CC BY-NC-SA，未注明版本 |

## 获取方式和文件对应

先实际读取 GitHub 递归文件树，按 commit 锁定清单；通过 GitHub codeload 下载归档，仅提取需要的文件。
每个提取文件先校验 Git blob SHA-1。遇到 Git LFS 指针时，从 GitHub 官方 media 地址获取真实 payload，
按指针的 SHA-256 和大小验证。最终所有落盘文件再保存 SHA-256，未改写上游 URDF/mesh/配置字节。
文件树中与模型无关的 BODex `.DS_Store` 未纳入选择；没有下载其余机器人或训练数据。
官网首次获取从真实页面解析链接；已有完整下载记录时，恢复只使用记录中的 URL、大小和 SHA-256，
不依赖官网最新页面，也不接受被上游替换的同名文件。

- 原文件到本地文件的完整映射：[sources.lock.json](../assets/sources.lock.json)。
- 实际 URL、字节大小、SHA-256 和 LFS oid：[downloads.json](../assets/downloads.json)。
- 人可读的实际下载列表：[download_inventory.md](download_inventory.md)。
- 每个模型的背景和安装参数：各资产根目录的 `SOURCE.md`。
- 官网 Right URDF ZIP 的 17 个解压文件全部保留，包括 8 个 STL、8 个 `.part` 和 `robot.urdf`。

官网的上掌板文件名是 `palm_upper_xarm_franka.*`，页面条目明确标为 xArm/Franka/UR5；
不能因为文件名未含 UR5 就另造路径。完整右手上游文件后缀为 `.step`，本地按 STP 类别保存为 `.stp`，内容不变。

## 版本和真实性边界

UR 官方来源按 `ur_type=ur5` 展开，保留四个 `config/ur5/` 参数文件和 14 个 UR5 mesh；没有选择 ur5e 配置/mesh。
UR5 配置明确引用 CB3 手册；肩部与腕部尺寸和 UR5e 不同，工厂校准仍需从实验室这台机械臂获取。

手的主来源明确是官网 v1 的 Download Right URDF；8 个网格和关节定义已与官方 Sim 模型交叉比较。
没有下载官网左手包，也没有使用 v2。CordViP 原资产目录包含未被当前模型引用的 left 网格，按完整保留参考目录的要求保存，
不代表选择了左手。Full 的电机参数还需要根据真机 XC330-M288-T 和实际控制设置核对。

官网 CAD 的非商业/相同方式共享声明与部分代码仓库的 MIT 声明分别保留；没有统一改写第三方资产许可。

## 大文件

沿用本仓库 2,000 KiB 的检查阈值。超过阈值的资产本地保留，用 `.gitignore` 排除，
以清单和下载脚本恢复；没有强制提交、删除或改成无法解析的假文件。
本目录 `.gitattributes` 对原始资产显式关闭父级 LFS 过滤及文本换行转换，以保持小文件字节一致；
大文件不进入普通 Git，也不进入此项目的 LFS。
服务器 `git pull` 后先执行 README 中的下载命令，再运行校验。大小和路径见 [large_files.md](large_files.md)。
