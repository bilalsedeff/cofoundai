
# CoFound.ai - Local Development Guide

Bu rehber, CoFound.ai'yi tamamen yerel ortamda Docker ile çalıştırmanız için hazırlanmıştır.

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Docker ve Docker Compose
- Git

### 1. Projeyi Klonlayın
```bash
git clone https://github.com/your-username/cofoundai.git
cd cofoundai
```

### 2. Servisleri Başlatın
```bash
# Tüm servisleri build edin ve başlatın
make up

# Alternatif olarak:
docker-compose --env-file local-dev.env up -d
```

### 3. Erişim Noktaları
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000
- **API Docs:** http://localhost:5000/docs
- **Chroma Vector DB:** http://localhost:8000

## 🛠️ Geliştirme Komutları

```bash
# Logları görüntüle
make logs

# Backend container'ına shell açın
make shell

# Testleri çalıştırın
make test

# Veritabanını sıfırlayın
make reset

# Tüm servisleri durdurun
make down

# Docker kaynaklarını temizleyin
make clean
```

## 📊 Sistem Bileşenleri

### Backend (FastAPI)
- **Port:** 5000
- **Özellikler:** Agent orchestration, LLM integration, REST API
- **Test Mode:** LLM çağrıları mock'lanır, API key gerekmez

### Frontend (React)
- **Port:** 3000
- **Özellikler:** Dream input, sistem durumu, sonuç görüntüleme

### PostgreSQL Database
- **Port:** 5432
- **Kullanıcı:** cofoundai_user
- **Veritabanı:** cofoundai

### Redis Cache
- **Port:** 6379
- **Kullanım:** Session cache, queue management

### Chroma Vector DB
- **Port:** 8000
- **Kullanım:** Document embeddings, semantic search

## 🧪 Test Etme

### Sistem Durumu Kontrolü
```bash
curl http://localhost:5000/health
```

### Dream API Test
```bash
curl -X POST http://localhost:5000/api/dream \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test-user",
    "projectId": "test-project",
    "promptText": "Create a simple todo app"
  }'
```

## 🔧 Yapılandırma

### Environment Variables
`local-dev.env` dosyasında tüm yapılandırma ayarları bulunur:
- Test mode aktif (LLM_PROVIDER=test)
- Local database bağlantıları
- Development ayarları

### Database Schema
`scripts/init-db.sql` dosyasında:
- Projects tablosu
- Dreams tablosu  
- Agent interactions tablosu

## 🎯 Sonraki Adımlar

1. **LLM Entegrasyonu:** Gerçek LLM provider'larını ekleyin
2. **Agent Geliştirme:** Daha gelişmiş agent'lar ekleyin
3. **UI Geliştirme:** Frontend'i genişletin
4. **Monitoring:** Prometheus/Grafana ekleyin
5. **Production:** Deployment için optimize edin

## 🐛 Sorun Giderme

### Portlar Kullanımda
```bash
# Kullanılan portları kontrol edin
lsof -i :3000
lsof -i :5000

# Docker container'ları durdurun
docker-compose down
```

### Database Bağlantı Hatası
```bash
# PostgreSQL container'ını yeniden başlatın
docker-compose restart postgres

# Database loglarını kontrol edin
docker-compose logs postgres
```

### Build Hataları
```bash
# Önbelleği temizleyip yeniden build edin
docker-compose build --no-cache
```

## 📝 Notlar

- Bu kurulum tamamen offline çalışır
- LLM çağrıları mock'lanır, gerçek API key gerekmez
- Tüm veriler local Docker volume'larda saklanır
- Production'a geçmek için sadece environment variables değiştirin
