# 我们的 UR5 CB3 + LEAP v1 Right

模型入口：`urdf/ur5_leap_right.urdf`；唯一根为 `base_link`，22 个可动关节。
UR5 从官方 xacro 按 `ur_type=ur5` 展开，LEAP 来自官网明确标为 Download Right URDF 的 ZIP。
没有把 CordViP 或 BODex 的联合模型当作此模型的源文件。

生成脚本：[build_combined.py](../../../scripts/build_combined.py)。
生成过程只移除机械臂的 world 锚定、重定位 mesh 路径、重命名手关节并添加两个 fixed joint。
官方连杆、关节坐标、质量、惯量、限制和碰撞形状按结构复核保留。

`config/mounting.json` 中的两个变换均为 **PLACEHOLDER / 未标定**：

```text
flange → mounting_adapter : xyz=0 0 0, rpy=0 0 0
mounting_adapter → palm_lower : xyz=0 0 0, rpy=0 0 0
```

**TODO: replace with measured lab UR5 flange → LEAP palm transform**

单位变换只建立结构，可能出现穿插；不代表安装板厚度为零。
`mounting_adapter` 是空 frame，实际 CAD 在 `../../official/leap_hand_v1_right/cad/`。
固定关节没有增加自由度。未添加真实安装板质量、惯量和 mesh，需后续实测后补齐。

联合模型共享官方资产目录下的 mesh，所有引用均为 POSIX 相对路径；复制时保留整个 `source/ur5_leap/`。
手关节映射、推荐控制顺序在 `config/joint_mapping.json`；Isaac Sim 的导入顺序需按名称核对。

许可为组合来源各自的条款：UR5 的 BSD-3-Clause，以及官网 LEAP CAD 的 CC BY-NC-SA 声明。
查看两个官方资产目录中的原始 LICENSE 和 SOURCE；不把整个联合资产统一标成 BSD 或 MIT。
