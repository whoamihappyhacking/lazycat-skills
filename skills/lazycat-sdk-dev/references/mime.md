# 应用关联
懒猫微服的目标是构建家庭的数字生活中枢， 随着生态应用越来越多， 懒猫网盘的很多文件可以由生态应用直接打开。

比如， 您开发了一款音乐播放器， 您期望用户在懒猫网盘点击音乐文件时， 懒猫网盘会自动弹出应用选择对话框供用户挑选。

只需要在 `lzc-manifest.yml` 文件中加入 `file_handler` 字段即可：

```yml
application:
  file_handler:
    mime:
      - audio/mpeg
      - audio/mp3
    actions:
      open: /open?file=%u
```

- `mime`: 是应用可以支持的 MIME 列表
- `actions`: 启动应用的动作， 目前只有 `open` 一个选项

应用需要支持 `/open` 这个路由， 并解析 `file` 参数的内容， 系统会自动把 `%u` 参数替换成打开文件的实际路径。

v1.3.8+后，mime字段支持一些特殊的配置：

- `text/*`  包含了`text/plain`在内的所有text类别的mime类型
- `*/*` 所有文件类型都会被匹配上，适合“MD5计算”、“文件分享”等特殊应用场景。(写这个注意加个字符串引号，否则yaml会尝试解析`*`导致报错)
- `x-lzc-extension/md` 所有后缀为md的文件
