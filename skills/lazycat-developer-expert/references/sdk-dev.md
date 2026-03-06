
# 懒猫微服 SDK 与扩展开发指南

你是一个专业的懒猫微服原生开发工程师。当用户希望用 Node.js/Go 从零开发一款微服应用，并希望调用微服底层系统 API（如获取设备列表、注册文件关联）时，请遵循本指南。

## 1. 引入 Lzc-SDK (@lazycatcloud/sdk)
官方提供了 JavaScript/TypeScript 和 Go 版本的 SDK。这让应用可以直接与懒猫微服的系统层、包管理层进行 gRPC 通信。

### JavaScript / TypeScript 示例
SDK 内部使用 `grpc-web`，可以直接在浏览器前端代码中使用。
**安装:** `npm install @lazycatcloud/sdk`
**用法:**
```javascript
import { lzcAPIGateway } from "@lazycatcloud/sdk"

// 初始化网关，使用当前页面的 origin (如 https://myapp.heiyu.space)
const lzcapi = new lzcAPIGateway(window.location.origin, false)

// 示例：获取微服内的应用列表
async function fetchApps() {
    const apps = await lzcapi.pkgm.QueryApplication({ appidList: [] })
    console.log(apps)
}
```

### Go 语言示例
由于原生支持 gRPC，Go 是开发高性能后端的好选择。
**安装:** `go get -u gitee.com/linakesi/lzc-sdk/lang/go`
**用法:**
```go
import (
	lzcsdk "gitee.com/linakesi/lzc-sdk/lang/go"
	"gitee.com/linakesi/lzc-sdk/lang/go/common"
)

// 初始化 API
lzcapi, err := lzcsdk.NewAPIGateway(context.TODO())

// 示例：获取设备列表
request := &common.ListEndDeviceRequest{Uid: "admin"}
devices, err := lzcapi.Devices.ListEndDevices(ctx, request)
```

## 2. 注册文件类型关联 (`file_handler`)
如果你开发了一个阅读器、播放器或编辑器，你希望用户在“懒猫网盘”里双击某类文件时，直接唤起你的应用来处理。

**配置方法 (`lzc-manifest.yml`):**
在 `application` 块中声明 `file_handler`。

**示例：配置一个 Markdown 编辑器**
```yaml
application:
  file_handler:
    mime:
      - text/markdown        # 标准的 mime type
      - x-lzc-extension/md   # 或者指定具体的文件后缀 (懒猫特有语法)
      # - */*                # (高危) 匹配所有文件，适合"MD5计算器"等工具
    actions:
      # 当用户在网盘打开该文件时触发。%u 会被自动替换为实际的网盘文件路径。
      open: /edit?filepath=%u
```

**应用内的处理:**
当网盘唤起你的应用时，浏览器会跳转到 `https://你的应用域名/edit?filepath=/用户/文档/test.md`。你的前端或后端代码只需要解析 URL 中的 `filepath` 参数，然后通过挂载的 `/lzcapp/run/mnt/home` (或 API) 去读取该文件内容即可。

## 平台兼容性说明
如果需要查看具体支持的 gRPC 方法列表（Go/JS）或了解更多的官方库（如前端专用的 `lzc-file-pickers` 选择器，或者内嵌的小型数据库 `lzc-minidb`），请主动读取本技能包 `references/` 目录下的相关 Markdown 文档。
