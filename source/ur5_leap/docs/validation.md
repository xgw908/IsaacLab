# 静态检查结果

只做 XML、树结构、关节限制、资源与原始文件校验；未做 USD 转换、动力学或真机验证。

| 模型 | 结果 | 根 link | 可动关节 | 唯一 mesh |
|---|---|---|---:|---:|
| ur5_cb3 | PASS | world | 6 | 14 |
| leap_right_website_original | PASS | palm_lower | 16 | 8 |
| leap_right_portable | PASS | palm_lower | 16 | 8 |
| leap_sim_original | PASS | palm_lower | 16 | 8 |
| combined | PASS | base_link | 22 | 22 |
| cordvip | PASS | base_link | 22 | 24 |
| bodex | PASS | base_link | 22 | 15 |
| bodex_simplified | PASS | base_link | 22 | 15 |
| bodex_hand | PASS | hand_base_link | 16 | 8 |
| bodex_hand_simplified | FAIL | hand_base_link | 16 | 0 |

原始下载文件 SHA-256 全部通过。联合模型的官方 link/joint、惯量、碰撞、限制和实际 mesh 目标与独立模型逐项比较通过；允许的变换只有去掉 UR5 的 world 锚定、重命名手关节、重定位相对路径和添加两个占位 fixed joint。

官网 Right 原文件需要显式空包名映射；BODex 需要把 ur_description 映射到其资产根。原文件保持不变，便携生成版本消除了这些依赖。

## 联合模型 22 关节顺序

以下是 XML 顺序；仿真器导入后仍须按名称解析索引。

```text
00 shoulder_pan_joint
01 shoulder_lift_joint
02 elbow_joint
03 wrist_1_joint
04 wrist_2_joint
05 wrist_3_joint
06 leap_joint_0
07 leap_joint_1
08 leap_joint_2
09 leap_joint_3
10 leap_joint_4
11 leap_joint_5
12 leap_joint_6
13 leap_joint_7
14 leap_joint_8
15 leap_joint_9
16 leap_joint_10
17 leap_joint_11
18 leap_joint_12
19 leap_joint_13
20 leap_joint_14
21 leap_joint_15
```
