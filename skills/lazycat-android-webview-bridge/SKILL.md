---
name: lazycat-android-webview-bridge
description: 懒猫 Android WebView 宿主桥接 API 使用指南。当用户提到底部提示、底部 Snackbar、下载提示、下载完成提示、关闭或恢复宿主提示、lzc_toast、setSnackBarEnabled() 时触发；仅适用于 Android 壳。
---

# 懒猫 Android WebView Bridge

当网页应用需要调用懒猫 Android 客户端注入的 JavaScript Bridge 时使用本技能。

以下需求通常对应本技能：

- 控制 Android 壳底部 Snackbar 或底部提示是否显示
- 关闭、恢复下载完成提示等宿主级提示
- 处理 `lzc_toast`、`setSnackBarEnabled`、`showSnake` 调用

## `lzc_toast.setSnackBarEnabled`

该接口由 Android WebView 宿主以 `lzc_toast` 名称注入，调用参数是布尔值：

```js
lzc_toast.setSnackBarEnabled(false) // 禁止宿主 Snackbar
lzc_toast.setSnackBarEnabled(true)  // 恢复宿主 Snackbar
```

它只控制宿主壳的 Snackbar 显示开关，不会改变网页自己的 Toast、Snackbar 或其他 UI。关闭后，宿主对 `lzc_toast.showSnake(...)` 和下载完成提示的显示请求会直接忽略；默认状态为开启。

## 兼容性与调用方式

- 仅适用于懒猫 Android WebView 壳；普通浏览器、桌面端、iOS 和未注入该桥的 WebView 不提供此接口。
- 调用前必须做能力检测，避免网页在非 Android 环境报错：

```js
if (globalThis.lzc_toast && typeof globalThis.lzc_toast.setSnackBarEnabled === 'function') {
  globalThis.lzc_toast.setSnackBarEnabled(false)
}
```

- 这是 Android `@JavascriptInterface` 暴露的方法，调用应在页面加载完成后进行；不要把它当作跨平台标准 API 或持久化设置。
- 需要恢复提示时显式传入 `true`。页面刷新或宿主生命周期重建后的状态不应假定由网页持久化。

实现依据：Android 壳将 `ToastInterface` 注入为 `lzc_toast`，`setSnackBarEnabled(Boolean)` 修改宿主内存中的 Snackbar 开关；该状态不是应用配置文件或服务端配置。
