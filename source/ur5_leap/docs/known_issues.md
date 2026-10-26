# 已确认的问题与验证边界

## BODex 单独简化手的相对路径

原始 `assets/references/bodex/ur5_leap/urdf/leap_hand_simplified.urdf` 使用
`meshes/leap_simplified/...`，但模型位于 `urdf/`，真实文件在同级的 `../meshes/`。
共涉及 8 个唯一 mesh 引用：palm_lower.stl、mcp_joint.stl、pip.stl、dip.stl、thumb_pip.stl、
thumb_dip.stl、convex_tip.obj、convex_tip_thumb.obj。

真实文件均已下载，不是丢失了 Git LFS payload。若要单独导入该变体，下一阶段应在派生副本中
把这些引用改成 `../meshes/leap_simplified/...`；本次按要求不修改原始参考 URDF。

完整单独手，以及 UR5 联合完整/简化两个版本均通过检查。`inspect_all.py` 的严格非零退出记录
只来自这个额外单独简化手变体；详情保留在 `validation.json`，没有将其改写为 PASS。

## 官方 Right 包的 URI

官网 Right ZIP 原始 URDF 使用 `package:///filename.stl`（空包名），不具备正常 ROS 包语义。
生成版本只将资源引用转换成实际 STL 的相对路径，原件仍保留。
与 LEAP_Hand_Sim 对照，16 个关节的 parent/child、xyz/rpy、limits 一致，8 个 STL 的 SHA-256 逐一一致。
两份原始 URDF 文本并不完全相同，XML 中关节出现顺序也不同。

## BODex 中其他型号的符号链接

`meshes/ur10e`、`meshes/ur5e` 原本是指向外部其他型号目录的符号链接；本次保留原始目标文本，
在锁定清单中注明上游模式 `120000`。它们不是实际 mesh，未用于任何被检查的 URDF。
没有为了这些未使用的链接额外下载 UR5e/UR10e 资产。

## 当前不代表已完成的事项

安装偏移、转接板物理参数、Full 电机动力学均未标定；占位安装可能导致穿插。
旧右手 USD 已下载但没有通过 USD 运行时加载，所以未验证层内部的外部依赖。
没有进行 USD 转换、Isaac Sim 6.1 运行、碰撞烹饪、物理步进、训练或真机控制。
LEAP 的几何来源明确为 v1 Right，Full 电机仍需核对实物 XC330-M288-T 和实际控制设置。
