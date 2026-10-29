# CordViP LEAP 与官网 LEAP Hand v1 Full Right 比较

日期：2026-10-28；仓库基线：`7ffe8150c`。只读检查现有资产，新增本 Markdown 与同名 JSON。

**判定：C. DIFFERENT_MODEL，具体是同一 v1 Full Right 基础的掌部几何改动版。**

不是左手、不是 v2、不是多出自由度，也不是质量或惯量被大幅修改。
决定性差异是 CordViP 的 palm_lower visual 网格沿 mesh Y 缩放为官网的 0.99；这不能归入颜色、文件格式或刚体坐标变换。
其余 7 种网格在格式精度内一致，16 关节运动学在小数截断容差内近似一致，17 个实体 link 的局部动力学声明完全相同。
因此按本次 A/B/C 定义选 C，而不是把这只手说成另一种机器人。

## 1. 基准、来源和版本边界

基准为 `assets/official/leap_hand_v1_right/generated/leap_hand_right.urdf`，来源是官网明确标注 LEAP Full Assembly Right 的 Right URDF ZIP。
生成版只重定位资源路径；本次逐 joint/link 和实际 STL 哈希再次核对其与 `urdf/website_right/robot.urdf` 一致。
官方 Sim 原始 URDF 单独交叉核对，不以旧 Lab USD 的材质、碰撞设置替代官网 CAD 基准。

| 资源 | 实际来源/位置 | 本次用途 |
|---|---|---|
| 官网 Right | https://v1.leaphand.com/leap_cad → https://v1.leaphand.com/static/cad/urdf/leap_right.zip | 主要几何与 URDF 基准 |
| 便携生成版 | official/leap_hand_v1_right/generated/leap_hand_right.urdf | 主要计算入口，内容已对照官网原件 |
| 官方 Sim | official/leap_hand_v1_right/sim_reference/leap_hand/robot.urdf | 交叉核对 |
| 旧官方 Lab USD | official/leap_hand_v1_right/isaac_lab_reference/ | 仅只读核对已有材质；不是本次几何基准 |
| CordViP | references/cordvip/ur5_leaphand/ur5_leaphand.urdf | 取 palm_lower 后代，不将 UR5 安装变换计入手部差异 |

| 仓库 | 分支 | 固定 commit |
|---|---|---|
| leap-hand/LEAP_Hand_Sim | master | `150bc3d4b61fd6619193ba5a8ef209f3609ced89` |
| leap-hand/LEAP_Hand_Isaac_Lab | main | `c576e6a83183ba504aef8f57015f2899b799db1a` |
| xuanxuanzzzii/cordvip | main | `ad6d441abe7b0480cf79b0311db266965c1313b6` |

官网保存页面明确使用 Full Assembly Right 标签。CordViP 的拓扑、拇指侧别、7 种原尺寸网格和掌网格的缩放对应关系，支持其来自同一 v1 Full Right 基础。
这里确认的是模型来源/手型；URDF 并不编码实物电机 SKU，不能据此独立确认真机使用 XC330-M288-T 或其标定参数。
未将目录中未被当前 URDF 引用的 `palm_lower_left.obj`、`pip_left.obj` 当成本次手部资源。

| 交叉检查 | 结果 |
|---|---|
| official_website | 16 joints 相同=True；17 links/mesh/material/inertia 相同=True |
| official_sim | 16 joints 相同=True；17 links/mesh/material/inertia 相同=True |

当前保存的官网与 Sim URDF 的 joint XML 顺序均为 0～15；本报告仍按拓扑和明确映射比较，文件顺序不能替代仿真器关节索引。

## 2. 手型、自由度和 link 拓扑

| 项目 | 官网基准 | CordViP |
|---|---|---|
| 手型基础 | LEAP v1 Full Right | 同一基础的改动版，手掌 Y 向 0.99 缩放 |
| 可动关节 | 16 revolute | 16 revolute |
| 手指 | 3 根长指 + 1 根拇指，每条 4 关节 | 相同 |
| 实体 link | 17 | 17 |
| 额外空 fixed frame | 0 | 4 个 tip_head，仅标记，不增加 DoF |

