# CordViP UR5 与官方 UR5 CB3 的结构化比较

比较日期：2026-10-28。检查的仓库基线：`7ffe8150c`。本报告结论为 **B. NOT_EQUIVALENT**。

CordViP 的六轴运动学属于 UR5 CB3，经过固定基座坐标对齐和 link frame 换算后与当前官方 CB3 描述一致。
但质量、质心、主惯量和速度限制存在实际差异；特别是腕部主惯量差异达到 100～256 倍，不能将两者视为同一个仿真动力学模型。
依照本次任务的失败分支，完成比较报告后停止切换学习模型，不创建指向 CordViP 的统一配置，不修改现有测试脚本。

## 1. 输入与方法

- 官方 URDF：`assets/official/ur5/generated/ur5_cb3.urdf`。
- CordViP URDF：`assets/references/cordvip/ur5_leaphand/ur5_leaphand.urdf`。
- 完整机器可读证据：[cordvip_vs_official_ur5.json](cordvip_vs_official_ur5.json)。包含原始关节字段、全部惯量矩阵、坐标换算矩阵、258 组输入姿态、mesh 几何摘要和完整 SHA-256。
- 直接解析 XML，只读取有效元素；被注释的 mount 参数没有参与比较。
- 使用 CPU 上的 Python 3、NumPy 2.2.6 做矩阵运算，没有启动 Isaac Sim、GPU 仿真、训练或真机标定。
- 位置/角度限制比较容差为 `1e-9`；运动学比较容差为 `1e-6 m/rad`。惯量判定同时比较质量和不随坐标旋转改变的主惯量。

| 来源 | 仓库 | 分支 | 固定 commit |
|---|---|---|---|
| ur | UniversalRobots/Universal_Robots_ROS2_Description | rolling | `81f7c9fe003c2f0e02eec5a7253f1b262ad38b61` |
| cord | xuanxuanzzzii/cordvip | main | `ad6d441abe7b0480cf79b0311db266965c1313b6` |

| 输入 | SHA-256 |
|---|---|
| official | `4f531238172e6b5e45c1921977bd55742569b9398e8ffae45cd9d4ab60ffd99b` |
| cordvip | `1ea131081012544a772bcd4e111456de966523304d3a8efb81e7edf42151ba24` |

## 2. 六个关节与 link 链

两者的指定六个关节均为 `revolute`，没有增加或减少机械臂自由度。下面列出实际 parent/child 和 axis（axis 是各自 joint frame 中的表示）。

| 关节 | 来源 | parent → child | axis |
|---|---|---|---|
| `shoulder_pan_joint` | official | `base_link_inertia` → `shoulder_link` | (0, 0, 1) |
| `shoulder_pan_joint` | cordvip | `base_link` → `shoulder_link` | (0, 0, 1) |
| `shoulder_lift_joint` | official | `shoulder_link` → `upper_arm_link` | (0, 0, 1) |
| `shoulder_lift_joint` | cordvip | `shoulder_link` → `upper_arm_link` | (0, 1, 0) |
| `elbow_joint` | official | `upper_arm_link` → `forearm_link` | (0, 0, 1) |
| `elbow_joint` | cordvip | `upper_arm_link` → `forearm_link` | (0, 1, 0) |
| `wrist_1_joint` | official | `forearm_link` → `wrist_1_link` | (0, 0, 1) |
| `wrist_1_joint` | cordvip | `forearm_link` → `wrist_1_link` | (0, 1, 0) |
| `wrist_2_joint` | official | `wrist_1_link` → `wrist_2_link` | (0, 0, 1) |
| `wrist_2_joint` | cordvip | `wrist_1_link` → `wrist_2_link` | (0, 0, 1) |
| `wrist_3_joint` | official | `wrist_2_link` → `wrist_3_link` | (0, 0, 1) |
| `wrist_3_joint` | cordvip | `wrist_2_link` → `wrist_3_link` | (0, 1, 0) |

官方完整链：

```text
world → fixed → base_link → fixed → base_link_inertia
  → shoulder_link → upper_arm_link → forearm_link
  → wrist_1_link → wrist_2_link → wrist_3_link
```

CordViP 链：

```text
base_link → shoulder_link → upper_arm_link → forearm_link
  → wrist_1_link → wrist_2_link → wrist_3_link
  → fixed → ee_link → fixed → palm_lower
```

官方的 `base_link_inertia` 是固定连接的物理基座，质量/几何应与 CordViP 的 `base_link` 比较。
`world`、`base`、`flange`、`tool0`、`ft_frame` 等辅助 frame，以及 CordViP 的 `ee_link` 和 LEAP 安装链，不作为机械臂本体不等价的依据。

