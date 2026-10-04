#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行待办清单(todo)

用法:
    python todo.py list            按序号列出所有任务
                                   未完成显示 [ ],已完成显示 [x]
    python todo.py add "内容"      添加一个任务
    python todo.py done <序号>     把第 N 个任务标记为已完成
    python todo.py rm <序号>       删除第 N 个任务
    python todo.py stats          统计任务总数、已完成和未完成数量
    python todo.py prio <序号>    把第 N 个任务标记为高优先级

    序号从 1 开始,与 list 输出的编号一一对应。
    高优先级任务在 list 中于方括号后显示一个 !,例如 1. [ ]! 写报告。

说明:
    任务数据保存在与本脚本同目录的 todos.json 中。
    不带任何参数运行时会打印本说明。
"""

import json
import sys
from pathlib import Path

# 数据文件固定在脚本所在目录,这样在任何工作目录下运行都读写同一个文件
DATA_FILE = Path(__file__).resolve().parent / "todos.json"


def load_todos():
    """读取 todos.json,返回任务列表。

    文件不存在、内容损坏或格式不对时一律按「空清单」处理,
    避免因为一个坏文件就让整个程序报错退出。
    """
    if not DATA_FILE.exists():
        return []
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    # 防御性检查:正常情况应该是一个列表
    return data if isinstance(data, list) else []


def save_todos(todos):
    """把任务列表写回 todos.json。

    ensure_ascii=False 让中文以原字面保存,文件可以直接阅读;
    indent=2 让 JSON 有缩进,方便人查看和手工修改。
    """
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def cmd_list():
    """子命令 list:按序号列出所有任务。"""
    todos = load_todos()

    print("=== TODO 清单 ===")
    if not todos:
        print("（暂无任务）")
        return

    # enumerate 从 1 开始,让序号和用户看到的一致
    for index, todo in enumerate(todos, start=1):
        # done 为真显示 [x],否则显示 [ ]
        mark = "[x]" if todo.get("done") else "[ ]"
        # 高优先级任务在方括号后紧跟一个 !,中间不留空格
        flag = "!" if todo.get("priority") else ""
        print(f"{index}. {mark}{flag} {todo.get('content', '')}")


def cmd_add(content):
    """子命令 add:在清单末尾追加一个未完成的任务。"""
    todos = load_todos()
    todos.append({"content": content, "done": False})
    save_todos(todos)
    print(f"已添加:{content}")


def parse_index(raw, total):
    """把命令行传来的序号解析成从 1 开始的下标。

    done 和 rm 都要做同样的校验,所以抽出来共用。
    校验不通过时打印友好提示并返回 None,由调用方决定怎么收场,
    这样任何非法输入都不会让程序抛异常崩掉。
    """
    # 清单为空时,任何序号都没有意义,提前拦掉避免下面的范围提示自相矛盾
    if total == 0:
        print("清单为空,没有可操作的任务")
        return None

    try:
        index = int(raw)
    except ValueError:
        # 传进来的是 abc、1.5 这类没法转成整数的东西
        print(f"序号必须是数字:{raw}")
        return None

    # 序号从 1 开始,合法范围是 1 ~ 任务总数
    if index < 1 or index > total:
        print(f"序号超出范围:{index}(当前共 {total} 个任务,有效范围 1-{total})")
        return None

    return index


def cmd_done(raw_index):
    """子命令 done:把第 N 个任务标记为已完成。"""
    todos = load_todos()

    index = parse_index(raw_index, len(todos))
    if index is None:
        return

    # 下标要减 1,因为列表从 0 开始而序号从 1 开始
    todos[index - 1]["done"] = True
    save_todos(todos)
    print(f"已完成：{todos[index - 1].get('content', '')}")


def cmd_rm(raw_index):
    """子命令 rm:删除第 N 个任务。"""
    todos = load_todos()

    index = parse_index(raw_index, len(todos))
    if index is None:
        return

    # pop 会返回被删掉的那一项,用来在提示里回显它的内容
    removed = todos.pop(index - 1)
    save_todos(todos)
    print(f"已删除：{removed.get('content', '')}")


def cmd_stats():
    """子命令 stats:统计任务总数、已完成数和未完成数。"""
    todos = load_todos()

    total = len(todos)
    # done 为真的才计入已完成,缺失该字段时按未完成处理
    done = sum(1 for todo in todos if todo.get("done"))

    # 未完成直接用总数减去已完成,不必再遍历一遍清单
    print(f"共 {total} 项，已完成 {done} 项，未完成 {total - done} 项")


def cmd_prio(raw_index):
    """子命令 prio:把第 N 个任务标记为高优先级。"""
    todos = load_todos()

    # 序号校验复用 parse_index,与 done / rm 的行为保持一致
    index = parse_index(raw_index, len(todos))
    if index is None:
        return

    todos[index - 1]["priority"] = True
    save_todos(todos)
    print(f"已标记为高优先级：{todos[index - 1].get('content', '')}")


def main():
    # sys.argv[0] 是脚本自身的路径,真正的参数从下标 1 开始
    args = sys.argv[1:]

    # 没给参数时打印用法说明,并以非零状态码退出
    if not args:
        print(__doc__.strip())
        sys.exit(1)

    command = args[0]

    if command == "list":
        cmd_list()

    elif command == "add":
        if len(args) < 2:
            print('用法:python todo.py add "内容"')
            sys.exit(1)
        # 内容本身带空格时,shell 可能会把它拆成多个参数,这里重新拼回一句
        cmd_add(" ".join(args[1:]))

    elif command == "done":
        if len(args) < 2:
            print("用法:python todo.py done <序号>")
            sys.exit(1)
        cmd_done(args[1])

    elif command == "rm":
        if len(args) < 2:
            print("用法:python todo.py rm <序号>")
            sys.exit(1)
        cmd_rm(args[1])

    elif command == "stats":
        # 纯统计,不需要额外参数
        cmd_stats()

    elif command == "prio":
        if len(args) < 2:
            print("用法:python todo.py prio <序号>")
            sys.exit(1)
        cmd_prio(args[1])

    else:
        # 未知子命令:给出提示而不是静默失败
        print(f"未知命令:{command}")
        print(__doc__.strip())
        sys.exit(1)


if __name__ == "__main__":
    main()