- 分支 1：官网 `1 → 0 → 2 → 3` ↔ CordViP `joint1 → joint0 → joint2 → joint3`。
- 分支 2：官网 `5 → 4 → 6 → 7` ↔ CordViP `joint5 → joint4 → joint6 → joint7`。
- 分支 3：官网 `9 → 8 → 10 → 11` ↔ CordViP `joint9 → joint8 → joint10 → joint11`。
- 分支 4：官网 `12 → 13 → 14 → 15` ↔ CordViP `joint12 → joint13 → joint14 → joint15`。

映射由 palm_lower 上四条根分支的 origin/mesh 类型匹配开始，再沿四关节链递归确认；名称只用于展示。

| 官网 link | CordViP link | visual 零件 |
|---|---|---|
| `palm_lower` | `palm_lower` | palm_lower |
| `mcp_joint` | `mcp_joint` | mcp_joint |
| `pip` | `pip` | pip |
| `dip` | `dip` | dip |
| `fingertip` | `fingertip` | fingertip |
| `mcp_joint_2` | `mcp_joint_2` | mcp_joint |
| `pip_2` | `pip_2` | pip |
| `dip_2` | `dip_2` | dip |
| `fingertip_2` | `fingertip_2` | fingertip |
| `mcp_joint_3` | `mcp_joint_3` | mcp_joint |
| `pip_3` | `pip_3` | pip |
| `dip_3` | `dip_3` | dip |
| `fingertip_3` | `fingertip_3` | fingertip |
| `pip_4` | `thumb_temp_base` | pip |
| `thumb_pip` | `thumb_pip` | thumb_pip |
| `thumb_dip` | `thumb_dip` | thumb_dip |
| `thumb_fingertip` | `thumb_fingertip` | thumb_fingertip |

拇指根 `pip_4` ↔ `thumb_temp_base`，两者都使用 pip 几何，这只是重命名。四个额外 tip_head 没有 visual、collision 或 inertial，详细 fixed origin 在 JSON 中。

## 3. 16 个关节逐一映射

每行的 parent/child 是各模型真实名称。xyz 单位 m，rpy 和位置限位单位 rad，effort N·m，velocity rad/s。

| CordViP ↔ 官网 | 官网 parent → child | CordViP parent → child | axis 两边 |
|---|---|---|---|
| `joint0` ↔ `0` | `mcp_joint` → `pip` | `mcp_joint` → `pip` | (0, 0, -1) |
| `joint1` ↔ `1` | `palm_lower` → `mcp_joint` | `palm_lower` → `mcp_joint` | (0, 0, -1) |
| `joint2` ↔ `2` | `pip` → `dip` | `pip` → `dip` | (0, 0, -1) |
| `joint3` ↔ `3` | `dip` → `fingertip` | `dip` → `fingertip` | (0, 0, -1) |
| `joint4` ↔ `4` | `mcp_joint_2` → `pip_2` | `mcp_joint_2` → `pip_2` | (0, 0, -1) |
| `joint5` ↔ `5` | `palm_lower` → `mcp_joint_2` | `palm_lower` → `mcp_joint_2` | (0, 0, -1) |
| `joint6` ↔ `6` | `pip_2` → `dip_2` | `pip_2` → `dip_2` | (0, 0, -1) |
| `joint7` ↔ `7` | `dip_2` → `fingertip_2` | `dip_2` → `fingertip_2` | (0, 0, -1) |
| `joint8` ↔ `8` | `mcp_joint_3` → `pip_3` | `mcp_joint_3` → `pip_3` | (0, 0, -1) |
| `joint9` ↔ `9` | `palm_lower` → `mcp_joint_3` | `palm_lower` → `mcp_joint_3` | (0, 0, -1) |
| `joint10` ↔ `10` | `pip_3` → `dip_3` | `pip_3` → `dip_3` | (0, 0, -1) |
| `joint11` ↔ `11` | `dip_3` → `fingertip_3` | `dip_3` → `fingertip_3` | (0, 0, -1) |
| `joint12` ↔ `12` | `palm_lower` → `pip_4` | `palm_lower` → `thumb_temp_base` | (0, 0, -1) |
| `joint13` ↔ `13` | `pip_4` → `thumb_pip` | `thumb_temp_base` → `thumb_pip` | (0, 0, -1) |
| `joint14` ↔ `14` | `thumb_pip` → `thumb_dip` | `thumb_pip` → `thumb_dip` | (0, 0, -1) |
| `joint15` ↔ `15` | `thumb_dip` → `thumb_fingertip` | `thumb_dip` → `thumb_fingertip` | (0, 0, -1) |