### 原始 joint origin

xyz 单位为 m，rpy 单位为 rad。下表是各自 parent frame 下的原始数字，不能直接逐列相减后判断运动学是否不同。

| 关节 | 来源 | origin xyz | origin rpy |
|---|---|---|---|
| `shoulder_pan_joint` | official | (0, 0, 0.089159) | (0, 0, 0) |
| `shoulder_pan_joint` | cordvip | (0, 0, 0.089159) | (0, 0, 3.14159) |
| `shoulder_lift_joint` | official | (0, 0, 0) | (1.570796327, 0, 0) |
| `shoulder_lift_joint` | cordvip | (0, 0.13585, 0) | (0, 1.57079632679, 0) |
| `elbow_joint` | official | (-0.425, 0, 0) | (0, 0, 0) |
| `elbow_joint` | cordvip | (0, -0.1197, 0.425) | (0, 0, 0) |
| `wrist_1_joint` | official | (-0.39225, 0, 0.10915) | (0, 0, 0) |
| `wrist_1_joint` | cordvip | (0, 0, 0.39225) | (0, 1.57079632679, 0) |
| `wrist_2_joint` | official | (0, -0.09465, -1.9413039509e-11) | (1.570796327, 0, 0) |
| `wrist_2_joint` | cordvip | (0, 0.093, 0) | (0, 0, 0) |
| `wrist_3_joint` | official | (0, 0.0823, -1.68800121668e-11) | (1.57079632659, 3.14159265359, 3.14159265359) |
| `wrist_3_joint` | cordvip | (0, 0, 0.09465) | (0, 0, 0) |

### 关节限制

位置单位 rad，速度单位 rad/s，effort 单位 N·m；每格顺序为官方 / CordViP。

| 关节 | lower | upper | velocity | effort |
|---|---|---|---|---|
| `shoulder_pan_joint` | -6.28318530718 / -6.28318530718 | 6.28318530718 / 6.28318530718 | 3.14159265359 / 3.15 | 150 / 150 |
| `shoulder_lift_joint` | -6.28318530718 / -6.28318530718 | 6.28318530718 / 6.28318530718 | 3.14159265359 / 3.15 | 150 / 150 |
| `elbow_joint` | -3.14159265359 / -3.14159265359 | 3.14159265359 / 3.14159265359 | 3.14159265359 / 3.15 | 150 / 150 |
| `wrist_1_joint` | -6.28318530718 / -6.28318530718 | 6.28318530718 / 6.28318530718 | 3.14159265359 / 3.2 | 28 / 28 |
| `wrist_2_joint` | -6.28318530718 / -6.28318530718 | 6.28318530718 / 6.28318530718 | 3.14159265359 / 3.2 | 28 / 28 |
| `wrist_3_joint` | -6.28318530718 / -6.28318530718 | 6.28318530718 / 6.28318530718 | 3.14159265359 / 3.2 | 28 / 28 |

六轴 lower/upper 和 effort 一致，位置限位的末位差异属于小数截断。官方六轴速度上限均为 π；
CordViP 前三轴为 3.15（高 0.2676%），后三轴为 3.2（高 1.8592%）。
速度差异单独记录；本次否决切换的主要证据是下面明显更大的动力学差异。

## 3. 排除 frame 表示差异后的运动学检查

没有把官方的局部 Z 轴与 CordViP 的局部 Y 轴直接判为不同机器人。先在零位比较六条转轴的空间方向和螺旋轴矩，再以一个固定基座变换对齐两者。
"官方基座 ← CordViP 基座" 的本次比较变换为 `Rz(-3.14159)`，平移为零。
这是比较用的坐标换算，不是 flange→palm 安装参数，也不是真机标定。

对每个对应 link，在 q=0 时计算一个固定 child-frame 换算 X，并在所有输入姿态中验证：

```text
T_official_link(q) · X_link ≈ A_base · T_cordvip_link(q)
```

使用零位、请求中的工作姿态 `(0,-π/2,0,-π/2,0,0)`，以及固定种子 `20261028` 的 256 组随机姿态，共 258 组。
两边使用相同的六个关节角，不做关节符号反转或重新拟合每个姿态。

| 检查 | 结果 |
|---|---|
| 最大转轴方向差 | 4.10324e-10 |
| 最大转轴矩差 [m] | 3.36169e-10 |
| 258 组姿态的最大位置差 [m] | 2.26034e-10 |
| 258 组姿态的最大旋转差 [rad] | 8.15469e-10 |
| 运动学和关节角约定 | 在上述固定 frame 对齐下匹配 |

