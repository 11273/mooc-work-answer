# 新手运行指南

## 直接运行打包版

从 [Releases](https://github.com/11273/mooc-work-answer/releases/latest) 下载对应系统和架构的文件，无需另行安装 Python。

- Windows x64：运行 `.exe` 文件。
- macOS：Intel 选择 `macos-x64`，Apple Silicon 选择 `macos-arm64`。
- Linux x64：选择 `linux-x64`。

macOS / Linux 在终端执行 `chmod +x 文件名`，再执行 `./文件名`。构建验证环境为 Windows Server 2022、Ubuntu 22.04 和 macOS 15；其他系统版本需要自行确认兼容性。

## 从源码运行

项目需要 Python 3.12.16 或更新版本。推荐按 [uv 官方说明](https://docs.astral.sh/uv/getting-started/installation/) 安装 uv，由它准备项目指定的 Python 和依赖。

在终端中进入项目目录，执行：

```bash
uv sync --locked
uv run StartWork.py
```

`uv` 会读取 `.python-version` 和 `uv.lock`，自动准备 Python 3.12.16 的独立环境。无需修改系统 Python，也无需编辑源码填写账号。

如果已有 Python 3.12.16 或更新版本，也可以安装依赖后运行：

```bash
python -m pip install -r requirements.txt
python StartWork.py
```

## 登录和选择功能

1. 在菜单中选择 MOOC / AI 优课或资源库。
2. 按提示在浏览器中完成登录，遇到验证码时手动完成。
3. 学习管理默认只处理进行中的课程。
4. MOOC 题目导出可选择进行中、未开始、已结束或全部课程，支持 Markdown 和 Word。

导出默认只读取已交卷内容，“我的答案”默认不写入文档。包含未交卷试卷需要显式选择，可能创建作答记录或开始计时。导出文件位于项目的 `tiku/` 目录。

## 自检和只读检查

检查本地依赖和导出能力，不登录账号、不访问网络：

```bash
uv run StartWork.py --self-test
```

登录后检查课程与资源兼容性，不保存学习进度：

```bash
uv run StartWork.py --check
```

当前菜单提供学习管理和题目导出。旧版讨论、AI 答题和自动交卷尚未接入新版入口。
