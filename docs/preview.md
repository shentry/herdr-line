# 预览图来源与隐私边界

`preview.png` 是 **Herdr 0.1.18 官方 Linux 运行时实际绘制的原生窗口帧**（1280 × 820），使用官方 `herdr-app shot` 导出；不是 AI 生成图，也不是 HTML 仿制界面。

## 渲染方法

- 使用 [官方发布安装说明](https://github.com/herdrdev/herdr-app#install) 的 Linux 发行包，并核对官方 release manifest 的 SHA256。
- 在隔离的临时 HOME、`HERDR_APP_HOME`、core session 与状态目录运行，关闭遥测；不使用个人 Herdr 配置、聊天或数据库。
- 临时 demo wrapper 继承本插件，直接调用 `mods/ccline/main.js` 的原始 `renderConfigurator()`，以及未修改的 `layout.js`。**产品组件源码保持逐字节一致**；wrapper 只注入合成状态、禁用真实采集/轮询，并加上 “SYNTHETIC DEMO DATA” 标识。
- 通过官方 `herdr-app check` 检查原插件和 wrapper，再用 `herdr-app shot preview.png` 导出原生渲染帧；不是桌面/浏览器自动截图。

Herdr Line 的截图已在更名后重新原生渲染，界面、预设名称及标题均使用新品牌。文中的 `mods/ccline/` 是保留的 legacy 安装标识，详见 README 的兼容说明。

## 示例数据

全部名称、终端编号、token/配额/性能数值和桥接状态均为人为构造的演示 fixture。截图不含真实聊天、私人绝对路径或实际会话 ID；`t1` / `t2` 等仅为合成终端示例，不是用户会话。

图像已做人工可视检查及 PNG 块检查：仅 IHDR、sRGB、IDAT、IEND，无 EXIF、文本块或嵌入文件。

## 限制

此图证明真实组件能在原生 Herdr 中渲染，但**不等于真实客户端端到端验收**；合成 wrapper 没有连接实际 agent、读取会话或执行桥接。Gallery 是否收录由 herdr.dev/mods 决定。
