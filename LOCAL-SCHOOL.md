# AI Academy Local School

把已有 Codex 或 Claude Code 变成本地学习导师。没有额外的 Academy API 订阅；模型由宿主提供，遵循宿主的服务和隐私设置。学习档案保存在本机，不由 Academy 上传。

## 安装

需要 Python 3.11+ 和已登录、可用的 Codex 或 Claude Code。Windows 可用 `py -3` 替代 `python`，macOS/Linux 可用 `python3`。

从 [官网](https://caitomato.github.io/ai-academy/) 下载 Bootstrap ZIP，解压，在解压目录执行：

```sh
python install.py --host codex
# 或
python install.py --host claude
python install.py --host codex --verify
```

无参数运行会显示中文宿主选择。默认 Codex 入口为 `~/.agents/skills/ai-academy/SKILL.md`，Claude 为 `~/.claude/skills/ai-academy/SKILL.md`。可用 `--skill-root` 指定现有宿主的自定义 skills 目录。安装器不改宿主配置；已有且无法验证归属的入口会保留并报错。重启宿主或开启新会话，使新 Skill 被发现。

输入“带我学习 AI Academy”。新生选择四条路线之一和难度，默认小白模式。也可以直接选课。Claude 支持 `/ai-academy`，Codex 可显式选择 `$ai-academy`。每课先讲解，再互动，再实操和复习。

旧 1.x Bootstrap 首次迁移到 2.x 需要下载新安装器一次：备份并手动移走原 `.codex/skills/ai-academy` 或 `.claude/skills/ai-academy` 入口后安装。保留 `.ai-academy/state` 和 courses，不删除学习记录。1.x 安装器的严格五文件包校验会拒绝 2.x 六文件核心，不能用旧 `--upgrade` 跨过这次迁移。2.x 以后课程更新无需重装。

## 本地目录

- `~/.ai-academy/bootstrap/versions/`：独立版本核心；当前 Skill 指向明确核心版本。
- `~/.ai-academy/courses/`：校验后的中央课程；新会话启用更新。
- `~/.ai-academy/state/school.json`：路线、课程位置、成绩、掌握度、错题、笔记、收藏和实操证据。
- `~/.ai-academy/backups/`：档案写入快照与导入前备份。
- `~/AI-Academy-Labs/chapterNN/课号/`：学生自己的实验。已有文件不会被脚本覆盖。

Windows 的 `~` 是 `%USERPROFILE%`。原四份 progress/mastery/mistakes/notes JSON 保留，启动返回 legacy 视图，导师按 migrations.json 查询。

## 更新、备份和卸载

说“检查 AI Academy 课程更新”可强制检查；自动检查每会话一次并有六小时缓存。离线继续使用缓存，首次加载需要网络。SHA-256 校验失败保持旧版；正在上课的会话固定版本。重大教学规则变更先提示确认。

让导师“导出学习档案到某个新文件”，或“从备份恢复”。导入需要确认，并生成恢复前备份。备份含个人学习记录，不要提交公共仓库。多设备手动迁移，不自动同步。

核心升级在当前解压目录运行 `python install.py --upgrade --host codex`。安装校验用 `--verify`。卸载使用 `python install.py --uninstall --host codex --confirm`，仅移除验证归属的 Skill 入口，保留课程、记录和实验；Claude 参数改成 claude。已修改的入口需要自行检查，安装器不会删除。

若无法识别 Skill，核对入口路径、YAML 的 name/description、宿主版本和是否已开启新会话。若提示没有教材，联网运行更新；若提示锁冲突，先确认没有另一个写入进程。不要直接清空 state。

## 教材与发布

唯一编辑源继续使用既有 `content/`，避免搬迁覆盖并行课程编辑。`scripts/skill_curriculum.py` 从九章 JSON 生成全部 90 节独立讲义、单课数据、题库、路线和索引，放在课程包的 `teaching/`。网页从同一包的 chapters 生成，不另维护教材。课程 ID 和 630 个题号不变。

`teaching/coverage.json` 明确列出缺少专用实操验证的课程。完整讲义与题目不等于所有项目已在所有环境验证。06-01 是包含真实 Python 文件和运行输出的验收样板；其余实验按现有讲义在宿主权限范围内操作，外部工具仍需环境检查。

教学规则版本见 pedagogy.md，Bootstrap/安装器版本见 install.py，课程语义版本见 content/release.json。课程以 `courses-v版本` Tag 发布，核心以 `bootstrap-v版本` Tag 独立发布。正式包地址和哈希由 Actions 生成。UI 提交不会自动升级课程版本。

## 验证

```sh
python -m unittest discover -s tests/updates -v
python scripts/build_content.py
npm test
npm run build
npm run test:e2e
```

单元与集成测试覆盖两种宿主安装布局、90 节内容一致性、首次/续学、实际 Python 输出、错题笔记保留、备份恢复、拒绝篡改、卸载保留档案，以及 A/B/C 更新、离线、回滚、会话固定和重复下载。跨平台 Actions 在 Windows、macOS、Linux 运行。宿主识别及对话测试需要各自有效账户，不能用脚本测试冒充真实模型教学测试。

## 规范依据

- [Codex Skills 官方文档](https://developers.openai.com/codex/skills/)；本次网页访问返回 403，另核对 [官方技能发现源码](https://github.com/openai/codex/blob/main/codex-rs/ext/skills/src/host_roots.rs) 与 loader 的 SKILL.md 规范。
- [Claude Code Skills 官方文档](https://code.claude.com/docs/en/skills)：个人/项目技能位置、YAML、自动激活、支持文件渐进加载。
- [参考产品](https://github.com/HA7CH/ha7ch-school)：只参考入口即教学、按课加载、主对话带学和学习档案的产品模式，没有移植其课程或实现。

原始视频、完整转录、私人资料、第三方肖像不进入安装包或课程包。课堂代码的真实执行由宿主负责；本产品不提供独立代码沙箱。
