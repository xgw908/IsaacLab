联合 URDF 通过相对路径复用 `assets/official/` 中的 UR5 与官网 Right 手网格。
因此需要一起保留整个 `source/ur5_leap/`，不能只复制 `combined/`。

`mounting_adapter` 当前只是空坐标系，没有捏造转接板的 mesh、质量或惯量。
官网下载的安装板 CAD 保存在 `assets/official/leap_hand_v1_right/cad/`，其坐标、尺寸与质量仍需和真机核对。
