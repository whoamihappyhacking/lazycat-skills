# 最小 LPK V2 静态站

先按技能内 `references/spec-sync.md` 校准，再将此目录复制到你的应用工作区。要求 lzc-cli >=2.0.0、目标 lzcos >=1.5.0。

在副本目录执行：

```bash
lzc-cli project build -o release.lpk
```

示例故意未提供图标，CLI 可能提示警告；正式发布前添加符合当前官方要求的 PNG 图标及 `icon` 构建项。这里不请求互联网/文稿等额外权限，也不配置 public_path。

仅当用户授权后，才用 `lzc-cli app install ./release.lpk` 安装。构建成功不等于真机登录、安装、升级和业务行为已通过验证。
