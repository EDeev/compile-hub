"""Реестр языков. Как собирать и запускать — решает воркер (worker/…/toolchains.py); здесь — то, что
нужно всем: id, название, расширения файлов, шаблон нового файла.

Включён ли язык, определяют живые воркеры: каждый в сердцебиении (`WorkerInfo`) сообщает версии
тулчейнов, которые у него включены (`WORKER_LANGUAGES`). Сохранять файлы можно на любом языке из реестра.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    id: str
    name: str
    extensions: tuple[str, ...]
    template: str


LANGUAGES: dict[str, Language] = {
    lang.id: lang
    for lang in (
        Language(
            "cpp",
            "C++",
            ("cpp", "cc", "cxx"),
            '#include <iostream>\n\nint main() {\n    std::cout << "Hello, world!" << std::endl;\n    return 0;\n}\n',
        ),
        Language(
            "c",
            "C",
            ("c",),
            '#include <stdio.h>\n\nint main(void) {\n    printf("Hello, world!\\n");\n    return 0;\n}\n',
        ),
        Language("python", "Python", ("py",), 'print("Hello, world!")\n'),
        Language("javascript", "JavaScript", ("js",), 'console.log("Hello, world!");\n'),
        Language(
            "go",
            "Go",
            ("go",),
            'package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello, world!")\n}\n',
        ),
        Language(
            "java",
            "Java",
            ("java",),
            "public class Main {\n    public static void main(String[] args) {\n"
            '        System.out.println("Hello, world!");\n    }\n}\n',
        ),
    )
}

BY_EXTENSION: dict[str, str] = {ext: lang.id for lang in LANGUAGES.values() for ext in lang.extensions}


def by_filename(name: str) -> str | None:
    _, dot, ext = name.rpartition(".")
    return BY_EXTENSION.get(ext.lower()) if dot else None
