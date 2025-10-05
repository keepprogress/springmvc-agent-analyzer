# Architecture Diagrams Collection

**SpringMVC Agent Analyzer - Complete Visual Reference**

Version: 0.1.0
Date: 2025-10-05

---

## Table of Contents

1. [Component Relationship Diagrams](#component-relationship-diagrams)
2. [Data Flow Diagrams](#data-flow-diagrams)
3. [Sequence Diagrams](#sequence-diagrams)
4. [State Diagrams](#state-diagrams)
5. [Class Diagrams](#class-diagrams)
6. [Deployment Diagrams](#deployment-diagrams)

---

## Component Relationship Diagrams

### 1. Layer Architecture

```mermaid
graph TB
    subgraph "Layer 1: Client Interface"
        direction LR
        CC[Claude Code]
        CLI[CLI Tools]
        Web[Web UI<br/>Future]
    end

    subgraph "Layer 2: MCP Protocol"
        MCP[MCP Server<br/>Tool Registry]
    end

    subgraph "Layer 3: Core Services"
        direction LR
        MR[Model Router]
        PM[Prompt Manager]
        CT[Cost Tracker]
        CM[Cache Manager]
    end

    subgraph "Layer 4: Analysis Agents"
        direction LR
        CA[Controller<br/>Agent]
        JA[JSP<br/>Agent]
        SA[Service<br/>Agent]
        MA[Mapper<br/>Agent]
        PA[Procedure<br/>Agent]
    end

    subgraph "Layer 5: Validators"
        direction LR
        JV[Java<br/>Validator]
        XV[XML<br/>Validator]
        SV[SQL<br/>Validator]
    end

    subgraph "Layer 6: Knowledge Graph"
        direction LR
        GB[Graph<br/>Builder]
        QE[Query<br/>Engine]
        VZ[Visualizer]
    end

    subgraph "Layer 7: External Services"
        direction LR
        API[Anthropic<br/>API]
        DB[Oracle<br/>DB]
    end

    CC --> MCP
    CLI --> MCP
    Web -.-> MCP

    MCP --> MR
    MCP --> PM
    MCP --> CT
    MCP --> CM

    MR --> CA
    MR --> JA
    MR --> SA
    MR --> MA
    MR --> PA

    CA --> JV
    JA --> XV
    SA --> JV
    MA --> XV
    MA --> SV

    CA --> GB
    JA --> GB
    SA --> GB
    MA --> GB
    PA --> GB

    GB --> QE
    QE --> VZ

    MR -.-> API
    PA -.-> DB

    style MCP fill:#ff9999,stroke:#cc0000,stroke-width:3px
    style MR fill:#ffcc99,stroke:#ff9900,stroke-width:2px
    style GB fill:#99ccff,stroke:#0066cc,stroke-width:2px
```

### 2. Agent Inheritance Hierarchy

```mermaid classDiagram
    class BaseAgent {
        <<abstract>>
        +agent_name: str
        +model_router: ModelRouter
        +prompt_manager: PromptManager
        +cost_tracker: CostTracker
        +cache_manager: CacheManager
        +config: Dict

        +analyze(file_path)* Dict
        #_query_llm(prompt) Dict
        #_load_file_with_context(path) str
        #_extract_json_from_response(response) Dict
        +validate_result(result) bool
    }

    class ControllerAgent {
        +analyze(file_path) Dict
        -_parse_request_mapping() List
        -_extract_dependencies() List
    }

    class JSPAgent {
        +analyze(file_path) Dict
        -_extract_includes() List
        -_extract_ajax_calls() List
        -_extract_forms() List
    }

    class ServiceAgent {
        +analyze(file_path) Dict
        -_extract_transactional() bool
        -_extract_mapper_deps() List
    }

    class MapperAgent {
        +analyze(file_path) Dict
        -_parse_sql_statements() List
        -_detect_procedure_calls() List
    }

    class ProcedureAgent {
        +analyze(procedure_name) Dict
        -_infer_business_purpose() str
        -_detect_trigger_method() str
    }

    BaseAgent <|-- ControllerAgent
    BaseAgent <|-- JSPAgent
    BaseAgent <|-- ServiceAgent
    BaseAgent <|-- MapperAgent
    BaseAgent <|-- ProcedureAgent
```

### 3. Core Infrastructure Components

```mermaid
graph TB
    subgraph "Model Router"
        MR[ModelRouter]
        H[Haiku Handler]
        S[Sonnet Handler]
        O[Opus Handler]

        MR --> H
        MR --> S
        MR --> O
    end

    subgraph "Prompt Manager"
        PM[PromptManager]
        T[Template Loader]
        E[Example Injector]
        L[Learning Engine]

        PM --> T
        PM --> E
        PM --> L
    end

    subgraph "Cache Manager"
        CM[CacheManager]
        K[Key Generator]
        R[Retriever]
        W[Writer]
        EV[Evictor]

        CM --> K
        CM --> R
        CM --> W
        CM --> EV
    end

    subgraph "Cost Tracker"
        CT[CostTracker]
        REC[Recorder]
        AGG[Aggregator]
        AL[Alerter]

        CT --> REC
        CT --> AGG
        CT --> AL
    end

    style MR fill:#ffcc99
    style PM fill:#99ccff
    style CM fill:#99ff99
    style CT fill:#ff9999
```

---

## Data Flow Diagrams

### 1. Single File Analysis Flow

```mermaid
flowchart TD
    Start([File: UserController.java]) --> Load[Load File Content]
    Load --> CheckCache{Cache Exists?}

    CheckCache -->|Hit| ReturnCache[Return Cached Result<br/>💰 Cost: $0]
    CheckCache -->|Miss| BuildPrompt[Build Prompt<br/>Template + Examples]

    BuildPrompt --> Route{Model<br/>Router}

    Route -->|70%| Haiku[Try Haiku<br/>$0.25/1M]
    Route -->|Direct| Sonnet[Try Sonnet<br/>$3/1M]
    Route -->|Rare| Opus[Try Opus<br/>$15/1M]

    Haiku --> HConf{Confidence<br/>>= 0.9?}
    HConf -->|Yes| ExtractH[Extract JSON]
    HConf -->|No| Sonnet

    Sonnet --> SConf{Confidence<br/>>= 0.85?}
    SConf -->|Yes| ExtractS[Extract JSON]
    SConf -->|No| Opus

    Opus --> ExtractO[Extract JSON]

    ExtractH --> Validate
    ExtractS --> Validate
    ExtractO --> Validate

    Validate[Validate Syntax] --> Valid{Valid?}
    Valid -->|Yes| SaveCache[Save to Cache]
    Valid -->|No| Error[Log Error<br/>Return Partial]

    SaveCache --> Track[Track Cost]
    Error --> Track

    Track --> Return[Return Result]
    ReturnCache --> Return

    Return --> End([Analysis Complete])

    style ReturnCache fill:#99ff99
    style Haiku fill:#99ccff
    style Sonnet fill:#ffcc99
    style Opus fill:#ff9999
```

### 2. Multi-File Batch Analysis

```mermaid
flowchart TD
    Start([Analyze 100 Files]) --> Discover[File Discovery<br/>Glob Patterns]
    Discover --> Group[Group by Type]

    Group --> C[Controllers: 20]
    Group --> J[JSPs: 40]
    Group --> S[Services: 25]
    Group --> M[Mappers: 15]

    C --> ParC[Parallel Workers<br/>4 threads]
    J --> ParJ[Parallel Workers<br/>4 threads]
    S --> ParS[Parallel Workers<br/>4 threads]
    M --> ParM[Parallel Workers<br/>4 threads]

    ParC --> AC{Analyze Each}
    ParJ --> AJ{Analyze Each}
    ParS --> AS{Analyze Each}
    ParM --> AM{Analyze Each}

    AC -->|Cache Hit 60%| CC[Cached: 12]
    AC -->|Cache Miss 40%| LC[LLM: 8]

    AJ -->|Cache Hit 60%| CJ[Cached: 24]
    AJ -->|Cache Miss 40%| LJ[LLM: 16]

    AS -->|Cache Hit 60%| CS[Cached: 15]
    AS -->|Cache Miss 40%| LS[LLM: 10]

    AM -->|Cache Hit 60%| CM[Cached: 9]
    AM -->|Cache Miss 40%| LM[LLM: 6]

    CC --> MergeC
    LC --> MergeC[Merge Results]

    CJ --> MergeJ
    LJ --> MergeJ[Merge Results]

    CS --> MergeS
    LS --> MergeS[Merge Results]

    CM --> MergeM
    LM --> MergeM[Merge Results]

    MergeC --> Aggregate[Aggregate All]
    MergeJ --> Aggregate
    MergeS --> Aggregate
    MergeM --> Aggregate

    Aggregate --> BuildGraph[Build Graph<br/>NetworkX]
    BuildGraph --> Stats[Calculate Stats]
    Stats --> End([Complete<br/>💰 Cost: ~$2.34<br/>⚡ Time: ~60s])

    style CC fill:#99ff99
    style CJ fill:#99ff99
    style CS fill:#99ff99
    style CM fill:#99ff99
```

### 3. Knowledge Graph Construction

```mermaid
flowchart TB
    Start([Analysis Results]) --> ParseC[Parse Controllers<br/>Extract Mappings]
    Start --> ParseJ[Parse JSPs<br/>Extract AJAX Calls]
    Start --> ParseS[Parse Services<br/>Extract Calls]
    Start --> ParseM[Parse Mappers<br/>Extract SQL]

    ParseC --> NodesC[Create CONTROLLER Nodes]
    ParseJ --> NodesJ[Create JSP Nodes]
    ParseS --> NodesS[Create SERVICE Nodes]
    ParseM --> NodesM[Create MAPPER Nodes]

    NodesC --> MergeNodes[Merge All Nodes]
    NodesJ --> MergeNodes
    NodesS --> MergeNodes
    NodesM --> MergeNodes

    MergeNodes --> Graph[(NetworkX Graph)]

    ParseJ --> EdgeJC[AJAX_CALL Edges<br/>JSP → Controller]
    ParseC --> EdgeCS[INVOKES Edges<br/>Controller → Service]
    ParseS --> EdgeSM[CALLS Edges<br/>Service → Mapper]
    ParseM --> EdgeMT[QUERIES Edges<br/>Mapper → Table]

    EdgeJC --> MergeEdges[Merge All Edges]
    EdgeCS --> MergeEdges
    EdgeSM --> MergeEdges
    EdgeMT --> MergeEdges

    MergeEdges --> Graph

    Graph --> ValidateGraph{Validate}
    ValidateGraph -->|Broken Refs| Warn[Log Warnings]
    ValidateGraph -->|OK| Stats[Calculate Stats]

    Warn --> Stats
    Stats --> SaveJSON[Save graph.json]
    SaveJSON --> End([Graph Ready])

    style Graph fill:#99ccff
```

---

## Sequence Diagrams

### 1. Controller Analysis with Cache Miss

```mermaid
sequenceDiagram
    participant U as User
    participant M as MCP Server
    participant A as ControllerAgent
    participant C as CacheManager
    participant PM as PromptManager
    participant R as ModelRouter
    participant H as Haiku API
    participant V as JavaValidator
    participant CT as CostTracker

    U->>M: analyze_controller("UserController.java")
    M->>A: analyze(file_path)

    A->>A: Load file content
    A->>C: get(agent, file_path, content)
    C-->>A: None (cache miss)

    A->>PM: build_prompt("controller_analysis", context)
    PM->>PM: Load template
    PM->>PM: Inject 2 few-shot examples
    PM-->>A: Complete prompt (1500 tokens)

    A->>R: query(prompt, complexity="simple")
    R->>H: messages.create(model="haiku", ...)
    H-->>R: Response (confidence: 0.92, tokens: 1245+356)

    R->>R: Extract confidence: 0.92
    R->>R: Check threshold: 0.92 >= 0.9 ✓

    R-->>A: {response, model, cost: $0.00234, confidence: 0.92}

    A->>A: Extract JSON from response
    A->>V: validate_syntax(extracted_json)
    V-->>A: {valid: true}

    A->>C: save(agent, file_path, content, result)
    C-->>A: Saved

    A->>CT: record(agent, model, tokens, cost)
    CT-->>A: Recorded

    A-->>M: {analysis: {...}, metadata: {...}}
    M-->>U: Analysis result
```

### 2. Controller Analysis with Cache Hit

```mermaid
sequenceDiagram
    participant U as User
    participant M as MCP Server
    participant A as ControllerAgent
    participant C as CacheManager

    U->>M: analyze_controller("UserController.java")
    M->>A: analyze(file_path)

    A->>A: Load file content
    A->>C: get(agent, file_path, content)
    C->>C: Compute hash: a3f5b9c2
    C->>C: Check .cache/controller_a3f5b9c2.pkl
    C->>C: File exists, not expired
    C->>C: Load pickle

    C-->>A: Cached result

    A->>A: Add cached=true to metadata
    A-->>M: {analysis: {...}, metadata: {cached: true, cost: 0}}
    M-->>U: Analysis result (instant, $0)

    Note over U,C: 60% of queries end here<br/>Saves ~$0.002 per file
```

### 3. Model Escalation (Haiku → Sonnet)

```mermaid
sequenceDiagram
    participant A as Agent
    participant R as ModelRouter
    participant H as Haiku API
    participant S as Sonnet API

    A->>R: query(complex_prompt, complexity="medium")

    R->>H: Try Haiku first
    H-->>R: Response (confidence: 0.75)

    R->>R: Extract confidence: 0.75
    R->>R: Check threshold: 0.75 < 0.9 ✗
    R->>R: Escalate to Sonnet

    Note over R: Log: "Haiku low confidence (0.75),<br/>escalating to Sonnet"

    R->>S: Same prompt to Sonnet
    S-->>R: Response (confidence: 0.88)

    R->>R: Extract confidence: 0.88
    R->>R: Check threshold: 0.88 >= 0.85 ✓

    R-->>A: {response, model: "sonnet", cost: $0.015,<br/>confidence: 0.88, escalations: 1}

    Note over A,S: Cost increased 6x ($0.002 → $0.015)<br/>but accuracy improved (0.75 → 0.88)
```

---

## State Diagrams

### 1. Analysis State Machine

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> LoadingFile: analyze(file_path)
    LoadingFile --> CheckingCache: File loaded

    CheckingCache --> ReturningCached: Cache hit
    CheckingCache --> BuildingPrompt: Cache miss

    BuildingPrompt --> QueryingLLM: Prompt ready
    QueryingLLM --> ProcessingResponse: LLM responded
    QueryingLLM --> Escalating: Low confidence

    Escalating --> QueryingLLM: Try higher model
    Escalating --> Failed: Max escalations

    ProcessingResponse --> Validating: JSON extracted
    ProcessingResponse --> Failed: Parse error

    Validating --> SavingCache: Valid
    Validating --> Failed: Invalid

    SavingCache --> TrackingCost: Cached
    TrackingCost --> Completed: Cost recorded

    ReturningCached --> Completed: Instant return
    Completed --> [*]
    Failed --> [*]
```

### 2. Model Router State Machine

```mermaid
stateDiagram-v2
    [*] --> CheckComplexity

    CheckComplexity --> TryHaiku: simple/medium
    CheckComplexity --> TrySonnet: complex

    TryHaiku --> CheckHaikuConf: Response received
    CheckHaikuConf --> ReturnHaiku: conf >= 0.9
    CheckHaikuConf --> TrySonnet: conf < 0.9

    TrySonnet --> CheckSonnetConf: Response received
    CheckSonnetConf --> ReturnSonnet: conf >= 0.85
    CheckSonnetConf --> TryOpus: conf < 0.85

    TryOpus --> ReturnOpus: Response received

    ReturnHaiku --> [*]
    ReturnSonnet --> [*]
    ReturnOpus --> [*]

    note right of ReturnHaiku
        70% of cases
        $0.25/1M tokens
    end note

    note right of ReturnSonnet
        25% of cases
        $3/1M tokens
    end note

    note right of ReturnOpus
        5% of cases
        $15/1M tokens
    end note
```

### 3. Cache Entry Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Empty: Cache miss

    Empty --> Fresh: save(result)
    Fresh --> Accessed: get() within TTL
    Accessed --> Fresh: Still valid

    Fresh --> Stale: TTL exceeded
    Stale --> Evicted: Cleanup task
    Evicted --> [*]

    Fresh --> Invalidated: clear() or max_size
    Invalidated --> [*]

    note right of Fresh
        TTL: 30 days
        Max size: 10,000 entries
    end note
```

---

## Class Diagrams

### 1. Core Infrastructure Classes

```mermaid
classDiagram
    class ModelRouter {
        +MODELS: Dict
        +THRESHOLDS: Dict
        -client: Anthropic
        -logger: Logger

        +query(prompt, complexity, max_tokens) Dict
        -_query_model(tier, prompt, max_tokens) Dict
        -_extract_confidence(response) float
        -_calculate_cost(tier, tokens) float
    }

    class PromptManager {
        +prompts_dir: Path
        +base_prompts: Dict
        +examples: Dict
        +learned_patterns: List

        +build_prompt(template, context, examples) str
        +learn_from_result(template, input, output, feedback)
        -_load_base_prompts() Dict
        -_load_examples() Dict
        -_format_examples(examples) str
        -_save_learned_pattern(template, pattern)
    }

    class CacheManager {
        +cache_dir: Path
        +ttl_days: int
        +max_cache_size: int
        +stats: Dict

        +get(agent, file_path, content) Dict
        +save(agent, file_path, content, result)
        +get_stats() Dict
        +clear(older_than_days)
        -_compute_cache_key(agent, file, content) str
        -_is_expired(cache_file) bool
    }

    class CostTracker {
        +output_file: Path
        +budget_per_project: float
        +alert_threshold: float
        +session_costs: List
        +total_cost: float

        +record(agent, model, tokens, cost)
        +get_summary() Dict
        +print_summary()
        +project_cost(remaining, avg) float
        +check_budget() Dict
    }

    class BaseAgent {
        <<abstract>>
        +agent_name: str
        +model_router: ModelRouter
        +prompt_manager: PromptManager
        +cost_tracker: CostTracker
        +cache_manager: CacheManager

        +analyze(file_path)* Dict
        #_query_llm(prompt) Dict
        #_load_file_with_context(path) str
        #_extract_json_from_response(response) Dict
        +validate_result(result) bool
    }

    BaseAgent --> ModelRouter: uses
    BaseAgent --> PromptManager: uses
    BaseAgent --> CacheManager: uses
    BaseAgent --> CostTracker: uses
```

### 2. Agent Classes

```mermaid
classDiagram
    class ControllerAgent {
        +analyze(file_path) Dict
        -_extract_mappings(code) List
        -_extract_dependencies(code) List
        -_combine_paths(class_path, method_path) str
    }

    class JSPAgent {
        +analyze(file_path) Dict
        -_extract_includes(html) List
        -_extract_ajax_calls(script) List
        -_extract_forms(html) List
        -_extract_el_expressions(content) List
    }

    class ServiceAgent {
        +analyze(file_path) Dict
        -_extract_transactional(code) bool
        -_extract_mapper_dependencies(code) List
        -_extract_business_methods(code) List
    }

    class MapperAgent {
        +analyze(file_path) Dict
        -_parse_xml(content) Dict
        -_extract_sql_statements(xml) List
        -_detect_procedure_calls(xml) List
        -_extract_parameter_types(statement) List
    }

    class ProcedureAgent {
        +analyze(procedure_name) Dict
        -_fetch_procedure_source(name) str
        -_infer_business_purpose(source) str
        -_detect_trigger_method(name, metadata) str
        -_analyze_impact(source) Dict
    }

    BaseAgent <|-- ControllerAgent
    BaseAgent <|-- JSPAgent
    BaseAgent <|-- ServiceAgent
    BaseAgent <|-- MapperAgent
    BaseAgent <|-- ProcedureAgent
```

### 3. Graph Classes

```mermaid
classDiagram
    class GraphBuilder {
        +graph: nx.DiGraph
        +node_counter: Dict

        +build_from_results(results) Graph
        +add_node(id, type, properties) str
        +add_edge(source, target, relation, attrs)
        +validate() List~str~
        +save(output_path)
        -_create_node_id(type, name) str
    }

    class QueryEngine {
        +graph: nx.DiGraph
        +edge_lookup: Dict

        +find_call_chains(start, end, max_depth, max_paths) List
        +find_impact(node_id) Dict
        +find_dependencies(node_id) Dict
        +find_orphans(node_type) List
        +find_cycles() List
        -_build_edge_lookup_map()
        -_dfs_paths(start, end, visited, path, results)
    }

    class Visualizer {
        +graph: nx.DiGraph
        +output_dir: Path

        +generate_mermaid(output_path) str
        +generate_pyvis(output_path, max_nodes) str
        +generate_graphml(output_path) str
        +generate_subgraph(node_ids, output_path)
        -_node_color(node_type) str
        -_node_shape(node_type) str
    }

    GraphBuilder --> QueryEngine: provides graph
    QueryEngine --> Visualizer: provides graph
```

---

## Deployment Diagrams

### 1. Local Development Setup

```mermaid
graph TB
    subgraph "Developer Laptop"
        subgraph "Terminal"
            CC[Claude Code CLI]
        end

        subgraph "Python Process"
            MCP[MCP Server<br/>Port: 5173]
            Agents[Agents<br/>In-Memory]
            Cache[File Cache<br/>.cache/]
        end

        subgraph "File System"
            Config[config/<br/>config.yaml]
            Prompts[prompts/<br/>templates + examples]
            Output[output/<br/>results + graphs]
        end
    end

    subgraph "External Network"
        API[Anthropic API<br/>api.anthropic.com:443]
        DB[(Oracle DB<br/>Optional)]
    end

    CC <-->|MCP Protocol<br/>stdio| MCP
    MCP <--> Agents
    Agents <--> Cache

    MCP -.->|Read| Config
    Agents -.->|Read| Prompts
    Agents -.->|Write| Output

    Agents -->|HTTPS| API
    Agents -.->|TCP/1521| DB

    style CC fill:#e1f5ff
    style MCP fill:#ffe1e1
    style API fill:#fff4e1
```

### 2. Multi-Worker Parallel Processing

```mermaid
graph LR
    subgraph "Main Process"
        Main[Main Thread]
        Queue[Task Queue]
    end

    subgraph "Worker Pool"
        W1[Worker 1<br/>Controller Agent]
        W2[Worker 2<br/>JSP Agent]
        W3[Worker 3<br/>Service Agent]
        W4[Worker 4<br/>Mapper Agent]
    end

    subgraph "Shared Resources"
        Cache[(Cache Manager<br/>Thread-Safe)]
        Cost[(Cost Tracker<br/>Thread-Safe)]
    end

    subgraph "External"
        API[Anthropic API<br/>Rate Limited]
    end

    Main -->|Enqueue Tasks| Queue
    Queue --> W1
    Queue --> W2
    Queue --> W3
    Queue --> W4

    W1 <-->|Lock-Free Read| Cache
    W2 <-->|Lock-Free Read| Cache
    W3 <-->|Lock-Free Read| Cache
    W4 <-->|Lock-Free Read| Cache

    W1 -->|Atomic Write| Cost
    W2 -->|Atomic Write| Cost
    W3 -->|Atomic Write| Cost
    W4 -->|Atomic Write| Cost

    W1 -->|Rate Limited| API
    W2 -->|Rate Limited| API
    W3 -->|Rate Limited| API
    W4 -->|Rate Limited| API

    style Queue fill:#ffcc99
    style Cache fill:#99ff99
    style Cost fill:#ff9999
```

### 3. Production Deployment (Future)

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[nginx<br/>Round Robin]
    end

    subgraph "API Tier"
        API1[Flask API 1<br/>Port 8000]
        API2[Flask API 2<br/>Port 8001]
    end

    subgraph "Worker Tier"
        W1[Celery Worker 1]
        W2[Celery Worker 2]
        W3[Celery Worker 3]
    end

    subgraph "Storage Tier"
        Redis[(Redis<br/>Cache + Queue)]
        PG[(PostgreSQL<br/>Results)]
        S3[(S3<br/>Graphs)]
    end

    subgraph "External"
        Claude[Anthropic API]
    end

    Internet --> LB
    LB --> API1
    LB --> API2

    API1 --> Redis
    API2 --> Redis

    Redis --> W1
    Redis --> W2
    Redis --> W3

    W1 --> Claude
    W2 --> Claude
    W3 --> Claude

    W1 --> PG
    W2 --> PG
    W3 --> PG

    API1 --> S3
    API2 --> S3

    style LB fill:#ff9999
    style Redis fill:#99ff99
    style PG fill:#99ccff
```

---

## Decision Trees

### 1. Agent Selection Decision Tree

```mermaid
graph TD
    Start{File<br/>Extension?}

    Start -->|.java| JavaFile{Contains?}
    Start -->|.jsp| JSPAgent[JSP Agent]
    Start -->|.xml| XMLFile{File Name?}
    Start -->|.sql| ProcedureAgent[Procedure Agent]

    JavaFile -->|@Controller<br/>@RestController| ControllerAgent[Controller Agent]
    JavaFile -->|@Service<br/>@Component| ServiceAgent[Service Agent]
    JavaFile -->|interface<br/>Mapper| JavaValidator[Java Validator<br/>Then Manual]

    XMLFile -->|*Mapper.xml| MapperAgent[Mapper Agent]
    XMLFile -->|Other| Skip[Skip Analysis]

    ControllerAgent --> End
    JSPAgent --> End
    ServiceAgent --> End
    MapperAgent --> End
    ProcedureAgent --> End
    Skip --> End

    End([Route to Agent])
```

### 2. Cost Optimization Decision Tree

```mermaid
graph TD
    Start{New Query}

    Start --> CheckCache{Cache<br/>Exists?}

    CheckCache -->|Yes| CheckFresh{Fresh?<br/>< 30 days}
    CheckCache -->|No| Complexity

    CheckFresh -->|Yes| Return[Return Cached<br/>💰 $0]
    CheckFresh -->|No| Complexity{File<br/>Complexity?}

    Complexity -->|Simple<br/>Standard patterns| Haiku[Query Haiku<br/>💰 $0.002]
    Complexity -->|Medium<br/>Some nesting| HaikuTry[Try Haiku First<br/>💰 $0.002]
    Complexity -->|Complex<br/>Edge cases| Sonnet[Query Sonnet<br/>💰 $0.015]

    Haiku --> SaveCache
    HaikuTry --> HConf{Confidence<br/>>= 0.9?}

    HConf -->|Yes| SaveCache[Save to Cache]
    HConf -->|No| Sonnet

    Sonnet --> SConf{Confidence<br/>>= 0.85?}
    SConf -->|Yes| SaveCache
    SConf -->|No| Opus[Query Opus<br/>💰 $0.075]

    Opus --> SaveCache
    SaveCache --> Track[Track Cost]
    Track --> End

    Return --> End([Complete])

    style Return fill:#99ff99
    style Haiku fill:#99ccff
    style Sonnet fill:#ffcc99
    style Opus fill:#ff9999
```

---

## Metrics & Monitoring

### 1. Performance Metrics Dashboard

```mermaid
graph LR
    subgraph "Analysis Metrics"
        A1[Files Analyzed<br/>Target: 30/min]
        A2[Avg Latency<br/>Target: < 2s]
        A3[Error Rate<br/>Target: < 5%]
    end

    subgraph "Cost Metrics"
        C1[Total Cost<br/>Budget: $5]
        C2[Cost per File<br/>Target: < $0.05]
        C3[Cache Hit Rate<br/>Target: >= 60%]
    end

    subgraph "Quality Metrics"
        Q1[Avg Confidence<br/>Target: >= 0.85]
        Q2[Validation Pass<br/>Target: >= 95%]
        Q3[Graph Coverage<br/>Target: >= 90%]
    end

    subgraph "Model Metrics"
        M1[Haiku Usage<br/>Target: 70%]
        M2[Sonnet Usage<br/>Target: 25%]
        M3[Opus Usage<br/>Target: 5%]
    end

    style A1 fill:#e1f5ff
    style C1 fill:#ffe1e1
    style Q1 fill:#e1ffe1
    style M1 fill:#fff4e1
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-05
**Maintained By**: Development Team

---

## How to Use These Diagrams

### 1. For Understanding Architecture
- Start with **Layer Architecture** diagram
- Review **Component Relationship** diagrams
- Study **Data Flow** diagrams

### 2. For Implementation
- Reference **Sequence Diagrams** for interaction patterns
- Check **State Diagrams** for logic flow
- Use **Class Diagrams** for API contracts

### 3. For Debugging
- Trace through **Sequence Diagrams**
- Check **State Machines** for invalid states
- Review **Data Flow** for bottlenecks

### 4. For Cost Optimization
- Study **Model Router Decision Tree**
- Review **Cost Optimization Decision Tree**
- Monitor **Cost Metrics** dashboard

---

**All diagrams are Mermaid-compatible and can be rendered in:**
- GitHub Markdown
- GitLab
- Obsidian
- VS Code (with Mermaid extension)
- Online: mermaid.live
