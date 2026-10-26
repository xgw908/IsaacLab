# UR5 CB3 + LEAP Hand v1 Full Right 资产工作区

目标硬件是 UR5 CB3（`ur5`，不是 `ur5e`）和 LEAP Hand v1 Full Right（16 DoF）。
本目录只整理资产、构建联合 URDF、做静态检查；没有新增任务、训练、reward 或 USD 转换结果。

## 目录

```text
assets/official/ur5/                         官方 UR5 原始 xacro、配置、mesh；generated/ 是展开结果
assets/official/leap_hand_v1_right/
    urdf/website_right/                      官网明确标为 Right 的原始 URDF 包，解压后未修改
    sim_reference/leap_hand/                 LEAP_Hand_Sim 的原始资产，未修改
    cad/                                    官网完整右手 STEP、Right URDF ZIP、安装上掌板 STL/STP
    isaac_lab_reference/                     旧 Isaac Lab 2.1 / Sim 4.5 右手 USD、配置，仅供参考
    generated/                              修正资源 URI 的便携右手 URDF；原始关节和物理数据保留
assets/combined/ur5_leap_right/               我们后续使用的 22 DoF 联合模型，安装变换尚未标定
assets/references/cordvip/ur5_leaphand/        完整 CordViP 联合资产，未修改
assets/references/bodex/ur5_leap/             BODex 联合/单手、完整/简化资产，未修改
assets/sources.lock.json                     五个仓库的完整 commit、原路径、Git blob SHA-1
assets/downloads.json                        每个真实下载文件的 URL、大小、SHA-256、LFS oid
scripts/                                    下载、生成、检查脚本，不依赖 Isaac Sim
docs/                                       来源、差异、完整目录树、下载清单、大文件清单、静态检查结果
```

完整实际目录树见 [docs/directory_tree.txt](docs/directory_tree.txt)。

## 恢复下载与重建

所有命令从 IsaacLab 仓库根目录执行。工具通过 uv 临时环境运行，不同步完整 Isaac Sim 依赖。

```bash
uv run --no-project python source/ur5_leap/scripts/download_assets.py --website
uv run --no-project --with-requirements source/ur5_leap/requirements-tools.txt python source/ur5_leap/scripts/build_combined.py
uv run --no-project python source/ur5_leap/scripts/inspect_ur5.py
uv run --no-project python source/ur5_leap/scripts/inspect_leap.py
uv run --no-project python source/ur5_leap/scripts/inspect_combined.py
uv run --no-project python source/ur5_leap/scripts/inspect_combined.py --model cordvip
uv run --no-project python source/ur5_leap/scripts/inspect_combined.py --model bodex
uv run --no-project python source/ur5_leap/scripts/inspect_combined.py --model bodex-simplified
uv run --no-project python source/ur5_leap/scripts/inspect_all.py
```

最后一条包含额外的 BODex 单独简化手检查：原始文件存在已知 mesh 相对路径错误，因此严格检查会返回非零，详情见 [known_issues.md](docs/known_issues.md)。五类主要资产的检查结果单独列在 [validation.md](docs/validation.md)。

大于仓库 2,000 KiB 限制的原始文件保留在本地，通过本目录 `.gitignore` 排除，并通过下载脚本恢复。
它们没有被删除，也没有提交成 Git LFS 指针。服务器 `git pull` 后应先运行上面的下载命令。
清单见 [large_files.md](docs/large_files.md)。只做字节复核可运行 `download_assets.py --verify-only`。

## 联合模型

入口：`assets/combined/ur5_leap_right/urdf/ur5_leap_right.urdf`。

```text
base_link → UR5 六个 revolute joints → flange
         → fixed → mounting_adapter → fixed → palm_lower
         → LEAP 十六个 revolute joints
```

`config/mounting.json` 中两个变换均为 **PLACEHOLDER**，当前采用单位变换，只证明结构连通。
它们没有采用 CordViP/BODex 的安装参数，不代表真实安装，也不保证几何无穿插。

**TODO: replace with measured lab UR5 flange → LEAP palm transform**

`mounting_adapter` 当前只是空 frame，没有捏造尺寸、质量和惯量。官网安装板 CAD 已保存，但其安装朝向、
CAD 原点与 URDF 原点之间的关系还未核对，因此没有擅自将其加入碰撞模型。

UR5 的 world 固定连接只在联合模型中移除，以 `base_link` 作为唯一根；导入 USD 时仅固定机械臂底座。
LEAP 关节在联合模型中由 `0..15` 改为 `leap_joint_0..leap_joint_15`，避免纯数字 USD 命名转换。
映射及推荐的 22 关节控制顺序见 `config/joint_mapping.json`；仿真器关节索引仍须按名称解析。
联合模型用相对路径共享官方 mesh，需保留整个本工作区，不能只复制 `combined/`。

## 来源与许可

- UR5：Universal Robots 官方 ROS2 Description，BSD-3-Clause。
- 官网 LEAP v1 Right URDF/CAD：官网声明 CC BY-NC-SA，页面未给出版本号。
- LEAP_Hand_Sim：仓库 MIT；官网 CAD 声明分别保留。
- 旧 LEAP_Hand_Isaac_Lab：README 声明 MIT；该提交未提供独立根 LICENSE。
- CordViP：项目 MIT；上游资产来源条款仍须保留。
- BODex：NVIDIA 非商业研究/评估许可，并保留 LICENSE_ASSETS，不能写成 MIT。
- 本目录新编工具的代码头为 BSD-3-Clause；不会覆盖模型资产的来源许可。

详细提交和目录对应见 [asset_sources.md](docs/asset_sources.md) 以及各资产的 `SOURCE.md`。

## 真机还需补齐

机械臂铭牌/代际和工厂运动学校准；法兰到手掌的 XYZ/RPY；转接板、垫片和指尖版本；
安装板质量/质心/惯量；桌面与机械臂底座的位姿；Full 电机型号、16 电机 ID、方向、零位、限位及实际控制设置。
几何相同不能代替 Full 电机动力学辨识。

## 后续导入 Isaac Lab 3.x / Isaac Sim 6.1

本轮没有启动 Isaac Sim，也没有把静态检查标为动力学验证。Docker 需挂载整个工作区。
恢复大文件后，在已配置好的 Isaac Lab 环境中使用当前仓库转换器，例如从仓库根目录执行：

```bash
uv run python scripts/tools/convert_urdf.py \
  source/ur5_leap/assets/combined/ur5_leap_right/urdf/ur5_leap_right.urdf \
  source/ur5_leap/generated_usd/ur5_leap_right --fix_base
```

此命令为下一阶段示例，本次未执行。输出参数是目录，实际 USD/USDA 路径以转换器打印结果为准。
初次不加 `--merge_joints`，便于保留安装 frame 并核对层级；随后检查 22 关节、惯量、碰撞、自碰撞过滤和驱动增益。
选择目标物理后端执行后续验证；成功导入不等同于完成 PhysX 稳定性验证。

旧右手 USD 的配置不可直接并入联合机器人：旧代码使用 WXYZ，当前 3.x 为 XYZW，状态读取/写入、
物理配置和执行器限制字段也需迁移。还要解除旧手单独固定到世界的设置，并重新考虑重力。
官方 UR5 默认参数不是实验室机械臂的校准参数；最终 Sim2Real 基础应使用官方组合并补上实测数据。
