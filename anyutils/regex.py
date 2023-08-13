from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, Iterable

import regex as re


def regex_info(text: Iterable[str], patt: Iterable[str]):
    """根据所给 `patt` 并行进行正则匹配"""
    ress: list[list[Future[re.Match[str] | None]]] = list()
    res: list[list[str | None]] = list()
    with ThreadPoolExecutor() as exec:
        for i in text:
            r = [exec.submit(re.search, j, i, concurrent=True) for j in patt]
            ress.append(r)
    res = [[None if j.result() is None else j.result().group() for j in i] for i in ress] # type: ignore
    return res


def regex_filter(
    text: Iterable[str],
    patt: Iterable[str],
    func: Callable[[list[str | None]], bool],
):
    """返回迭代结果为 `true` 的 text elem"""
    res = regex_info(text, patt)
    _r: list[tuple[int, str]] = list()
    for i, j in zip(enumerate(res), text):
        if func(i[1]):
            _r.append((i[0], j))
    return _r
