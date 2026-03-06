deploy-params
=============

`lzc-deploy-params.yml` 是开发者定义安装时参数的配置文件。 本文档将详细描述其结构和各字段的含义。

# DeployParams

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `params` | `[]DeployParam` | 开发者定义的部署参数列表|
| `locales` | `map` | 国际化相关 |

-------------------------------

# DeployParam
| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `id` | `string` | 应用内的唯一ID，供国际化和manifest.yml中引用|
| `type` | `string` | 字段类型，目前支持`bool`、`lzc_uid`、`string`、`secret` |
| `name` | `string`| 字段渲染时的名称，支持国际化|
| `description` | `string`| 字段渲染时详细介绍，支持国际化|
| `optional` | `bool` | 此字段是否可选。若可选则不会强制要求用户填写，若所有字段均为可选则会直接跳过部署界面|
| `default_value`| `string`| 开发者提供的默认值，支持 `$random(len=5)` 生成随机串（lzcos 1.5.0+） |
| `hidden` | `bool` | 字段依旧生效，但不在界面中渲染 |
