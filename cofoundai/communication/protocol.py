"""
CoFound.ai Agent Protocol Adapter

Bu modül, LangChain Agent Protocol (AP) ile CoFound.ai arasında 
bir köprü görevi görerek standartlaştırılmış API entegrasyonu sağlar.

AP Özellikleri:
- Runs API - Ajan çalıştırmaları
- Threads API - Durum yönetimi
- Store API - Kalıcı depolama
- Introspection - Ajan şemaları
"""

from typing import Dict, Any, List, Optional, Union, Literal, TypeVar, Generic, cast
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
import json
import logging
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse

from cofoundai.communication.message import Message, MessageContent
from cofoundai.communication.agent_command import Command, CommandType, CommandTarget
from cofoundai.orchestration.agentic_graph import AgenticGraph

# Logger tanımla
logger = logging.getLogger(__name__)

# Agent Protocol Modelleri

class Content(BaseModel):
    """Agent Protocol Content modeli."""
    type: str
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class APMessage(BaseModel):
    """Agent Protocol Message modeli."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: str
    role: str
    content: List[Content]
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)

class Thread(BaseModel):
    """Agent Protocol Thread modeli."""
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)

class ThreadState(BaseModel):
    """Agent Protocol Thread State modeli."""
    thread_id: str
    state: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ThreadPatch(BaseModel):
    """Agent Protocol Thread Patch modeli."""
    metadata: Optional[Dict[str, Any]] = None
    
class ThreadSearchRequest(BaseModel):
    """Agent Protocol Thread Search Request modeli."""
    thread_ids: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_before: Optional[datetime] = None
    created_after: Optional[datetime] = None
    limit: Optional[int] = None

class RunCreate(BaseModel):
    """Agent Protocol Run oluşturma modeli."""
    thread_id: Optional[str] = None
    agent_id: Optional[str] = None
    input: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    stream: Optional[bool] = False
    config: Optional[Dict[str, Any]] = None

class Run(BaseModel):
    """Agent Protocol Run modeli."""
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: str
    agent_id: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class RunSearchRequest(BaseModel):
    """Agent Protocol Run Search Request modeli."""
    run_ids: Optional[List[str]] = None
    thread_ids: Optional[List[str]] = None
    agent_ids: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_before: Optional[datetime] = None
    created_after: Optional[datetime] = None
    limit: Optional[int] = None

class Item(BaseModel):
    """Store Item modeli."""
    key: str
    namespace: List[str]
    value: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class StorePutRequest(BaseModel):
    """Store Item ekleme/güncelleme isteği."""
    namespace: List[str]
    key: str
    value: Dict[str, Any]

class StoreDeleteRequest(BaseModel):
    """Store Item silme isteği."""
    namespace: List[str]
    key: str

class StoreSearchRequest(BaseModel):
    """Store Item arama isteği."""
    namespace: Optional[List[str]] = None
    query: Optional[str] = None
    
class SearchItemsResponse(BaseModel):
    """Store Item arama sonucu."""
    items: List[Item]

class StoreListNamespacesRequest(BaseModel):
    """Store Namespaces listeleme isteği."""
    pass

class AgentSchema(BaseModel):
    """Agent şema modeli."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

class RunWaitResponse(BaseModel):
    """Run bekleme yanıtı."""
    run: Run
    messages: List[APMessage] = []

# CoFound.ai ve Agent Protocol arasında dönüşüm fonksiyonları

def convert_to_ap_message(message: Message, thread_id: str) -> APMessage:
    """CoFound.ai Message'ı AP Message'a çevir."""
    content = [
        Content(
            type="text",
            text=message.content.text if hasattr(message.content, "text") else str(message.content),
            data=message.content.data if hasattr(message.content, "data") else {}
        )
    ]
    
    return APMessage(
        thread_id=thread_id,
        role=message.sender,
        content=content,
        metadata=message.metadata
    )

def convert_from_ap_message(ap_message: APMessage) -> Message:
    """AP Message'ı CoFound.ai Message'a çevir."""
    content_text = ""
    content_data = {}
    
    if ap_message.content:
        for content in ap_message.content:
            if content.type == "text" and content.text:
                content_text += content.text
            if content.data:
                content_data.update(content.data)
    
    return Message(
        sender=ap_message.role,
        recipient="system",  # Varsayılan alıcı
        content=MessageContent(text=content_text, data=content_data),
        metadata=ap_message.metadata or {},
        message_id=ap_message.message_id
    )

# Agent Protocol API Adapter