### 原始 joint origin

| joint（官网名） | 来源 | xyz | rpy |
|---|---|---|---|
| `0` | official | (-0.0122, 0.0381, 0.0145) | (-1.570796327, -1.006521266e-15, 1.570796327) |
| `0` | cordvip | (-0.0122, 0.0381, 0.0145) | (-1.57079, 0, 1.57079) |
| `1` | official | (-0.007095249653, 0.02305775613, -0.01872240358) | (1.570796327, 1.570796327, 0) |
| `1` | cordvip | (-0.007, 0.023, -0.0187) | (1.57079, 1.57079, 0) |
| `2` | official | (0.015, 0.0143, -0.013) | (1.570796327, -1.570796327, 0) |
| `2` | cordvip | (0.015, 0.0143, -0.013) | (1.57079, -1.57079, 0) |
| `3` | official | (-4.08805825e-09, -0.03610000421, 0.0002) | (4.593502943e-17, -2.873007191e-16, 4.439548105e-32) |
| `3` | cordvip | (0, -0.0361, 0.0002) | (0, 0, 0) |
| `4` | official | (-0.0122, 0.0381, 0.0145) | (-1.570796327, -1.006521276e-15, 1.570796327) |
| `4` | cordvip | (-0.0122, 0.0381, 0.0145) | (-1.57079, 0, 1.57079) |
| `5` | official | (-0.007095249653, -0.02239224387, -0.01872240358) | (1.570796327, 1.570796327, 0) |
| `5` | cordvip | (-0.0071, -0.0224, -0.0187) | (1.57079, 1.57079, 0) |
| `6` | official | (0.015, 0.0143, -0.013) | (1.570796327, -1.570796327, 0) |
| `6` | cordvip | (0.015, 0.0143, -0.013) | (1.57079, -1.57079, 0) |
| `7` | official | (1.006139616e-16, -0.0361, 0.0002) | (4.593502943e-17, -2.873007191e-16, 1.440818322e-31) |
| `7` | cordvip | (0, -0.0361, 0.0002) | (0, 0, 0) |
| `8` | official | (-0.0122, 0.0381, 0.0145) | (-1.570796327, -1.006521266e-15, 1.570796327) |
| `8` | cordvip | (-0.0122, 0.0381, 0.0145) | (-1.57079, 0, 1.57079) |
| `9` | official | (-0.007095245443, -0.06784224387, -0.01872240767) | (1.570796327, 1.570796327, 0) |
| `9` | cordvip | (-0.00709, -0.0678, -0.0187) | (1.57079, 1.57079, 0) |
| `10` | official | (0.015, 0.0143, -0.013) | (1.570796327, -1.570796327, 0) |
| `10` | cordvip | (0.015, 0.0143, -0.013) | (1.57079, -1.57079, 0) |
| `11` | official | (9.714451465e-17, -0.0361, 0.0002) | (4.593502943e-17, -2.873007191e-16, 1.556541161e-32) |
| `11` | cordvip | (0, -0.03609, 0.0002) | (0, 0, 0) |
| `12` | official | (-0.06939524965, -0.001242243865, -0.02162240358) | (-8.238176646e-17, 1.570796327, 0) |
| `12` | cordvip | (-0.0693, -0.0012, -0.0216) | (0, 1.57079, 0) |
| `13` | official | (-2.775557562e-17, 0.0143, -0.013) | (1.570796327, -1.570796327, 0) |
| `13` | cordvip | (0, 0.0143, -0.013) | (1.57079, -1.57079, 0) |
| `14` | official | (0, 0.0145, -0.017) | (-1.570796327, 1.605019844e-46, -1.972152263e-31) |
| `14` | cordvip | (0, 0.0145, -0.017) | (-1.57079, 0, 0) |
| `15` | official | (-1.249000903e-16, 0.0466, 0.0002) | (1.506395849e-44, 5.423418723e-31, 3.141592654) |
| `15` | cordvip | (0, 0.0466, 0.0002) | (0, 0, 3.14159) |

### joint limits / effort / velocity

下表两边完全一致，JSON 同时保存两边的原始值及差值。

