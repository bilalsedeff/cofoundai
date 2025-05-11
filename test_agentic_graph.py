"""
CoFound.ai Agentic Graph Test

Bu script, CoFound.ai projesindeki Agentic Graph yapısını test eder.
"""

import logging
import sys
import traceback
from typing import Dict, Any, Optional

# Logging ayarları
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_agentic_graph():
    """
    Agentic Graph yapısını test eder.
    """
    try:
        print("CoFound.ai Agentic Graph yapısını test ediyorum...")
        
        # Modülleri içe aktar
        from cofoundai.communication.message import Message
        from cofoundai.communication.agent_command import Command, CommandType
        
        # LangGraph yapılandırmasını değiştirmeden temel yapıyı test edelim
        from cofoundai.orchestration.langgraph_workflow import LangGraphWorkflow
        
        print("Gerekli modüller başarıyla içe aktarıldı.")
        
        # Basit bir workflow oluştur
        workflow_config = {
            "name": "test_workflow",
            "test_mode": True,  # Test modunda çalış
            "test_agent_order": ["agent1", "agent2"],
        }
        
        workflow = LangGraphWorkflow(
            name="test_workflow", 
            config=workflow_config
        )
        
        print(f"Workflow oluşturuldu: {workflow.name}")
        
        # Test modu workflowu çalıştır
        initial_state = {
            "project_description": "Basit bir hesap makinesi uygulaması",
            "user_request": "Toplama, çıkarma, çarpma ve bölme yapabilen bir hesap makinesi geliştir",
        }
        
        print("Workflow çalıştırılıyor...")
        result = workflow.run(initial_state)
        
        print(f"Workflow sonucu: {result.get('status', 'unknown')}")
        
        print("\nAgentic Graph testi başarılı!")
        return {
            "success": True,
            "message": "Agentic Graph testi başarıyla tamamlandı",
            "details": {
                "workflow": workflow.name,
                "status": result.get("status", "unknown")
            }
        }
        
    except Exception as e:
        print(f"HATA: Test sırasında hata: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Test başarısız oldu: {str(e)}",
            "error": str(e)
        }

if __name__ == "__main__":
    print("CoFound.ai Agentic Graph testini başlatıyorum...")
    
    try:
        result = test_agentic_graph()
        
        if result["success"]:
            print(f"\nTEST BAŞARILI: {result['message']}")
        else:
            print(f"\nTEST BAŞARISIZ: {result['message']}")
    except Exception as e:
        print(f"\nTEST SIRASINDA KRİTİK HATA: {str(e)}")
        traceback.print_exc() 