class AgentProtocolAdapter:
    """
    CoFound.ai'yi Agent Protocol ile uyumlu hale getiren adaptör.
    
    Bu sınıf, CoFound.ai agentic_graph yapısını Agent Protocol API
    standartlarına uyumlu hale getirir.
    """
    
    def __init__(self, app: FastAPI = None):
        """
        Adaptörü başlat.
        
        Args:
            app: FastAPI uygulaması (opsiyonel)
        """
        self.app = app
        self.graphs: Dict[str, AgenticGraph] = {}
        self.runs: Dict[str, Run] = {}
        self.threads: Dict[str, Thread] = {}
        self.thread_states: Dict[str, ThreadState] = {}
        self.store: Dict[str, Dict[str, Item]] = {}
        
        if app:
            self._register_routes()
            logger.info("Agent Protocol API rotaları kaydedildi")
    
    def _register_routes(self):
        """API rotalarını kaydet."""
        # Agent API
        self.app.get("/agents/{agent_id}")(self.get_agent)
        self.app.get("/agents/{agent_id}/schemas")(self.get_agent_schemas)
        self.app.post("/agents/search")(self.search_agents)
        
        # Runs API
        self.app.post("/runs", response_model=Run)(self.create_run)
        self.app.get("/runs/{run_id}", response_model=Run)(self.get_run)
        self.app.post("/runs/stream")(self.create_and_stream_run)
        self.app.post("/runs/wait", response_model=RunWaitResponse)(self.create_and_wait_run)
        self.app.get("/runs/{run_id}/stream")(self.stream_run)
        self.app.post("/runs/search")(self.search_runs)
        
        # Threads API
        self.app.post("/threads", response_model=Thread)(self.create_thread)
        self.app.get("/threads/{thread_id}", response_model=Thread)(self.get_thread)
        self.app.patch("/threads/{thread_id}", response_model=Thread)(self.patch_thread)
        self.app.get("/threads/{thread_id}/state")(self.get_thread_state)
        self.app.post("/threads/{thread_id}/runs", response_model=Run)(self.create_run_in_thread)
        self.app.post("/threads/search")(self.search_threads)
        
        # Store API
        self.app.put("/store/items")(self.put_item)
        self.app.get("/store/items/{key}")(self.get_item)
        self.app.delete("/store/items")(self.delete_item)
        self.app.post("/store/items/search", response_model=SearchItemsResponse)(self.search_items)
        self.app.post("/store/namespaces", response_model=List[List[str]])(self.list_namespaces)
    
    def register_agent_graph(self, agent_id: str, graph: AgenticGraph):
        """
        Agent grafiğini kaydet.
        
        Args:
            agent_id: Ajan ID'si
            graph: Agentic Graph nesnesi
        """
        self.graphs[agent_id] = graph
        logger.info(f"Agent ID {agent_id} için graph kaydedildi")
        return True
    
    # Agent API implementasyonları
    async def get_agent(self, agent_id: str):
        """Ajan bilgilerini al."""
        if agent_id not in self.graphs:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        graph = self.graphs[agent_id]
        
        # Ajan şemasını oluştur
        return AgentSchema(
            name=agent_id,
            description=f"Agentic graph for {agent_id}",
            input_schema={"type": "object", "properties": {"message": {"type": "string"}}},
            output_schema={"type": "object"}
        )
    
    async def get_agent_schemas(self, agent_id: str):
        """Ajan şemalarını al."""
        if agent_id not in self.graphs:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Basit girdi/çıktı şemaları
        input_schema = {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Input message for the agent"
                }
            }
        }
        
        output_schema = {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Output message from the agent"
                },
                "status": {
                    "type": "string",
                    "description": "Status of the agent execution"
                }
            }
        }
        
        return {
            "input_schema": input_schema,
            "output_schema": output_schema
        }
    
    async def search_agents(self, request: dict = Body(...)):
        """Ajanları ara."""
        agent_list = []
        
        for agent_id, graph in self.graphs.items():
            agent_list.append({
                "agent_id": agent_id,
                "name": agent_id,
                "description": f"Agentic graph for {agent_id}"
            })
            
        return {"agents": agent_list}
    
    # Runs API implementasyonları
    async def create_run(self, run_create: RunCreate):
        """Yeni bir çalıştırma oluştur."""
        agent_id = run_create.agent_id
        if agent_id not in self.graphs:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Thread oluştur veya kullan
        thread_id = run_create.thread_id
        if not thread_id:
            thread = Thread()
            self.threads[thread.thread_id] = thread
            thread_id = thread.thread_id
        elif thread_id not in self.threads:
            thread = Thread(thread_id=thread_id)
            self.threads[thread_id] = thread
        
        # Run oluştur
        run = Run(
            agent_id=agent_id,
            thread_id=thread_id,
            input=run_create.input,
            metadata=run_create.metadata
        )
        self.runs[run.run_id] = run
        
        # Asenkron işleme başlat
        asyncio.create_task(self._execute_run(run))
        
        return run
    
    async def _execute_run(self, run: Run):
        """Run'ı yürüt."""
        try:
            # Durumu güncelle
            run.status = "running"
            run.started_at = datetime.now()
            
            # Girdiyi çıkart
            user_input = run.input.get("message", "")
            if isinstance(user_input, dict) and "content" in user_input:
                user_input = user_input["content"]
            
            # Graph'ı çalıştır
            graph = self.graphs[run.agent_id]
            result = graph.run(user_input)
            
            # Çıktıyı sakla
            run.output = result
            run.status = "completed"
            run.completed_at = datetime.now()
            
        except Exception as e:
            # Hata durumunda
            logger.error(f"Run execution error: {str(e)}")
            run.status = "failed"
            run.output = {"error": str(e)}
            run.completed_at = datetime.now()
    
    async def get_run(self, run_id: str):
        """Run bilgilerini al."""
        if run_id not in self.runs:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        
        return self.runs[run_id]
    
    async def create_and_stream_run(self, run_stream: Dict[str, Any] = Body(...)):
        """Yeni bir run oluştur ve akış başlat."""
        # RunCreate nesnesine dönüştür
        run_create = RunCreate(
            agent_id=run_stream.get("agent_id"),
            thread_id=run_stream.get("thread_id"),
            input=run_stream.get("input", {}),
            metadata=run_stream.get("metadata", {}),
            stream=True
        )
        
        # Run oluştur
        run = await self.create_run(run_create)
        
        # Akış başlat
        return await self.stream_run(run.run_id)
    
    async def create_and_wait_run(self, run_create: RunCreate):
        """Yeni bir run oluştur ve tamamlanmasını bekle."""
        # Run oluştur
        run = await self.create_run(run_create)
        
        # Tamamlanmasını bekle
        for _ in range(100):  # Maksimum 100 saniye bekle
            current_run = self.runs[run.run_id]
            if current_run.status in ["completed", "failed"]:
                # Mesajları al
                messages = []  # Gerçek implementasyonda thread'deki mesajları getir
                
                return RunWaitResponse(run=current_run, messages=messages)
            
            await asyncio.sleep(1)
        
        # Zaman aşımı durumu
        run.status = "failed"
        run.output = {"error": "Run timeout"}
        self.runs[run.run_id] = run
        
        return RunWaitResponse(run=run, messages=[])
    
    async def stream_run(self, run_id: str):
        """Run çıktısını akış olarak al."""
        if run_id not in self.runs:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        
        run = self.runs[run_id]
        if run.status != "running":
            # Zaten tamamlanmış veya başarısız olan run
            yield json.dumps({"status": run.status, "output": run.output})
            return
        
        # Akış formatında yanıt üret
        graph = self.graphs[run.agent_id]
        user_input = run.input.get("message", "")
        
        async def stream_generator():
            try:
                for chunk in graph.stream(user_input):
                    # Chunk'ı JSON formatına dönüştür
                    if isinstance(chunk, dict):
                        yield json.dumps(chunk) + "\n"
                    else:
                        yield json.dumps({"chunk": str(chunk)}) + "\n"
            except Exception as e:
                yield json.dumps({"error": str(e)}) + "\n"
        
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    
    async def search_runs(self, search_request: RunSearchRequest):
        """Run'ları ara."""
        filtered_runs = []
        
        for run_id, run in self.runs.items():
            include = True
            
            # Run ID filtreleme
            if search_request.run_ids and run_id not in search_request.run_ids:
                include = False
                
            # Thread ID filtreleme
            if include and search_request.thread_ids and run.thread_id not in search_request.thread_ids:
                include = False
                
            # Agent ID filtreleme
            if include and search_request.agent_ids and run.agent_id not in search_request.agent_ids:
                include = False
                
            # Status filtreleme
            if include and search_request.statuses and run.status not in search_request.statuses:
                include = False
                
            # Oluşturma zamanı filtreleme
            if include and search_request.created_after and run.created_at < search_request.created_after:
                include = False
                
            if include and search_request.created_before and run.created_at > search_request.created_before:
                include = False
                
            # Metadata filtreleme
            if include and search_request.metadata:
                for key, value in search_request.metadata.items():
                    if not run.metadata or key not in run.metadata or run.metadata[key] != value:
                        include = False
                        break
            
            if include:
                filtered_runs.append(run)
                
        # Limit uygula
        if search_request.limit and len(filtered_runs) > search_request.limit:
            filtered_runs = filtered_runs[:search_request.limit]
                
        return {"runs": filtered_runs}
    
    # Threads API implementasyonları
    async def create_thread(self, thread: Thread = Body(...)):
        """Yeni thread oluştur."""
        self.threads[thread.thread_id] = thread
        return thread
    
    async def get_thread(self, thread_id: str):
        """Thread bilgilerini al."""
        if thread_id not in self.threads:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        
        return self.threads[thread_id]
    
    async def patch_thread(self, thread_id: str, thread_patch: ThreadPatch):
        """Thread bilgilerini güncelle."""
        if thread_id not in self.threads:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        
        thread = self.threads[thread_id]
        
        # Metadata güncelle
        if thread_patch.metadata:
            if not thread.metadata:
                thread.metadata = {}
            thread.metadata.update(thread_patch.metadata)
        
        return thread
    
    async def get_thread_state(self, thread_id: str):
        """Thread durumunu al."""
        if thread_id not in self.threads:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        
        # Thread state varsa getir, yoksa oluştur
        if thread_id in self.thread_states:
            return self.thread_states[thread_id]
        
        # Varsayılan boş durum
        thread_state = ThreadState(
            thread_id=thread_id,
            state={}
        )
        self.thread_states[thread_id] = thread_state
        return thread_state
    
    async def create_run_in_thread(self, thread_id: str, run_create: RunCreate):
        """Thread içinde yeni bir run oluştur."""
        if thread_id not in self.threads:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        
        # Thread ID'yi ekle
        run_create.thread_id = thread_id
        
        # Run oluştur
        return await self.create_run(run_create)
    
    async def search_threads(self, search_request: ThreadSearchRequest):
        """Thread'leri ara."""
        filtered_threads = []
        
        for thread_id, thread in self.threads.items():
            include = True
            
            # Thread ID filtreleme
            if search_request.thread_ids and thread_id not in search_request.thread_ids:
                include = False
                
            # Oluşturma zamanı filtreleme
            if include and search_request.created_after and thread.created_at < search_request.created_after:
                include = False
                
            if include and search_request.created_before and thread.created_at > search_request.created_before:
                include = False
                
            # Metadata filtreleme
            if include and search_request.metadata:
                for key, value in search_request.metadata.items():
                    if not thread.metadata or key not in thread.metadata or thread.metadata[key] != value:
                        include = False
                        break
            
            if include:
                filtered_threads.append(thread)
                
        # Limit uygula
        if search_request.limit and len(filtered_threads) > search_request.limit:
            filtered_threads = filtered_threads[:search_request.limit]
                
        return {"threads": filtered_threads}
    
    # Store API implementasyonları
    async def put_item(self, request: StorePutRequest):
        """Store'a item ekle."""
        namespace_key = "/".join(request.namespace)
        
        if namespace_key not in self.store:
            self.store[namespace_key] = {}
        
        # Item oluştur veya güncelle
        item = Item(
            key=request.key,
            namespace=request.namespace,
            value=request.value,
            updated_at=datetime.now()
        )
        
        if request.key in self.store[namespace_key]:
            # Varolan itemi güncelle, oluşturma zamanını koru
            item.created_at = self.store[namespace_key][request.key].created_at
        
        self.store[namespace_key][request.key] = item
        return {"status": "success"}
    
    async def get_item(self, key: str, namespace: List[str] = None):
        """Store'dan item al."""
        namespace = namespace or []
        namespace_key = "/".join(namespace)
        
        if namespace_key not in self.store or key not in self.store[namespace_key]:
            raise HTTPException(status_code=404, detail=f"Item {key} not found in namespace {namespace}")
        
        return self.store[namespace_key][key]
    
    async def delete_item(self, request: StoreDeleteRequest):
        """Store'dan item sil."""
        namespace_key = "/".join(request.namespace)
        
        if namespace_key in self.store and request.key in self.store[namespace_key]:
            del self.store[namespace_key][request.key]
            return {"status": "success"}
        else:
            raise HTTPException(status_code=404, detail=f"Item {request.key} not found in namespace {request.namespace}")
    
    async def search_items(self, request: StoreSearchRequest):
        """Store'da arama yap."""
        items = []
        namespaces = []
        
        if request.namespace:
            # Belirli namespace'lerde ara
            for ns in request.namespace:
                ns_key = "/".join(ns if isinstance(ns, list) else [ns])
                if ns_key in self.store:
                    namespaces.append(ns_key)
        else:
            # Tüm namespace'lerde ara
            namespaces = list(self.store.keys())
        
        for namespace_key in namespaces:
            for key, item in self.store[namespace_key].items():
                # Basit arama, query varsa key içinde ara
                if not request.query or request.query.lower() in key.lower():
                    items.append(item)
        
        return SearchItemsResponse(items=items)
    
    async def list_namespaces(self, request: StoreListNamespacesRequest):
        """Namespace'leri listele."""
        namespaces = []
        
        for namespace_key in self.store.keys():
            if namespace_key:
                # namespace_key string'i liste formatına dönüştür
                ns_parts = namespace_key.split("/")
                namespaces.append(ns_parts)
                
        return namespaces 