"""
CoFound.ai LangGraph Workflow Testi ve Şema Görselleştirme

Bu script, CoFound.ai projesindeki LangGraph iş akışlarını görselleştirir.
"""

import yaml
from pathlib import Path

def create_mermaid_diagram(workflow):
    """Bir iş akışı için Mermaid diagram kodu oluşturur."""
    lg_config = workflow.get("langgraph", {})
    states = lg_config.get("states", [])
    transitions = lg_config.get("transitions", [])
    
    if not states:
        return "Bu iş akışı için LangGraph durumları tanımlanmamış."
    
    # Diagram kodunu oluştur
    diagram = ["```mermaid", "graph TD"]
    
    # Düğümleri ekle
    for state in states:
        state_name = state.get('name', '')
        agent_name = state.get('agent', '')
        diagram.append(f"    {state_name}[\"{state_name}<br>{agent_name}\"]")
    
    # END düğümünü ekle
    diagram.append("    END((Son))")
    
    # Geçişleri ekle
    for transition in transitions:
        from_state = transition.get('from', '')
        to_state = transition.get('to')
        
        if to_state:
            diagram.append(f"    {from_state} --> {to_state}")
        else:
            diagram.append(f"    {from_state} --> END")
    
    diagram.append("```")
    return "\n".join(diagram)

def main():
    """Ana işlev - iş akışı şemasını oluşturur."""
    print("CoFound.ai LangGraph Workflow Görselleştirme")
    print("===========================================\n")
    
    # Workflow yapılandırmasını yükle
    print("İş akışı yapılandırması yükleniyor...")
    config_path = Path("cofoundai/config/workflows.yaml")
    
    try:
        with open(config_path, 'r') as f:
            workflow_config = yaml.safe_load(f)
        
        # İş akışı listesini al
        workflows = workflow_config.get("main", {}).get("workflows", [])
        
        if not workflows:
            print("Hata: Geçerli iş akışı bulunamadı!")
            return
        
        # İş akışları listelensin
        print(f"{len(workflows)} adet iş akışı bulundu:")
        for i, wf in enumerate(workflows):
            print(f"  {i+1}. {wf.get('id')} - {wf.get('name')}")
        
        # Her bir iş akışı için şema oluştur
        for idx, wf in enumerate(workflows):
            workflow_id = wf.get("id")
            workflow_name = wf.get("name")
            
            print(f"\n{'='*60}")
            print(f"İş Akışı {idx+1}: {workflow_id} - {workflow_name}")
            print(f"Açıklama: {wf.get('description')}")
            print(f"{'-'*60}")
            
            # LangGraph yapılandırmasını al
            lg_config = wf.get("langgraph", {})
            states = lg_config.get("states", [])
            transitions = lg_config.get("transitions", [])
            
            if not states:
                print("  Bu iş akışı için LangGraph durumları tanımlanmamış.")
                continue
                
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
            mermaid_diagram = create_mermaid_diagram(wf)
            print(mermaid_diagram)
            
            # Kopyalama için mesaj
            print(f"\nYukarıdaki Mermaid diagramını https://mermaid.live/ adresine kopyalayarak")
            print(f"'{workflow_id}' iş akışını görselleştirebilirsiniz.")
            
    except Exception as e:
        print(f"Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 