| CordViP ↔ 官网 | lower | upper | effort | velocity |
|---|---|---|---|---|
| `joint0` ↔ `0` | -1.047 | 1.047 | 0.95 | 8.48 |
| `joint1` ↔ `1` | -0.314 | 2.23 | 0.95 | 8.48 |
| `joint2` ↔ `2` | -0.506 | 1.885 | 0.95 | 8.48 |
| `joint3` ↔ `3` | -0.366 | 2.042 | 0.95 | 8.48 |
| `joint4` ↔ `4` | -1.047 | 1.047 | 0.95 | 8.48 |
| `joint5` ↔ `5` | -0.314 | 2.23 | 0.95 | 8.48 |
| `joint6` ↔ `6` | -0.506 | 1.885 | 0.95 | 8.48 |
| `joint7` ↔ `7` | -0.366 | 2.042 | 0.95 | 8.48 |
| `joint8` ↔ `8` | -1.047 | 1.047 | 0.95 | 8.48 |
| `joint9` ↔ `9` | -0.314 | 2.23 | 0.95 | 8.48 |
| `joint10` ↔ `10` | -0.506 | 1.885 | 0.95 | 8.48 |
| `joint11` ↔ `11` | -0.366 | 2.042 | 0.95 | 8.48 |
| `joint12` ↔ `12` | -0.349 | 2.094 | 0.95 | 8.48 |
| `joint13` ↔ `13` | -0.47 | 2.443 | 0.95 | 8.48 |
| `joint14` ↔ `14` | -1.2 | 1.9 | 0.95 | 8.48 |
| `joint15` ↔ `15` | -1.34 | 1.88 | 0.95 | 8.48 |

### frame 等价与精度

两边 palm_lower 坐标作共同根，未使用镜像或关节角符号反转。比较零位、限位中点及 256 组固定种子的随机姿态，共 258 组。

| 项目 | 测得结果 |
|---|---|
| 最大原始 joint origin 平移差 | 0.113623 mm |
| 最大原始 joint origin 旋转差 | 8.94743915e-06 rad |
| 直接 palm 对齐后的最大 link FK 位置差 | 0.114119 mm |
| 直接 palm 对齐后的最大旋转差 | 1.78356877e-05 rad |
| 允许常量 child-frame 换算后的最大位置残差 | 0.225101 mm |

CordViP 把许多 xyz 截为 4～5 位小数、rpy 截为 1.57079 一类数值，因此不是严格逐位相同。
本报告将 0.5 mm FK 位置、1e-4 rad FK 旋转作为学习阶段近似一致阈值；原始 joint-origin 阈值是 0.2 mm 和 5e-5 rad。
测得误差均在这些范围内，没有发现手指长度、关节方向或关节范围的实质变化。这些小数截断不作为 C 判定的主要依据。

## 4. visual mesh 几何比较

直接读取官网 STL 与 CordViP OBJ 的顶点和面。STL 是重复顶点的 triangle soup，OBJ 有索引、UV seam 和材质分组，不能用存储顶点数或文件哈希直接判断几何不同。
所有比较对象的 URDF mesh scale 均为 `(1,1,1)`；mesh origin 分别纳入 link-frame 比较，完整 origin 在 JSON 中。

| 零件 | STL / OBJ 字节数 | STL存储V / OBJ存储V | STL独立V / OBJ独立V | 三角面 F（两边） | 原始顶点双向最大距离 |
|---|---|---|---|---|---|
| palm_lower | 4,347,184 / 2,978,219 | 260,826 / 43,139 | 43,139 / 43,139 | 86,942 | 1257.367256 µm |
| mcp_joint | 1,608,784 / 1,065,471 | 96,522 / 15,983 | 15,983 / 15,983 | 32,174 | 0.821136 µm |
| pip | 1,051,084 / 673,869 | 63,060 / 10,408 | 10,408 / 10,408 | 21,020 | 0.819414 µm |
| dip | 1,538,284 / 1,013,886 | 92,292 / 15,244 | 15,244 / 15,244 | 30,764 | 0.809080 µm |
| fingertip | 562,684 / 359,831 | 33,756 / 5,680 | 5,608 / 5,603 | 11,252 | 0.852214 µm |
| thumb_pip | 468,884 / 294,575 | 28,128 / 4,624 | 4,624 / 4,624 | 9,376 | 0.785604 µm |
| thumb_dip | 1,451,484 / 968,312 | 87,084 / 14,428 | 14,428 / 14,428 | 29,028 | 0.832840 µm |
| thumb_fingertip | 1,111,984 / 734,609 | 66,714 / 11,138 | 11,069 / 11,066 | 22,238 | 0.823491 µm |

