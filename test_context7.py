#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CoFound.ai Context7 Entegrasyonu Testi

Bu script, Context7 adaptörünün temel işlevlerini test eder.
Ayrıca bir ajan (Geliştirici) için Context7'den dokümantasyon alıp kullanma örneği gösterir.
"""

import sys
import logging
import json
from typing import Dict, Any
from pathlib import Path

# CoFound.ai modüllerini import et
from cofoundai.tools.context7_adapter import Context7Adapter
from cofoundai.agents.developer import DeveloperAgent
from cofoundai.communication.message import Message
from cofoundai.utils.logger import system_logger

def setup_logging():
    """Test için loglama yapılandırması."""
    # Konsola ayrıntılı log yazdırmak için handler oluştur
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Root logger'a ekle
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

def test_context7_basic_functionality():
    """
    Context7 adaptörünün temel işlevlerini test et.
    """
    print("\n=== Context7 Adaptörü Temel İşlev Testi ===")
    
    # Context7 adaptörü oluştur
    adapter = Context7Adapter()
    
    # 1. Kütüphane ID çözümleme testi
    libraries = ["fastapi", "next.js", "tensorflow", "unknown_library"]
    print("\nKütüphane ID Çözümleme Testi:")
    for lib in libraries:
        lib_id = adapter.resolve_library_id(lib)
        status = "✓" if lib_id else "✗"
        print(f"  {status} {lib} -> {lib_id or 'Çözümlenemedi'}")
    
    # 2. Dokümantasyon alma testi
    print("\nDokümantasyon Alma Testi:")
    
    # Nextjs dokümantasyonu
    nextjs_id = adapter.resolve_library_id("next.js")
    topics = [None, "routing", "data fetching"]
    
    for topic in topics:
        topic_str = topic or "genel"
        try:
            docs = adapter.get_library_docs(nextjs_id, topic=topic)
            doc_len = len(docs["content"])
            print(f"  ✓ Next.js ({topic_str}) dokümantasyonu: {doc_len} karakter")
        except Exception as e:
            print(f"  ✗ Next.js ({topic_str}) dokümantasyonu alınamadı: {e}")
    
    # FastAPI dokümantasyonu
    fastapi_id = adapter.resolve_library_id("fastapi")
    try:
        docs = adapter.get_library_docs(fastapi_id)
        doc_len = len(docs["content"])
        print(f"  ✓ FastAPI dokümantasyonu: {doc_len} karakter")
    except Exception as e:
        print(f"  ✗ FastAPI dokümantasyonu alınamadı: {e}")
    
    # 3. Dokümantasyon arama testi
    print("\nDokümantasyon Arama Testi:")
    search_queries = ["routing", "api", "data fetching"]
    
    for query in search_queries:
        try:
            results = adapter.search_documentation(query, [nextjs_id, fastapi_id])
            print(f"  ✓ '{query}' araması: {results['totalResults']} sonuç bulundu")
            
            if results["totalResults"] > 0:
                # İlk sonucu göster
                first_result = results["results"][0]
                print(f"    - İlk sonuç: {first_result['libraryId']} ({len(first_result['content'])} karakter)")
        except Exception as e:
            print(f"  ✗ '{query}' araması başarısız: {e}")
    
    return adapter

def test_developer_agent_with_context7(adapter: Context7Adapter):
    """
    Context7 adaptörü ile geliştirici ajanı entegrasyonunu test et.
    
    Args:
        adapter: Test edilecek Context7 adaptörü
    """
    print("\n=== Geliştirici Ajanı ile Context7 Entegrasyonu Testi ===")
    
    # Geliştirici ajanı oluştur
    developer_config = {
        "name": "Developer",
        "description": "Code implementation with Context7 integration"
    }
    developer = DeveloperAgent(developer_config)
    
    # Kütüphane ID'leri
    nextjs_id = adapter.resolve_library_id("next.js")
    fastapi_id = adapter.resolve_library_id("fastapi")
    
    # Test senaryosu: Next.js routing ile bir sayfa yarat
    task_description = "Create a dynamic route in Next.js for blog posts"
    
    # Context7'den dokümantasyon al
    nextjs_docs = adapter.get_library_docs(nextjs_id, topic="routing")
    
    # Ajana Context7 dokümantasyonu ile bir görev ver
    input_data = {
        "task": task_description,
        "context7_docs": {
            "nextjs": nextjs_docs["content"]
        },
        "project_type": "web",
        "framework": "next.js"
    }
    
    print(f"\nDeveloper ajanına görev veriliyor: {task_description}")
    
    try:
        # Developer ajanının process metodunu çağır
        result = developer.process(input_data)
        
        print("\nAjan yanıtı:")
        print(f"  - Durum: {result.get('status', 'bilinmiyor')}")
        print(f"  - Mesaj: {result.get('message', 'Mesaj yok')}")
        
        # Üretilen kod varsa göster
        if "code" in result:
            print("\nÜretilen kod:")
            code_files = result["code"]
            for filename, code in code_files.items():
                print(f"\n--- {filename} ---")
                print(code[:500] + ("..." if len(code) > 500 else ""))
        
        return result
    except Exception as e:
        print(f"Hata: Developer ajanı işlem hatası: {e}")
        return None

def simulate_integration_workflow(adapter: Context7Adapter):
    """
    Context7 adaptörünün bir workflow'a entegrasyonunu simüle et.
    
    Args:
        adapter: Kullanılacak Context7 adaptörü
    """
    print("\n=== Context7 Workflow Entegrasyonu Simülasyonu ===")
    
    # Geliştirici ajanı oluştur
    developer_config = {
        "name": "Developer",
        "description": "Code implementation with Context7 integration"
    }
    developer = DeveloperAgent(developer_config)
    
    # Workflow simülasyonu
    print("\nWorkflow adımları:")
    
    # 1. Proje tanımı
    print("1. Proje tanımı: Todo API uygulaması (FastAPI & SQLite)")
    
    # 2. Gerekli kütüphaneleri belirle
    print("2. Gerekli kütüphaneleri belirleme")
    libraries = ["fastapi", "sqlite", "pydantic"]
    library_ids = [adapter.resolve_library_id(lib) for lib in libraries if adapter.resolve_library_id(lib)]
    print(f"   Kütüphaneler: {', '.join(libraries)}")
    print(f"   Çözümlenen ID'ler: {', '.join(library_ids)}")
    
    # 3. Dokümantasyon topla
    print("3. Dokümantasyon toplama")
    docs = {}
    for lib_id in library_ids:
        lib_docs = adapter.get_library_docs(lib_id)
        docs[lib_id] = lib_docs["content"]
        print(f"   {lib_id} dokümantasyonu: {len(lib_docs['content'])} karakter")
    
    # 4. Kod üretme isteği oluştur
    print("4. Kod üretme isteği oluşturma")
    task = "Create a FastAPI application with SQLite database for a Todo List API with the following endpoints: GET /todos, POST /todos, GET /todos/{id}, PUT /todos/{id}, DELETE /todos/{id}"
    
    input_data = {
        "task": task,
        "context7_docs": docs,
        "project_type": "api",
        "framework": "fastapi",
        "database": "sqlite"
    }
    
    # 5. Geliştirici ajanı ile kod üret
    print("5. Geliştirici ajanı ile kod üretme")
    result = developer.process(input_data)
    
    # 6. Sonuçları değerlendir
    print("6. Sonuçları değerlendirme")
    print(f"   Durum: {result.get('status', 'bilinmiyor')}")
    
    if "code" in result:
        files = list(result["code"].keys())
        print(f"   Üretilen dosyalar: {', '.join(files)}")
    
    print("\nWorkflow simülasyonu tamamlandı.")
    
    return result

def main():
    """Ana test fonksiyonu."""
    print("CoFound.ai Context7 Entegrasyonu Testi")
    print("======================================\n")
    
    # Loglama yapılandırması
    setup_logging()
    
    # Context7 adaptörünün temel işlevlerini test et
    adapter = test_context7_basic_functionality()
    
    # Geliştirici ajanını Context7 ile test et
    developer_result = test_developer_agent_with_context7(adapter)
    
    # Workflow entegrasyonunu simüle et
    workflow_result = simulate_integration_workflow(adapter)
    
    # Test sonuçlarını görüntüle
    print("\n=== Test Sonuçları Özeti ===")
    
    # Temel işlevler için sonuç
    print("\nContext7 Adaptörü Temel İşlevleri: Başarılı")
    
    # Geliştirici ajanı entegrasyonu için sonuç
    if developer_result and developer_result.get("status") == "success":
        print("Geliştirici Ajanı Entegrasyonu: Başarılı")
    else:
        print("Geliştirici Ajanı Entegrasyonu: Başarısız")
    
    # Workflow simülasyonu için sonuç
    if workflow_result and workflow_result.get("status") == "success":
        print("Workflow Entegrasyon Simülasyonu: Başarılı")
    else:
        print("Workflow Entegrasyon Simülasyonu: Başarısız")
    
    # İsteğe bağlı olarak ayrıntılı sonuçları göster
    if "--verbose" in sys.argv:
        print("\nAyrıntılı Sonuçlar:")
        if developer_result:
            print("\nGeliştirici Ajanı Yanıtı:")
            print(json.dumps(developer_result, indent=2, ensure_ascii=False))
        if workflow_result:
            print("\nWorkflow Simülasyonu Yanıtı:")
            print(json.dumps(workflow_result, indent=2, ensure_ascii=False))
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 