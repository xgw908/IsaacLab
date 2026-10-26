# UR5 CB3 + LEAP v1 Right 资产比较

检查日期：2026-10-26；本报告基于已下载的实际文件。静态可解析不代表已通过 Isaac Sim 6.1 动力学验证。

| 项目 | 官方 UR5 + 官网 Right（分别保存） | 我们的 Combined | CordViP | BODex |
|---|---|---|---|---|
| UR5 来源 | Universal Robots ROS2 Description，ur5 | 同左，官方 xacro 展开 | 项目内旧式 UR5 描述 | 项目内旧式 UR5 描述 |
| LEAP 来源 | v1 官网明确的 Right URDF；Sim/旧 Lab 另存参考 | 直接采用官网 Right；不取第三方联合手 | 项目内修改过的手，含额外 frame 和碰撞近似 | 项目内修改过的手，完整/简化两组 mesh |
| UR5 DoF | 6 | 6 | 6 | 6 |
| LEAP DoF | 16 | 16 | 16 | 16 |
| 总 DoF | 两个独立模型 6 与 16，尚未连接 | 22，一个 robot tree | 22，一个 robot tree | 联合完整/简化均 22 |
| LEAP 根 link | palm_lower | palm_lower，是联合树内部节点 | palm_lower，是联合树内部节点 | hand_base_link，是联合树内部节点 |
| robot 根 link | UR5 展开为 world；手为 palm_lower | base_link | base_link | base_link |
| link 数量 | UR5 13；手 17 | 30 | 29 | 联合完整/简化均 24 |
| 机械臂连接 link | 官方推荐 flange | flange → mounting_adapter → palm_lower | wrist_3_link → ee_link → palm_lower | wrist_3_link → hand_base_link |
| mount xyz [m] | 未组合 | 两段均 0 0 0，PLACEHOLDER | ee_link → palm：0 0.03 0.06 | wrist_3 → hand：0.033030643865100524 0.09357759647153979 -0.05747874965286254 |
| mount rpy [rad] | 未组合 | 两段均 0 0 0，PLACEHOLDER | ee_link → palm：3.14159 -1.57079 3.14159 | wrist_3 → hand：1.5707963267948966 1.5707963267948966 0 |
| mesh 类型 | UR5 visual DAE/collision STL；手 STL | 复用官方 DAE/STL，相对路径 | visual DAE/OBJ，附 GLB/MTL；碰撞含几何近似 | DAE/STL/OBJ，分完整与简化目录 |
| collision 元素数 | UR5 7；手 17 | 24，未给占位 adapter 伪造碰撞 | 79，包含多段几何近似 | 联合完整/简化均 33 |
| inertial 元素数 | UR5 7；手 17 | 24，空安装 frame 无伪造惯量 | 25 | 联合完整/简化均 24 |
| 手关节命名 | 官网/Sim 为 0..15；旧 USD 配置 a_0..a_15 | leap_joint_0..leap_joint_15 | joint0..joint15 | j0..j15 |
| 资源解析 | 原始 UR5 package://；官网手 package:///；生成视图已转相对路径 | 全部 POSIX 相对路径，依赖共享 official/ | 相对路径，直接 mesh 和材质依赖检查通过 | package://ur_description 显式映射到 BODex 资产根 |
| license | UR BSD-3-Clause；官网 CAD CC BY-NC-SA；各代码仓库声明另存 | 继承官方部件许可，未统一重标 | 项目 MIT，保留上游资产条款 | NVIDIA 非商业研究/评估，附 LICENSE_ASSETS，非 MIT |
| Isaac Lab 3.x 可用性 | 转换输入已就绪；未运行导入 | 结构与资源检查通过，安装未标定 | 原始联合静态通过，需转换和驱动检查 | 两个联合静态通过，需包路径映射和转换 |
| 主要用途 | 机械真实性、参数和来源基准 | 后续实验室 Sim2Real 的首选基础 | 真机项目组合、坐标和碰撞参考 | 规划/简化模型与结构对比参考 |

## 三类关键差异

### 1. UR5 frame 定义不同

当前官方模型保留 base_link、base_link_inertia、base、flange、tool0 等 frame。
base 与 base_link 有绕 Z 的 180° 差异，比较示教器数值时要使用正确参考系。
当前官方 wrist_3_link → flange 为零平移、rpy=(0,-π/2,-π/2)。

CordViP 的 wrist_3_link → ee_link 则含 xyz=(0,0.0823,0)、rpy=(0,0,π/2)。
因此它的 mount_joint 后半段不能直接接到当前官方 flange 上。
BODex 的变换又直接表达 wrist_3_link → hand_base_link，父子 frame 与 CordViP 也不同。

### 2. 手关节名称与次序不同

官网 Right 的 XML 关节次序是 0..15；Sim 的 XML 中 1 先于 0。
16 个同名关节的 parent/child、xyz/rpy 和 limits 一致，8 个 STL 逐个字节一致，
但文件布局和 URI 不同，不能按 XML 次序建立电机列映射。
旧 Isaac Lab 配置使用 a_0..a_15；我们的联合版显式改名并保存 name mapping。
BODex 的 XML 次序为 j12..j15、j0..j3、j8..j11、j4..j7。
完整 22 关节顺序及每个关节限制见 [validation.json](validation.json)。

### 3. 几何与物理近似不同

CordViP 有额外固定指尖 frame、不同碰撞近似和更多碰撞元素；BODex 的手根改名、
碰撞和完整/简化网格选择也不同。它们适合参考工程做法，不能仅凭同为 22 DoF 判断模型等价。
我们的生成器还逐项复核联合模型中官方部件的 link/joint、惯量、碰撞、限制和实际 mesh 目标，
没有从第三方组合复制 UR5/手部数值或安装偏移。

## BODex 简化版

`ur5_leap_simplified.urdf` 选用 `meshes/ur5/visual_simplified/` 和 `meshes/leap_simplified/`；
和完整联合版具有相同可动自由度及安装变换，不能用“简化”理解为关节数量减少。
`leap_hand_simplified.urdf` 的 8 个相对 mesh 引用存在上游少写 `../` 的问题；原件未修改，
严格单独检查不通过。其他三个原始 BODex URDF 均通过，详见 [known_issues.md](known_issues.md)。

## 最适合作为实验室基础的模型

采用我们的官方来源 Combined，随后换入真机工厂运动学校准、实测 flange→palm 安装变换，
补齐 adapter 质量/惯量、Full 电机控制参数、指尖接触特性和桌面位姿。
当前单位安装变换只是 PLACEHOLDER，可能造成穿插，不能宣称已完成真实硬件匹配。

原始和第三方文件持续保留作对照。旧 USD 仅作参考，不能直接复制其 WXYZ 姿态、旧状态读写接口、
旧执行器字段或独立手掌固定设置到 Isaac Lab 3.x。
