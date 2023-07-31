from os import scandir
from pathlib import Path

from ._logger import rootLogger as logger


def scan_folder(path: Path, dfs: bool = True):
    """快速扫描指定 `path` 下文件"""
    folder = [str(path.resolve(strict=True))]
    file: list[str] = list()
    while folder:
        now = folder.pop(0)
        logger.info(f"正在遍历 {now}.")
        with scandir(now) as dir:
            for it in dir:
                if it.is_file():
                    file.append(it.path)
                elif dfs:
                    folder.append(it.path)
    return file
