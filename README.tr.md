# FlowPy — Modern Algoritma IDE

Algoritmik akışları **sürükle-bırak düğümlerle** modelleyip anında çalıştıran, otomatik Python kodu üreten masaüstü IDE.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)]()
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-41cd52?style=flat-square)]()
[![Platform](https://img.shields.io/badge/platform-Windows-brightgreen?style=flat-square)]()
[![License](https://img.shields.io/badge/license-UNKNOWN-lightgrey?style=flat-square)](#lisans)

> 🌐 [English README →](README.en.md)

---

## İçindekiler

- [Hakkında](#hakkında)
- [Öne Çıkan Özellikler](#öne-çıkan-özellikler)
- [Ekran Görüntüleri](#ekran-görüntüleri)
- [İndirme ve Kurulum](#i̇ndirme-ve-kurulum)
- [İlk Çalıştırma Rehberi](#i̇lk-çalıştırma-rehberi)
- [Arayüz Kılavuzu](#arayüz-kılavuzu)
- [Düğüm Referansı](#düğüm-referansı)
- [Klavye Kısayolları](#klavye-kısayolları)
- [Proje Yapısı](#proje-yapısı)
- [Sık Sorulan Sorular](#sık-sorulan-sorular)
- [Sorun Giderme](#sorun-giderme)
- [Katkıda Bulunma](#katkıda-bulunma)
- [Yol Haritası](#yol-haritası)
- [Teknolojiler](#teknolojiler)
- [Destek](#destek)

---

## Hakkında

FlowPy, Python tabanlı algoritma akışlarını **grafiksel olarak** modelleyen ve çalıştıran bir masaüstü IDE'dir. Kullanıcılar düğüm paletinden blokları canvas üzerine sürükler, birbirine bağlar; FlowPy akışı yorumlar, değişkenleri canlı gösterir ve tüm akıştan Python kodu üretir.

**Kod yazmadan algoritma tasarla — tasarımından kod üret.**

---

## Öne Çıkan Özellikler

| Özellik | Açıklama |
|---------|----------|
| 🖱️ **Sürükle-bırak editör** | Düğümleri palette seçip canvas üzerinde konumlandırın |
| ▶️ **Run / Step / Stop** | Tam hızda veya adım adım yürütme; aktif düğüm vurgulanır |
| 📊 **Canlı değişken izleme** | Çalışma zamanında değişken değerleri ve sparkline grafikleri |
| ✅ **Akış doğrulama** | Geçersiz bağlantı ve eksik başlangıç düğümü tespiti |
| 💻 **Çoklu dil kodu üretimi** | Python, Java, C, C++, JavaScript ve Sözde Kod çıktısı |
| 🧩 **Zengin düğüm kütüphanesi** | Döngüler, koşullar, I/O, dosya, fonksiyon, hata yakalama, listeler |
| ↩️ **Undo / Redo** | Ctrl+Z / Ctrl+Y ile sınırsız geri/ileri alma |
| 🗺️ **Minimap, cetvel ve zoom** | Büyük akışları kolayca yönetin |
| 📄 **Çok sayfalı canvas** | Page-1, Page-2 ve **+** butonuyla sınırsız sayfa ekleyin |
| 🎨 **Stil özelleştirme** | Düğüm renkleri, opaklık ve kenarlık stilini değiştirin |
| 📦 **Hazır örnek akışlar** | FizzBuzz, Faktöriyel, Bubble Sort ve daha fazlası |
| 🔗 **Paylaşım linki** | Akışı URL üzerinden tek tıkla paylaşın |
| 📸 **Dışa aktarma** | PNG görüntüsü veya PDF rapor olarak kaydedin |
| 🧭 **Rehberli tur** | 7 adımlı interaktif arayüz turu |

---

## Ekran Görüntüleri

| Ana Ekran | File Menüsü — Örnekler |
|-----------|----------------------|
| ![Ana Ekran](../uygulama_gorselleri/1.png) | ![Örnekler Menüsü](../uygulama_gorselleri/2.png) |

| Faktöriyel Akışı | Çalışma — Girdi Diyaloğu |
|-----------------|--------------------------|
| ![Faktöriyel](../uygulama_gorselleri/3.png) | ![Girdi Diyaloğu](../uygulama_gorselleri/4.png) |

| Kod Üretimi | Düğüm Düzenleme |
|-------------|-----------------|
| ![Kod Üretimi](../uygulama_gorselleri/5.png) | ![Düğüm Düzenle](../uygulama_gorselleri/6.png) |

---

## İndirme ve Kurulum

### GitHub Releases üzerinden kurulum

1. [Releases](https://github.com/flowpy-ide/FlowPy/releases/tag/v1.0.0) sayfasını açın.
2. En son sürümü indirin: `FlowPy.exe` veya `FlowPy-win64.zip`.
3. ZIP indirdiyseniz içeriğini çıkartın.
4. `FlowPy.exe` dosyasını çalıştırın.
5. Windows SmartScreen uyarısı çıkarsa **"Daha fazla bilgi" → "Yine de çalıştır"** seçin.

> `.exe` dağıtımı kullanıyorsanız Python kurulumu **gerekmez**.

### Kaynak koddan çalıştırma

**Gereksinimler:** Python 3.10+, pip

```powershell
cd C:\yedekler\Flow-py\FlowPy
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

---

## İlk Çalıştırma Rehberi

1. Uygulamayı başlatın — açılış karşılama ekranı görünür.
2. **"Örnek Akış ile Başla"** veya **"Boş Canvas ile Başla"** seçin.
3. **Rehberli tur** başlarsa (7 adım) arayüzü keşfedin veya "Turu Geç" ile atlayın.
4. Sol panelden bir **Başlangıç** düğümünü canvas'a sürükleyin.
5. Düğümleri ekleyip **portlarını birbirine bağlayın** (çıkış portunu giriş portuna sürükleyin).
6. Düğüme **çift tıklayarak** özelliklerini düzenleyin.
7. **Run All** ile akışı çalıştırın veya **Step** ile adım adım ilerleyin.
8. Konsol panelinde çıktıyı, sağ panelde üretilen kodu izleyin.
9. `Dosya > Kaydet (Ctrl+S)` ile `.flowpy` dosyası olarak kaydedin.

---

## Arayüz Kılavuzu

### Araç Çubuğu

| Buton | Kısayol | İşlev |
|-------|---------|-------|
| **Run All** | — | Akışı baştan sona çalıştırır |
| **Step** | — | Bir sonraki düğümü yürütür |
| **Stop** | — | Çalışan akışı durdurur |
| **Hız kaydırıcısı** | — | "Çabuk" modunda animasyonlar atlanır |

### Düğüm Paleti (Sol Panel)

Düğümleri canvas'a eklemek için iki yöntem:
- **Sürükle & bırak** — palette düğüme tıklayıp canvas'a sürükleyin
- **Çift tıklama** — düğüm canvas merkezine eklenir

Üstteki arama kutusuyla düğümleri filtreleyin.

### Canvas

- **Pan modu** — alt çubuktaki `··` butonunu etkinleştirin, sonra canvas'ı sürükleyin
- **Zoom** — `−` / `+` butonları veya `Ctrl + fare tekerleği`
- **Çoklu seçim** — boş alana tıklayıp dikdörtgen çizin
- **Cetvel** — yatay/dikey koordinat cetvelleri kılavuz sağlar
- **Minimap** — sağ alt köşede küçük akış önizlemesi; büyük akışlarda yön bulmayı kolaylaştırır

### Çok Sayfalı Canvas

Alt çubukta **Page-1**, **Page-2** ve **+** butonu bulunur.

- **+** butonuna her tıklamada yeni bağımsız bir sayfa (Page-3, Page-4, …) eklenir
- Her sayfa kendi akışını ve canvas durumunu bağımsız saklar
- Sayfa geçişi tek tıkla, geçerli akış otomatik korunur

### Denetçi Paneli (Sağ Panel)

| Sekme | İçerik |
|-------|--------|
| **Özellikler** | Seçili düğümün türü, ID ve property değerleri; stil düzenleme |
| **Değişkenler** | Çalışma sırasında anlık değişken tablosu ve sparkline grafikler |
| **Kod** | Akıştan üretilen Python / Sözde Kod — Kopyala / Dışa Aktar butonları |

### Edit Menüsü

| Eylem | Kısayol | Açıklama |
|-------|---------|----------|
| Undo | Ctrl+Z | Son değişikliği geri al |
| Redo | Ctrl+Y | Geri alınanı yeniden uygula |
| Kopyala | Ctrl+C | Seçili düğümleri panoya kopyala |
| Yapıştır | Ctrl+V | Panodaki düğümleri yapıştır |
| Çoğalt | Ctrl+D | Seçili düğümleri kopyalayıp hemen yapıştır |
| Hizala > Yatay | — | Seçili düğümleri yatay eksende hizala |
| Hizala > Dikey | — | Seçili düğümleri dikey eksende hizala |
| Hizala > Izgara | — | Seçili düğümleri ızgara düzenine otomatik yerleştir |

### File Menüsü

| Eylem | Kısayol | Açıklama |
|-------|---------|----------|
| Kaydet | Ctrl+S | `.flowpy` veya `.json` formatında kaydet |
| Aç | Ctrl+O | Kayıtlı akış dosyasını yükle |
| Flow Görüntüsü Dışa Aktar | Ctrl+Shift+E | Canvas'ı PNG görüntüsü olarak kaydet |
| PDF Rapor Dışa Aktar | Ctrl+Shift+P | Akış + kod içeren PDF raporu oluştur |
| Paylaşım Linki Oluştur | Ctrl+Shift+L | Akışı URL üzerinden paylaş |
| Linkten Aç | — | Paylaşım URL'sini yapıştırarak yükle |

---

## Düğüm Referansı

### Temel

| Düğüm | Açıklama |
|-------|----------|
| **Başlangıç** | Akışın tek ve zorunlu başlangıç noktası |
| **İşlem** | Herhangi bir Python ifadesi veya değişken ataması |
| **Karar** | `if / elif / else` dallanma; True ve False çıkış portları |
| **Durdur** | Akışı o noktada sonlandırır |
| **Yorum** | Kod üretmez; canvas'a not eklemek için kullanılır |

### Veri & Değişken

| Düğüm | Açıklama |
|-------|----------|
| **Değişken** | Değişkene değer atar (`x = 5`) |
| **Matematik** | Matematiksel ifade hesaplar |
| **Metin İşlemi** | String birleştirme, bölme, biçimlendirme |
| **Tip Dönüşümü** | `int()`, `float()`, `str()` vb. dönüşümler |
| **Liste İşlemi** | Liste oluşturma, `append`, `remove`, dilimleme |

### Akış Kontrolü

| Düğüm | Açıklama |
|-------|----------|
| **While Döngüsü** | Koşul sağlandığı sürece döner; Loop ve Exit portları |
| **For Döngüsü** | Sayaç aralığı döngüsü; Loop ve Exit portları |
| **If / Elif / Else** | Çok dallı koşullu akış |
| **Break** | En yakın döngüyü anında bitirir |
| **Continue** | Geçerli iterasyonu atlayıp devam eder |
| **Try / Except** | Hata yakalama bloğu; Try ve Except portları |
| **Switch / Match** | Python 3.10+ `match-case` yapısı |

### G/Ç (Giriş / Çıkış)

| Düğüm | Açıklama |
|-------|----------|
| **Girdi** | `input()` ile kullanıcıdan değer alır; çalışırken diyalog açılır |
| **Çıktı** | Değişken veya ifadeyi ekrana yazar |
| **Yazdır** | Formatlı metin çıktısı (`print`) |
| **Dosya Oku** | Dosyadan veri okur, değişkene atar |
| **Dosya Yaz** | Değişkeni veya metni dosyaya yazar |
| **Rastgele** | `random` modülü ile rastgele sayı üretir |

### Fonksiyon

| Düğüm | Açıklama |
|-------|----------|
| **Fonksiyon** | `def` ile fonksiyon tanımlar; **＋ Parametre Ekle** ile dinamik parametre satırları eklenir, **×** ile silinir |
| **Return** | Fonksiyondan değer döndürür |

> **Fonksiyon Parametreleri:** Düğümü çift tıkladığınızda her parametre ayrı bir satırda görünür.
> `＋ Parametre Ekle` → yeni satır açılır. `×` → o parametre kaldırılır.
> Kaydedilince `a, b, c` formatında saklanır → `def fonksiyon_adi(a, b, c):`

---

## Klavye Kısayolları

| Kısayol | İşlev |
|---------|-------|
| `Ctrl+S` | Kaydet |
| `Ctrl+O` | Aç |
| `Ctrl+Z` | Geri al |
| `Ctrl+Y` | İleri al |
| `Ctrl+C` | Seçili düğümleri kopyala |
| `Ctrl+V` | Yapıştır |
| `Ctrl+D` | Seçili düğümleri çoğalt |
| `Ctrl+Shift+E` | Canvas görüntüsünü PNG olarak dışa aktar |
| `Ctrl+Shift+P` | PDF rapor oluştur |
| `Ctrl+Shift+L` | Paylaşım linki oluştur |
| `Ctrl++` | Yakınlaştır |
| `Ctrl+-` | Uzaklaştır |
| `Delete` / `Backspace` | Seçili düğüm ve bağlantıları sil |
| Çift tıklama | Düğüm düzenleme penceresini aç |
| Sürükle & bırak | Paletten canvas'a düğüm ekle |

---

## Proje Yapısı

```
FlowPy/
├── main.py                   # Ana giriş noktası ve MainWindow
├── requirements.txt          # Python bağımlılıkları
├── core/
│   ├── interpreter.py        # Akış yorumlayıcı (çalıştırıcı)
│   ├── generator.py          # Çoklu dil kod üreteci
│   ├── validator.py          # Akış doğrulama motoru
│   ├── serializer.py         # .flowpy kayıt / yükleme
│   ├── templates.py          # Hazır örnek akış şablonları
│   ├── undo.py               # Undo / Redo yöneticisi
│   ├── registry.py           # Düğüm kayıt defteri
│   ├── settings_manager.py   # Uygulama ayarları
│   ├── node_visuals.py       # Düğüm görsel stilleri
│   ├── i18n.py               # Çoklu dil desteği (TR / EN)
│   ├── i18n_nodes.py         # Düğüm etiket çevirileri
│   ├── i18n_node_docs.py     # Düğüm dokümantasyon metinleri
│   └── syntax_highlighter.py # Kod sekmesi sözdizimi vurgulama
├── models/
│   ├── node.py               # Düğüm veri modeli
│   └── edge.py               # Kenar (bağlantı) veri modeli
├── views/
│   ├── mainwindow.ui         # Qt Designer arayüz tanımı
│   ├── canvas.py             # Flow canvas sahnesi
│   ├── node_editor_dialog.py # Düğüm düzenleme diyaloğu
│   ├── settings_dialog.py    # Ayarlar penceresi
│   ├── welcome_screen.py     # Açılış karşılama ekranı
│   ├── guided_tour.py        # 7 adımlı rehberli tur
│   ├── minimap.py            # Minimap widget
│   ├── variable_chart.py     # Değişken sparkline grafikleri
│   └── node_tooltip.py       # Düğüm ipucu balonu
├── created_flows/            # Hazır .flowpy örnek akışlar
└── docs/                     # Belgeler ve tasarım dosyaları
```

---

## Sistem Gereksinimleri

| Gereksinim | Detay |
|------------|-------|
| İşletim sistemi | Windows 10 / 11 (64-bit) |
| RAM | 4 GB önerilir |
| Disk | 200 MB boş alan |
| Python | 3.10+ (kaynak koddan çalıştırma için) |
| Bağımlılık | PyQt6 (kaynak koddan çalıştırma için) |

---

## Sık Sorulan Sorular

**Akışım çalışmıyor, ne yapmalıyım?**
- Canvas'ta bir **Başlangıç** düğümü olduğundan emin olun.
- Tüm düğümlerin birbirine bağlı olduğunu kontrol edin; bağlantısız düğümler atlanır.
- Konsol panelindeki hata mesajını okuyun; düğüm ID'si sorunu gösterir.

**Birden fazla sayfa nasıl eklerim?**
Alt çubuktaki **+** butonuna tıklayın. Her sayfa bağımsız bir canvas ve akış içerir. Sayfa sayısında sınır yoktur.

**Fonksiyon düğümüne birden fazla parametre nasıl eklenir?**
Fonksiyon düğümünü çift tıklayın. Düzenleme penceresinde **＋ Parametre Ekle** butonuyla istediğiniz kadar parametre satırı açın. Her satıra parametre adını yazın, `×` ile silin.

**Windows SmartScreen uyarısı alırsam?**
"Daha fazla bilgi" → "Yine de çalıştır" seçin. Alternatif: `.exe` üzerinde sağ tıklayın → Özellikler → Engellemeyi kaldır.

**Üretilen kodu nasıl alırım?**
Sağ panelde **Denetçi > Kod** sekmesini açın. **Kopyala** ile panoya alın veya **Dışa Aktar** ile `.py` dosyası oluşturun.

**Akışı nasıl paylaşabilirim?**
`Dosya > Paylaşım Linki Oluştur (Ctrl+Shift+L)` ile URL oluşturun. Karşı taraf bağlantıyı `Dosya > Linkten Aç` ile yükleyebilir.

**Rehberli turu tekrar başlatabilir miyim?**
Evet, **View** menüsünden rehberli turu istediğiniz zaman yeniden başlatabilirsiniz.

---

## Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| Uygulama açılmıyor | Python 3.10+ ve PyQt6 kurulduğundan emin olun |
| Eksik bağımlılık hatası | `pip install -r requirements.txt` çalıştırın |
| Kaydetme hatası | Uygulamayı yazma izni olan bir klasörden çalıştırın |
| Akış yüklenmiyor | `.flowpy` dosyası bozulmuş olabilir; `created_flows/` içindeki örneği deneyin |
| SmartScreen engeli | `.exe` → sağ tıklayın → Özellikler → Engellemeyi kaldır |
| Konsol çıktısı yok | Başlangıç düğümü mevcut mu? Tüm düğümler bağlı mı? |

---

## Katkıda Bulunma

1. Depoyu fork edin.
2. Yeni dal açın: `git checkout -b feature/<kısa-açıklama>`
3. Değişikliklerinizi commitleyin.
4. Pull request gönderin.

Mevcut `core/` → `models/` → `views/` mimarisine ve TR/EN dil desteğine (`core/i18n*.py`) uyun.

---

## Yol Haritası

- [ ] Windows için otomatik GitHub Releases paketleme
- [ ] macOS / Linux desteği
- [ ] `.flowpy` sürümleme ve import/export geliştirmeleri
- [ ] Eklenti desteği ve özel düğüm şablonları
- [ ] Gerçek zamanlı işbirliği (multiplayer flow editing)

---

## Teknolojiler

- **Python 3.10+**
- **PyQt6** — Qt tabanlı masaüstü arayüz
- **Qt Designer** — `.ui` tabanlı arayüz tanımı
- Görsel akış sahnesi, undo/redo, canlı değişken izleme
- Çoklu dil kodu üretimi: Python, Java, C, C++, JavaScript, Sözde Kod

---

## Lisans

Bu depo henüz bir `LICENSE` dosyası içermemektedir. Resmi dağıtımdan önce uygun bir açık kaynak lisansı ekleyin.

---

## Destek

- 🐛 **Hata & özellik talebi:** `https://github.com/<ORG>/<REPO>/issues`
- 👤 **Proje sahipleri:** Erkan TURGUT, Aslı AYDIN
- 📦 **Sürüm notları:** GitHub Releases sayfası
