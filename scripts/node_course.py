"""Independent project-based Node lesson; stable lesson and question identities."""
def apply_sample(lesson):
    if lesson['id'] != '02-04':
        return
    lesson.update(title='让 JavaScript 在电脑上运行', subtitle='从运行环境到项目依赖，理解 Node.js、npm 和现代 JavaScript 项目的运行方式。',minutes=35,
        introduction='你用 AI 生成了一个“学习计时器”网页项目。文件已经在电脑上，双击页面却没有预期效果，运行命令也报错。为什么代码写好了还不能运行？为什么这个项目需要 Node.js？npm 又负责什么？本节从项目的运行条件出发，把这三个问题连起来。普通 HTML 可以直接由浏览器打开；使用构建工具的项目通常还需要开发环境与项目依赖。',
        objectives=['区分 Node.js、npm 和 package.json 的职责','读懂项目目录、依赖声明与启动脚本','按证据定位启动失败，并验证修复结果'],
        sections=[dict(title='Node.js：执行 JavaScript 的运行时',text='浏览器可以执行网页里的 JavaScript。Node.js 则让 JavaScript 在浏览器之外执行，例如运行本地脚本或开发服务器。现代网页项目的开发工具常在 Node 中工作，最终网页仍由浏览器展示。并非每个网页都需要 Node，也不是所有浏览器代码都能原样在 Node 运行：例如 document 属于浏览器环境。'),dict(title='npm：把项目需要的工具准备好',text='npm 是包管理器：按项目清单安装依赖，也可以执行项目定义的脚本。npm run dev 并不是一个固定的服务器程序；它查找当前项目 scripts 里的 dev，然后运行对应命令。开发服务器由脚本指定的工具提供。'),dict(title='package.json：项目的配置清单',text='这个 JSON 文件记录项目名称、依赖、脚本等配置。scripts 是可执行命令的名字和内容；dependencies 通常声明应用运行所依赖的包；devDependencies 通常声明开发、构建或测试工具。开发环境一般两者都需要。打包后的浏览器应用如何携带依赖取决于构建过程，不能简单理解为两类包都会直接发送给用户。')],
        example='小岚的学习计时器使用 Vite 启动开发服务器。她先检查 Node 版本，在项目目录读取 package.json，确认 dev 对应 vite、Vite 声明在开发依赖中，安装依赖后执行 npm run dev，最后打开终端给出的本地地址并测试按钮。她没有猜测脚本名，也没有把“命令退出”当成启动成功。',
        task='为一个你信任的本地网页项目制作启动验收卡：记录项目目录、Node/npm 版本、脚本定义、安装结果、本地地址和一次界面操作结果。没有本地环境时完成三个模拟实验，并明确注明“仅完成模拟，尚未本机验证”。',
        steps=['确认项目要求与运行环境','在正确目录检查配置与依赖','安装依赖并执行已定义的脚本','打开本地地址验收交互结果'],
        terms=['运行时','包管理器','package.json','scripts','依赖','锁文件'],
        misconception='所有项目都能直接运行 npm run dev，且启动成功就等于上线。',
        summary='先确认环境，再定位项目，再读取配置，然后安装依赖、执行脚本、验证页面。Node 负责运行，npm 负责管理包与调度脚本，package.json 负责声明；package-lock.json 记录解析结果，node_modules 保存本地安装内容。开发服务器运行在本机，不等于公开部署。',
        sourceNote='本课程以原创“学习计时器”情境组织。研发参考《AI学习文档》Node 主题（物理页 36–39）及配套教学资料；概念与命令按下列官方资料核验。示意环境与版本是教学约定。',
        references=[dict(title='Node.js：运行脚本',href='https://nodejs.org/en/learn/command-line/run-nodejs-scripts-from-the-command-line'),dict(title='Node.js：官方下载与受支持版本',href='https://nodejs.org/en/download'),dict(title='npm：package.json 配置',href='https://docs.npmjs.com/cli/v11/configuring-npm/package-json'),dict(title='npm：安装依赖',href='https://docs.npmjs.com/cli/v11/commands/npm-install'),dict(title='npm：运行项目脚本',href='https://docs.npmjs.com/cli/v11/commands/npm-run-script'),dict(title='npm：package-lock.json',href='https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json')])
    lesson.pop('lab',None)
    fields=[dict(name='scripts',explanation='命令入口表。npm run dev 查找 dev 的值，并在项目上下文执行 vite。dev 是约定名称，可以不存在，也可以叫 start。先读配置，再决定输入哪个命令。',content='"scripts": { "dev": "vite", "build": "vite build" }'),dict(name='dependencies',explanation='应用需要的包。本例用 dayjs 处理计时记录的日期；版本范围不是已经安装的确切版本。声明依赖后，还需要实际安装。',content='"dependencies": { "dayjs": "^1.11.13" }'),dict(name='devDependencies',explanation='开发、构建与测试所用的包。本例 Vite 提供开发服务器和构建工具。开发时通常需要安装它；不能因为名字带 dev 就跳过。',content='"devDependencies": { "vite": "^7.0.0" }')]
    lesson['experience']=dict(kind='node-project',projectName='study-timer',fields=fields,files=[
        dict(name='package.json',description='先看这份清单：scripts 决定可用命令，依赖字段说明项目需要哪些包。engines 描述运行时要求，普通 npm install 不一定会强制阻止不满足要求的环境。',content='{\n  "name": "study-timer",\n  "private": true,\n  "type": "module",\n  "engines": { "node": ">=22.12.0" },\n  "scripts": { "dev": "vite", "build": "vite build" },\n  "dependencies": { "dayjs": "^1.11.13" },\n  "devDependencies": { "vite": "^7.0.0" }\n}'),
        dict(name='package-lock.json',description='npm 自动维护的锁文件，记录具体依赖树与完整性信息。通常随项目提交，便于重复安装；不要把删除锁文件作为万能修复。npm ci 要求它与清单一致。'),
        dict(name='src/',description='应用源代码目录，是本项目的组织约定。名字并非 Node 的强制要求。'),
        dict(name='  main.js',description='网页入口脚本：操作页面按钮和计时显示。本例由 index.html 引入，再由浏览器执行；它依赖 DOM，不能仅用 node src/main.js 替代网页启动。',content='const button = document.querySelector("button");\nbutton.addEventListener("click", () => {\n  button.textContent = "计时中";\n});'),
        dict(name='index.html',description='浏览器入口，包含按钮和 module 脚本。Vite 为它提供本地开发服务。',content='<button>开始计时</button>\n<script type="module" src="/src/main.js"></script>'),
        dict(name='node_modules/',description='本地安装的软件包目录，npm install 通常生成。一般不提交到 Git；可以依据清单和锁文件重新安装。它不是你手写的源代码，也不是公开部署的替代品。')],walkthrough=[
        dict(title='确认是否存在 Node',action='在 PowerShell、终端或编辑器的终端中检查命令能否找到。',command='node --version',expected='显示 v 开头的版本号。没有输出版本、只有错误就未通过。',reason='没有运行时，依赖它的开发工具无法启动。',recovery='如果命令无法识别，先确认已安装受支持的 Node，并重新打开终端检查 PATH；不在这里安装 Claude Code。'),
        dict(title='检查版本要求',action='记录两个版本，并与项目 README、engines 和工具文档核对。本例要求 Node >=22.12.0；这不是所有项目通用的要求。',command='node --version\nnpm --version',expected='两条命令均返回版本，并满足此项目的要求。',reason='“已安装”不代表兼容。npm 与 Node 也不是同一个版本号。',recovery='版本过低时使用官方支持的兼容版本；npm.ps1 被阻止时可检查 npm.cmd --version，不必盲目关闭系统策略。'),
        dict(title='进入项目目录',action='用实际保存项目的位置替换示例路径，再列出文件。含空格的路径加引号。',command='cd "C:\\Projects\\study-timer"\ndir',expected='列表中能看到 package.json、index.html 和 src。macOS/Linux 可用 ls。',reason='npm 根据当前目录定位项目，正确的文件在别处也不能帮助当前命令。',recovery='路径不存在就先在文件管理器确认位置；不要在错误目录新建一个空清单来掩盖问题。'),
        dict(title='读项目清单',action='用编辑器打开 package.json，或在 PowerShell 中查看文本和脚本列表。',command='Get-Content package.json\nnpm run',expected='看见 scripts.dev 为 vite，npm run 列出 dev 和 build。macOS/Linux 查看文件可用 cat。',reason='确认项目支持的命令，而不是猜每个项目都用 dev。',recovery='ENOENT 通常说明路径/文件缺失；JSON 解析错误应根据行号修正格式，保留原有配置。'),
        dict(title='区分依赖类别',action='查看 dependencies 与 devDependencies，注意 Vite 是开发工具。本例清单中的版本仅用于教学。',command='npm pkg get dependencies devDependencies engines',expected='看见 dayjs、vite 与 node 要求；此时不代表这些包已经安装。',reason='声明说明“需要什么”，安装目录说明“本机有什么”。',recovery='某些字段可以省略；字段不存在不必硬加。以项目实际需要为准。'),
        dict(title='安装项目依赖',action='在信任并检查过的项目目录中安装本地依赖，先读安装脚本与项目说明。',command='npm install',expected='安装退出码为 0，所需包可用，通常生成 node_modules 与锁文件；警告不一定是失败。',reason='把清单声明的包准备到本地。安装可能执行包脚本，本练习页面不会执行它。',recovery='依据错误码检查网络、包名/版本、注册表或权限；E404 不能推断为重复安装。不要直接删锁文件、改全局配置或反复重装。'),
        dict(title='运行已定义的脚本',action='确认 scripts 中有 dev，再启动开发服务器。',command='npm run dev',expected='显示开发服务器就绪及本地地址，终端通常保持运行。',reason='npm 找到 dev 的内容，执行已安装的 Vite，而不是自己生成服务器。',recovery='Missing script: dev 先检查 scripts 与目录；vite not found 再检查开发依赖是否安装；端口占用按终端提示处理。'),
        dict(title='验收网页行为',action='打开终端实际显示的本地地址，点击“开始计时”，检查页面与终端错误；完成后在终端按 Ctrl+C 停止。',command='浏览器打开终端给出的 Local 地址',expected='页面显示按钮，点击后文字变为“计时中”；不是只有空白页或错误页。',reason='进程启动只证明服务器运行，界面还需要实际验证。localhost 只指本机，不等于公开上线。',recovery='地址打不开先确认服务器仍在运行、地址和端口正确；页面空白检查浏览器控制台与入口脚本。')],troubleshooting=[
        dict(symptom='node 命令无法识别',diagnosis='先确认终端是否重开、Node 是否已安装、PATH 是否包含可执行文件。',resolution='使用官方支持的安装方式或版本管理器修复环境，再运行 node --version 验证。'),
        dict(symptom='npm 命令执行失败',diagnosis='区分“命令不存在”、PowerShell 脚本策略、还是 npm 已运行但报业务错误。',resolution='分别检查 npm --version / npm.cmd --version 与 Node 安装；保留完整错误，不把所有失败都当作网络问题。'),
        dict(symptom='找不到 package.json',diagnosis='查看当前目录和文件列表，确认是否进入了项目根目录。',resolution='进入包含真实清单的目录或恢复缺失文件；不随意 npm init 覆盖项目意图。'),
        dict(symptom='npm install 安装失败',diagnosis='从首个具体错误码定位网络、包名版本、注册表或权限，区分警告和非零退出。',resolution='按证据做最小修复，再运行安装并检查退出状态；必要时查官方文档。'),
        dict(symptom='npm run dev 提示脚本不存在',diagnosis='先看 package.json 的 scripts 和 npm run 输出，再核对是否在正确目录。',resolution='若项目使用 start，按 README 运行对应脚本；只有确认工具链后才添加缺失脚本，不猜测命令。')])
    def q(suffix,kind,prompt,options,answer,explanation,hint):
        return dict(id='02-04-'+suffix,lessonId='02-04',type=kind,prompt=prompt,options=options,answer=answer,explanation=explanation,hint=hint)
    lesson['questions']=[
        q('p1','single','项目用 npm run dev 启动。真正决定 dev 执行什么的是？',['package.json 中的 scripts.dev','文件夹叫 dev 就会自动启动','Node 的版本号'],['package.json 中的 scripts.dev'],'npm 查找当前项目的脚本定义，再执行对应命令；名称 dev 没有内置固定行为。','区分命令的名字与命令的定义位置。'),
        q('p2','single','清单中声明了 Vite，但没有安装依赖。哪项判断合理？',['写进清单就已经装好了','开发工具也需要在开发环境准备好','只安装 Node 就能得到任意项目的所有包'],['开发工具也需要在开发环境准备好'],'声明表达项目需要什么；安装才把所需包准备到本地。','比较配置文件与磁盘上的实际内容。'),
        q('p3','single','你想运行独立的 hello.js，文件中只有 console.log("ready")。应该选择？',['node hello.js','npm hello.js','cd hello.js'],['node hello.js'],'Node 运行独立 JavaScript 文件。这个例子不使用浏览器 DOM。','先判断这是运行文件还是切换目录。')]
    lesson['test']=[
        q('t1','single','下载 AI 生成的前端项目后，npm run dev 报 Missing script: dev。最先检查什么？',['卸载 Node','当前目录的 package.json 中 scripts 及项目说明','删除 package-lock.json'],['当前目录的 package.json 中 scripts 及项目说明'],'报错说明请求的脚本未定义。先确认目录和脚本名，不能据此认定运行时损坏。','从错误涉及的对象开始定位。'),
        q('t2','order','已有项目要首次在本机启动，按依赖关系排序。',['验收本地页面','执行项目定义的启动脚本','检查环境并进入正确项目目录','读取配置并安装所需依赖'],['检查环境并进入正确项目目录','读取配置并安装所需依赖','执行项目定义的启动脚本','验收本地页面'],'环境与目录提供前提，配置决定依赖和命令，最后通过页面行为验收。','找出每一步需要的前提。'),
        q('t3','multiple','关于本课计时器项目，选择所有成立的说法。',['node_modules 通常可以依据清单和锁文件重新生成','开发时通常需要 devDependencies 中的工具','package-lock.json 记录具体依赖树','本地服务器就绪就等于网站已经公开部署'],['node_modules 通常可以依据清单和锁文件重新生成','开发时通常需要 devDependencies 中的工具','package-lock.json 记录具体依赖树'],'锁文件记录解析结果，本地包目录可重新安装；开发服务器地址不等于公开部署地址。','分别考虑可重建文件、开发环境和访问范围。'),
        q('t4','single','Node 已满足项目要求，但运行 dev 时提示 vite not found。最有针对性的下一步是？',['检查 Vite 的声明及开发依赖是否已在该项目安装','给所有安装命令加 -g','换浏览器就能修复'],['检查 Vite 的声明及开发依赖是否已在该项目安装'],'运行时已通过，应继续检查脚本所依赖的本地工具，而不是盲目重装 Node 或全局安装。','沿着环境、配置、依赖、脚本的链条排查。')]
