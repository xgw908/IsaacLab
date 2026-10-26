# LEAP Hand v1 Full Right 官方来源

获取日期：2026-10-26。目标为 v1 Right；没有使用 v2 或左手 URDF 作为模型。

## 官网 Right URDF / CAD（联合模型的手部来源）

页面：https://v1.leaphand.com/leap_cad ，明确选择 LEAP Full Assembly Right。

| 页面条目 | 实际上游 URL | 本地保存 |
|---|---|---|
| Download Right URDF | https://v1.leaphand.com/static/cad/urdf/leap_right.zip | `cad/right_urdf.zip`，原字节解压到 `urdf/website_right/` |
| Download Right STP | https://v1.leaphand.com/static/cad/stp/full_assembly_right.step | `cad/full_assembly_right.stp`，只更改保存文件名，未改变内容 |
| Xarm/Franka/UR5 STL | https://v1.leaphand.com/static/cad/stl/palm_upper_xarm_franka.stl | `cad/palm_upper_xarm_franka_ur5.stl` |
| Xarm/Franka/UR5 STP | https://v1.leaphand.com/static/cad/stp/palm_upper_xarm_franka.stp | `cad/palm_upper_xarm_franka_ur5.stp` |

官网没有提供这些下载的 Git commit；使用获取日期、原始页面 HTML、原始 URL 和 SHA-256 定位。
CAD 页面许可为 CC BY-NC-SA，未标明具体版本，见 `LICENSE_CAD_NOTICE.md` 和 `cad/leap_cad.html`。
完整 STEP 曾遇 TLS 中断，重试后成功；最终无未下载项。

官网 Right URDF 的根为 `palm_lower`，16 个 revolute joint，名称 `0..15`。
原始 mesh URI 是 `package:///filename.stl`，工作副本 `generated/leap_hand_right.urdf` 改为相对路径，
原 URDF 和 STL 均保留。8 个 STL 与下面 Sim 来源逐一按 SHA-256 对应，关节变换和限制也一致。

## 官方 LEAP_Hand_Sim 原始参考

- Repository: https://github.com/leap-hand/LEAP_Hand_Sim
- Branch: `master`
- Commit: `150bc3d4b61fd6619193ba5a8ef209f3609ced89`（2024-05-18）
- 原路径：完整 `assets/leap_hand/` → 本地 `sim_reference/leap_hand/`
- 保留根 `LICENSE.txt`（MIT）及 `README.md`。
- 根 `palm_lower`、16 DoF；关节 XML 次序与官网 Right 不同，不能用排列顺序代替名称映射。
- Isaac Gym Preview 4 / Python 3.8 的旧环境代码未搬入当前 Isaac Lab 配置。

## 官方旧 Isaac Lab 右手参考

- Repository: https://github.com/leap-hand/LEAP_Hand_Isaac_Lab
- Branch: `main`
- Commit: `c576e6a83183ba504aef8f57015f2899b799db1a`（2025-09-04）
- 原路径：`source/LEAP_Isaaclab/LEAP_Isaaclab/assets/leap_hand_v1_right/` 和同级 `leap.py`
- 保存到 `isaac_lab_reference/`，保持 `leap.py` 到 USD 目录的相对关系。
- README 声明 MIT；锁定文件树未提供独立根 LICENSE，不伪造许可证文件。
- 测试环境为 Isaac Sim 4.5 / Isaac Lab 2.1.0；USD 关节配置命名 `a_0..a_15`。
- USD 层保留完整，但本次未打开 USD 运行时验证其内部依赖。

所有 GitHub 原路径和校验值见 `../../sources.lock.json`、`../../downloads.json`。
Full/Lite 结构类似，Full 使用 XC330-M288-T，仍需核对实验室电机、电流和零位设置。
几何、官方 URDF effort 值和旧示例驱动参数不能替代实物动力学辨识。
