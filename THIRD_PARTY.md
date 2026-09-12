# 第三方组件与许可边界

本仓库的 MIT 许可证只适用于本仓库原创的生成及验证脚本，不改变任何第三方项目的许可。

## Cyber Engine Tweaks

- 项目：https://github.com/maximegmd/CyberEngineTweaks
- 本次验证版本：1.37.1
- 上游许可证：MIT
- 本项目只读取其安装包内已经编译的 `version.dll`。

上游 MIT 许可证副本见 `licenses/CET-LICENSE.txt`。

## Ultimate ASI Loader

- 项目：https://github.com/ThirteenAG/Ultimate-ASI-Loader
- 上游许可证：MIT
- CET 的 `version.dll` 使用该加载器；本项目在其 PE 导出表上增加转发项。

上游 MIT 许可证副本见 `licenses/UltimateASILoader-LICENSE.txt`。

## RED4ext

- 项目：https://github.com/WopsS/RED4ext
- 本次验证版本：1.30.0
- 上游许可证：MIT
- RED4ext 使用独立的 `winmm.dll`，不参与本项目的 DLL 生成。

## DLSSG Native / dlssg_for_sm86

- 项目：https://github.com/sdli1995/dlssg_for_sm86
- 本次验证版本：0.2.4
- 本地输入 DLL 包含上游及 NVIDIA 相关二进制材料。

上游 `THIRD_PARTY_NOTICES.txt` 明确区分项目源码与 NVIDIA 运行时、模型、图和内核资产的许可范围。该声明副本见 `licenses/DLSSG-THIRD_PARTY-NOTICES.txt`。本仓库不对这些材料重新授权，也不提交或发布 DLSSG DLL；使用者必须从上游自行取得。

## 游戏及 NVIDIA 组件

《赛博朋克 2077》、游戏自带 `nvngx_dlssg.dll`、DLSS、NGX、NVIDIA 驱动及其相关商标和资产属于各自权利人。本项目不包含这些文件，也不授予相关权利。
