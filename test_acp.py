#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CoFound.ai - Ajan İletişim Protokolü (ACP) Testi

Bu script, LLM API çağrıları yapmadan ajanların birbirleriyle iletişim kurmasını test eder.
Tüm ajanların process() metodunun senkronize olduğunu ve workflow içinde doğru şekilde
veri akışının sağlandığını kontrol eder.
"""

import sys
import json
import tempfile
from pathlib import Path
import yaml
import logging
import os
import shutil

# CoFound.ai modüllerini import et
from cofoundai.core.base_agent import BaseAgent
from cofoundai.agents.planner import PlannerAgent
from cofoundai.agents.architect import ArchitectAgent
from cofoundai.agents.developer import DeveloperAgent
from cofoundai.agents.tester import TesterAgent
from cofoundai.agents.reviewer import ReviewerAgent
from cofoundai.agents.documentor import DocumentorAgent
from cofoundai.orchestration.langgraph_workflow import LangGraphWorkflow
from cofoundai.utils.logger import system_logger, get_workflow_logger
from cofoundai.tools import FileManager, VersionControl, Context7Adapter

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

def load_workflow_config(workflow_id):
    """
    Workflow yapılandırmasını yükle.
    
    Args:
        workflow_id: Workflow ID'si
        
    Returns:
        Workflow yapılandırması veya None
    """
    config_path = Path("cofoundai/config/workflows.yaml")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        if not config or "main" not in config or "workflows" not in config["main"]:
            print("Hata: Geçerli workflow yapılandırması bulunamadı!")
            return None
            
        # ID'ye göre workflow'u bul
        for workflow in config["main"]["workflows"]:
            if workflow.get("id") == workflow_id:
                return workflow
                
        print(f"Hata: '{workflow_id}' ID'li workflow bulunamadı!")
        return None
    except Exception as e:
        print(f"Yapılandırma dosyası yüklenirken hata: {e}")
        return None

def initialize_tools():
    """
    Test için araçları başlat.
    
    Returns:
        Araç adı -> araç objesi eşleştirmesi içeren sözlük
    """
    # Geçici çalışma dizini oluştur
    workspace_dir = tempfile.mkdtemp(prefix="cofoundai_workspace_")
    print(f"Geçici çalışma dizini oluşturuldu: {workspace_dir}")
    
    # Araçları oluştur
    file_manager = FileManager(workspace_dir=workspace_dir)
    version_control = VersionControl(workspace_dir=workspace_dir)
    context7_adapter = Context7Adapter(cache_dir=os.path.join(workspace_dir, "context7_cache"))
    
    tools = {
        "FileManager": file_manager,
        "VersionControl": version_control,
        "Context7Adapter": context7_adapter,
        "workspace_dir": workspace_dir  # Temizlik için dizini sakla
    }
    
    print(f"Araçlar başlatıldı: {', '.join([k for k in tools.keys() if k != 'workspace_dir'])}")
    return tools

def initialize_agents(tools):
    """
    Test için tüm ajanları başlat.
    
    Args:
        tools: Kullanılacak araçlar sözlüğü
        
    Returns:
        Ajan adı -> ajan objesi eşleştirmesi içeren sözlük
    """
    # Temel konfigürasyonlar
    planner_config = {"name": "Planner", "description": "Project planning and task breakdown"}
    architect_config = {"name": "Architect", "description": "System architecture design"}
    developer_config = {"name": "Developer", "description": "Code implementation"}
    tester_config = {"name": "Tester", "description": "Code testing and quality assurance"}
    reviewer_config = {"name": "Reviewer", "description": "Code review and improvements"}
    documentor_config = {"name": "Documentor", "description": "Project documentation"}
    
    # Her ajana araçları ekle
    for config in [planner_config, architect_config, developer_config, 
                  tester_config, reviewer_config, documentor_config]:
        config["tools"] = {
            "file_manager": tools["FileManager"],
            "version_control": tools["VersionControl"],
            "context7_adapter": tools["Context7Adapter"]
        }
    
    # Ajanları oluştur
    agents = {
        "Planner": PlannerAgent(planner_config),
        "Architect": ArchitectAgent(architect_config),
        "Developer": DeveloperAgent(developer_config),
        "Tester": TesterAgent(tester_config),
        "Reviewer": ReviewerAgent(reviewer_config),
        "Documentor": DocumentorAgent(documentor_config)
    }
    
    print(f"Ajanlar başlatıldı: {', '.join(agents.keys())}")
    return agents

def main():
    """Ana test fonksiyonu."""
    print("CoFound.ai Ajan İletişim Protokolü (ACP) Testi")
    print("==============================================\n")
    
    # Loglama yapılandırması
    setup_logging()
    
    # Araçları başlat
    tools = initialize_tools()
    
    # Ajanları başlat (araçlarla)
    agents = initialize_agents(tools)
    
    # Test edilecek workflow ID'si
    workflow_id = "develop_app"
    print(f"Workflow ID: {workflow_id}\n")
    
    # Workflow yapılandırmasını yükle
    workflow_config = load_workflow_config(workflow_id)
    if not workflow_config:
        cleanup(tools)
        return 1
        
    # Test modu aktif et (LLM çağrıları yapmasın)
    workflow_config["test_mode"] = True
    
    print("Workflow bilgileri:")
    print(f"  İsim: {workflow_config.get('name')}")
    print(f"  Açıklama: {workflow_config.get('description')}")
    print(f"  Faz sayısı: {len(workflow_config.get('phases', []))}\n")
    
    # LangGraph workflow oluştur
    workflow = LangGraphWorkflow(workflow_id, workflow_config, agents)
    
    # Git reposunu başlat
    tools["VersionControl"].init_repository("TodoApp")
    print("Git reposu başlatıldı: TodoApp\n")
    
    # Test girdisi
    input_data = {
        "project_description": "Todo list API with FastAPI backend, SQLite database, and basic CRUD operations",
        "workflow_id": workflow_id,
        "workspace_dir": tools["workspace_dir"]  # Çalışma dizinini ekle
    }
    
    print(f"Test girdisi: {input_data['project_description']}\n")
    print("Workflow çalıştırılıyor...")
    
    try:
        # Workflow'u çalıştır
        result = workflow.run(input_data)
        
        # Sonuçları yazdır
        print("\nWorkflow tamamlandı!")
        print(f"Sonuç durumu: {result.get('status', 'bilinmiyor')}")
        
        # Her ajanın işlediği durumu göster
        print("\nAjan çıktıları:")
        for agent_name in agents.keys():
            if agent_name in result:
                status = result[agent_name].get("status", "bilinmiyor")
                message = result[agent_name].get("message", "Mesaj yok")
                print(f"  {agent_name}: {status} - {message}")
        
        # Üretilen dosyaları listele
        workspace_dir = tools["workspace_dir"]
        print(f"\nÜretilen dosyalar ({workspace_dir}):")
        for root, dirs, files in os.walk(workspace_dir):
            for file in files:
                if not file.startswith('.git'):
                    rel_path = os.path.relpath(os.path.join(root, file), workspace_dir)
                    print(f"  {rel_path}")
    
        # İsteğe bağlı olarak tüm sonuçları göster
        print("\nAyrıntılı sonuçları görmek için --verbose parametresi ekleyin.")
        if "--verbose" in sys.argv:
            print("\nAyrıntılı sonuçlar:")
            print(json.dumps(result, indent=2))
        
        return 0
    except Exception as e:
        print(f"Workflow çalıştırılırken hata: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Temizlik yap
        cleanup(tools)

def cleanup(tools):
    """
    Test sonrası temizlik.
    
    Args:
        tools: Temizlenecek araçlar sözlüğü
    """
    try:
        workspace_dir = tools.get("workspace_dir")
        if workspace_dir and os.path.exists(workspace_dir):
            print(f"\nTemizlik yapılıyor: {workspace_dir} siliniyor...")
            shutil.rmtree(workspace_dir, ignore_errors=True)
    except Exception as e:
        print(f"Temizlik yapılırken hata: {e}")

if __name__ == "__main__":
    sys.exit(main()) 