### 包围盒（mesh 自身坐标，单位 mm）

| 零件 | 来源 | min XYZ | max XYZ | 尺寸 XYZ |
|---|---|---|---|---|
| palm_lower | official | (-79.99999821, -125.7293671, 0) | (23.00000004, 1.647635342e-16, 46.00000009) | (102.9999983, 125.7293671, 46.00000009) |
| palm_lower | cordvip | (-80, -124.472, 0) | (23, -0, 46) | (103, 124.472, 46) |
| mcp_joint | official | (-51.40690133, -15.70276357, -17.45735481) | (1.593097695, 54.8337549, 18.34264584) | (52.99999902, 70.53651847, 35.80000065) |
| mcp_joint | cordvip | (-51.407, -15.703, -17.457) | (1.593, 54.834, 18.343) | (53, 70.537, 35.8) |
| pip | official | (-23.78403395, -19.14336346, -14.76544607) | (-0.7840340259, 14.85663652, 14.76544607) | (22.99999993, 33.99999999, 29.53089215) |
| pip | cordvip | (-23.784, -19.143, -14.765) | (-0.784, 14.857, 14.765) | (23, 34, 29.53) |
| dip | official | (-31.13335371, -16.36863872, -22.01491222) | (3.366647055, 37.6678817, 12.58508861) | (34.50000077, 54.03652042, 34.60000083) |
| dip | cordvip | (-31.133, -16.369, -22.015) | (3.367, 37.668, 12.585) | (34.5, 54.037, 34.6) |
| fingertip | official | (-24.38453771, -14.05075751, -17.30000041) | (-3.286424093, 43.38576272, 17.30000041) | (21.09811362, 57.43652023, 34.60000083) |
| fingertip | cordvip | (-24.385, -14.051, -17.3) | (-3.286, 43.386, 17.3) | (21.099, 57.437, 34.6) |
| thumb_pip | official | (-21.96191996, -9.083870798, -17.30000041) | (-1.961920876, 15.85264876, 17.30000041) | (19.99999909, 24.93651956, 34.60000083) |
| thumb_pip | cordvip | (-21.962, -9.084, -17.3) | (-1.962, 15.853, 17.3) | (20, 24.937, 34.6) |
| thumb_dip | official | (-62.46871501, -67.45295227, -22.97132276) | (-33.96871686, -3.416433465, 11.62867621) | (28.49999815, 64.0365188, 34.59999897) |
| thumb_dip | cordvip | (-62.469, -67.453, -22.971) | (-33.969, -3.416, 11.629) | (28.5, 64.037, 34.6) |
| thumb_fingertip | official | (-73.65765423, -140.5596882, -79.79290932) | (-44.05953735, -68.95968318, -46.79291323) | (29.59811687, 71.60000503, 32.9999961) |
| thumb_fingertip | cordvip | (-73.658, -140.56, -79.793) | (-44.06, -68.96, -46.793) | (29.598, 71.6, 33) |

### 七种零件：格式转换精度内相同

MCP、PIP、DIP、fingertip、thumb_pip、thumb_dip、thumb_fingertip 的原始顶点双向最大差均小于 1 µm。
在仅用于内存分析的 2 µm 顶点容差合并后，三角面的空间顶点组合全部对应。指尖 OBJ 因材质边界/UV seam 拆分顶点，六位小数又使少量近重合点合并，这解释了其精确 unique vertex 数不同。
没有为了获得这个结果对这七种网格做额外缩放或镜像。白色指尖的几何本身与官网对应零件一致，颜色变化不意味着换了一种指尖。

### 手掌：可复现的 1% 定向缩放

官网 palm_lower 的 Y 尺寸为 **125.729367 mm**；CordViP 为 **124.472000 mm**，比例约为 **0.99**。X/Z 尺寸保持一致。
原始顶点双向最大差为 **1.257367 mm**；计入 URDF origin 后的手掌 link-frame 差异仍约 **1.253413 mm**。

只在内存中对官网掌网格施加 `diag(1,0.99,1)`：

