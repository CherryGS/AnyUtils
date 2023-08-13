from os import DirEntry, scandir
from pathlib import Path

from ._logger import rootLogger as logger


def scan_folder(path: Path, dfs: bool = True):
    """快速扫描指定 `path` 下文件, 如果 `path` 是文件则扫描文件所在目录."""
    if path.is_file():
        path = path.parent
    folder = [str(path.resolve(strict=True))]
    file: list[DirEntry[str]] = list()
    while folder:
        now = folder.pop(0)
        logger.info(f"正在遍历 '{now}'.")
        with scandir(now) as dir:
            for it in dir:
                if it.is_file():
                    file.append(it)
                elif dfs:
                    folder.append(it.path)
    return file
