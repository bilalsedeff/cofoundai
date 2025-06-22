# Maturation Screen - Figma Import Guide

Bu klasör, "Maturation" ekranını Figma'ya aktarmanız için gereken dosyaları içerir.

## Dosyalar ve Kullanımları

1. **maturation-design-spec.json** - Tüm renk kodlarını, tipografi stillerini, komponent özelliklerini ve boyutlarını içerir.

2. **maturation-layout.svg** - Ana düzeni gösteren SVG şeması. Figma'ya direkt import edilebilir.

## Figma'ya Aktarma Adımları

### 1. Yöntem: SVG Import

1. Figma'da yeni bir dosya açın
2. File > Import > `maturation-layout.svg` dosyasını seçin
3. SVG tüm tasarım öğelerini ayrı ayrı katmanlar olarak içerecektir
4. Figma'nın "Unsupported features" uyarısı olursa "Import anyway" diyebilirsiniz

### 2. Yöntem: Tarayıcıdan Ekran Görüntüsü

1. HTML/CSS ile oluşturduğumuz sayfayı tarayıcıda açın
2. Ekran görüntüsü alın (Windows: Win+Shift+S, Mac: Cmd+Shift+4)
3. Figma'da yeni bir frame oluşturun (1400x900px)
4. Ekran görüntüsünü frame'e yapıştırın
5. Üzerine Figma bileşenleri ekleyerek etkileşimli hale getirin

### 3. Yöntem: Design Spec Kullanımı

JSON dosyasındaki tasarım özelliklerini Figma'da manuel olarak uygulayabilirsiniz:

1. Figma'da renk stilleri (Color Styles) oluşturun
   - Temel renk: #665DFF (mor)
   - İkincil renk: #FC76A1 (pembe)
   - Arkaplan renkleri: #0f0f1e, #1e1e42

2. Tipografi stilleri oluşturun:
   - Başlık: Inter/40px/Bold
   - Alt başlık: Inter/18px/Regular/Opasite 0.8
   - İçerik: Inter/14px/Regular

3. JSON dosyasındaki komponent özelliklerini ve ölçüleri referans alarak Figma komponentleri oluşturun

## Renk Paleti

- Primary: `#665DFF`
- Secondary: `#FC76A1`
- Background Dark: `#0f0f1e`
- Background Medium: `#1e1e42`
- Background Light: `rgba(30, 30, 50, 0.7)`
- Success: `#27AE60`
- Warning: `#F2C94C`
- Danger: `#EB5757`

## Gradients

- Header Gradient: `linear-gradient(90deg, #665DFF, #FC76A1)`
- Progress Bar: `linear-gradient(90deg, #665DFF, #FC76A1)`
- Background: `linear-gradient(120deg, #0f0f1e, #1e1e42)` 