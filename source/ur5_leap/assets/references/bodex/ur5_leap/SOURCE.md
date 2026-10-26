# BODex 原始联合/单手资产

- Repository: https://github.com/JYChen18/BODex
- Branch: `main`
- Commit: `06b9a3c90870d33bde9d6c665d4ed2819471407e`
- 下载日期：2026-10-26
- 原路径：`src/curobo/content/assets/robot/leap_description/`
- 保留四个 URDF 和完整 meshes/，不保留与模型无关的 `.DS_Store`。
- 根 `LICENSE` 为 NVIDIA 非商业研究/评估许可，另保留 `LICENSE_ASSETS`，不是 MIT。
- 原始 URDF 没有修改。Git LFS 指针已获取真实 payload，并按上游 oid SHA-256 和大小校验。
- 原路径/commit：`../../../sources.lock.json`；实际 payload URL、校验值：`../../../downloads.json`。

UR5 联合完整和简化版均为 6+16=22 DoF，根 `base_link`。手根名 `hand_base_link`，关节名 `j0..j15`。
XML 中手的关节次序是 j12..j15、j0..j3、j8..j11、j4..j7，不能直接按列号向真机发送。

```text
ee_fixed_joint (fixed): wrist_3_link → hand_base_link
xyz=0.033030643865100524 0.09357759647153979 -0.05747874965286254
rpy=1.5707963267948966 1.5707963267948966 0
```

此变换是该项目的安装定义，不是实验室标定。
完整模型和简化模型引用不同的手部/手臂 mesh 集合，碰撞几何也采用近似；细节见差异报告和 validation.json。
URDF 的 `package://ur_description/meshes/...` 应把 `ur_description` 映射到本目录，不能映射到另一个官方 UR 包。

额外发现：`urdf/leap_hand_simplified.urdf` 的 8 个 `meshes/leap_simplified/...` 相对引用缺少 `../`。
所有实际 mesh 存在，但原文件单独导入需要在派生副本中修正；本次保留错误并报告，未偷偷改动。
两个 UR5 联合版本及完整单独手均通过静态检查。

`meshes/ur10e`、`meshes/ur5e` 在上游是 Git 符号链接，指向本资产目录以外的其他型号。
本次在 Windows 中保留其原始链接目标文本，未冒充为 mesh，也未下载其他型号。
这四个 URDF 均不引用它们；记录见锁定清单的 `git_mode` / `materialization`。