- 顶点双向最大差降到 **0.857529 µm**。
- 86,942 个三角面的空间对应全部匹配（2 µm 精度容差）。
- 最小二乘仿射变换的奇异值约为 `(1.00000035, 1.000000095, 0.9900002723)`；其中一个不是 1，证明存在非刚体缩放。
- 对应地标点间距从 `126.207693 mm` 变成 `124.955092 mm`，刚体平移/旋转不能改变这个距离。

没有把上述诊断缩放写回任何 mesh/URDF/USD。它证明 CordViP 是同一掌几何的缩放派生，而不是格式转换误差；这也是本次严格分类选 C 的原因。
不能因为改动只有 1% 就把它隐去，也不应把它夸大为另一代机械手或左右手混用。

### mesh 文件与 hash

完整 64 位 SHA-256 及路径均在 JSON。下面显示前 16 位；OBJ/STL 哈希不同本身不作为几何判定依据。

| 零件 | 官网 STL SHA-256 | CordViP OBJ SHA-256 | 对应结果 |
|---|---|---|---|
| palm_lower | `eae47756f1a1978b` | `90d1d9b2a1c9eea1` | 需 Y×0.99 才对应 |
| mcp_joint | `56af82c57b469d49` | `3d7194a6a33626ff` | 2 µm 格式精度内相同 |
| pip | `b778405c95127023` | `3fff19dc1f0100bb` | 2 µm 格式精度内相同 |
| dip | `9222f0ee1fa0077c` | `472e054348c5a0e9` | 2 µm 格式精度内相同 |
| fingertip | `e149e01e395b5895` | `6bfa2afb2a06557c` | 2 µm 格式精度内相同 |
| thumb_pip | `40532d5d555e1507` | `d28876cc3b674323` | 2 µm 格式精度内相同 |
| thumb_dip | `7261cf99cd44ae42` | `5b402876601f2b0b` | 2 µm 格式精度内相同 |
| thumb_fingertip | `b43c5a13cf67a25d` | `4695d72a70285e8a` | 2 µm 格式精度内相同 |

## 5. 黑白与红/黄/浅灰的来源

### CordViP：OBJ → MTL → 已有 USD 材质

手部 URDF 的 visual 没有显式 material；OBJ 的 `mtllib` / `usemtl` 指向以下 MTL。没有找到手部贴图图像引用，颜色来自常量材质。

| MTL 文件 | material → Kd | 三角面材质分组 |
|---|---|---|
| palm_lower.mtl | black_metal → (0.023153, 0.023153, 0.023153) | {'black_metal': 86942} |
| mcp_joint.mtl | black_metal → (0.023153, 0.023153, 0.023153) | {'black_metal': 32174} |
| pip.mtl | black_metal → (0.023153, 0.023153, 0.023153) | {'black_metal': 21020} |
| dip.mtl | black_metal → (0.023153, 0.023153, 0.023153) | {'black_metal': 30764} |
| fingertip.mtl | White_tip → (0.8, 0.8, 0.8); black_metal → (0.023153, 0.023153, 0.023153) | {'black_metal': 9802, 'White_tip': 1450} |
| thumb_pip.mtl | black_metal → (0.023153, 0.023153, 0.023153) | {'black_metal': 9376} |
| thumb_dip.mtl | black_metal → (0.023153, 0.023153, 0.023153) | {'black_metal': 29028} |
| thumb_fingertip.mtl | White_tip → (0.8, 0.8, 0.8); black_metal → (0.023153, 0.023153, 0.023153) | {'black_metal': 20794, 'White_tip': 1444} |

`black_metal` 的 Kd 为 `(0.023153,0.023153,0.023153)`，`White_tip` 为 `(0.8,0.8,0.8)`。
已有 CordViP `payloads/materials.usda` 中保留同名材质，`instances.usda` 中存在实际绑定。其线性 diffuseColor 约为 0.001792 与 0.603827，与上述值的 sRGB→linear 转换对应。
因此黑主体、白指尖有具体材质来源，不是因为黑色代表另一种型号或左右手。这里没有渲染截图，实际屏幕亮度仍受灯光和渲染器影响。

### 官网 Right URDF：逐 link 显式 RGBA

八个 STL 的 attribute 字段均未记录非零颜色；本基准的颜色来自 URDF material。可核对的颜色是暗红、黄和浅灰；用户看到的“白”不应被解释成 STL 中存在一套不同的白色机械结构。

