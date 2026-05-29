# core/syntax_highlighter.py
# ──────────────────────────────────────────────────────────────────────
# Çok dilli sözdizimi renklendiricisi
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression

LANG_KEYWORDS = {
    "Python": [
        "def", "return", "if", "elif", "else", "while", "for", "in", "range",
        "import", "from", "as", "lambda", "assert", "break", "continue",
        "try", "except", "class", "True", "False", "None", "and", "or", "not",
        "print", "input", "len", "int", "float", "str", "bool", "list", "sorted",
        "match", "case", "with", "open",
    ],
    "Java": [
        "public", "private", "static", "void", "int", "double", "String", "boolean",
        "if", "else", "while", "for", "return", "new", "class", "import",
        "System", "out", "println", "scanner", "Scanner", "break", "continue",
        "true", "false", "var",
    ],
    "C": [
        "int", "float", "char", "void", "if", "else", "while", "for", "return",
        "include", "stdio", "printf", "scanf", "break", "continue", "struct", "typedef",
    ],
    "C++": [
        "int", "double", "string", "bool", "void", "auto", "if", "else", "while", "for",
        "return", "include", "cout", "cin", "endl", "break", "continue",
        "vector", "sort", "swap", "namespace", "using", "class",
    ],
    "JavaScript": [
        "let", "const", "var", "function", "if", "else", "while", "for", "return",
        "console", "log", "prompt", "break", "continue", "true", "false", "null",
        "undefined", "typeof", "new", "class", "import", "export",
    ],
    "Pseudocode": [
        "BAŞLA", "BİTİR", "EĞER", "İSE", "DEĞİLSE", "DÖNGÜ", "DÖNGÜDEN", "SONU",
        "TANIMLA", "OKU", "YAZDIR", "ÇIKTI", "İŞLEM", "DÖNÜŞ", "FONKSİYON",
        "SIRALA", "ARA", "GEÇİCİ", "DUR", "ATLA",
    ],
}


class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self._lang = "Python"
        self._keywords: list[str] = LANG_KEYWORDS["Python"]
        self._build_rules()

    def set_language(self, lang: str):
        self._lang = lang
        self._keywords = LANG_KEYWORDS.get(lang, LANG_KEYWORDS["Python"])
        self._build_rules()
        self.rehighlight()

    def _build_rules(self):
        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#cc7832"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        type_format = QTextCharFormat()
        type_format.setForeground(QColor("#569cd6"))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#6a8759"))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080"))
        comment_format.setFontItalic(True)

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#6897bb"))

        for word in self._keywords:
            if word.replace("_", "").isalnum():
                pattern = QRegularExpression(rf"\b{QRegularExpression.escape(word)}\b")
            else:
                pattern = QRegularExpression(QRegularExpression.escape(word))
            self.highlighting_rules.append((pattern, keyword_format))

        for t in ["True", "False", "None", "print", "input", "eval"]:
            pattern = QRegularExpression(rf"\b{t}\b")
            self.highlighting_rules.append((pattern, type_format))

        self.highlighting_rules.append((QRegularExpression(r"\".*\""), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*'"), string_format))
        self.highlighting_rules.append((QRegularExpression(r"\b\d+\b"), number_format))
        self.highlighting_rules.append((QRegularExpression(r"//[^\n]*"), comment_format))
        self.highlighting_rules.append((QRegularExpression(r"#[^\n]*"), comment_format))
        self.highlighting_rules.append((QRegularExpression(r"/\*.*\*/"), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
