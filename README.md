# mooc-work-answer

[![stars](https://img.shields.io/github/stars/11273/mooc-work-answer)](https://github.com/11273/mooc-work-answer)
[![forks](https://img.shields.io/github/forks/11273/mooc-work-answer)](https://github.com/11273/mooc-work-answer)
[![visitors](https://visitor-badge.glitch.me/badge?page_id=11273.mooc-work-answer)](https://github.com/11273/mooc-work-answer)
[![issues](https://img.shields.io/github/issues/11273/mooc-work-answer)](https://github.com/11273/mooc-work-answer/issues)
[![downloads](https://img.shields.io/github/downloads/11273/mooc-work-answer/total)](https://github.com/11273/mooc-work-answer/releases)

- **智慧职教 【 ~~考试+测验+作业+~~ 刷课】+ 新版 【刷课】**

- **仅适用于: <https://mooc.icve.com.cn/>**

- **详细刷课技术参考** [刷课技术篇>>>](https://www.52pojie.cn/thread-1338063-1-1.html)

- **网关认证技术参考** [网关认证技术篇>>>](https://www.52pojie.cn/thread-1713942-1-1.html)

  ***

## 🎄 通 🎄 知 🎄

> - 🧰 答题模块某些原因暂不开放
> - 🎉 之前出现的 **[网关扫码](http://u6e.cn/dnDP0)** 提供教程学习 **[点击前往>>>](https://www.52pojie.cn/thread-1713942-1-1.html)**
> - 🎉 添加协程批量刷小节
> - 📢 代码部分简化, 移除自动识别验证码, 运行成本较大
> - 📢 直接运行请前往下载已打包版本 **[点击前往>>>](https://github.com/11273/mooc-work-answer/releases)**
> - 📣 讨论请前往 Discussions **[点击前往>>>](https://github.com/11273/mooc-work-answer/discussions)**
> - 📣 提交问题请前往 Issues **[点击前往>>>](https://github.com/11273/mooc-work-answer/issues)**
> - **新版测试使用说明:**
> - 新版目前临时测试使用，暂不稳定，打开 `NewMoocMain/init_mooc.py` 中 `auth(session, "此处填写登录账号", "此处填写登录密码")` 填写账号密码即可运行(仅需运行 `init_mooc.py` 文件)

- **[新手运行此项目前往 >](REAEME_RUN.md)**

## 下载

- v1.0.0 [Download exe 绿色运行版](https://github.com/11273/mooc-work-answer/releases/tag/v1.0.0)
- v2.0.0-beta [Download exe 绿色运行版](https://github.com/11273/mooc-work-answer/releases/tag/v2.0.0-beta)
- v2.0.0 [Download exe 绿色运行版 >>>](https://github.com/11273/mooc-work-answer/releases/tag/v2.0.0)

## 更新状态

- 2022/4/2: 移除自动识别验证码（识别验证码的库太大不好装，减少运行成本）

- 2022/4/3: 代码优化，效率提高，配置项启用

- 2022/4/4: 多个空的填空题不作答

- 2022/4/12: Pillow 库安装失败时，可手动打开验证码

- 2022/5/4: 验证码登录优化，整体效率优化

- 2022/5/4: windows 运行版发布

- 2022/11/4: 速度优化

- 2022/12/26: 兼容新版刷课(Beta)

## 实现功能

|   功能   |     介绍     |  完成  |
| :------: | :----------: | :----: |
|   刷课   |   速刷模式   |   ✅   |
| 新版刷课 |     Beta     |   ✅   |
| ~~测验~~ | ~~代码移除~~ | ~~✅~~ |
| ~~考试~~ | ~~代码移除~~ | ~~✅~~ |
| ~~作业~~ | ~~代码移除~~ | ~~✅~~ |

## 运行环境

- python ≥ 3.6 < 3.9 (3.9 部分用户安装不了 Pillow 库)
- 运行所需 pip 包请自行切换到本项目根目录使用以下命令进行安装（推荐使用完整版）

  ```pip
   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
  ```

  或 (**必装**: requests、aiohttp 库，**选装**: lxml(过网关须使用)、pillow(自动打开验证码图片))

  ```pip
   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requests
   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r aiohttp
   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r pillow==8.4.0
   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r lxml
  ```

## 技术简述

- 功能部分都是调用 mooc 的 api 模拟行为，当前已连续测试课程数 38，测试成功，项目单线程运行，刷课、作答时间可控，非必要请勿修改
- 答题时间： **300-1000** 秒区间内随机
- 刷课时间：比原课件时长多 **20-100** 秒区间内随机

## 使用方法

1. 填入账号密码
2. ~~里面配置暂时无法自定义，熟悉 `python` 可自行修改，有时间再更新，目前默认 \_\_刷课+测验+考试+测验~~
3. 运行 `StartWork.py`

## BUG 提交

- 请详细提供 **错误信息** 以及错误出现的 **代码行**
- [提交 BUG 规范](https://github.com/11273/mooc-work-answer/issues/22)
- 提交请前往: [点击前往 >>>](https://github.com/11273/mooc-work-answer/issues/new)
- 邮箱: darbydavid336@gmail.com (提交至 issues 更快回复)

## 免责声明

⚠️ 本项目仅限于学习交流使用，项目中使用的代码及功能如有侵权或违规请联系作者删除

⚠️ 本项目接口数据均来自于 mooc，请勿用于其它商业目的

⚠️ 如使用本项目代码造成侵权与作者无关

[![Stargazers over time](https://starchart.cc/11273/mooc-work-answer.svg)](https://starchart.cc/11273/mooc-work-answer)

## 效果展示

![1](./images/1.jpg)

---

![2](./images/2.jpg)

---

![3](./images/3.jpg)

---

![4](./images/4.jpg)

---

![5](./images/5.jpg)

---

![6](./images/6.jpg)

---
