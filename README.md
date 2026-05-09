# 👗 Aynora — AI-Powered Outfit Recommendation System

> Bir kıyafet fotoğrafı yükle, kriterleri belirle — yapay zeka sana özel kombin önerisi sunsun.

---

## 🎯 Proje Özeti

Aynora, kullanıcıların bir kıyafet görseli yükleyerek **beden**, **renk tercihi** ve **konsept** (düğün, toplantı, özel davet, günlük vb.) kriterlerine göre kişiselleştirilmiş kombin önerileri aldığı bir yapay zeka destekli moda asistanıdır.

Proje, **Visual RAG (Retrieval-Augmented Generation)** mimarisi üzerine kuruludur:
- Yüklenen görsel **CLIP** ile embedding'e çevrilir
- **ChromaDB**'de saklanan fashion görseli arasından en benzer kombinler bulunur
- **Gemini 3 Flash** bu kombinleri yorumlayarak kullanıcıya özel, açıklamalı öneriler üretir

---

## ✨ Özellikler

- 📸 **Görsel Analiz** — Kıyafet rengi, stili ve kategorisi otomatik tespit edilir
- 🎨 **Renk Uyumu** — Renk teorisine dayalı tamamlayıcı parça önerileri
- 👔 **Parça Önerileri** — Üst / alt / ayakkabı / aksesuar kombinleri
- 📐 **Beden Filtresi** — Kullanıcının bedenine göre özelleştirme
- 🎭 **Konsept Seçimi** — Düğün / toplantı / özel davet / günlük / spor
- 🛍️ **Alışveriş Yönlendirme** — Önerilen parçaların nereden temin edilebileceği

---

## 🏗️ Mimari

```
[React Frontend]
      │
      │  görsel + beden + konsept + renk tercihi
      ▼
[FastAPI Backend]
      │
      ├──► CLIP Model
      │         └── Görseli vektöre çevir
      │
      ├──► ChromaDB
      │         └── En benzer 20 kombini getir (cosine similarity)
      │
      └──► Gemini 3 Flash
                └── RAG prompt ile kullanıcıya özel öneri üret
                      + Alışveriş yönlendirmesi ekle
```

---

## 🛠️ Tech Stack

| Katman | Teknoloji              |
|---|------------------------|
| **Frontend** | React + Tailwind CSS   |
| **Backend** | FastAPI (Python)       |
| **Görsel Embedding** | CLIP (ViT-B/32)        |
| **Vector Database** | ChromaDB               |
| **LLM** | Gemini 3 Flash         |
| **Veri Seti** | DeepFashion + Polyvore |
| **Embedding İşlemi** | Google Colab (GPU)     |

---

## 📁 Proje Yapısı

```
aynora/
├── backend/
│   ├── main.py
│   ├── routers/
│   │   └── outfit.py
│   ├── services/
│   │   ├── clip_service.py
│   │   ├── chroma_service.py
│   │   └── gemini_service.py
│   └── requirements.txt
│
├── data/
│   ├── embed_dataset.ipynb   # Colab'da bir kere çalıştırılır
│   └── chroma_db/            # Oluşturulan vector DB
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── UploadSection.jsx
    │   │   ├── FilterPanel.jsx
    │   │   └── OutfitResults.jsx
    │   └── App.jsx
    └── package.json
```

---

## 🚀 Kurulum

### Gereksinimler
- Python 3.10+
- Node.js 18+
- Google Gemini API Key

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Veri Seti & Embedding (Bir kere yapılır)

```bash
# Google Colab'da embed_dataset.ipynb dosyasını çalıştır
# Oluşan chroma_db/ klasörünü backend/data/ altına koy
```

---

## 🔑 Ortam Değişkenleri

```env
GEMINI_API_KEY=your_gemini_api_key_here
CHROMA_DB_PATH=./data/chroma_db
```

---


## 🤝 Katkı

Bu proje bir hackathon kapsamında geliştirilmektedir.

---

## 📄 Lisans

MIT