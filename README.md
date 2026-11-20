# 建设项目环评分类管理名录修订对照

可直接发布的静态站点。覆盖 2021 年版和 2027 年版的对照，支持关键词、新旧项号、章目和修订栏目筛选，并附 Word 对照表及 2021 年版官方 PDF。新版正式全文由网页链接至生态环境部。

## 本地预览

解压后双击 `index.html`。搜索、筛选和展开表格均可在本地预览。无需安装依赖或运行构建命令。

## 发布到 GitHub Pages

1. 将压缩包**解压后的内容**上传到 GitHub 仓库选定分支的根目录。确认 `index.html`、`styles.css`、`app.js`、`.nojekyll` 和 `files/` 位于同一级。若通过 GitHub 网页上传时漏掉隐藏文件，可在同一目录新建一个空白的 `.nojekyll`。
2. 打开仓库的 **Settings → Pages**，在 **Source** 选择 **Deploy from a branch**。
3. 选择上传文件的分支（通常为 `main`）及 **/ (root)**，点击 **Save**。若把文件上传到 `docs/`，则在此选择 **/docs**。
4. 构建成功后，在同一 Pages 页面点击 **Visit site**。站点使用相对路径，也可发布在 `https://用户名.github.io/仓库名/`。

[GitHub Pages 官方配置说明](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)

## 文件

| 文件 | 用途 |
| --- | --- |
| `index.html` | 页面与完整对照内容，可直接编辑文本 |
| `styles.css` | 桌面、手机和打印样式 |
| `app.js` | 关键词检索、筛选、加载更多、条目定位 |
| `files/eia-catalogue-comparison.docx` | 完整 Word 对照 |
| `files/catalogue-2021.pdf` | 2021 年版官方 PDF |
| `icon.svg` | 站点图标 |
| `.nojekyll` | 在分支发布时关闭 Jekyll 转换 |

支持直接定位，例如 `#item-120` 打开新第 120 项。关键词可输入“新120”“旧95”“污水处理”等。部署后可分享筛选结果的链接。
