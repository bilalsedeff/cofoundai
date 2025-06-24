# CoFound.ai Free Alternatives Guide

## Mevcut GCP Servisleri vs Free Alternatifler

| GCP Servisi | Aylık Maliyet | Free Alternatif | Geçiş Kolaylığı |
|-------------|---------------|-----------------|-----------------|
| **Cloud SQL PostgreSQL** | ~$25-50 | PlanetScale, Neon, Supabase | ✅ Kolay |
| **Redis** | ~$15-30 | Upstash Redis, Railway | ✅ Kolay |
| **Cloud Storage** | ~$5-10 | Cloudflare R2, AWS S3 Free | ✅ Kolay |
| **GKE Cluster** | ~$70-100 | Railway, Render, Fly.io | 🟡 Orta |
| **Pub/Sub** | ~$5-15 | BullMQ + Redis, SQS Free | 🟡 Orta |

## Önerilen Free Stack:

### 1. **Database: Supabase** (Ücretsiz 500MB)
```env
DATABASE_URL=postgresql://user:pass@db.supabase.co:5432/postgres
```

### 2. **Cache: Upstash Redis** (10K requests/day free)
```env
REDIS_URL=redis://default:xxx@xxx.upstash.io:6379
```

### 3. **Hosting: Railway** (5$ credit/month)
```env
RAILWAY_PROJECT_ID=your-project
```

### 4. **File Storage: Cloudflare R2** (10GB free)
```env
R2_ACCOUNT_ID=your-account
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
```

## Hızlı Geçiş Komutu:

```bash
# Free stack için environment variables
cp config.env.example config.env.free

# Docker Compose ile local çalıştır
docker-compose -f docker-compose.free.yml up
```

## Hybrid Yaklaşım:
- **Development:** Free services kullan
- **Production:** GCP'de scale et
- **Staging:** Railway/Render gibi orta seviye

## Config Değişikliği:
```yaml
# config/system_config.yaml
deployment:
  type: "free" # gcp, free, hybrid
  database:
    provider: "supabase" # gcp-sql, supabase, postgresql
  cache:
    provider: "upstash" # gcp-redis, upstash, local
  storage:
    provider: "r2" # gcp-storage, r2, local
``` 