因此，请求中的 UR5 工作关节角可以表达同样的机械臂构形，但两个模型的原始世界朝向、局部 link frame 和末端 frame 不能直接混用。

### CB3 / UR5e 型号判断

CordViP 的结构化结果与本地官方 `config/ur5/default_kinematics.yaml` 对应，肩部高度 0.089159 m、上臂长度 0.425 m、前臂长度 0.39225 m，
以及腕部的 0.10915 / 0.09465 / 0.0823 m 轴间尺寸共同匹配 UR5 CB3。官方 `config/ur5/joint_limits.yaml` 的来源明确是 UR5/CB3 手册。
结合六条转轴和多姿态比较，判定 CordViP 使用旧式 UR5 CB3 描述，不是 UR5e。这个型号结论不等于动力学参数与当前官方版本等价，也不能替代实验室设备铭牌及工厂校准。

## 4. visual / collision mesh 的实际内容

逐个解析实际 mesh 路径，而非比较 URI 字符串。7 个 visual DAE、7 个 collision STL 均存在，未遇到 Git LFS 指针假 mesh。所有 scale 均为 `(1,1,1)`。
DAE 同时比较数值数组、拓扑、规范化 library_geometries、实际 instance_geometry 的变换、材质和效果；相机节点的差异没有作为模型几何差异。

| link | visual DAE 字节 | DAE 几何/实例 | collision STL 字节 |
|---|---|---|---|
| `base_link` | 不同 | 不同 | 不同 |
| `shoulder_link` | 不同 | 一致 | 完全相同 |
| `upper_arm_link` | 不同 | 一致 | 完全相同 |
| `forearm_link` | 不同 | 一致 | 完全相同 |
| `wrist_1_link` | 不同 | 一致 | 完全相同 |
| `wrist_2_link` | 不同 | 一致 | 完全相同 |
| `wrist_3_link` | 不同 | 一致 | 完全相同 |

- 肩、上臂、前臂及三个腕部：DAE 文件虽然哈希不同，规范化几何与实例变换一致；对应 6 个 STL 逐字节一致，支持它们来自同一组 UR5 CB3 几何。
- 底座：DAE 几何数值和 STL 均不同；CordViP 底座 visual 的 z 范围约为 `[-0.003,0.021]`，官方约为 `[0,0.024]`。
- 底座 collision：官方 235 个三角形，CordViP 578 个；CordViP 的 z 包围盒也比官方向下偏约 0.003 m。不能把这一项解释成路径不同。
- 把 link frame 对齐后，其余相同 STL 的放置还存在前臂约 0.35 mm、wrist_2 约 0.35 mm、wrist_3 约 0.50 mm 的偏移，完整 origin 和变换在 JSON 中。
- 基座绕 Z 的 frame 对齐会改变底座外形相对全局的朝向，不能把同名 `base_link` 当作已对齐的几何原点。

### 材质单独记录

CordViP 的 UR5 visual 在 URDF 中指定 `LightGrey`、RGBA `(0.7,0.7,0.7,1)`；当前官方 URDF 未添加这个显式覆盖。
6 个非底座 DAE 的材料/效果库一致，底座的效果库存在差异。CordViP LEAP 的黑白 visual 保持原样。
这些材质、颜色和 DAE 相机节点差异不参与运动学或动力学否决。

### 文件哈希

下表显示 SHA-256 的前 16 位便于阅读；完整 64 位、文件路径及几何摘要在同名 JSON 中。

| mesh | 官方 SHA-256 前缀 | CordViP SHA-256 前缀 |
|---|---|---|
| visual/base.dae | `366e6cb99a2bf502` | `2059aec60ceea579` |
| collision/base.stl | `81c2ad265f714031` | `c7af57d109de6a73` |
| visual/shoulder.dae | `fd15be6d2edbc640` | `2bfa801f928dd92e` |
| collision/shoulder.stl | `1d62e23a8c3ff9e6` | `1d62e23a8c3ff9e6` |
| visual/upperarm.dae | `06b46dce3dadb55a` | `0577221909b0b764` |
| collision/upperarm.stl | `55c11ac0ad1e144f` | `55c11ac0ad1e144f` |
| visual/forearm.dae | `2fabc6738b33365b` | `d7b40d794f81ba16` |
| collision/forearm.stl | `8e79aa80a532494b` | `8e79aa80a532494b` |
| visual/wrist1.dae | `3eb98c0a440ea8f4` | `1cc29d29a40f2eef` |
| collision/wrist1.stl | `0a1fd12150140efd` | `0a1fd12150140efd` |
| visual/wrist2.dae | `2a60ae57fd85ee06` | `d8cc770127fc7cc3` |
| collision/wrist2.stl | `c1d9f7843366068c` | `c1d9f7843366068c` |
| visual/wrist3.dae | `23430d8b8ec0c94c` | `8ee319c507ad0e0d` |
| collision/wrist3.stl | `cf7220397b56f1d3` | `cf7220397b56f1d3` |

