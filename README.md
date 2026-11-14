# GraphicalMath - Grafik Hesap Makinesi

Python + PyQt6 + pyqtgraph ile yazılmış, masaüstü grafik hesap makinesi.  
Desmos benzeri arayüz ve özelliklerle matematiğin görselleştirilmesi.

![GraphicalMath](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.12%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Özellikler

### Grafik Türleri
- **Açık fonksiyonlar**: `y = x^2`, `sin(x)`, `x^3 - 2x + 1`
- **İçsel fonksiyonlar**: `x^2 + y^2 = 1`, `y^2 = x^3 - x`
- **Kutupsal koordinatlar**: `r = sin(θ)`, `r = 2 + cos(3θ)`
- **Parametrik denklemler**: `(cos t, sin t)`, `(t^2, t^3)`
- **Noktalar**: `(1, 2)`, `(cos t, sin t)` (hareketli nokta)
- **Sliderlar**: `a = [0, 10]` → `y = a*x^2` ile interaktif kontrol

### Matematik İşlemleri (Hesap Makinesi)
- **Türev**: 1., 2., 3. ve n. derece türevler
- **İntegral**: Belirli (`∫_a^b f(x)dx`) ve belirsiz integral
- **Kök bulma**: `f(x) = 0` kökleri
- **Kesişim**: `f(x) = g(x)` kesişim noktaları
- **Ekstremum**: Minimum/maximum noktaları
- **Bükülme noktaları**: İkinci türev sıfır olan noktalar
- **Taylor serisi**: Belirli nokta etrafında seriler

### Arayüz
- **Sol panel**: İfade listesi (renk, göz, sil, kopyala, düzenle)
- **Orta**: Etkileşimli grafik (zoom, pan, hover nokta bilgisi)
- **Sağ panel**: Slider kontrolleri
- **Koyu/Açık tema**
- **Dosya kaydet/yükle** (.gmath JSON format)
- **Görüntü dışa aktar** (PNG, JPG, PDF, SVG)

## Kurulum

```bash
# Repository'yi klonlayın
git clone https://github.com/yourusername/GraphicalMath.git
cd GraphicalMath

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

## Çalıştırma

```bash
python main.py
```

## Kullanım

### İfade Girme
Sol altta bulunan giriş kutusuna ifade yazıp Enter'a basın:

```
y = x^2                    # Parabol
sin(x)                     # y = sin(x) olarak yorumlanır
x^2 + y^2 = 4              # Yarıçap 2 çember
r = 2 + cos(3*theta)       # 3 yapraklı gül
(cos(t), sin(t))           # Birim çember (parametrik)
a = [0, 5]                 # Slider: a 0-5 arası
y = a*x^2                  # Slider'ı kullanan fonksiyon
```

### Desteklenen Fonksiyonlar
| Fonksiyon | Açıklama |
|-----------|----------|
| `sin, cos, tan` | Trigonometrik |
| `asin, acos, atan` | Ters trigonometrik |
| `sinh, cosh, tanh` | Hiperbolik |
| `exp, log, ln` | Üstel ve logaritma |
| `sqrt, abs` | Kök ve mutlak değer |
| `floor, ceil, sign` | Yuvarlama ve işaret |
| `pi, e` | Sabitler |
| `^` | Üstel (Python'da `**` olarak işlenir) |

### Klavye Kısayolları
| Kısayol | İşlem |
|---------|-------|
| `Ctrl+N` | Yeni dosya |
| `Ctrl+O` | Dosya aç |
| `Ctrl+S` | Kaydet |
| `Ctrl+E` | Görüntü kaydet |
| `Ctrl+M` | Hesap makinesi |
| `Ctrl+D` | İfade kopyala |
| `Delete` | Seçili ifadeyi sil |
| `↑/↓` | İfadeler arası geçiş |
| `Ctrl+0` | Tümünü sığdır |
| `Ctrl+1` | Varsayılan görünüm |
| `Mouse Wheel` | Zoom in/out |
| `Ctrl+Wheel` | Sadece Y ekseni zoom |
| `Shift+Wheel` | Sadece X ekseni zoom |
| `Drag` | Pan (kaydırma) |

> **Not:** İfade giriş kutusu (sol alt) odaklıyken `Enter` tuşu ifadeyi ekler. Kutuyu odaklamak için `Tab` veya fare ile tıklayın.

### Hesap Makinesi
Araç çubuğundan "🧮 Hesap Makinesi" butonuna tıklayın veya `Ctrl+M` basın.

## Dosya Formatı (`.gmath`)

```json
{
  "expressions": [
    {"raw": "y = x^2", "type": "explicit_y", "color": "#FF6B6B", "visible": true, "latex": "y = x^{2}"},
    {"raw": "a = [0, 10]", "type": "slider", "color": "#4ECDC4", "visible": true, "latex": "a = [0, 10]"}
  ],
  "view": {"x_range": [-10, 10], "y_range": [-10, 10]}
}
```

## Proje Yapısı

```
GraphicalMath/
├── main.py                 # Giriş noktası
├── main_window.py          # Ana pencere (toolbar, menü, splitter layout)
├── graph_widget.py         # Grafik çizim (pyqtgraph + OpenGL)
├── expression_parser.py    # Matematik ifade ayrıştırıcı (SymPy)
├── expression_list.py      # Sol panel - ifade listesi
├── slider_widget.py        # Sağ panel - slider kontrolleri
├── calculus.py             # Türev, integral, kök, ekstremum hesaplama
├── requirements.txt        # Bağımlılıklar
├── LICENSE                 # MIT Lisansı
├── .gitignore              # Git ignore dosyası
└── README.md               # Bu dosya
```

## Teknik Detaylar

- **PyQt6**: Modern Qt binding'i
- **pyqtgraph**: OpenGL hızlandırılıklı grafik çizim
- **SymPy**: Sembolik matematik (türev, integral, çözme)
- **NumPy**: Sayısal hesaplamalar
- **mpmath**: Yüksek hassasiyetli matematik

## Geliştirme

```bash
# Geliştirme modunda çalıştırma
python main.py

# Testleri çalıştırma (gelecekte eklenecek)
pytest tests/
```

## Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Branch'inizi pushlayın (`git push origin feature/yeni-ozellik`)
5. Pull Request oluşturun

## Lisans

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

**GraphicalMath** - Matematiği görselleştirin, keşfedin, öğrenin.
