# 学习档案 schema 2

state/school.json 为教学事务主档，schemaVersion=2。包含 profile（路线、难度、入学时间）、current（课号、版本、phase、位置）、completed、skipped、attempts、mastery、mistakes、notes、bookmarks、weakPoints、labs、recommendation、lastLearningAt。

旧 state/progress.json、mastery.json、mistakes.json、notes.json 原样保留，读取时作为 legacy 独立返回，导师按迁移映射兼容查询。导出包含主档及旧四份记录，校验完整内容哈希；导入只接受已知字段和大小限制，通过确认后原子写入主档并保留旧备份。课程更新程序不会写 state。

每次写操作持有文件锁，先写 backups/school/ 快照，再原子替换 school.json。损坏原档不会自动清空；提供错误及恢复说明。没有跨设备自动同步；手动导出/导入完成迁移。
