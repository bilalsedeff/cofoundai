"""
CoFound.ai Agent Protocol API

Bu modül, CoFound.ai agent graph yapısını Agent Protocol ile
uyumlu bir API uygulaması olarak sunar. FastAPI kullanarak
HTTP API'sini oluşturur ve Agent Protocol'e uygun olarak
ajanları, thread'leri ve run'ları yönetir.
"""

from fastapi import FastAPI
from typing import Dict, Any, List, Optional
import logging
import uvicorn
import os

from cofoundai.communication.protocol import AgentProtocolAdapter
from cofoundai.orchestration.agentic_graph import AgenticGraph

# Logger yapılandırması
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Agent Protocol API uygulaması
app = FastAPI(
    title="CoFound.ai Agent Protocol API",
    description="LangChain Agent Protocol ile uyumlu CoFound.ai API",
    version="0.1.0"
)

# Agent Protocol adaptörünü başlat
ap_adapter = AgentProtocolAdapter(app)

@app.get("/")
async def root():
    """API kök endpoint."""
    return {
        "name": "CoFound.ai Agent Protocol API",
        "version": "0.1.0",
        "description": "LangChain Agent Protocol (AP) standardına uygun API"
    }

@app.get("/health")
async def health_check():
    """API sağlık kontrolü."""
    return {"status": "ok"}

# Agent graph kaydetme yardımcı fonksiyonu
def register_agent_graph(agent_id: str, graph: AgenticGraph):
    """
    Agent grafiğini AP adaptörüne kaydet.
    
    Args:
        agent_id: Kaydetmek istediğiniz agent ID'si
        graph: Kaydedilecek AgenticGraph örneği
        
    Returns:
        Başarı durumu
    """
    try:
        result = ap_adapter.register_agent_graph(agent_id, graph)
        logger.info(f"Agent {agent_id} başarıyla kaydedildi")
        return result
    except Exception as e:
        logger.error(f"Agent {agent_id} kaydedilirken hata: {str(e)}")
        return False

# Uygulama önyükleme olayı
@app.on_event("startup")
async def startup_event():
    """API başlangıç olayı."""
    logger.info("CoFound.ai Agent Protocol API başlatılıyor")
    
    # Burada test amaçlı varsayılan ajanlar kaydedilebilir
    # Örnek: register_agent_graph("default", ...)

# Uygulama kapanış olayı
@app.on_event("shutdown")
async def shutdown_event():
    """API kapanış olayı."""
    logger.info("CoFound.ai Agent Protocol API kapatılıyor")

# Geliştirme sunucusu başlatma
if __name__ == "__main__":
    # Bağlantı noktası ve adres yapılandırması
    host = os.environ.get("COFOUNDAI_AP_HOST", "0.0.0.0")
    port = int(os.environ.get("COFOUNDAI_AP_PORT", 8000))
    
    # Sunucuyu başlat
    logger.info(f"Sunucu başlatılıyor: {host}:{port}")
    uvicorn.run(app, host=host, port=port) 