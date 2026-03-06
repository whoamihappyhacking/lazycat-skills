# Lzc-SDK 是什么?

Lzc-SDK 是懒猫微服平台提供的 SDK， 使开发者能够与系统和应用状态进行交互， 创建更多好玩，  有趣的应用程序，  并将其发布到懒猫微服商店。

使用 Lzc-SDK， 开发者可以专注于构建创新应用， 无需担心服务器搭建、 后端逻辑、 API 设计或网络安全。 SDK 简化了开发过程， 让您只需几个函数调用就能创建和部署应用。

SDK 支持多种编程语言的支持， 包含系统层， 应用层， 客户端层所需 API， 允许开发者全方位扩展懒猫微服。

::: info
目前支持 Go、 Javascript/Typescript， 后续会提供更多语言版本， 例如 Rust、 Dart、 Cpp、 Java、 Python、 Ruby、 C#、  PHP、 Objective-C、 Kotlin 敬请期待...
:::

## 扩展

对应一些比较常见的场景， 懒猫微服平台中也提供了以下扩展:
  - [lzc-minidb](https://www.npmjs.com/package/@lazycatcloud/minidb)， 一个类似 MongoDB 类型的小数据库， 方便开发者可以直接开发 Serverless 的应用。
  - [lzc-file-pickers](https://www.npmjs.com/package/@lazycatcloud/lzc-file-pickers)， 一个懒猫微服中的文件选择器，  让您的应用支持直接打开微服中的文件。

::: info
目前提供的扩展都是 Javascript/Typescript 的， 方便 Web 端使用。 如果不能满足您的需求， 欢迎反馈， 我们会尽快加上。 :)
:::

## Javascript 示例
Javascript(Typescript)的 SDK  使用 npm 分发， 需要在您的项目中安装对应的  npm 包。

```bash
npm install @lazycatcloud/sdk
# 或者
pnpm install @lazycatcloud/sdk
```

JS/TS 版本是使用 [grpc-web](https://github.com/improbable-eng/grpc-web) 提供服务， 下面提供了一个获取所有应用列表的示例:

```js
import { lzcAPIGateway } from "@lazycatcloud/sdk"

// 初始化 lzcapi
const lzcapi = new lzcAPIGateway(window.location.origin, false)

// 使用 lzcapi 调用 package manager 服务以获取所有应用列表
const apps = await lzcapi.pkgm.QueryApplication({ appidList: [] })

console.debug("applicatons: ", apps)
```

::: info
```js
{
  "infoList": [
    {
      "appid": "cloud.lazycat.developer.tools",
      "status": 4,
      "version": "0.1.3",
      "title": "懒猫云开发者工具",
      "description": "",
      "icon": "//lcc.heiyu.space/sys/icons/cloud.lazycat.developer.tools.png",
      "domain": "dev.lcc.heiyu.space",
      "builtin": false,
      "unsupportedPlatforms": []
    }
  ]
}
```
:::

简单几步， 就可以很方便的和微服进行交互， 详细的 API 文档请查看 [LzcSDK API(JavaScript)](./api/javascript.md)。

## Go 示例

Go 原生支持 [grpc-go](https://github.com/grpc/grpc-go)， LzcSDK 也提供了对应的[支持](https://pkg.go.dev/gitee.com/linakesi/lzc-sdk/lang/go)。

下面使用几行代码快速体验和微服生态交互的能力。

首先需要先在项目里安装 Lzc SDK 的依赖:

```shell
go get -u gitee.com/linakesi/lzc-sdk/lang/go
```

随后只需要简单几步， 即可调用 SDK 提供的 API 了。

```go
package main

import (
	lzcsdk "gitee.com/linakesi/lzc-sdk/lang/go"
	"gitee.com/linakesi/lzc-sdk/lang/go/common"
)

func main(){
	ctx := context.TODO()
	// 初始化 LzcAPI
	lzcapi, err := lzcsdk.NewAPIGateway(ctx)
	if err != nil {
		fmt.Println("Initial Lzc Api failed:", err)
		return
	}
	// 构建请求内容， 表示要获取 lazycat 这个用户的所有设备
	request := &common.ListEndDeviceRequest{
		Uid: "lazycat"
	}
	// 获取 lazycat 用户所有设备
	devices, err := lzcAPI.Devices.ListEndDevices(ctx, request)
	if devices == nil {
		fmt.Println("lazycat 没有任何设备")
		return
	}
	var onLineDevices []*common.EndDevice
	for _, device := range devices.Devices {
		d := device
		// 判断设备是否在线
		if d.IsOnline {
			onLineDevices = append(onLineDevices, d)
			fmt.Printf("%s 设备在线\n", d.Name)
			}
	}
    fmt.Printf("在线的设备共有%d 个\n", len(onLineDevices))
}
```

:::info
```txt:no-line-numbers
evan 设备在线
wwh 设备在线
在线的设备共有 2 个
```
:::

调用 SDK 的 API 十分简单自然， 更详细的 API 请参阅 [LzcSDk API(Golang)](./api/golang.md)。
