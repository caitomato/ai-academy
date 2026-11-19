# 中央课程库与发布

`content/` 是唯一正式教材源。`content/chapters/` 保存九章讲义、课堂题、课后题、案例和操作；`teaching/` 保存教学方法与提示词；`labs/` 保存实验文件；`migrations.json` 保存历史 ID 映射；`release.json` 和 `CHANGELOG.md` 描述正式更新。网页与本地导师从相同 JSON 学习。

## 编辑与验证

编辑 `content/`，运行 `python scripts/build_content.py` 生成网页课程、实验下载与轻量 Bootstrap ZIP，再运行 `npm test`、`npm run build`、`npm run test:e2e`。运行 `python -m unittest discover -s tests/updates -v` 验证更新契约。

`src/data/curriculum/`、`public/practice-kit/` 是生成目录，不独立编辑。旧 `scripts/build-curriculum.py` 和旧编辑脚本暂时保留，供同时进行的课程迁移收尾；不在任何正式构建、发布链中执行。迁移后的正式发布只读取 content/，不要维护两套教材。旧编辑改动须审阅后单向导入 content/；正式编辑完成迁移后可移除旧工具。

## 正式课程发布

1. 编辑中央内容，更新 `content/release.json` 的语义化版本、发布日期、变更分类及日志，同时更新 `content/CHANGELOG.md`。
2. 完成测试并提交 main。
3. 创建并推送 `courses-v1.1.0` 形式的标签。版本必须与 release.json 一致且高于已发布稳定版。
4. Actions 验证数据、ID、答案、解析、实验引用和旧 ID 迁移，生成确定性 ZIP 与 SHA-256，发布 GitHub Release，保留 `updates/versions/<version>/manifest.json` 并推进 `updates/stable.json`，随后显式触发 Pages 发布。

只改 UI 的提交不会创建课程版本。生产 Pages 构建从最新已发布课程包生成网页讲义，避免把未正式发布的教材提前带到网页。修改教材后需要正式标签才对两端生效。本地预览可以构建 content/ 草稿。

stable 入口：`https://github.com/caitomato/ai-academy/releases/latest/download/stable.json`。只有课程稳定版标记为 latest；Bootstrap 发布不抢占 latest。`--channel beta` 可生成测试清单，预留发布渠道；默认客户端只读取 stable，beta 不覆盖 stable。发布历史永久保留，不覆盖既有版本资产。

客户端使用 HTTPS，按 GitHub Release Asset 重定向下载二进制，限制官方域名、包大小和解压大小，逐项验证路径、文件清单、文件哈希和完整课程结构，拒绝 ZIP 路径穿越、符号链接及重复文件。SHA-256 提供完整性，来源信任依赖官方 GitHub HTTPS 与仓库权限；没有额外签名体系。

## 本地布局

- `~/.ai-academy/bootstrap/launch.py`：稳定启动器。
- `bootstrap/versions/<version>/`：可并存的核心实现；`current.json` 原子指定当前核心。
- `courses/<version>/`：只含公开课程；`courses/current/version.json` 是当前版本指针，避免 Windows 符号链接权限问题。
- `courses/previous.json`：可回滚的旧课程版本。
- `state/{progress,mastery,mistakes,notes}.json`：学生记录，仅导师记录程序写入。
- `cache/latest-manifest.json`：六小时检查缓存；sessions/ 固定会话版本，不含原始会话 ID。
- `backups/state/`：学生记录写入前备份。

课程更新程序不会写 state/ 或 backups/。新版本先完整暂存校验，再重命名为版本目录并原子切换指针；失败不切换，旧目录保留。回滚后自动检查不会立刻重新启用被回滚的同一版本，手动强制检查或更高版本可继续更新。

首版可靠性优先：哈希对比展示变化文件和受影响课程，但实际下载完整 ZIP，不是假称按文件下载。同一版本已完整缓存时不下载包。旧目录不自动删除，因此在有磁盘压力时由用户选择清理非当前、非上一版本且没有活跃会话引用的版本。

## 学生入口与隐私

解压官网 Bootstrap ZIP 后，用 Python 3.11+ 执行 `python install.py --host codex` 或 `--host claude`。仅安装宿主 Skill 和轻量核心。首次学习联网下载课程；后续无需重装。当前会话固定一个 ID，第一次启动检查，主动检查用 check 命令。重大教学规则版本 requiresConfirmation=true 时，说明更新并在得到同意后的新会话使用 --accept-major。

启动会话读取版本目录的 teaching/guide.md 与 prompts.json，然后读取章节 JSON。课堂题逐题互动，课后题统一评分，章节考试从该章 test 中抽题。state.py 提供本地原子保存和旧记录备份。ID 重命名必须提供 lessonIds/questionIds 映射，导师查询旧记录的映射视图；网页导入或启动时添加新 ID 别名并保留旧键。历史映射应累计保留以支持跨版本升级。

默认无遥测、无用户账号、无上传学生记录。网络只获取公开清单和包，不发送学习进度、错题、个人资料或对话。

## Bootstrap 核心与安装器

Bootstrap/安装器各有版本；课程包的 minBootstrapVersion 控制兼容要求。普通教学方法随课程包更新，无需改 Bootstrap。

核心修改后创建 `bootstrap-v<version>` 标签，独立工作流生成核心 ZIP 和 `updates/bootstrap.json`。核心升级运行已安装 `install.py --upgrade --host codex`。新核心通过包及文件哈希检查后并存安装，原子切换核心指针；旧核心保留。运行中的进程与已加载教学规则不被替换。稳定 launch.py 与安装器不被课程更新覆盖；未来需调整安装器协议时单独发布安装器版本。

异常进程可能留下 `.update.lock`。首先确认没有更新进程运行，再手动移除该锁；不要在另一个更新执行期间删除。缓存损坏或包校验失败不会把不完整课程切为当前版本。网络失败没有有效本地课程时返回明确错误。

## 验证范围

tests/updates/test_updates.py 使用真实 ZIP/哈希、真实隔离文件目录和可控分发器模拟三个学生、1.0.0 → 1.1.0、断网、恢复、记录保留、坏包、回滚、重复下载、会话固定、重大逻辑确认、非法路径、ID 迁移与安装器。真实 GitHub 发布与公网下载另行验收，不能把模拟测试称为公网测试。
