# lzc-build.yml 规范文档

## 一、 概述

`lzc-build.yml` 是用于定义应用构建相关配置的文件。 本文档将详细描述其结构和各字段的含义。

## 二、顶层数据结构 `BuildConfig`

### 2.1 基本信息 {#basic-config}

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `buildscript` | `string` | 可以为构建脚本的路径地址或者 sh 的命令 |
| `manifest` | `string` | 指定 lpk 包的 manifest.yml 文件路径 |
| `contentdir` | `string` | 指定打包的内容目录，将会打包到 lpk 中 |
| `pkgout` | `string` | 指定 lpk 包的输出路径 |
| `icon` | `string` | 指定 lpk 包 icon 的路径路径，如果不指定将会警告，目前仅允许 png 后缀的文件 |
| `devshell` | `DevshellConfig` | 开发依赖配置 |
| `compose_override` | `ComposeOverrideConfig` | 高级 compose override 配置，**需要更新 lzc-os 版本 >= v1.3.0** |

## 三、开发依赖 `DevshellConfig` {#devshell}

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `routes` | `[]string` | 开发路由规则配置 |
| `dependencies` | `[]string` | 开发依赖安装，自动安装 |
| `setupscript` | `string` | 开发依赖安装，手动安装 |
| `image` | `string` | 非必选，使用指定 image 镜像 |
| `pull_policy` | `string` | 非必选，参数 `build` 为使用指定 dockerfile 构建镜像，此时 image 参数可填 `${package}-devshell:${version}` |
| `build` | `string` | 非必选，构建容器时使用的 dockerfile 文件路径 |

详情见 [开发依赖安装](../devshell-install-and-use.md)

::: warning ⚠️ 注意

如果 `dependencies` 和 `build` 同时存在，将会优先使用 dependencies

:::

## 四、高级 compose override 配置 `ComposeOverrideConfig` {#compose-override}

1. compose override 是 lzc-cli@1.2.61 及以上版本支持的特性， 用于在构建时指定 compose override 的配置。
2. compose override 属于 lzcos v1.3.0+ 后，针对一些 lpk 规范目前无法覆盖到的运行权限需求的配置。

详情见 [compose override](../advanced-compose-override.md)

::: details 配置示例
```yml
# 整个文件中，可以通过 ${var} 的方式，使用 manifest 字段指定的文件定义的值

# buildscript
# - 可以为构建脚本的路径地址
# - 如果构建命令简单，也可以直接写 sh 的命令
# - ⚠️ 边界情况警告：绝对不要在指定的 buildscript 脚本中再次执行 `lzc project build` 相关的构建命令，否则会导致死循环。
buildscript: sh build.sh

# manifest: 指定 lpk 包的 manifest.yml 文件路径
manifest: ./lzc-manifest.yml

# contentdir: 指定打包的内容，将会打包到 lpk 中
contentdir: ./dist

# pkgout: lpk 包的输出路径
pkgout: ./

# icon 指定 lpk 包 icon 的路径路径，如果不指定将会警告
# icon 仅仅允许 png 后缀的文件
icon: ./lzc-icon.png

compose_override:
  services:
    # 指定服务名称
    some_container:
      # 指定需要 drop 的 cap
      cap_drop:
        - SETCAP
        - MKNOD
      # 指定需要挂载的文件
      volumes:
        - /data/playground:/lzcapp/run/playground:ro

# dvshell 指定开发依赖的情况
# 这种情况下，选用 alpine:latest 作为基础镜像，在 dependencies 中添加所需要的开发依赖即可
# 如果 dependencies 和 build 同时存在，将会优先使用 dependencies
devshell:
  routes:
    - /=http://127.0.0.1:5173
  dependencies:
    - nodejs
    - npm
    - python3
    - py3-pip
  setupscript: |
    export npm_config_registry=https://registry.npmmirror.com
    export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple   
```
:::
