from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, Iterable
import regex as re


def regex_info(text: Iterable[str], patt: Iterable[str]):
    """根据所给 `patt` 并行进行正则匹配"""
    res: list[tuple[str, list[Future[re.Match[str] | None]]]] = list()
    with ThreadPoolExecutor() as exec:
        for i in text:
            r = [exec.submit(re.search, j, i, concurrent=True) for j in patt]
            res.append((i, r))
    return res


def regex_filter(
    text: Iterable[str],
    patt: Iterable[str],
    func: Callable[[list[str | None]], bool],
):
    """返回迭代器, 迭代结果为 `true` 的 text elem"""
    res = regex_info(text, patt)
    for i in res:
        _r = [j.result() if j.result() is not None else None for j in i[1]]
        _r = [j.group() if j is not None else None for j in _r]
        if func(_r):
            yield i[0]
