# UR5 CB3 官方来源

- Repository: https://github.com/UniversalRobots/Universal_Robots_ROS2_Description
- Branch: `rolling`
- Commit: `81f7c9fe003c2f0e02eec5a7253f1b262ad38b61`（4.4.0，2026-10-22）
- 下载日期：2026-10-26
- License: BSD-3-Clause，原始 `LICENSE`、`package.xml`、`README.md` 均保留。

原始 `urdf/`、`config/ur5/`、`meshes/ur5/` 保持上游相对目录；另保留
`config/initial_positions.yaml`，使一并保存的 mock xacro 也有其配置依赖；以及
`doc/index.rst`、`doc/robot_frames.rst` 作为运动学和坐标系说明。
具体文件原路径、commit 和 Git blob SHA-1 见 `../../sources.lock.json` 的 `ur`；
下载后 SHA-256 见 `../../downloads.json`。没有保存 `config/ur5e/` 或 `meshes/ur5e/`。

选择 `ur5` 是因为目标为 UR5 CB3；`config/ur5/joint_limits.yaml` 引用 UR5/CB3 手册。
UR5e 的肩部、腕部运动学尺寸和质量/惯量不同，不能替代 CB3。
通用宏中列出的其他型号名称是上游参数接口，不表示下载了其他型号资产。

原始 xacro 没有修改。`generated/ur5_cb3.urdf` 是本地派生文件：在临时副本中解析 ROS 包查找，
按 `ur_type=ur5` 展开，再把 mesh URI 转成相对路径。该独立展开结果保留 world 固定基座。
联合模型才移除这一个 world 锚定，以便后续在导入时固定机械臂底座。

当前官方 `flange` 为末端安装 frame；`wrist_3_link → flange` 是零平移和非零旋转，
不能直接复制旧式 `wrist_3_link/ee_link` 安装数值。
默认运动学不是实验室这台机器人校准数据，部分惯量是估计值。
