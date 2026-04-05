# FlowPy

FlowPy, akış diyagramları tabanlı algoritma geliştirme için modern bir IDE'dir. PyQt6 kullanılarak geliştirilmiş ve sürükle-bırak düğüm tabanlı grafik arayüz ile akış çizimi, çalıştırma, adım adım izleme, kod üretme ve değişken takibi gibi özellikler sunar.

## Özellikler

- Düğüm tabanlı akış diyagramı oluşturma
- Akışı çalıştırma, adım adım yürütme ve durdurma
- Kod üretimi için canlı önizleme
- Değişken tablosu ile çalışma zamanı verilerini izleme
- Undo / redo geçmiş desteği
- Farklı node kategorileri ve renk özelleştirmesi

## Gereksinimler

- Python 3.10+ (3.11 önerilir)
- PyQt6

## Kurulum

1. Depoyu klonlayın veya indirin.
2. Terminal veya PowerShell içinde proje klasörüne gidin:

```powershell
cd indirdiginiz klasör
```

3. Sanal bir ortam oluşturun (önerilir):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

4. Gereksinimleri yükleyin:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Çalıştırma

Aşağıdaki komutla uygulamayı başlatabilirsiniz:

```powershell
python main.py
```

## Proje Yapısı

- `main.py` — Uygulamanın ana giriş noktası, UI ve uygulama bağlantılarını kurar.
- `requirements.txt` — Proje bağımlılıkları.
- `core/` — İş mantığı, yorumlayıcı, kod üretimi, seri hale getirme, geri alma/yeniden alma, syntax vurgulama ve doğrulama.
- `models/` — Node ve edge modelleri.
- `views/` — UI bileşenleri, canvas sahnesi ve Qt arayüz dosyası.
- `created_flows/` — Örnek .flowpy akış dosyaları.

## Geliştirme Notları

- UI dosyası `views/mainwindow.ui` içerisinde saklanır.
- `core/interpreter.py` kod yürütme mantığını yönetir.
- `core/generator.py` akıştan kod üretir.
- `views/canvas.py` grafik sahne ve kullanıcı etkileşimlerini tanımlar.

## Test ve Geliştirme Tavsiyesi

- Yeni bağımlılık eklediğinizde `requirements.txt` dosyasını güncelleyin.
- UI değişiklikleri yaparken `mainwindow.ui` dosyasını Qt Designer ile düzenlemek daha kolaydır.
- Kodda yeni node türleri eklemek için `core/registry.py` ve `models/node.py` incelenmelidir.

