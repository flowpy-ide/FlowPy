# core/syntax_highlighter.py
# ──────────────────────────────────────────────────────────────────────
# C, Java, Python ve Pseudocode için basit sözdizimi renklendiricisi
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression

class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.highlighting_rules = []

        # ── Ortak Formatlar ──────────────────────────────────────────
        
        # Anahtar Kelimeler (Keywords)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#cc7832")) # IntelliJ Turuncu / Kahve
        keyword_format.setFontWeight(QFont.Weight.Bold)

        # Built-in / Tipler
        type_format = QTextCharFormat()
        type_format.setForeground(QColor("#569cd6")) # VS Code Mavi
        
        # String
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#6a8759")) # Yeşil
        
        # Yorum (Comment)
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080")) # Gri
        comment_format.setFontItalic(True)
        
        # Sayılar (Numbers)
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#6897bb")) # Açık mavi / camgöbeği

        # ── Kurallar ───────────────────────────────────────────────
        
        keywords = [
            "def", "class", "if", "else", "elif", "while", "for", "in", 
            "return", "print", "pass", "import", "from", "as",
            "public", "static", "void", "main", "System.out.println",
            "include", "int", "float", "double", "char", "String", "boolean",
            # Pseudocode için
            "BAŞLA", "BİTİR", "İŞLEM YAP:", "KULLANICIDAN OKU", "EKRANA YAZDIR:",
            "EĞER", "İSE:", "DEĞİLSE:", "EĞER BİTİR", "DÖNGÜ SÜRDÜKÇE", "DÖNGÜ BİTİR",
            "SAYAÇ DÖNGÜSÜ:", "SAYAÇ BİTİR", "FONKSİYON TANIMLA:", "GERİ DÖNDÜR:"
        ]

        for word in keywords:
            # Word border \b kelime kuralları
            # Python/Java/C için tam eşleşme
            # Türkçe Pseudocode için alfabe farklılıklarından dolayı b bazen patlayabilir,
            # bu yüzden pattern'i basitleştiriyoruz
            if word.isalpha() or word in ("def", "if", "else", "for", "while", "return", "int", "void"):
                pattern = QRegularExpression(rf"\b{word}\b")
            else:
                pattern = QRegularExpression(word) # Noktalama barındıranlar
            
            self.highlighting_rules.append((pattern, keyword_format))

        # Tipler ve Built-in'ler
        types = ["True", "False", "None", "print", "input", "eval"]
        for t in types:
            pattern = QRegularExpression(rf"\b{t}\b")
            self.highlighting_rules.append((pattern, type_format))

        # Çift Tırnak String
        self.highlighting_rules.append((QRegularExpression(r"\".*\""), string_format))
        # Tek Tırnak String
        self.highlighting_rules.append((QRegularExpression(r"'.*'"), string_format))

        # Sayılar (\b\d+\b)
        self.highlighting_rules.append((QRegularExpression(r"\b\d+\b"), number_format))

        # Yorum Satırları (// veya #)
        self.highlighting_rules.append((QRegularExpression(r"//[^\n]*"), comment_format))
        self.highlighting_rules.append((QRegularExpression(r"#[^\n]*"), comment_format))
        
        # Multi-line comment (/* ... */) için QTextDocument block durumu kullanmamız lazım ama 
        # C/Java jeneratörümüzde basitçe tek blokta veya satır satır olduğu için bunu regex ile yapalım
        self.highlighting_rules.append((QRegularExpression(r"/\*.*\*/"), comment_format))


    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