| 官网零件 | URDF RGBA |
|---|---|
| palm_lower | (0.6039215686, 0.1490196078, 0.1490196078, 1) |
| mcp_joint | (0.8666666667, 0.8666666667, 0.05098039216, 1) |
| pip | (0.7490196078, 0.7490196078, 0.7490196078, 1) |
| dip | (0.8666666667, 0.8666666667, 0.05098039216, 1) |
| fingertip | (0.8666666667, 0.8666666667, 0.05098039216, 1) |
| thumb_pip | (0.8666666667, 0.8666666667, 0.05098039216, 1) |
| thumb_dip | (0.8666666667, 0.8666666667, 0.05098039216, 1) |
| thumb_fingertip | (0.6039215686, 0.1490196078, 0.1490196078, 1) |

### 旧官方 Lab USD 并不是红黄 URDF 材质的同义词

额外用 CPU 的 Sdf 读取旧 `leap_hand_right_base.usd`，发现它已经包含 `black_metal` 与 `White_tip`，diffuse_color_constant 分别约为 0.023153 和 0.8，而且存在材质绑定。
所以不能笼统地说“所有官方 LEAP 资源都是红黄白”。官网原始 Right URDF 与官方 Lab 仓库保存的旧仿真 USD 是不同资产阶段；本报告坚持以前者作为几何基准。
颜色差异本身属于 visual/material 差异，不影响关节运动学；掌网格的 1% 缩放是另一个独立发现。

## 6. collision 差异

官网 17 个实体 link 各使用一个对应 STL collision，origin 与本 link 的 visual 一致。CordViP 将它们改为多 box 加白指尖 collision OBJ 的近似。

| 模型 | collision 元素数 | 类型数量 |
|---|---|---|
| official | 17 | {'mesh': 17} |
| cordvip | 71 | {'box': 67, 'mesh': 4} |

| 官网 link | CordViP link | 官网元素数 | CordViP 元素数 | CordViP 类型 |
|---|---|---|---|---|
| palm_lower | palm_lower | 1 | 10 | box |
| mcp_joint | mcp_joint | 1 | 6 | box |
| pip | pip | 1 | 1 | box |
| dip | dip | 1 | 5 | box |
| fingertip | fingertip | 1 | 4 | box, mesh |
| mcp_joint_2 | mcp_joint_2 | 1 | 6 | box |
| pip_2 | pip_2 | 1 | 1 | box |
| dip_2 | dip_2 | 1 | 5 | box |
| fingertip_2 | fingertip_2 | 1 | 4 | box, mesh |
| mcp_joint_3 | mcp_joint_3 | 1 | 6 | box |
| pip_3 | pip_3 | 1 | 1 | box |
| dip_3 | dip_3 | 1 | 5 | box |
| fingertip_3 | fingertip_3 | 1 | 4 | box, mesh |
| pip_4 | thumb_temp_base | 1 | 1 | box |
| thumb_pip | thumb_pip | 1 | 3 | box |
| thumb_dip | thumb_dip | 1 | 5 | box |
| thumb_fingertip | thumb_fingertip | 1 | 4 | box, mesh |

例如手掌官网 collision 跟随 visual 的长精度 origin；CordViP 的第一个 box 使用 `xyz=(-0.009,0.008,-0.011)`、`size=(0.022,0.026,0.034)`，其余 9 个 box 各有独立 origin。
三根长指末端用 `leaphand/collision/white_tip.obj`，拇指末端用 `white_tip_thumb.obj`。每个 collision 的实际 origin/rpy、box size、mesh 路径和哈希均完整保存在 JSON 的 link_comparison 中。
这属于碰撞近似变化，可能影响接触面积、接触点和抓取结果，按用户规则不单独判为不同手型。

## 7. mass / COM / inertia

17 个对应实体 link 的 mass、局部 inertial origin 与完整 3×3 inertia matrix 逐项完全一致，没有发现 CordViP 对 LEAP 施加 UR5 腕部那种百倍惯量改动。
两边实体 link 的总质量均为 `0.746 kg`。四个额外 tip_head 是空 frame，不增加质量或动力学自由度。
关节/visual origin 的小数截断会带来前述小量世界坐标偏差；此处“相同”指文件声明的局部动力学参数。

