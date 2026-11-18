"""Original Node sample questions based on reviewed online transcript and courseware."""
def apply_sample(lesson):
    if lesson['id'] != '02-04':
        return
    def q(suffix, kind, prompt, options, answer, explanation):
        return dict(id='02-04-'+suffix,lessonId='02-04',type=kind,prompt=prompt,options=options,answer=answer,explanation=explanation,hint='结合视频融合区的提示符、输出和错误说明判断。')
    lesson['questions']=[
        q('p1','single','想查看 Node 版本，应该在系统终端输入哪条命令？',['npm install -g','node --version','let a = 10'],['node --version'],'node --version 查看 Node 版本，不安装包。'),
        q('p2','single','已经输入 node，出现 > 提示符。此时你处于什么环境？',['Node 的 JavaScript 交互环境','浏览器地址栏','npm 包搜索页'],['Node 的 JavaScript 交互环境'],'REPL 允许逐行输入 JavaScript；.exit 可返回系统终端。'),
        q('p3','single','let a = 10 和 let b = 20 后，console.log(a + b) 打印什么？',['1020','undefined，所以程序失败','30'],['30'],'先打印数值 30。随后 REPL 显示的 undefined 是调用的返回值，不能据此判断失败。')]
    lesson['test']=[
        q('t1','single','Node.js 和 npm 的分工是什么？',['Node 运行 JavaScript，npm 管理包','npm 是编辑器，Node 是账号','两者都是网页播放器'],['Node 运行 JavaScript，npm 管理包'],'运行时负责执行程序，包管理器负责管理软件包。'),
        q('t2','order','把本节最小环境验收流程排序。',['记录打印的 30 并退出','进入 Node REPL','检查 Node/npm 版本','定义 a、b 并打印和'],['检查 Node/npm 版本','进入 Node REPL','定义 a、b 并打印和','记录打印的 30 并退出'],'先验证环境，再进入 REPL 执行运算，最后记录结果并退出。退出方式为原创补充。'),
        q('t3','single','npm 提示 E404 / Not Found，接下来最合理的动作是？',['立即认定重复安装，卸载所有包','核对包名、官方说明和注册表，再判断原因','忽略报错并标记成功'],['核对包名、官方说明和注册表，再判断原因'],'画面表明没有找到请求的包，不能凭空推断重复安装。'),
        q('t4','multiple','选择可以写入环境验收卡的有效证据。',['Node/npm 的实际版本输出','console.log(a + b) 打印 30','只看到下载完成就认定所有命令可用','退出后恢复系统终端提示符'],['Node/npm 的实际版本输出','console.log(a + b) 打印 30','退出后恢复系统终端提示符'],'验收卡应记录实际运行结果。模拟输出要注明模拟，不能冒充本机验证。')]