## 5. mass、inertial origin 与 inertia matrix

质量单位 kg，质心位置 m，惯量单位 kg·m²。底座按 `official/base_link_inertia` 对应 `cordvip/base_link`。

| link | 官方质量 | CordViP 质量 | 对齐后质心距离 [m] |
|---|---|---|---|
| `base_link` | 4 | 4 | 0 |
| `shoulder_link` | 3.7 | 3.7 | 0.0256826205828 |
| `upper_arm_link` | 8.393 | 8.393 | 0.0711480857086 |
| `forearm_link` | 2.33 | 2.275 | 0.012930003867 |
| `wrist_1_link` | 1.219 | 1.219 | 0.0926522293323 |
| `wrist_2_link` | 1.219 | 1.219 | 0.0942768163702 |
| `wrist_3_link` | 0.1879 | 0.1879 | 0.0811409999612 |

前臂质量从官方 2.33 kg 变为 CordViP 2.275 kg；质量不随坐标系旋转改变，因此这是实质差异。质心距离已在固定基座对齐后的同一空间计算，不是直接比较不同 link frame 的原始 xyz。

### 原始 inertial origin

以下 origin 仍按各自 link frame 表达；需要结合上面的 frame 换算理解。

| link | 来源 | xyz | rpy |
|---|---|---|---|
| `base_link` | official | (0, 0, 0) | (0, 0, 0) |
| `base_link` | cordvip | (0, 0, 0) | (0, 0, 0) |
| `shoulder_link` | official | (0, -0.00193, -0.02561) | (0, 0, 0) |
| `shoulder_link` | cordvip | (0, 0, 0) | (0, 0, 0) |
| `upper_arm_link` | official | (-0.2125, 0, 0.11336) | (0, 1.57079632679, 0) |
| `upper_arm_link` | cordvip | (0, 0, 0.28) | (0, 0, 0) |
| `forearm_link` | official | (-0.24225, 0, 0.0265) | (0, 1.57079632679, 0) |
| `forearm_link` | cordvip | (0, 0, 0.25) | (0, 0, 0) |
| `wrist_1_link` | official | (0, -0.01634, -0.0018) | (0, 0, 0) |
| `wrist_1_link` | cordvip | (0, 0, 0) | (0, 0, 0) |
| `wrist_2_link` | official | (0, 0.01634, -0.0018) | (0, 0, 0) |
| `wrist_2_link` | cordvip | (0, 0, 0) | (0, 0, 0) |
| `wrist_3_link` | official | (0, 0, -0.001159) | (0, 0, 0) |
| `wrist_3_link` | cordvip | (0, 0, 0) | (0, 0, 0) |

### 完整惯量矩阵与坐标旋转不变量

这 7 个机械臂 link 的两套矩阵均满足 `ixy=ixz=iyz=0`，因此下表的 `diag(ixx,iyy,izz)` 就是各自 inertial frame 中的完整 3×3 矩阵。

| link | 官方 diag(I) | CordViP diag(I) | 最大主惯量之比 C/O |
|---|---|---|---|
| `base_link` | (0.00443333156, 0.00443333156, 0.0072) | (0.00443333156, 0.00443333156, 0.0072) | 1 |
| `shoulder_link` | (0.0149723583333, 0.0149723583333, 0.01040625) | (0.010267495893, 0.010267495893, 0.00666) | 0.68576343582 |
| `upper_arm_link` | (0.133885835417, 0.133885835417, 0.0151074) | (0.22689067591, 0.22689067591, 0.0151074) | 1.69465780457 |
| `forearm_link` | (0.0312168035156, 0.0312168035156, 0.004095) | (0.049443313556, 0.049443313556, 0.004095) | 1.58386855756 |
| `wrist_1_link` | (0.00201388958333, 0.00201388958333, 0.0021942) | (0.111172755531, 0.111172755531, 0.21942) | 100 |
| `wrist_2_link` | (0.00183103958333, 0.00183103958333, 0.0021942) | (0.111172755531, 0.111172755531, 0.21942) | 100 |
| `wrist_3_link` | (8.06247583333e-05, 8.06247583333e-05, 0.0001321171875) | (0.0171364731454, 0.0171364731454, 0.033822) | 256 |

