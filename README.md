# AI Academy · AI 零基础学院

一个无后端、无需登录的中文互动学习网站。包含 9 章、90 节原创改写课程与 630 道练习及测试题，支持六类题型、章节随机考试、错题复练、收藏、笔记和本地进度。前五章的 47 节课程提供可复制任务卡；02-04 提供独立的项目交互实验与八步启动教程。

中央课程库位于 `content/`，网页与 Codex / Claude Code 本地导师共用同一教材。维护者编辑一次，通过正式课程 Tag 发布版本；学生的新学习会话自动检查更新，离线使用缓存，学习记录独立保存。课程版本、Bootstrap 安装、发布及回滚说明见 [UPDATES.md](UPDATES.md)。

课程编辑后运行 `npm run content:build`，再运行测试和构建。生产网页使用最新正式 Release 的课程包，UI 提交不会升级课程版本。旧课程编辑脚本暂为并行迁移保留，不参与正式发布链；新教材仅编辑 `content/`。

## 本地运行

使用 Node.js 24 或兼容的受支持版本。

```sh
npm ci
npm run dev
```

```sh
npm test
npm run build
npm run preview
```

`npm run test:e2e` 验证真实浏览器中的学习流程，Windows 默认使用已安装的 Edge。CI 使用 Chromium，并在工作流中安装浏览器。测试覆盖子目录刷新、手机导航、九章访问、答题、错题处理、课后与章节评分、进度恢复和损坏存储保护。

## 发布到 GitHub Pages

本目录作为独立仓库根目录。默认分支为 `main`，在仓库 Settings → Pages 中选择 GitHub Actions。之后 `git push` 自动运行测试、构建并部署。工作流位于 `.github/workflows/deploy.yml`。

Vite 使用 `base: './'`，页面导航使用 Hash 路由，例如 `/ai-academy/#lesson/01-02`。刷新仍请求站点根 HTML，不需要服务器重写规则；资源地址适配仓库子目录。不要直接打开源代码 HTML，应通过开发服务或构建后静态托管访问。

## 数据与课程

- `src/data/curriculum/chapter01.json` 至 `chapter09.json`：各章独立课程，包含目标、讲解、案例、实践、术语、误区、题目和本地 PDF 页码。
- `src/types.ts`：课程、题目和学习记录结构。
- `src/components/Quiz.tsx`：六类题目与统一测试组件。
- `src/progress.ts`：评分、抽题、备份验证和连续学习统计。
- `src/App.tsx`：仪表盘、课程、考试、错题与学习档案。
- `content/chapters/`：中央课程发布源；`src/data/curriculum/` 是其网页投影。`scripts/course-seeds.txt` 及配套编辑脚本由 `scripts/build-curriculum.py` 导出到这两处；直接编辑中央 JSON 后不要再用旧编辑源覆盖。发布构建使用 `scripts/build_content.py`。
- `scripts/video_enrichment.py`：视频主题的原创实操与情境题编辑源，由生成器合并到课程。运行 `python scripts/build-curriculum.py` 更新 JSON；保留原有课号，新增课程追加在对应章末。
- `scripts/operation_guides.py`：具体操作、命令与材料链接；Claude Code 安装内容按产品要求排除。
- `src/components/PracticeLab.tsx`：可复制任务卡、分步操作、验收与可展开故障说明。
- `src/components/NodeProject.tsx`：独立项目地图、配置探索、命令分类和六种启动情境；仅浏览器模拟。
- `scripts/node_course.py`：02-04 原创课程编辑源，保留课号及七个题号。
- `scripts/course_quality.py` 与 `scripts/concept-checks.txt`：九章教学整理与逐课概念辨析题。
- `scripts/audit-curriculum.py`：扫描课程及构建产物，内部报告写入已忽略的 materials/reports/。
- `COURSE-DESIGN.md`：统一教学契约、按知识类型设计实验的方法及发布验收标准。
- `public/practice-kit/`：虚构笔记、CSV、公告页、知识库、技能样例与分镜模板，可直接下载使用。
- `CONTENT.md`：目录合并、内容来源和版本说明。

每课 3 道即时互动题、4 道统一提交的课后题；每章抽取 12 题。完成课程与测试掌握分开记录，最近一次课后成绩达到 80 分显示“已掌握”。章节全部标记完成后进入章节考试，也可随时直接挑战。

Python 示例为代码阅读与本机实践，不在浏览器中执行。网站不调用在线大模型，不需要 API Key；课程中涉及外部工具的实践可先以纸面设计完成。

## 学习记录

LocalStorage 键为 `ai-academy.progress.v1`，保存进度、收藏、作答、考试、学习日期、实践状态和笔记。刷新保留，但清除浏览器数据会删除记录，也不会自动跨设备同步。在“学习档案”导出 JSON 备份，再在另一浏览器导入。导入前检查格式并确认覆盖。

存储损坏时不自动覆盖原始数据；页面提供原始导出与重置。存储不可用时显示提示，并允许导出当前内存记录。未提交的考试答案不跨刷新保存。

## 本地资料与发布边界

`local-source/` 包含仅供本地核对的原 PDF 与提取文本，已加入 `.gitignore`，不进入构建产物。公开站点只包含主题结构、原创讲解、案例及练习，不分发 PDF、会员信息或原文长段落。讲解标明原资料主题与补充内容；安装、版本和价格不作为当前事实保证。

`materials/` 同样不进入版本控制，可存放 `videos/`、`pdf/`、`transcripts/`、`frames/` 与 `reports/`。在线检查不会伪造这些目录中的本地音频、完整转录或逐帧成果。在线文稿阅读与音频转录分别记录，课程生成与来源覆盖质量检查分别记录；未满足条件的状态保持待处理。

02-04 新实验以 `02-04:project-lab-v2` 记录在原 LocalStorage tasks 中，旧模拟记录继续保留但不算新版实验完成。原有成绩、收藏、笔记与完成状态不清空。