| 官网 link | CordViP link | mass [kg] 两边 | COM xyz 两边 | 最大惯量元素差 |
|---|---|---|---|---|
| palm_lower | palm_lower | 0.237 | (0, 0, 0) | 0 |
| mcp_joint | mcp_joint | 0.044 | (0, 0, 0) | 0 |
| pip | pip | 0.032 | (0, 0, 0) | 0 |
| dip | dip | 0.037 | (0, 0, 0) | 0 |
| fingertip | fingertip | 0.016 | (0, 0, 0) | 0 |
| mcp_joint_2 | mcp_joint_2 | 0.044 | (0, 0, 0) | 0 |
| pip_2 | pip_2 | 0.032 | (0, 0, 0) | 0 |
| dip_2 | dip_2 | 0.037 | (0, 0, 0) | 0 |
| fingertip_2 | fingertip_2 | 0.016 | (0, 0, 0) | 0 |
| mcp_joint_3 | mcp_joint_3 | 0.044 | (0, 0, 0) | 0 |
| pip_3 | pip_3 | 0.032 | (0, 0, 0) | 0 |
| dip_3 | dip_3 | 0.037 | (0, 0, 0) | 0 |
| fingertip_3 | fingertip_3 | 0.016 | (0, 0, 0) | 0 |
| pip_4 | thumb_temp_base | 0.032 | (0, 0, 0) | 0 |
| thumb_pip | thumb_pip | 0.003 | (0, 0, 0) | 0 |
| thumb_dip | thumb_dip | 0.038 | (0, 0, 0) | 0 |
| thumb_fingertip | thumb_fingertip | 0.049 | (0, 0, 0) | 0 |

以下为每类零件的完整对称惯量六分量 `(ixx,iyy,izz,ixy,ixz,iyz)`，单位 kg·m²；两边相同，所有 inertial rpy 都为零。JSON 另按全部 17 link 存储完整矩阵。

| 零件 | 完整对称惯量六分量 |
|---|---|
| palm_lower | (0.000354094, 0.000260915, 0.000529257, -1.193e-06, -2.445e-06, -2.905e-06) |
| mcp_joint | (1.1499e-05, 7.796e-06, 1.4759e-05, 3.049e-06, 1.21e-07, 1.12e-07) |
| pip | (4.798e-06, 2.862e-06, 4.234e-06, 1.2e-08, 4e-09, 1.1e-08) |
| dip | (5.542e-06, 5.727e-06, 6.682e-06, -6.07e-07, -1.7e-08, -2.3e-08) |
| fingertip | (3.368e-06, 1.556e-06, 2.863e-06, 1.15e-07, 0, 0) |
| thumb_pip | (5.93e-07, 5.49e-07, 2.24e-07, 0, 0, 0) |
| thumb_dip | (8.474e-06, 3.841e-06, 7.679e-06, 2.41e-07, 2.6e-08, 2.5e-08) |
| thumb_fingertip | (2.0372e-05, 4.336e-06, 1.9845e-05, -4.89e-07, -3e-08, -9.7e-08) |

这些值只是两套文件共同声明的仿真参数，不是本轮对真机做出的质量或电机动力学标定。掌 visual 被缩放时，CordViP 也没有同步重算这些参数。

## 8. 判定、适用性和本轮变更范围

- A SAME_MODEL：不选，因为 palm_lower 几何存在可量测的非刚体缩放。
- B SAME_KINEMATICS_DIFFERENT_DYNAMICS：不选，17 个对应 link 的动力学声明没有改变。
- C DIFFERENT_MODEL：选择，具体含义是同一 v1 Full Right 基础的掌几何改动版本，非另一代或左手。

如果目标是“与官网 Right 原始几何等价的标准资产”，不建议直接把 CordViP 认定为完全等价并采用。
如果后续明确接受手掌 Y 向 1% 缩放、joint origin 截断和简化碰撞，它仍是可用于控制学习的候选；这些差异是否可以接受由用户看完报告后决定，本轮没有切换。
本报告只评价 LEAP 子树，不能据此消除此前 CordViP UR5 本体的惯量差异。

本轮没有修改 CordViP、官网/Sim 资产、旧 combined、URDF、USD、配置或测试；没有创建联合模型、ur5_leap.py 或重新生成 USD。仅新增本报告和同名 JSON。
输入校验和完整映射、材质绑定、collision origin、mass/inertia、容差和分析方法均见 [机器可读报告](cordvip_vs_official_leap.json)。

**最终判定：C. DIFFERENT_MODEL。**
