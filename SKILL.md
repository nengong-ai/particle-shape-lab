---
name: particle-showcase-public
description: 将简单SVG或透明/黑白PNG转换成粒子引擎可用的形状数据；用户已有兼容外部运行目录时可导出交互页面。不携带渲染器、官方品牌素材或私有品牌动画预设。
---

# Particle Showcase Public

先明确输入与输出目录。普通SVG/PNG转换直接调用本Skill的 `scripts/shape.py --input <file> --out <new-directory>`。SVG只需Python标准库，PNG需已有Pillow/NumPy；缺少时按用户授权准备隔离环境，不假设系统Python已经装好。

输出包含原图、normalized.svg、shape.json和manifest。遵守README的输入范围；PNG先查看前景/孔洞/分离部件，再决定自动或明确的alpha/dark/light阈值。不能把trace逐像素匹配说成任意微小细节都能在粒子中辨认。

只有用户提供可用且有权使用的外部运行目录时，调用 `scripts/export.py --runtime <directory> --shape <shape.json> --dest <new-directory>`。外部源码必须匹配固定契约；不自动下载，不跳过哈希，也不把完整本地版的品牌预设/补丁搬入公开仓库。[运行说明](docs/RUNTIME.md)和[许可范围](THIRD_PARTY.md)说明两者边界。

导出目录放在本公开仓库外，避免把外部引擎加入Git。进入导出目录，按授权准备锁定依赖 `npm ci`，运行 `node build.mjs --check`、`node build.mjs`，再 `python serve.py --port <free-port>`。安装使用该目录独立依赖，不复用旧node_modules链接；不要全局升级工具或抢占别人的服务。

需要交付交互作品时必须实际打开浏览器，查看原图可辨、孔洞与独立部件、至少10秒持续动态、拖动/松手/重播、H/Esc、桌面与窄屏及控制台。无法查看时明确未验收。外部运行时决定粒子渲染质量；本工具不承诺私有完整版的品牌动效、3D重建或跨设备逐像素一致。

保留原图与外部来源文件。shape/导出manifest的browserVerified:false仅是生成状态，验收另写记录。公开README、ZIP和Git暂存内容中不应出现外部引擎、官方品牌素材、个人路径、依赖目录或临时输出；上传/建远程仓库需要用户明确要求。
