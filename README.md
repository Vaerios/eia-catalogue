# 建设项目环评分类管理名录修订对照（2021 版 → 2027 版）

纯静态网站，无需构建、无需后端，也不依赖任何外部字体或 CDN（国内访问更稳）。

- 191 个行业条目、条文对照、移出项目等内容均由 Word 原文生成，已逐字校验一致
- 修订标记：旧版删除线、新版荧光笔；可在顶栏关闭
- 全文搜索（支持多关键词、项号）、按“报告书 / 报告表 / 登记表 / 敏感区”标签筛选
- 每个条目有独立链接，如 `https://你的用户名.github.io/仓库名/#n120`
- 手机、深色模式、打印均已适配

## 部署到 GitHub Pages

### 方式一：网页上传（不用命令行）
1. 登录 GitHub，右上角 **+ → New repository**，仓库名随意（如 `eia-catalogue`），选 **Public**，创建。
2. 进入仓库，点 **uploading an existing file**，把本文件夹里的**所有内容**拖进去
   （`index.html`、`assets/`、`tools/`、`.nojekyll`、`README.md`；
   注意要上传文件夹里面的内容，而不是外面再套一层文件夹）。点 **Commit changes**。
3. 进入 **Settings → Pages**，**Source** 选 **Deploy from a branch**，
   Branch 选 **main**，目录选 **/ (root)**，点 **Save**。
4. 等 1–2 分钟，页面顶部会出现网址：`https://你的用户名.github.io/仓库名/`。

### 方式二：命令行
```bash
cd 本文件夹
git init -b main
git add .
git commit -m "init: 环评名录修订对照"
git remote add origin git@github.com:你的用户名/仓库名.git
git push -u origin main
# 然后在 Settings → Pages 选择 main 分支、/ (root)
```

> 想用 `https://你的用户名.github.io/` 作为根地址，把仓库命名为 `你的用户名.github.io` 即可。

## 文件结构
```
index.html          页面（由脚本生成，勿手改）
assets/style.css    样式
assets/app.js       搜索 / 筛选 / 主题 / 目录高亮
assets/favicon.svg  图标
tools/build.py      从 Word 文档重新生成 index.html
tools/template.html 页面外壳模板
.nojekyll           告诉 GitHub Pages 不要用 Jekyll 处理
```

## 以后更新内容
Word 文档改了之后，重新生成页面即可：
```bash
pip install python-docx
python tools/build.py 你的新文档.docx      # 会覆盖 index.html
```
再把改动提交推送，GitHub Pages 会自动更新。
要求文档的结构与现有版本一致（五个章节、12 张表、行业表第一列为“新 项号  名称 / 旧 项号〔页码〕”）。

## 声明
本页是对照整理，便于查阅，不具法律效力；具体适用以生态环境部发布的官方文本为准。
