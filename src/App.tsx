import { useEffect, useState } from "react";
import type { Question, State } from "./types";
import { chapters, lessons, lessonById, questionById } from "./data";
import {
  emptyState,
  grade,
  parseState,
  sample,
  STORAGE_KEY,
  streak,
  today,
} from "./progress";
import { Quiz, Test } from "./components/Quiz";
import { PracticeLab } from "./components/PracticeLab";
import { CourseUpdates } from "./components/CourseUpdates";
import { VideoLesson } from "./components/VideoLesson";
import {
  ArrowRight,
  ArrowLeft,
  BookOpen,
  LayoutDashboard,
  Bookmark,
  CircleCheck,
  Search,
  Flame,
  GraduationCap,
  Target,
  ChartNoAxesCombined,
  Menu,
  X,
  ChevronRight,
  Clock3,
  Download,
  Upload,
  Check,
  NotebookPen,
  Layers,
  BrainCircuit,
  Code2,
  Video,
  AudioLines,
  Terminal,
  Bot,
} from "lucide-react";
const icons = [
  BrainCircuit,
  Terminal,
  Bot,
  Code2,
  Video,
  Code2,
  Layers,
  BrainCircuit,
  AudioLines,
];
const navItems = [
  ["home", "学习概览", LayoutDashboard],
  ["courses", "全部课程", BookOpen],
  ["wrong", "错题本", NotebookPen],
  ["bookmarks", "我的收藏", Bookmark],
  ["profile", "学习档案", ChartNoAxesCombined],
] as const;
function go(path: string) {
  window.location.hash = path;
}
function Progress({ value }: { value: number }) {
  return (
    <div
      className="progress"
      role="progressbar"
      aria-label="学习进度"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <span style={{ width: `${value}%` }} />
    </div>
  );
}
function initial() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return { state: raw ? parseState(raw) : emptyState(), error: "" };
  } catch {
    return {
      state: emptyState(),
      error:
        "无法读取学习记录，可能是存储被禁用或记录损坏。请先导出原始记录，再重置本地存储。当前操作仅保存在本次页面中。",
    };
  }
}
export default function App() {
  const [boot] = useState(initial);
  const [state, setState] = useState<State>(boot.state);
  const [storageError, setStorageError] = useState(boot.error);
  const [route, setRoute] = useState(location.hash.slice(1) || "home");
  const [mobile, setMobile] = useState(false);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState(0);
  const [showResolved, setShowResolved] = useState(false);
  const [notice, setNotice] = useState("");
  const [examItems, setExamItems] = useState<Question[]>([]);
  const [examRound, setExamRound] = useState(0);
  const [page, id] = route.split("/");
  const lesson = lessonById[id];
  const chapter = chapters.find(
    (c) => c.id === (lesson?.chapterId || Number(id)),
  );
  useEffect(() => {
    const handler = () => {
      setRoute(location.hash.slice(1) || "home");
      setMobile(false);
      window.scrollTo({ top: 0 });
    };
    addEventListener("hashchange", handler);
    return () => removeEventListener("hashchange", handler);
  }, []);
  useEffect(() => {
    if (boot.error) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      setStorageError("");
    } catch {
      setStorageError(
        "本地存储不可用或空间不足。当前记录仅在本次页面中，请导出备份。",
      );
    }
  }, [state, boot.error]);
  useEffect(() => {
    if (page === "lesson" && lesson)
      setState((s) => ({
        ...s,
        recent: [lesson.id, ...s.recent.filter((x) => x !== lesson.id)].slice(
          0,
          8,
        ),
        days: [...new Set([...s.days, today()])],
      }));
  }, [page, lesson]);
  useEffect(() => {
    if (page === "exam" && chapter) {
      const perLesson = chapter.lessons.map((l) => sample(l.test, 1)[0]);
      const pool = chapter.lessons
        .flatMap((l) => l.test)
        .filter((q) => !perLesson.some((p) => p.id === q.id));
      setExamItems(
        sample(
          [
            ...perLesson.slice(0, 12),
            ...sample(pool, Math.max(0, 12 - perLesson.length)),
          ],
          12,
        ),
      );
    }
  }, [page, chapter, examRound]);
  function toggle(key: "completed" | "bookmarks" | "tasks", lid: string) {
    setState((s) => ({
      ...s,
      taskDays:
        key === "tasks" && !s.tasks.includes(lid)
          ? [...new Set([...s.taskDays, today()])]
          : s.taskDays,
      [key]: s[key].includes(lid)
        ? s[key].filter((x) => x !== lid)
        : [...s[key], lid],
    }));
  }
  function record(
    answers: Record<string, string[]>,
    score?: number,
    exam = false,
  ) {
    setState((s) => {
      const entries = Object.entries(answers).filter(
        ([qid]) => questionById[qid],
      );
      const attempts = entries.map(([qid, a]) => ({
        id: crypto.randomUUID(),
        questionId: qid,
        answer: a,
        correct: grade(questionById[qid], a),
        date: new Date().toISOString(),
      }));
      const wrong = attempts.filter((a) => !a.correct).map((a) => a.questionId);
      return {
        ...s,
        attempts: [...s.attempts, ...attempts],
        resolved: s.resolved.filter((q) => !wrong.includes(q)),
        days: [...new Set([...s.days, today()])],
        scores:
          score !== undefined && !exam
            ? { ...s.scores, [id]: score }
            : s.scores,
        exams:
          score !== undefined && exam
            ? [
                ...s.exams,
                {
                  chapterId: Number(id),
                  score,
                  date: new Date().toISOString(),
                },
              ]
            : s.exams,
      };
    });
  }
  function complete() {
    if (!lesson || !chapter) return;
    const completed = [...new Set([...state.completed, lesson.id])];
    setState((s) => ({ ...s, completed }));
    if (chapter.lessons.every((l) => completed.includes(l.id)))
      go("exam/" + chapter.id);
    else setNotice("已标记为完成。课后测试达到 80 分会另行标记为“已掌握”。");
  }
  const totalDone = lessons.filter((l) =>
    state.completed.includes(l.id),
  ).length;
  const percent = Math.round((totalDone / lessons.length) * 100);
  const accuracy = state.attempts.length
    ? Math.round(
        (state.attempts.filter((a) => a.correct).length /
          state.attempts.length) *
          100,
      )
    : 0;
  const current =
    lessonById[state.recent[0]] ||
    lessons.find((l) => !state.completed.includes(l.id)) ||
    lessons[0];
  const wrongIds = [
    ...new Set(
      state.attempts.filter((a) => !a.correct).map((a) => a.questionId),
    ),
  ].filter((q) => questionById[q]);
  const activeWrong = wrongIds.filter((q) => !state.resolved.includes(q));
  const filtered = lessons.filter(
    (l) =>
      (!filter || l.chapterId === filter) &&
      (!search.trim() ||
        `${l.title} ${l.terms.join(" ")}`
          .toLowerCase()
          .includes(search.toLowerCase().trim())) &&
      (page !== "bookmarks" || state.bookmarks.includes(l.id)),
  );
  function exportData(raw = false) {
    try {
      const data = raw
        ? localStorage.getItem(STORAGE_KEY) || "{}"
        : JSON.stringify(state, null, 2);
      const url = URL.createObjectURL(
        new Blob([data], { type: "application/json" }),
      );
      const a = document.createElement("a");
      a.href = url;
      a.download = `ai-academy-${raw ? "raw-" : ""}${today()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setNotice("当前浏览器不允许读取存储，无法导出原始记录。");
    }
  }
  const chapterPercent = (cid: number) => {
    const ls = chapters[cid - 1].lessons;
    return Math.round(
      (ls.filter((l) => state.completed.includes(l.id)).length / ls.length) *
        100,
    );
  };
  function LessonList() {
    return (
      <div className="lesson-list">
        {filtered.map((l) => (
          <a className="lesson-row" key={l.id} href={`#lesson/${l.id}`}>
            <span
              className={`lesson-index ${state.completed.includes(l.id) ? "done" : ""}`}
            >
              {state.completed.includes(l.id) ? (
                <Check size={17} />
              ) : (
                l.id.split("-")[1]
              )}
            </span>
            <span>
              <small>
                第 {l.chapterId} 章 · {chapters[l.chapterId - 1].title}
              </small>
              <strong>{l.title}</strong>
            </span>
            <span className="row-meta">
              {(state.scores[l.id] ?? 0) >= 80 ? (
                <span className="tag green">已掌握</span>
              ) : state.completed.includes(l.id) ? (
                <span className="tag">已完成</span>
              ) : (
                <span>{l.minutes} 分钟</span>
              )}
              <ChevronRight size={17} />
            </span>
          </a>
        ))}
        {!filtered.length && (
          <div className="empty">
            <Bookmark />
            <h3>这里还没有课程</h3>
            <p>试试其他关键词，或进入课程点击收藏。</p>
            <button
              className="secondary"
              onClick={() => {
                setSearch("");
                setFilter(0);
                go("courses");
              }}
            >
              浏览全部课程
            </button>
          </div>
        )}
      </div>
    );
  }
  return (
    <div className="app">
      <a
        className="skip"
        href="#main-content"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("main-content")?.focus();
        }}
      >
        跳到主要内容
      </a>
      {mobile && (
        <button
          className="scrim"
          aria-label="关闭导航"
          onClick={() => setMobile(false)}
        />
      )}
      <aside className={`sidebar ${mobile ? "open" : ""}`}>
        <a href="#home" className="brand">
          <span className="brand-icon">
            <GraduationCap size={24} />
          </span>
          <span>
            AI Academy<small>AI 零基础学院</small>
          </span>
        </a>
        <button
          className="mobile-close icon-button"
          aria-label="关闭导航"
          onClick={() => setMobile(false)}
        >
          <X />
        </button>
        <div className="sidebar-label">我的学习空间</div>
        <nav>
          {navItems.map(([key, label, Icon]) => (
            <a
              key={key}
              href={`#${key}`}
              className={`nav-item ${page === key ? "active" : ""}`}
            >
              <Icon size={19} />
              {label}
              {key === "wrong" && activeWrong.length > 0 && (
                <span className="count">{activeWrong.length}</span>
              )}
            </a>
          ))}
        </nav>
        <div className="sidebar-label route-label">
          学习路线 <span>9 章</span>
        </div>
        <div className="chapter-nav">
          {chapters.map((c, i) => {
            const Icon = icons[i];
            return (
              <details key={c.id} open={chapter?.id === c.id || undefined}>
                <summary>
                  <Icon size={16} />
                  <span>
                    {String(c.id).padStart(2, "0")} · {c.title}
                  </span>
                  <ChevronRight size={14} />
                </summary>
                <div className="sub-lessons">
                  {c.lessons.map((l) => (
                    <a
                      key={l.id}
                      href={`#lesson/${l.id}`}
                      className={lesson?.id === l.id ? "current" : ""}
                    >
                      <span>{state.completed.includes(l.id) ? "✓" : "·"}</span>
                      {l.title}
                    </a>
                  ))}
                  <a href={`#exam/${c.id}`}>↗ 章节考试</a>
                </div>
              </details>
            );
          })}
        </div>
        <div className="sidebar-bottom">
          <span className="status-dot" />
          本地学习 · 无需登录<small>进度仅保存在当前浏览器</small>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <button
            className="mobile-menu icon-button"
            aria-label="打开导航"
            onClick={() => setMobile(true)}
          >
            <Menu />
          </button>
          <div className="breadcrumb">
            我的学习空间 <ChevronRight size={14} />
            <b>
              {page === "lesson"
                ? "逐节学习"
                : page === "exam"
                  ? "章节考试"
                  : navItems.find((n) => n[0] === page)?.[1] || "学习概览"}
            </b>
          </div>
          <div className="header-right">
            <span>
              <Flame size={17} /> 连续学习 {streak(state.days)} 天
            </span>
            <div className="avatar">学</div>
          </div>
        </header>
        <main id="main-content" tabIndex={-1}>
          <div key={route} className="page-content">
            {storageError && (
              <div className="notice warning">
                {storageError}
                <button onClick={() => exportData(true)}>导出原始记录</button>
                <button
                  onClick={() => {
                    if (
                      confirm(
                        "重置后将清除当前浏览器记录。请先导出备份，确定继续？",
                      )
                    ) {
                      try {
                        localStorage.removeItem(STORAGE_KEY);
                        location.reload();
                      } catch {
                        setNotice("存储被禁用，无法重置。");
                      }
                    }
                  }}
                >
                  重置存储
                </button>
              </div>
            )}
            {notice && (
              <div className="notice" role="status">
                {notice}
                <button aria-label="关闭消息" onClick={() => setNotice("")}>
                  <X size={16} />
                </button>
              </div>
            )}
            {page === "home" && (
              <>
                <div className="page-heading">
                  <div>
                    <span className="eyebrow">AI Academy / 学习手册</span>
                    <h1>从零开始，学会使用 AI</h1>
                    <p>9 章系统课程，按自己的节奏学习、练习和复习。</p>
                  </div>
                  <span className="edition">入门 · 实践 · 原理</span>
                </div>
                <div className="dashboard-grid">
                  <div className="dashboard-main">
                    <section className="hero">
                      <div className="hero-copy">
                        <span className="hero-label">
                          {state.recent.length
                            ? "当前学习"
                            : "第一课 · 约 12 分钟"}
                        </span>
                        <h2>
                          {state.recent.length ? (
                            current.title
                          ) : (
                            <>
                              先认识 AI，
                              <br />
                              再做一个小作品
                            </>
                          )}
                        </h2>
                        <p>
                          {state.recent.length
                            ? "回到上次的课程，接着完成讲解、实践和测试。"
                            : "从大模型、提示词到智能体。每节课都有具体案例，学完就能试一试。"}
                        </p>
                        <a
                          className="hero-button"
                          href={`#lesson/${current.id}`}
                        >
                          {state.recent.length ? "继续学习" : "开始第一课"}
                          <ArrowRight size={18} />
                        </a>
                      </div>
                      <div className="lesson-preview">
                        <div className="preview-heading">
                          <span>本节学习单</span>
                          <span>{current.id.replace("-", " / ")}</span>
                        </div>
                        <h3>{current.title}</h3>
                        <div className="preview-note">
                          {current.objectives[0]}
                        </div>
                        <ol>
                          {[
                            "读懂概念与案例",
                            "完成一个小练习",
                            "用课后测试检查理解",
                          ].map((step, i) => (
                            <li key={step}>
                              <span>{String(i + 1).padStart(2, "0")}</span>
                              {step}
                            </li>
                          ))}
                        </ol>
                        <a
                          href={`#lesson/${current.id}`}
                          className="preview-link"
                        >
                          查看这节课 <ArrowRight size={16} />
                        </a>
                      </div>
                    </section>
                    <div className="stat-grid">
                      {[
                        [
                          BookOpen,
                          `${totalDone} / ${lessons.length}`,
                          "已完成课程",
                        ],
                        [Target, `${accuracy}%`, "答题正确率"],
                        [
                          CircleCheck,
                          String(state.attempts.length),
                          "累计作答",
                        ],
                      ].map(([, value, label], i) => {
                        return (
                          <div className="stat-card" key={i}>
                            <div>
                              <strong>{String(value)}</strong>
                              <small>{String(label)}</small>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <div className="section-heading">
                      <div>
                        <span className="eyebrow">学习位置</span>
                        <h2>
                          {state.recent.length ? "继续学习" : "从这一课开始"}
                        </h2>
                      </div>
                      <a className="text-link" href="#courses">
                        全部课程 <ArrowRight size={15} />
                      </a>
                    </div>
                    <a href={`#lesson/${current.id}`} className="continue-card">
                      <div className="continue-art">
                        {current.id.replace("-", ".")}
                      </div>
                      <div>
                        <span className="eyebrow">
                          第 {current.chapterId} 章 · 第{" "}
                          {Number(current.id.split("-")[1])} 节
                        </span>
                        <h3>{current.title}</h3>
                        <p>
                          <Clock3 size={14} />
                          {current.minutes} 分钟 <span>·</span> 3 道互动练习 + 4
                          道课后测试
                        </p>
                      </div>
                      <span className="round-arrow">
                        <ArrowRight size={20} />
                      </span>
                    </a>
                    <div className="section-heading">
                      <div>
                        <span className="eyebrow">课程目录</span>
                        <h2>九章学习路线</h2>
                      </div>
                      <span className="muted">循序渐进，也可以自由探索</span>
                    </div>
                    <div className="chapter-grid">
                      {chapters.map((c, i) => {
                        const Icon = icons[i];
                        const p = chapterPercent(c.id);
                        return (
                          <a
                            href={`#lesson/${c.lessons[0].id}`}
                            className="chapter-card"
                            key={c.id}
                          >
                            <div className="chapter-card-top">
                              <span className={`chapter-icon color-${i % 4}`}>
                                <Icon size={23} />
                              </span>
                              <span className="chapter-no">
                                第 {String(c.id).padStart(2, "0")} 章
                              </span>
                            </div>
                            <h3>{c.title}</h3>
                            <p>{c.description}</p>
                            <div className="chapter-meta">
                              <span>{c.lessons.length} 节课程</span>
                              <span>{p}%</span>
                            </div>
                            <Progress value={p} />
                          </a>
                        );
                      })}
                    </div>
                  </div>
                  <aside className="right-rail">
                    <section className="panel overall">
                      <div className="section-heading">
                        <h3>学习进度</h3>
                        <ChartNoAxesCombined size={18} />
                      </div>
                      <div className="overall-number">
                        {percent}
                        <small>%</small>
                      </div>
                      <Progress value={percent} />
                      <p>
                        已完成 {totalDone} 节，共 {lessons.length} 节
                      </p>
                      <div className="two-stats">
                        <div>
                          <strong>{totalDone}</strong>
                          <small>已完成</small>
                        </div>
                        <div>
                          <strong>{lessons.length - totalDone}</strong>
                          <small>待探索</small>
                        </div>
                      </div>
                    </section>
                    <section className="panel daily">
                      <div className="section-heading">
                        <h3>今日小目标</h3>
                        <Target size={19} />
                      </div>
                      <p>建议每次完成一节课</p>
                      {[
                        ["读懂一个新概念", state.days.includes(today())],
                        [
                          "完成一次互动练习",
                          state.attempts.some(
                            (a) =>
                              new Date(a.date).toDateString() ===
                              new Date().toDateString(),
                          ),
                        ],
                        ["完成一次动手实践", state.taskDays.includes(today())],
                      ].map(([label, done]) => (
                        <div
                          className={`goal ${done ? "checked" : ""}`}
                          key={String(label)}
                        >
                          <CircleCheck size={19} />
                          {label}
                        </div>
                      ))}
                      <a href={`#lesson/${current.id}`} className="text-link">
                        打开当前课程 <ArrowRight size={15} />
                      </a>
                    </section>
                    <section className="tip-card">
                      <span className="eyebrow">学习小贴士</span>
                      <h3>先动手，再深入</h3>
                      <p>
                        不必等到全部理解。先试着做一个小任务，把遇到的问题带回课程里。
                      </p>
                    </section>
                    <section className="panel">
                      <h3>最近学习</h3>
                      {state.recent.length ? (
                        state.recent.slice(0, 3).map(
                          (lid) =>
                            lessonById[lid] && (
                              <a
                                className="recent-link"
                                href={`#lesson/${lid}`}
                                key={lid}
                              >
                                <span>{lessonById[lid].title}</span>
                                <ChevronRight size={15} />
                              </a>
                            ),
                        )
                      ) : (
                        <p className="muted">你的学习足迹将从这里开始。</p>
                      )}
                    </section>
                  </aside>
                </div>
              </>
            )}
            {(page === "courses" || page === "bookmarks") && (
              <>
                <div className="page-heading">
                  <div>
                    <span className="eyebrow">课程</span>
                    <h1>{page === "bookmarks" ? "收藏的课程" : "全部课程"}</h1>
                    <p>
                      9 大章节，90 个循序渐进的小课。随时选择你感兴趣的方向。
                    </p>
                  </div>
                </div>
                <div className="filters">
                  <label className="search-box">
                    <Search size={18} />
                    <input
                      aria-label="搜索课程"
                      placeholder="搜索课程或关键词"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                    />
                  </label>
                  <select
                    aria-label="筛选章节"
                    value={filter}
                    onChange={(e) => setFilter(Number(e.target.value))}
                  >
                    <option value={0}>全部章节</option>
                    {chapters.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.id}. {c.title}
                      </option>
                    ))}
                  </select>
                </div>
                <p className="muted">找到 {filtered.length} 节课程</p>
                <LessonList />
              </>
            )}
            {page === "lesson" && lesson && chapter && (
              <>
                <div className="lesson-header">
                  <a className="text-link" href="#courses">
                    <ArrowLeft size={16} />
                    返回课程
                  </a>
                  <span className="tag">
                    第 {chapter.id} 章 · {chapter.title}
                  </span>
                  <h1>{lesson.title}</h1>
                  <div className="lesson-header-meta">
                    <span>
                      <Clock3 size={16} />
                      {lesson.minutes} 分钟
                    </span>
                    <span>{lesson.pages === "视频补充" ? "视频主题补充" : `原资料第 ${lesson.pages} 页`}</span>
                    <span>原创教学改写</span>
                    <button
                      className={`text-button ${state.bookmarks.includes(id) ? "saved" : ""}`}
                      onClick={() => toggle("bookmarks", id)}
                    >
                      <Bookmark size={17} />
                      {state.bookmarks.includes(id) ? "已收藏" : "收藏课程"}
                    </button>
                  </div>
                </div>
                <div className="lesson-layout">
                  <div className="lesson-content">
                    <section id="objectives" className="objectives">
                      <span className="eyebrow">这一节，你将能够</span>
                      {lesson.objectives.map((o) => (
                        <div key={o}>
                          <CircleCheck size={18} />
                          {o}
                        </div>
                      ))}
                    </section>
                    <section id="concepts" className="reading">
                      <span className="eyebrow">01 · 理解概念</span>
                      <h2>先理解，再记住</h2>
                      {lesson.sections.map((s) => (
                        <div key={s.title}>
                          <h3>{s.title}</h3>
                          <p>{s.text}</p>
                        </div>
                      ))}
                      <div className="term-list">
                        {lesson.terms.map((t) => (
                          <span className="tag" key={t}>
                            {t}
                          </span>
                        ))}
                      </div>
                      <div className="flow-diagram" aria-label="本节流程示意">
                        {lesson.steps.map((s, i) => (
                          <div key={s}>
                            <span>{String(i + 1).padStart(2, "0")}</span>
                            <strong>{s}</strong>
                            {i < lesson.steps.length - 1 && (
                              <ArrowRight size={17} />
                            )}
                          </div>
                        ))}
                      </div>
                    </section>
                    <VideoLesson key={id} lessonId={id} completed={state.tasks.includes(`${id}:video-sim`)} onComplete={() => setState((s) => ({ ...s, tasks: [...new Set([...s.tasks, `${id}:video-sim`])] }))} />
                    <section id="example" className="reading">
                      <span className="eyebrow">02 · 案例演示</span>
                      <h2>把知识放进真实任务</h2>
                      <div className="example-box">
                        <BookOpen size={18} />
                        <p>{lesson.example}</p>
                      </div>
                      {lesson.code && (
                        <>
                          <h3>按行读一读</h3>
                          <pre>
                            <code>{lesson.code}</code>
                          </pre>
                          <p className="muted">
                            这是代码阅读示例，不会在浏览器中执行
                            Python。先预测输出，再完成后面的代码题。
                          </p>
                        </>
                      )}
                    </section>
                    <section id="practice" className="reading">
                      <span className="eyebrow">03 · 动手实践</span>
                      <h2>轮到你来试一试</h2>
                      <p>{lesson.task}</p>
                      <ol className="practice-steps">
                        {lesson.steps.map((s) => (
                          <li key={s}>{s}</li>
                        ))}
                      </ol>
                      {lesson.lab && <PracticeLab key={id} lab={lesson.lab} />}
                      <label className="note-label" htmlFor="practice-note">
                        记录你的结果与发现
                      </label>
                      <textarea
                        id="practice-note"
                        value={state.notes[id] || ""}
                        placeholder="写下你的方案、观察到的结果，或者还没弄懂的问题…（自动保存）"
                        onChange={(e) =>
                          setState((s) => ({
                            ...s,
                            notes: { ...s.notes, [id]: e.target.value },
                          }))
                        }
                      />
                      <button
                        className="secondary"
                        onClick={() => toggle("tasks", id)}
                      >
                        <Check size={16} />
                        {state.tasks.includes(id)
                          ? "实践已完成 · 点击取消"
                          : "我已完成这次实践"}
                      </button>
                    </section>
                    <section id="interact" className="reading">
                      <span className="eyebrow">04 · 学一点，练一点</span>
                      <h2>检查一下你的理解</h2>
                      {lesson.questions.map((q) => (
                        <Quiz
                          key={q.id}
                          q={q}
                          onAnswer={(q, a) => record({ [q.id]: a })}
                        />
                      ))}
                    </section>
                    <section id="summary" className="summary-box">
                      <span className="eyebrow">05 · 带走这几件事</span>
                      <h2>本节小结</h2>
                      <p>{lesson.sections[0].text}</p>
                      <h3>常见误区</h3>
                      <p>不要把“{lesson.misconception}”当作正确结论。</p>
                      <h3>关键术语</h3>
                      <div className="term-list">
                        {lesson.terms.map((t) => (
                          <span className="tag" key={t}>
                            {t}
                          </span>
                        ))}
                      </div>
                    </section>
                    <section id="test">
                      <Test
                        key={lesson.id}
                        title="课后测试"
                        items={lesson.test}
                        onFinish={(answers, score) => record(answers, score)}
                      />
                    </section>
                    <p className="source-note">
                      {lesson.sourceNote}{" "}
                        PDF 资料日期：2026-06-03；课程整理日期：2026-11-19。
                      {lesson.id === "03-08" &&
                        "本节原文仅有简略条目，流程与练习为补充教学。"}
                    </p>
                    <div className="lesson-footer">
                      <button
                        className="secondary"
                        disabled={lessons.indexOf(lesson) === 0}
                        onClick={() =>
                          go(
                            "lesson/" + lessons[lessons.indexOf(lesson) - 1].id,
                          )
                        }
                      >
                        <ArrowLeft size={16} />
                        上一节
                      </button>
                      <button className="primary" onClick={complete}>
                        <Check size={17} />
                        {state.completed.includes(id)
                          ? "已完成 · 检查章节进度"
                          : "标记为已完成"}
                      </button>
                      <button
                        className="secondary"
                        onClick={() =>
                          go(
                            lessons.indexOf(lesson) === lessons.length - 1
                              ? "exam/" + chapter.id
                              : "lesson/" +
                                  lessons[lessons.indexOf(lesson) + 1].id,
                          )
                        }
                      >
                        {lessons.indexOf(lesson) === lessons.length - 1
                          ? "章节考试"
                          : "下一节"}
                        <ArrowRight size={16} />
                      </button>
                    </div>
                  </div>
                  <aside className="lesson-toc panel">
                    <span className="eyebrow">本节导航</span>
                    {[
                      ["objectives", "学习目标"],
                      ["concepts", "知识讲解"],
                      ...(id === "02-04" ? [["video-knowledge", "视频知识点"], ["video-frames", "重点画面"], ["video-practical", "视频实操"]] : []),
                      ["example", "案例演示"],
                      ["practice", "动手实践"],
                      ["interact", "互动练习"],
                      ["summary", "本节总结"],
                      ["test", "课后测试"],
                    ].map(([target, label], i) => (
                      <button
                        key={target}
                        onClick={() =>
                          document
                            .getElementById(target)
                            ?.scrollIntoView({ behavior: "smooth" })
                        }
                      >
                        <span>{String(i + 1).padStart(2, "0")}</span>
                        {label}
                      </button>
                    ))}
                    <hr />
                    <h4>本章完成度 · {chapterPercent(chapter.id)}%</h4>
                    <Progress value={chapterPercent(chapter.id)} />
                    <p className="muted">
                      最近课后测试：
                      {state.scores[id] === undefined
                        ? "尚未作答"
                        : state.scores[id] + " 分"}
                    </p>
                    <a className="text-link" href={`#exam/${chapter.id}`}>
                      进入章节考试 <ArrowRight size={15} />
                    </a>
                  </aside>
                </div>
              </>
            )}
            {page === "exam" && chapter && (
              <div className="narrow">
                <div className="page-heading">
                  <div>
                    <span className="eyebrow">章节考试</span>
                    <h1>{chapter.title} · 章节考试</h1>
                    <p>
                      随机抽取 12
                      道题。可以自由复习，提交后查看成绩与薄弱知识点。
                    </p>
                  </div>
                </div>
                <button
                  className="secondary"
                  onClick={() => {
                    if (confirm("重新抽题会清空当前未提交的答案，继续吗？"))
                      setExamRound((r) => r + 1);
                  }}
                >
                  重新抽取一套题
                </button>
                {examItems.length > 0 && (
                  <Test
                    key={`${id}-${examRound}`}
                    title="检验这一章的收获"
                    items={examItems}
                    onFinish={(answers, score) => record(answers, score, true)}
                  />
                )}
              </div>
            )}
            {page === "wrong" && (
              <>
                <div className="page-heading">
                  <div>
                    <span className="eyebrow">错题复习</span>
                    <h1>错题本</h1>
                    <p>
                      {activeWrong.length} 道待复习 ·
                      每次重新理解，都是一次进步。
                    </p>
                  </div>
                </div>
                <div className="filters">
                  <select
                    aria-label="筛选错题章节"
                    value={filter}
                    onChange={(e) => setFilter(Number(e.target.value))}
                  >
                    <option value={0}>全部章节</option>
                    {chapters.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.title}
                      </option>
                    ))}
                  </select>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={showResolved}
                      onChange={(e) => setShowResolved(e.target.checked)}
                    />
                    显示已解决
                  </label>
                </div>
                <div className="narrow">
                  {wrongIds
                    .filter(
                      (q) =>
                        (showResolved || !state.resolved.includes(q)) &&
                        (!filter ||
                          lessonById[questionById[q].lessonId].chapterId ===
                            filter),
                    )
                    .map((qid) => {
                      const q = questionById[qid];
                      return (
                        <div className="wrong-item" key={qid}>
                          <a
                            className="text-link"
                            href={`#lesson/${q.lessonId}`}
                          >
                            {lessonById[q.lessonId].title}
                            <ArrowRight size={14} />
                          </a>
                          <Quiz
                            q={q}
                            onAnswer={(q, a) => record({ [q.id]: a })}
                          />
                          <details className="review-answer">
                            <summary>查看正确答案与解析</summary>
                            <p>{q.answer.join(" → ")}</p>
                            <p>{q.explanation}</p>
                          </details>
                          <button
                            className="secondary"
                            onClick={() =>
                              setState((s) => ({
                                ...s,
                                resolved: s.resolved.includes(qid)
                                  ? s.resolved.filter((x) => x !== qid)
                                  : [...s.resolved, qid],
                              }))
                            }
                          >
                            {state.resolved.includes(qid)
                              ? "重新加入复习"
                              : "我已理解 · 标记为已解决"}
                          </button>
                        </div>
                      );
                    })}
                  {!wrongIds.some(
                    (q) =>
                      (showResolved || !state.resolved.includes(q)) &&
                      (!filter ||
                        lessonById[questionById[q].lessonId].chapterId ===
                          filter),
                  ) && (
                    <div className="empty">
                      <CircleCheck />
                      <h3>当前没有待显示的错题</h3>
                      <p>继续学习，做题结果会自动记录在这里。</p>
                      <a className="primary" href="#courses">
                        去学习
                      </a>
                    </div>
                  )}
                </div>
              </>
            )}
            {page === "profile" && (
              <>
                <div className="page-heading">
                  <div>
                    <span className="eyebrow">学习档案</span>
                    <h1>学习记录</h1>
                    <p>记录属于你。可以导出备份，再导入另一个浏览器。</p>
                  </div>
                </div>
                <div className="stat-grid">
                  {[
                    [`${totalDone}`, "已完成课程"],
                    [`${streak(state.days)} 天`, "连续学习"],
                    [`${accuracy}%`, "累计答题正确率"],
                  ].map(([v, l]) => (
                    <div className="stat-card" key={l}>
                      <div>
                        <strong>{v}</strong>
                        <small>{l}</small>
                      </div>
                    </div>
                  ))}
                </div>
                <section className="panel">
                  <h2>章节掌握情况</h2>
                  {chapters.map((c) => (
                    <div className="mastery-row" key={c.id}>
                      <a href={`#exam/${c.id}`}>
                        {String(c.id).padStart(2, "0")} · {c.title}
                      </a>
                      <Progress value={chapterPercent(c.id)} />
                      <span>{chapterPercent(c.id)}% 已完成</span>
                      <small>
                        {state.exams.filter((e) => e.chapterId === c.id).length
                          ? `最近考试 ${state.exams.filter((e) => e.chapterId === c.id).at(-1)?.score} 分`
                          : "尚未考试"}
                      </small>
                    </div>
                  ))}
                </section>
                <section className="panel backup">
                  <h2>学习记录备份</h2>
                  <p>
                    包含进度、收藏、笔记、答题记录与考试成绩。仅保存于当前浏览器，不会自动跨设备同步。导入会覆盖当前记录。
                  </p>
                  <div className="button-row">
                    <button className="primary" onClick={() => exportData()}>
                      <Download size={17} />
                      导出备份
                    </button>
                    <label className="secondary upload">
                      <Upload size={17} />
                      导入备份
                      <input
                        type="file"
                        accept="application/json,.json"
                        aria-label="导入备份"
                        onChange={async (e) => {
                          const f = e.target.files?.[0];
                          if (!f) return;
                          try {
                            if (f.size > 20_000_000)
                              throw new Error(
                                "文件过大，请选择 20 MB 以内的学习备份。",
                              );
                            const imported = parseState(await f.text());
                            if (
                              confirm(
                                "导入将覆盖当前记录。确认已备份现有进度并继续？",
                              )
                            ) {
                              setState(imported);
                              setNotice("学习记录已导入。");
                            }
                          } catch (err) {
                            setNotice(
                              err instanceof Error
                                ? err.message
                                : "导入失败，原有记录未改变。",
                            );
                          }
                          e.target.value = "";
                        }}
                      />
                    </label>
                  </div>
                </section>
                <section className="panel">
                  <h2>最近考试</h2>
                  {state.exams.length ? (
                    state.exams
                      .slice(-10)
                      .reverse()
                      .map((e, i) => (
                        <div className="exam-history" key={i}>
                          <span>{chapters[e.chapterId - 1]?.title}</span>
                          <time>
                            {new Date(e.date).toLocaleString("zh-CN")}
                          </time>
                          <strong>{e.score} 分</strong>
                        </div>
                      ))
                  ) : (
                    <p className="muted">
                      完成一次章节考试后，成绩会显示在这里。
                    </p>
                  )}
                </section>
              </>
            )}
            {(![
              "home",
              "courses",
              "bookmarks",
              "lesson",
              "exam",
              "wrong",
              "profile",
            ].includes(page) ||
              (page === "lesson" && !lesson) ||
              (page === "exam" && !chapter)) && (
              <div className="empty">
                <h1>没有找到这个页面</h1>
                <a className="primary" href="#home">
                  回到学习概览
                </a>
              </div>
            )}
          </div>
          <CourseUpdates />
          <footer className="site-footer">
            <span>
              AI Academy <i>·</i> AI 零基础学习手册
            </span>
            <span>
              本地保存学习记录 <i>·</i>{" "}
              <a
                href="https://github.com/heydamir/unslop"
                target="_blank"
                rel="noreferrer"
              >
                Design craft: unslop / @heydamir
              </a>
            </span>
          </footer>
        </main>
      </div>
    </div>
  );
}