比较时额外计算了惯量特征值（主惯量）。改变 inertial frame 只会做 `R·I·Rᵀ`，不会改变这些特征值；
因此 wrist_1 / wrist_2 的最大主惯量 100 倍、wrist_3 的 256 倍差异，不可能通过 link 旋转、ee_link 或材质变化消除。
这些值会影响关节加速度、重力/惯性负载、驱动响应和接触过程。本报告没有宣称已在 GPU 上量测具体响应差多少，也不把官方估计参数当成真机标定值。

## 6. CordViP 现有安装参数与 USD（保留参考）

以下参数直接从当前有效 XML 读取，仅记录而未采用为新的标准模型：

| fixed joint | parent → child | xyz [m] | rpy [rad] |
|---|---|---|---|
| `ee_fixed_joint` | `wrist_3_link` → `ee_link` | (0, 0.0823, 0) | (0, 0, 1.57079632679) |
| `mount_joint` | `ee_link` → `palm_lower` | (0, 0.03, 0.06) | (3.14159, -1.57079, 3.14159) |

该安装链不作为机械臂本体不等价的原因，也没有被当作实验室 flange→palm 的实测参数。

已经存在的参考 USD 入口：

`source/ur5_leap/assets/references/cordvip/generated/usd/cordvip_ur5_leap.usd/ur5_leaphand/ur5_leaphand.usda`

检查了其 `payloads/Physics/physics.usda` 文本，22 个 PhysicsRevoluteJoint 的声明名称与下面 URDF 顺序一致；
该物理层还保留了 CordViP 的前臂质量和腕部惯量。因此不能假定现有 USD 已经自动修复了上述动力学差异。
此处仅为 USDA 文本检查，没有执行 USD stage 组合和仿真器关节索引验证。

### 22 个实际关节名称

UR5 六轴（0～5）：

```text
00 shoulder_pan_joint
01 shoulder_lift_joint
02 elbow_joint
03 wrist_1_joint
04 wrist_2_joint
05 wrist_3_joint
```

LEAP 十六轴（6～21）：

```text
06 joint0
07 joint1
08 joint2
09 joint3
10 joint4
11 joint5
12 joint6
13 joint7
14 joint8
15 joint9
16 joint10
17 joint11
18 joint12
19 joint13
20 joint14
21 joint15
```

没有采用 `tn__0_` 或 `leap_joint_0` 等其他资产命名。以上为参考模型的声明顺序，实际 Articulation 索引仍需按名称查找。

## 7. 条件执行结果及服务器后续

- 新增本报告及同名 JSON 两个文件，所有原始官方/参考 URDF、mesh、旧 combined 均保留。
- 现有 combined 模型没有被指定为新的标准；本轮也没有采纳 CordViP 替代它。
- 未创建 `assets/ur5_leap.py` / `UR5_LEAP_CFG`，没有伪造一个可用的 import；统一配置与 Python package 接入属于等价检查通过后的分支。
- 两个指定测试脚本均存在；本轮没有修改、删除或替换其中逻辑，也未迁移其 USD 路径。
- 已阅读当前 `isaaclab_assets/robots/franka.py`。当前配置采用 `clone/replace` 及新版 actuator 字段；没有套用旧 API 创建配置。
- 当前主工作区开始时已有 9 个 combined USD 文件的 Git 改动，本轮不修复其 LFS/指针状态，不覆盖这些文件。比较在独立工作树中进行。

服务器本轮无需重新生成 USD，也不应把尚未通过比较的 CordViP USD 切换成标准学习模型。需要复核现有模型的静态结构时，可在恢复大文件后从仓库根目录运行：

```bash
uv run --no-project python source/ur5_leap/scripts/inspect_ur5.py
uv run --no-project python source/ur5_leap/scripts/inspect_combined.py --model cordvip
```

这两个命令检查树和资源可解析性；通过并不表示两套模型动力学等价。
后续若要采用 CordViP 安装方式，应另做经过明确选择的派生联合模型，处理动力学、速度限制和 frame 换算，同时保留全部上游原件。

## 最终结论

**B. NOT_EQUIVALENT**

CordViP 确认为 UR5 CB3 运动学，六轴构形和位置/effort 限制可对应；但它与当前官方 UR5 CB3 的质量、质心、主惯量、速度上限及底座几何并不等价。
本结论的决定性依据是不能由坐标变换消除的动力学差异，不是路径、颜色、辅助 link 或 LEAP 安装链。按任务条件停止切换模型。

B. NOT_EQUIVALENT
