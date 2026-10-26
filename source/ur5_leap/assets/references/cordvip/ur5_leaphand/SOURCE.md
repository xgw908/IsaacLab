# CordViP 原始联合资产

- Repository: https://github.com/xuanxuanzzzii/cordvip
- Branch: `main`
- Commit: `ad6d441abe7b0480cf79b0311db266965c1313b6`
- 下载日期：2026-10-26
- 原路径：`generate_pc/assets/ur5_leaphand/`，完整资产目录保留。
- License：根 `LICENSE` 为 MIT，已保留；不能据此取消模型上游许可。
- 原始 URDF/mesh 未修改。原路径和 Git blob SHA-1 在 `../../../sources.lock.json`；下载 SHA-256 在 `../../../downloads.json`。

6 个 UR5 可动关节＋16 个 LEAP 可动关节＝22 DoF，根 `base_link`；手关节 `joint0..joint15`。
该研究项目 README 明确使用真实 UR5 + LEAP，当前资产用于点云/运动学流程，不能等同于已通过 PhysX 动力学验证。

```text
wrist_3_link → ee_link → palm_lower

ee_fixed_joint (fixed):
  parent=wrist_3_link, child=ee_link
  xyz=0 0.0823 0
  rpy=0 0 1.57079632679

mount_joint (fixed):
  parent=ee_link, child=palm_lower
  xyz=0 0.03 0.06
  rpy=3.14159 -1.57079 3.14159
```

这里记录的是有效 XML 元素，未把被注释掉的替代安装参数当成当前值。
**以上仅作为参考，不代表实验室真机安装偏移。**旧 UR5 wrist/ee frame 定义与当前官方 flange 不同。
保留目录内未被当前 URDF 引用的 left mesh 只是为了完整保存上游目录；本次联合模型没有使用这些左手 mesh。
