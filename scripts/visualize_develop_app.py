"""
CoFound.ai "develop_app" İş Akışı Görselleştirme

Bu script, CoFound.ai 'develop_app' iş akışını görselleştirir.
"""

import yaml
from pathlib import Path

def main():
    """Ana işlev - develop_app iş akışı şemasını oluşturur."""
    print("CoFound.ai 'develop_app' İş Akışı Görselleştirme")
    print("===============================================\n")
    
    # Workflow yapılandırmasını yükle
    print("İş akışı yapılandırması yükleniyor...")
    config_path = Path("cofoundai/config/workflows.yaml")
    
    try:
        with open(config_path, 'r') as f:
            workflow_config = yaml.safe_load(f)
        
        # develop_app iş akışını bul
        workflow_data = None
        for wf in workflow_config.get("main", {}).get("workflows", []):
            if wf.get("id") == "develop_app":
                workflow_data = wf
                break
        
        if not workflow_data:
            print("Hata: 'develop_app' iş akışı bulunamadı!")
            return
        
        workflow_name = workflow_data.get("name")
        print(f"İş Akışı: {workflow_name}")
        print(f"Açıklama: {workflow_data.get('description')}")
        print("-" * 60)
        
        # LangGraph yapılandırmasını al
        lg_config = workflow_data.get("langgraph", {})
        states = lg_config.get("states", [])
        transitions = lg_config.get("transitions", [])
        
        # Düğümleri listele
        print("\nDüğümler (Nodes):")
        for state in states:
            print(f"  - {state.get('name')}: {state.get('description')} ({state.get('agent')})")
        
        # Geçişleri listele
        print("\nGeçişler (Edges):")
        for transition in transitions:
            from_state = transition.get('from')
            to_state = transition.get('to') or "END"
            print(f"  - {from_state} -> {to_state}")
        
        # Mermaid diagramı oluştur
        print("\nMermaid Diagramı:")
        print("```mermaid")
        print("graph TD")
        
        # Düğümleri ekle
        for state in states:
            state_name = state.get('name', '')
            agent_name = state.get('agent', '')
            print(f"    {state_name}[\"{state_name}<br>{agent_name}\"]")
        
        # END düğümünü ekle
        print("    END((Son))")
        
        # Geçişleri ekle
        for transition in transitions:
            from_state = transition.get('from', '')
            to_state = transition.get('to')
            
            if to_state:
                print(f"    {from_state} --> {to_state}")
            else:
                print(f"    {from_state} --> END")
        
        print("```")
        
        # Kopyalama için mesaj
        print("\nYukarıdaki Mermaid diagramını https://mermaid.live/ adresine kopyalayarak")
        print("'develop_app' iş akışını görselleştirebilirsiniz.")
            
    except Exception as e:
        print(f"Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 