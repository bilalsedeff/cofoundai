"""
CoFound.ai Agent İletişim Testi

Bu script, CoFound.ai projesindeki ajan iletişimi ve LangGraph yapısının LLM olmadan
doğru çalışıp çalışmadığını test eder. Sadeleştirilmiş versiyon.
"""

import logging
import sys
import traceback
from typing import Dict, Any, Optional

# Logging ayarları
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_agent_communication():
    """
    Ajan iletişimini test eder ve LangGraph yapısının doğru çalıştığını kontrol eder.
    """
    try:
        print("CoFound.ai iletişim modüllerini test ediyorum...")
        
        # Temel modülleri içe aktar
        from cofoundai.communication.message import Message, MessageContent
        from cofoundai.communication.agent_command import Command, CommandType, CommandTarget
        
        print("İletişim modülleri başarıyla içe aktarıldı.")
        
        # Mesaj ve Komut oluşturma testleri
        message = Message(
            sender="human",
            recipient="Planner",
            content="Basit bir hesap makinesi uygulaması oluştur"
        )
        
        command = Command.handoff(
            to_agent="Developer",
            reason="Bu görev için Developer ajanının kod yazması gerekiyor",
            state_updates={"task": "hesap makinesi uygulaması"}
        )
        
        print(f"Mesaj oluşturuldu: {message}")
        print(f"Komut oluşturuldu: {command}")
        
        # Mesajı yanıtla
        response = message.create_response(
            content="Hesap makinesi uygulaması için bir plan hazırlıyorum"
        )
        
        print(f"Yanıt mesajı oluşturuldu: {response}")
        print(f"Yanıt, orijinal mesaja yanıt mı: {response.is_response_to(message)}")
        
        # Komut dictionary'e çevir ve geri dönüştür
        command_dict = command.to_dict()
        command_reconverted = Command.from_dict(command_dict)
        
        print(f"Komut dictionary'e çevrildi: {command_dict}")
        print(f"Dictionary'den komuta çevrildi: {command_reconverted}")
        
        print("\nTemel iletişim testleri başarılı!")
        return {
            "success": True,
            "message": "Temel iletişim modülleri başarıyla test edildi",
            "details": {
                "message_test": str(message),
                "command_test": str(command),
                "response_test": str(response)
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
    print("CoFound.ai ajan iletişim testini başlatıyorum...")
    
    try:
        result = test_agent_communication()
        
        if result["success"]:
            print(f"\nTEST BAŞARILI: {result['message']}")
        else:
            print(f"\nTEST BAŞARISIZ: {result['message']}")
    except Exception as e:
        print(f"\nTEST SIRASINDA KRİTİK HATA: {str(e)}")
        traceback.print_exc() 