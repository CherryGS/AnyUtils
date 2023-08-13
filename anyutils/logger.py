import logging
import os
from datetime import date
from logging import LogRecord
from pathlib import Path
from types import ModuleType, TracebackType
from typing import Any, Callable, Iterable, Type

from rich.console import Console, ConsoleRenderable
from rich.logging import RichHandler
from rich.traceback import LOCALS_MAX_LENGTH, LOCALS_MAX_STRING, Traceback

# from AzurlaneAutoScript , thx
console_formatter = logging.Formatter(
    fmt="%(asctime)s.%(msecs)03d │ %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
file_formatter = logging.Formatter(
    fmt="%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_console = Console(record=True)


class RichCustomHandler(RichHandler):
    """用来适配上面的 `formatter` 特制的"""

    def __init__(
        self,
        level: int | str = logging.NOTSET,
    ) -> None:
        super().__init__(
            level,
            show_time=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )


class RichRecordHandler(RichHandler):
    """
    用来进行主进程中的控制台输出和记录
    """

    def __init__(
        self,
        level: int | str = logging.NOTSET,
    ) -> None:
        super().__init__(
            level,
            console=_console,
            show_time=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )


class RichCallbackHandler(RichHandler):
    """
    用来进行子进程中 log 的传递
    简单的将原代码中 `emit` 部分的直接输出变成以 `log_renderable` 为参数的 `callback` 调用, 大概是不支持 `jupter` 了
    """

    def __init__(
        self,
        level: int | str = logging.NOTSET,
        console: Console | None = None,
        *,
        callback: Callable[[ConsoleRenderable], Any],
    ) -> None:
        """
        callback : 回调函数 , 在 `emit` 最后获取到拼接好的 log 后执行 , 要求瞬间完成 , 否则会阻塞函数
        对于 `Queue` 可以考虑使用 `put_nowait`
        ! 此处的代码尤其是参数是基于 `RichHandler` 的方法修改而得到 , 可能会因原代码的微小改变而失效 .
        """
        self.callback = callback
        super().__init__(
            level,
            console,
        )

    def emit(self, record: LogRecord) -> None:
        """
        由 `logging` 模块自动调用
        ! 此处的代码是基于 `RichHandler` 的方法修改而得到 , 可能会因原代码的微小改变而失效 .
        """
        message = self.format(record)
        traceback = None
        if (
            self.rich_tracebacks
            and record.exc_info
            and record.exc_info != (None, None, None)
        ):
            exc_type, exc_value, exc_traceback = record.exc_info
            assert exc_type is not None
            assert exc_value is not None
            traceback = Traceback.from_exception(
                exc_type,
                exc_value,
                exc_traceback,
                width=self.tracebacks_width,
                extra_lines=self.tracebacks_extra_lines,
                theme=self.tracebacks_theme,
                word_wrap=self.tracebacks_word_wrap,
                show_locals=self.tracebacks_show_locals,
                locals_max_length=self.locals_max_length,
                locals_max_string=self.locals_max_string,
                suppress=self.tracebacks_suppress,
            )
            message = record.getMessage()
            if self.formatter:
                record.message = record.getMessage()
                formatter = self.formatter
                if hasattr(formatter, "usesTime") and formatter.usesTime():
                    record.asctime = formatter.formatTime(record, formatter.datefmt)
                message = formatter.formatMessage(record)

        message_renderable = self.render_message(record, message)
        log_renderable = self.render(
            record=record, traceback=traceback, message_renderable=message_renderable
        )

        try:
            # * 调用 callback
            self.callback(log_renderable)
        except Exception:
            self.handleError(record)


class RichFileHandler(RichHandler):
    """
    用来进行文件的写入
    `RichHandler` 本身并没有有关文件的设置 , 重定向到文件需要一个设定了文件输出的 `Console` 作为 console 参数传入
    """

    def __init__(
        self,
        level: int | str = logging.NOTSET,
        console: Console | None = None,
        **kwargs,
    ) -> None:
        assert (
            console and console._file is not None
        ), "文件 `RichHandler` 需要设置了 `file` 属性的 `Console` 实例"
        super().__init__(
            level,
            console,
            show_time=False,
            show_level=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            **kwargs,
        )

    @classmethod
    def quick(cls, log_path: Path, cycle: int = 0):
        """
        快速创建一个 FileHandler , console 应该不会被 gc 干掉的吧
        """
        if cycle <= 0:
            log = log_path / f"{date.today()}_main_0.log"
        else:
            log = log_path
            for i in range(cycle):
                log = log_path / f"{date.today()}_main_{i}.log"
                if os.path.getsize(log) / 1024 / 1024 < 10:
                    break
            if os.path.getsize(log) / 1024 / 1024 < 10:
                log = log_path / f"{date.today()}_main_{0}.log"
                os.remove(log)
        f = open(log, "a+", encoding="utf8")
        console = Console(file=f)
        return cls(console=console)


def hook_exception(
    *,
    callback: Callable[[Traceback], Any],
    console: Console | None = None,
    width: int | None = 100,
    extra_lines: int = 3,
    theme: str | None = None,
    word_wrap: bool = False,
    show_locals: bool = False,
    locals_max_length: int = LOCALS_MAX_LENGTH,
    locals_max_string: int = LOCALS_MAX_STRING,
    locals_hide_dunder: bool = True,
    locals_hide_sunder: bool | None = None,
    indent_guides: bool = True,
    suppress: Iterable[str | ModuleType] = (),
    max_frames: int = 100,
) -> Callable[[Type[BaseException], BaseException, TracebackType | None], Any]:
    """
    hook 未捕获异常并调用 callback
    ! 此处的代码是基于 `rich.traceback` 中的 `install` 修改而得到 , 可能会因原代码的微小改变而失效 .
    """
    traceback_console = Console(stderr=True) if console is None else console

    locals_hide_sunder = (
        True
        if (traceback_console.is_jupyter and locals_hide_sunder is None)
        else locals_hide_sunder
    )

    def excepthook(
        type_: Type[BaseException],
        value: BaseException,
        traceback: TracebackType | None,
    ) -> None:
        renderable = Traceback.from_exception(
            type_,
            value,
            traceback,
            width=width,
            extra_lines=extra_lines,
            theme=theme,
            word_wrap=word_wrap,
            show_locals=show_locals,
            locals_max_length=locals_max_length,
            locals_max_string=locals_max_string,
            locals_hide_dunder=locals_hide_dunder,
            locals_hide_sunder=bool(locals_hide_sunder),
            indent_guides=indent_guides,
            suppress=suppress,
            max_frames=max_frames,
        )
        try:
            callback(renderable)
            sys.__excepthook__(type_, value, traceback)
        except Exception:
            info = sys.exc_info()
            sys.__excepthook__(info[0], info[1], info[2])  # type: ignore

    import sys

    old_excepthook = sys.excepthook
    sys.excepthook = excepthook
    return old_excepthook


def get_env_logger_info():
    debug = os.environ.get("DEBUG")
    if debug is None:
        return logging.INFO
    if debug.lower() in ["debug", "dbg", "1", 1, "true", True]:
        return logging.DEBUG
    else:
        return logging.INFO


def get_rich_logger(name: str = ""):
    """初始化一个配备了 `RichHandler` 且 level 为环境变量 `debug` 的 logger"""
    logger = logging.getLogger(name)
    hdlr = RichCustomHandler(get_env_logger_info())
    hdlr.setFormatter(console_formatter)
    logger.addHandler(hdlr)
    return logger
