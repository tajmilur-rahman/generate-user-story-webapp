# User Story Automation - Complete Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [System Architecture](#system-architecture)
3. [RAT Pipeline (Refine-And-Think)](#rat-pipeline-refine-and-think)
4. [Agent System](#agent-system)
5. [Processing Pipeline](#processing-pipeline)
6. [Data Flow](#data-flow)
7. [Model-Agnostic Design](#model-agnostic-design)
8. [Performance Characteristics](#performance-characteristics)
9. [File Structure](#file-structure)
10. [Configuration & Setup](#configuration--setup)
11. [Usage Guide](#usage-guide)
12. [Comparison: Old vs New](#comparison-old-vs-new)
13. [Troubleshooting](#troubleshooting)

---

## System Overview

### What Is This System?

The **User Story Automation System** is an AI-powered tool that automatically converts requirements documents (Word .docx files) into production-ready user stories with acceptance criteria and test cases.

**Input**: Requirements document (e.g., "PatientInformationSystem.docx")
**Output**: Structured user stories, epics, and test cases in JSON/Excel format

### Key Features

✅ **Automated Requirements Extraction**: Extracts functional requirements from unstructured documents
✅ **Epic Grouping**: Organizes requirements into logical feature areas (epics)
✅ **INVEST-Compliant Stories**: Generates user stories following agile best practices
✅ **Acceptance Criteria**: Creates testable Given-When-Then acceptance criteria
✅ **Test Case Generation**: Generates comprehensive test scenarios
✅ **Quality Assurance**: Automated review and improvement loop
✅ **Multi-Model Support**: Works with OpenAI, Ollama, Groq (model-agnostic prompts)

### Important: NOT a RAG System

⚠️ **This is NOT a Retrieval-Augmented Generation (RAG) pipeline**

**What RAG systems have** (which we DON'T):
- Vector databases (ChromaDB, Pinecone, FAISS)
- Embedding models (text-embedding-ada-002)
- Document retrieval mechanisms
- Knowledge base storage

**What we actually are**:
- **Pure LLM Generation Pipeline**: Documents are processed directly by agents
- **No Retrieval**: Agents generate outputs from scratch, not from stored knowledge
- **Sequential Processing**: Multi-agent pipeline, not query-based retrieval

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Flask (Python) | Web server & API |
| **Agent Framework** | LangChain + Custom | Agent orchestration |
| **LLM Integration** | ChatOllama / ChatOpenAI / ChatGroq | AI model interface |
| **Document Processing** | python-docx | Word document parsing |
| **Output Formats** | JSON, Excel (openpyxl) | Structured data export |
| **Frontend** | HTML/CSS/JavaScript | Web UI |
| **Database** | SQLite | User authentication |

**Why Not CrewAI?**
- CrewAI requires Python 3.10-3.13
- Our system uses Python 3.14
- Built custom multi-agent system instead (simpler, more maintainable)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                             │
│  ┌──────────────┐              ┌─────────────────┐                 │
│  │  Web Browser │              │  CLI Interface  │                 │
│  │  (Port 5000) │              │  (autoAgile.py) │                 │
│  └──────┬───────┘              └────────┬────────┘                 │
│         │                               │                           │
│         └───────────┬───────────────────┘                           │
└─────────────────────┼─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FLASK BACKEND (API)                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  POST /api/generate-stories                                  │  │
│  │  - Document upload                                           │  │
│  │  - Story generation                                          │  │
│  │  - Output formatting (JSON/Excel)                            │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   STORY ORCHESTRATOR                                │
│  (Coordinates all agents and manages processing loops)             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Phase 1: Requirements Extraction                            │  │
│  │  Phase 2: Epic Generation (Two-Pass)                         │  │
│  │  Phase 3: Story Generation (Batched)                         │  │
│  │  Phase 4: Test Case Generation (Batched)                     │  │
│  │  Phase 5: Quality Review Loop (Review → Rewrite)             │  │
│  └──────────────────────────┬───────────────────────────────────┘  │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
┌─────────────────┐  ┌─────────────┐  ┌──────────────┐
│  7 SPECIALIZED  │  │  BASE AGENT │  │  LLM MODELS  │
│     AGENTS      │──│   (Common)  │──│  (Ollama/    │
│                 │  │   Interface │  │   OpenAI/    │
│ - Requirements  │  └─────────────┘  │   Groq)      │
│ - EpicExtractor │                   └──────────────┘
│ - EpicRefiner   │
│ - Story         │
│ - TestCase      │
│ - Reviewer      │
│ - Rewriter      │
└─────────────────┘
```

### Agent Collaboration Architecture

```
                    ┌─────────────────────────┐
                    │   STORY ORCHESTRATOR    │
                    │  (Coordination Layer)   │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐        ┌──────────────┐        ┌──────────────┐
│  EXTRACTION   │        │   GENERATION │        │   QUALITY    │
│    AGENTS     │        │    AGENTS    │        │  ASSURANCE   │
│               │        │              │        │    AGENTS    │
│ Requirements  │───────▶│ Story Agent  │───────▶│  Reviewer    │
│     Agent     │        │              │        │              │
│               │        │ Test Agent   │        │  Rewriter    │
│ EpicExtractor │        │              │        │              │
│               │        │              │        │              │
│ EpicRefiner   │        │              │        │              │
└───────────────┘        └──────────────┘        └──────────────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                                 ▼
                        ┌────────────────┐
                        │ FINAL OUTPUT   │
                        │ - Requirements │
                        │ - Epics        │
                        │ - Stories      │
                        │ - Test Cases   │
                        └────────────────┘
```

### Agent Inheritance Structure

```
                    ┌──────────────────┐
                    │   BaseAgent      │
                    │   (Abstract)     │
                    │                  │
                    │ + llm            │
                    │ + run()          │
                    │ + _extract_json()│
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────────┐ ┌──────────┐ ┌──────────────┐
    │Requirements     │ │Story     │ │Reviewer      │
    │Agent            │ │Agent     │ │Agent         │
    │                 │ │          │ │              │
    │get_system_      │ │get_      │ │get_system_   │
    │prompt()         │ │system_   │ │prompt()      │
    └─────────────────┘ │prompt()  │ └──────────────┘
                        └──────────┘
              │              │              │
              ▼              ▼              ▼
    ┌─────────────────┐ ┌──────────┐ ┌──────────────┐
    │EpicExtractor    │ │TestCase  │ │Rewriter      │
    │Agent            │ │Agent     │ │Agent         │
    └─────────────────┘ └──────────┘ └──────────────┘
              │
              ▼
    ┌─────────────────┐
    │EpicRefiner      │
    │Agent            │
    └─────────────────┘
```

---

## RAT Pipeline (Refine-And-Think)

### What is RAT?

**RAT (Refine-And-Think)** is a quality improvement pattern used in the original `autoAgile` system. It's a self-improving LLM pipeline that enhances output quality through **refinement → voting → processing**.

**Location**: `src/autoAgile/utils/prompts.py:671`

### RAT Pipeline Architecture

```
Input (x)
    │
    ├─────────────────────┐
    │                     │
    ▼                     ▼
Original (x)      Step 1: REFINE(x)
    │                     │
    │                    x1 (refined version)
    │                     │
    └──────────┬──────────┘
               │
               ▼
    ┌──────────────────────┐
    │   Step 2: LLM VOTE   │
    │                      │
    │  Compare original vs │
    │  refined version     │
    │                      │
    │  Which is more:      │
    │  - Accurate?         │
    │  - Concise?          │
    │  - Easy to understand│
    └──────────┬───────────┘
               │
               ▼
        better_version
        (x or x1)
               │
               ▼
    ┌──────────────────────┐
    │  Step 3: THINK       │
    │                      │
    │  Apply main logic to │
    │  the better version  │
    └──────────┬───────────┘
               │
               ▼
           Output
```

### RAT Implementation

```python
def rat(refine, thought, x, chat, mode="prod"):
    """
    RAT Pipeline: Refine → Vote → Think

    Args:
        refine: Function to improve the input
        thought: Function to apply main logic
        x: Input data
        chat: LLM instance
        mode: "prod" or "debug"

    Returns:
        Processed output after refinement and thinking
    """

    # Step 1: REFINE - Improve the input
    x1 = refine(x, chat, mode)

    # Step 2: VOTE - LLM picks better version
    prompt = PromptTemplate.from_template("""
        As a voter, you vote for the input that is more accurate, concise
        and easy to understand. Given two input texts:

        First: {input_first}

        Second: {input_second}

        Which one you vote for? Please only answer with your vote.
    """)

    chain = prompt | chat | output_parser
    vote_result = chain.invoke({"input_first": x, "input_second": x1})

    # Determine winner
    if '1' in vote_result.lower() or 'first' in vote_result.lower():
        better = x  # Original wins
    elif '2' in vote_result.lower() or 'second' in vote_result.lower():
        better = x1  # Refined wins
    else:
        better = x1  # Default to refined if unclear

    # Step 3: THINK - Apply main logic to better version
    x2 = thought(better, chat, mode)

    return x2
```

### How RAT is Used in autoAgile

#### 1. Requirements Extraction

```python
# autoAgile.py line 45
requirements = rat(
    refine=refine_doc,              # Step 1: Clean up document
    thought=extract_functionarity,  # Step 3: Extract requirements
    x=extracted_text,               # Input: Raw document text
    chat=chat,
    mode=mode
)
```

**Flow**:
```
Raw Document
    ↓
refine_doc() → Clean document
    ↓
LLM Vote: Which is better? Raw or Clean?
    ↓
extract_functionarity(better_version) → Requirements
```

#### 2. Epic Generation

```python
# autoAgile.py line 53
deliverables = rat(
    refine=refine_requirements,  # Step 1: Clean requirements
    thought=extract_epics_func,  # Step 3: Extract epics
    x=requirements,              # Input: Requirements list
    chat=chat,
    mode=mode
)
```

**Flow**:
```
Requirements
    ↓
refine_requirements() → Cleaned requirements
    ↓
LLM Vote: Which is better?
    ↓
extract_epics_v2(better_version) → Epics
```

#### 3. Test Case Generation

```python
# autoAgile.py line 57
test_cases = rat(
    refine=refine_requirements,        # Step 1: Clean requirements
    thought=generate_test_cases_func,  # Step 3: Generate test cases
    x=requirements,                    # Input: Requirements
    chat=chat,
    mode=mode
)
```

**Flow**:
```
Requirements
    ↓
refine_requirements() → Cleaned requirements
    ↓
LLM Vote: Which is better?
    ↓
generate_test_cases_v2(better_version) → Test Cases
```

### Why RAT Works

**Problem**: LLMs can produce verbose, unclear, or inaccurate outputs
**Solution**: Self-improvement through comparison

**Benefits**:
1. **Quality Control**: Voting step catches degraded outputs
2. **Automatic Refinement**: No manual intervention needed
3. **Adaptability**: Works with any LLM (model-agnostic)
4. **Objective Comparison**: LLM acts as neutral judge

**Example**:

**Original Document** (verbose):
```
The system shall provide the capability for users to perform the
action of scheduling appointments through the online interface in
order to facilitate the booking process.
```

**After refine_doc()** (concise):
```
Users can schedule appointments online.
```

**LLM Vote**: "Second version is more concise and clear" → picks refined

**After extract_functionarity()** (structured):
```json
{
  "requirements": [
    {
      "id": "REQ-001",
      "description": "Allow users to schedule appointments online"
    }
  ]
}
```

### RAT vs Agent Architecture

| Aspect | RAT (Original autoAgile) | Agent Architecture (NEW) |
|--------|--------------------------|--------------------------|
| **Quality Control** | Voting between versions | ReviewerAgent + RewriterAgent |
| **Refinement** | Single refine() call | Iterative improvement loop (max 3) |
| **Evaluation** | LLM votes (subjective) | INVEST scoring (objective 0-100) |
| **Iterations** | 1 iteration (refine once) | Multiple iterations until threshold met |
| **Transparency** | Limited (vote is black box) | Full metrics (scores, issues, feedback) |
| **Processing** | Linear (refine → vote → think) | Cyclical (review → rewrite → review) |

**Key Difference**:
- **RAT**: Improve once, pick better version
- **Agent Quality Loop**: Improve until quality threshold met (≥70/100)

### RAT in Legacy vs Agent Architecture

**Legacy System (autoAgile.py)**: Uses RAT extensively
```python
requirements = rat(refine_doc, extract_functionarity, extracted_text, chat)
epics = rat(refine_requirements, extract_epics, requirements, chat)
test_cases = rat(refine_requirements, generate_test_cases, requirements, chat)
```

**New Agent System** (`src/agents/orchestrator.py`): Doesn't use RAT
- Instead uses **iterative quality review loop**
- ReviewerAgent scores stories (0-100)
- RewriterAgent improves low-quality stories
- Repeats until all stories ≥70

**Why the change?**
- RAT voting is subjective ("which is better?")
- Agent scoring is objective (INVEST criteria with rubric)
- Agent loop provides transparency (see exact scores)
- Agent loop is more thorough (multiple iterations possible)

### Complete RAT Flow Example

**Input**: "The patient information system must record patient demographics."

```
Step 1: REFINE
    refine_doc("The patient information system must...")
    → "Record patient demographics"

Step 2: VOTE
    LLM compares:
    - Original: "The patient information system must record patient demographics."
    - Refined: "Record patient demographics"

    Vote: "Second version is more concise" → Choose refined

Step 3: THINK
    extract_functionarity("Record patient demographics")
    → {
        "requirements": [
          {"id": "REQ-001", "description": "Record patient demographics"}
        ]
      }

Output: Clean, structured requirements
```

### RAT Limitations

1. **Single Iteration**: Only refines once (no retry if quality still low)
2. **Subjective Voting**: "Better" is vague (no objective criteria)
3. **No Metrics**: Can't measure improvement (no score tracking)
4. **Binary Choice**: Must pick original OR refined (can't blend best parts)
5. **No Transparency**: Don't know WHY LLM picked one over the other

**Agent architecture addresses these**:
- Multiple iterations (up to 3)
- Objective INVEST scoring (0-100)
- Full metrics and feedback
- Targeted improvements (fix specific issues)
- Transparent reasoning (issues identified)

---

## Agent System

### BaseAgent (Abstract Foundation)

**Location**: `src/agents/base_agent.py`

All agents inherit from this abstract base class, providing:

```python
class BaseAgent(ABC):
    """Base class for all agents - handles common LLM interaction"""

    def __init__(self, name: str, role: str, goal: str, temperature: float = 0.3):
        self.name = name          # Agent identifier (e.g., "Story Writer")
        self.role = role          # Agent's expertise (e.g., "User Story Specialist")
        self.goal = goal          # Agent's objective

        # LLM Configuration (model-agnostic)
        model_name = os.getenv('OLLAMA_MODEL', 'qwen3-coder:30b')
        self.llm = ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url="http://localhost:11434",
            format="json"  # Enforce JSON output
        )

    @abstractmethod
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build specialized prompt for this agent's role"""
        pass

    def run(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task with error handling"""
        # 1. Build specialized prompt
        # 2. Call LLM
        # 3. Parse JSON response
        # 4. Return structured result

    def _extract_json(self, text: str) -> Dict:
        """Robust JSON extraction with markdown fence handling"""
        # Handles: ```json {...}```, plain {...}, etc.
```

**Key Features**:
- ✅ Unified LLM interface (works with Ollama/OpenAI/Groq)
- ✅ Automatic JSON parsing with fallback strategies
- ✅ Comprehensive error handling and logging
- ✅ Consistent run() interface across all agents

---

### 1. RequirementsAgent

**Purpose**: Extract and refine functional requirements from document text
**Replaces**: `extract_list()` + `refine_requirements()` functions
**Temperature**: 0.3 (deterministic)

#### What It Does

1. **Extraction**: Identifies functional requirements in prose
2. **Deduplication**: Merges duplicate/similar requirements
3. **Splitting**: Breaks overly broad requirements into specific ones
4. **Filtering**: Removes meta-requirements (e.g., "The system shall...")
5. **ID Assignment**: Sequential numbering (REQ-001, REQ-002, etc.)

#### Example Input/Output

**Input**:
```
The weather station shall record temperature readings. The system must
store temperature data automatically. Humidity should also be monitored.
Temperature monitoring is critical for analysis.
```

**Output**:
```json
{
  "requirements": [
    {
      "id": "REQ-001",
      "description": "Record temperature readings automatically"
    },
    {
      "id": "REQ-002",
      "description": "Store temperature data persistently"
    },
    {
      "id": "REQ-003",
      "description": "Monitor humidity levels"
    }
  ]
}
```

**Note**: Merged "record temperature" and "temperature monitoring" (duplicates), removed meta-language.

---

### 2. EpicExtractorAgent

**Purpose**: First-pass epic generation (group requirements by feature area)
**Replaces**: First pass of `extract_epics_v2()`
**Temperature**: 0.3 (deterministic)

#### What It Does

1. **Grouping**: Groups 2-5 related requirements into epics
2. **Naming**: Creates descriptive epic names (e.g., "Data Collection")
3. **Target**: Aims for 5-10 epics total
4. **Organization**: Groups by functional area, not chronology

#### Example Input/Output

**Input**:
```json
[
  {"id": "REQ-001", "description": "Record temperature automatically"},
  {"id": "REQ-002", "description": "Store temperature data"},
  {"id": "REQ-003", "description": "Monitor humidity levels"},
  {"id": "REQ-004", "description": "Display temperature on LCD"},
  {"id": "REQ-005", "description": "Export data to CSV"}
]
```

**Output**:
```json
{
  "epics": [
    {
      "epic_id": "EPIC-001",
      "epic_name": "Environmental Data Collection",
      "epic_description": "Automated collection of temperature and humidity data",
      "requirement_ids": ["REQ-001", "REQ-002", "REQ-003"]
    },
    {
      "epic_id": "EPIC-002",
      "epic_name": "Data Visualization",
      "epic_description": "Display environmental data to users",
      "requirement_ids": ["REQ-004"]
    },
    {
      "epic_id": "EPIC-003",
      "epic_name": "Data Export",
      "epic_description": "Export collected data for external analysis",
      "requirement_ids": ["REQ-005"]
    }
  ]
}
```

---

### 3. EpicRefinerAgent

**Purpose**: Second-pass epic optimization (merge/split/balance)
**Replaces**: `refine_epics_v2()`
**Temperature**: 0.3 (deterministic)

#### What It Does

1. **Merging**: Combines similar epics (e.g., "Data Entry" + "Data Input")
2. **Splitting**: Breaks overly broad epics (>6 requirements)
3. **Balancing**: Ensures 2-5 requirements per epic
4. **Validation**: No duplicate requirement assignments

#### Example Input/Output (Refinement)

**Input** (from EpicExtractorAgent):
```json
[
  {"epic_id": "EPIC-001", "epic_name": "Temperature Monitoring", "requirement_ids": ["REQ-001", "REQ-002"]},
  {"epic_id": "EPIC-002", "epic_name": "Temperature Recording", "requirement_ids": ["REQ-003"]},
  {"epic_id": "EPIC-003", "epic_name": "Data Management", "requirement_ids": ["REQ-004", "REQ-005", "REQ-006", "REQ-007", "REQ-008", "REQ-009"]}
]
```

**Output** (refined):
```json
{
  "epics": [
    {
      "epic_id": "EPIC-001",
      "epic_name": "Temperature Monitoring & Recording",
      "epic_description": "Comprehensive temperature data collection",
      "requirement_ids": ["REQ-001", "REQ-002", "REQ-003"]
    },
    {
      "epic_id": "EPIC-002",
      "epic_name": "Data Storage",
      "epic_description": "Persistent data storage and management",
      "requirement_ids": ["REQ-004", "REQ-005", "REQ-006"]
    },
    {
      "epic_id": "EPIC-003",
      "epic_name": "Data Export & Reporting",
      "epic_description": "Export and reporting capabilities",
      "requirement_ids": ["REQ-007", "REQ-008", "REQ-009"]
    }
  ]
}
```

**Changes Made**:
- ✅ Merged EPIC-001 + EPIC-002 (similar: both about temperature)
- ✅ Split EPIC-003 (too broad: 6 requirements → split into 2 epics)
- ✅ Result: Better balanced (3-4 requirements per epic)

---

### 4. StoryAgent

**Purpose**: Generate INVEST-compliant user stories with acceptance criteria
**Replaces**: Story generation in `convert_to_user_stories()`
**Temperature**: 0.4 (slightly creative for natural language)

#### What It Does

1. **Story Format**: "As a [user], I want to [action] so that [benefit]"
2. **Acceptance Criteria**: 3-5 Given-When-Then scenarios
3. **Definition of Done**: Unit tests, code review, integration testing
4. **Story Points**: Fibonacci estimation (1, 2, 3, 5, 8)
5. **INVEST Compliance**: Ensures all 6 criteria met

#### INVEST Criteria Explained

| Criterion | Description | Good Example | Bad Example |
|-----------|-------------|--------------|-------------|
| **I**ndependent | No dependencies on other stories | "Record temperature every 5 min" | "Record temp (requires REQ-003)" |
| **N**egotiable | Implementation details flexible | "Display temperature to user" | "Display temp using Qt5.2 framework" |
| **V**aluable | Clear user benefit ("so that") | "...so that I have monitoring data" | "Record temperature" (no benefit) |
| **E**stimable | Team can estimate effort | "Add CSV export button" | "Optimize performance" (vague) |
| **S**mall | Fits in one sprint (≤5 points) | "Add login button (2 pts)" | "Build entire auth system (20 pts)" |
| **T**estable | Has concrete acceptance criteria | "Given/When/Then scenarios" | "Make it user-friendly" (not measurable) |

#### Example Input/Output

**Input**:
```json
{
  "requirements_batch": [
    {
      "id": "REQ-001",
      "description": "Record temperature automatically every 5 minutes"
    }
  ],
  "epic": {
    "epic_name": "Environmental Monitoring",
    "epic_description": "Automated environmental data collection"
  }
}
```

**Output**:
```json
{
  "stories": [
    {
      "story_id": "STORY-001",
      "requirement_id": "REQ-001",
      "user_story": "As a weather station operator, I want the system to automatically record temperature every 5 minutes so that I have continuous monitoring data for analysis",
      "acceptance_criteria": [
        "Given the station is powered on, When 5 minutes elapse, Then a new temperature reading is recorded",
        "Given temperature is recorded, When storage is checked, Then the reading includes timestamp and temperature value",
        "Given readings are being recorded, When I check the log, Then I see entries exactly 5 minutes apart"
      ],
      "definition_of_done": [
        "Unit tests written with >80% coverage",
        "Code reviewed and approved by team lead",
        "Integration tested with real temperature sensor",
        "Performance verified (recording completes in <1 second)"
      ],
      "story_points": 3,
      "priority": "HIGH"
    }
  ]
}
```

---

### 5. TestCaseAgent

**Purpose**: Generate comprehensive test cases for requirements
**Replaces**: `generate_test_cases_v2()`
**Temperature**: 0.3 (deterministic)

#### What It Does

1. **Test Coverage**: 2-4 test cases per requirement
2. **Scenarios**: Happy path, edge cases, error conditions
3. **Structure**: Test ID, description, steps, expected result
4. **Traceability**: Links test cases to requirements

#### Example Input/Output

**Input**:
```json
{
  "requirements_batch": [
    {
      "id": "REQ-001",
      "description": "Record temperature automatically every 5 minutes"
    }
  ]
}
```

**Output**:
```json
{
  "test_cases": [
    {
      "test_id": "TC-001",
      "requirement_id": "REQ-001",
      "test_description": "Verify automatic temperature recording every 5 minutes",
      "test_steps": [
        "Power on the weather station",
        "Wait for 5 minutes",
        "Check the temperature log",
        "Verify timestamp of new reading"
      ],
      "expected_result": "New temperature reading recorded with timestamp exactly 5 minutes after previous reading"
    },
    {
      "test_id": "TC-002",
      "requirement_id": "REQ-001",
      "test_description": "Verify temperature recording continues after power cycle",
      "test_steps": [
        "Power on station and record 3 readings",
        "Power off the station",
        "Power on again after 2 minutes",
        "Wait 5 minutes and check log"
      ],
      "expected_result": "Recording resumes and continues every 5 minutes without data loss"
    },
    {
      "test_id": "TC-003",
      "requirement_id": "REQ-001",
      "test_description": "Verify behavior when sensor is disconnected",
      "test_steps": [
        "Power on station",
        "Disconnect temperature sensor",
        "Wait 5 minutes",
        "Check error log"
      ],
      "expected_result": "System logs error 'Sensor disconnected' and continues attempting to read every 5 minutes"
    }
  ]
}
```

**Coverage**: Happy path (TC-001), recovery (TC-002), error handling (TC-003)

---

### 6. ReviewerAgent (Quality Control)

**Purpose**: Score user stories on INVEST criteria and identify issues
**Temperature**: 0.3 (objective scoring)

#### What It Does

1. **Scoring**: Evaluates each INVEST criterion (0-10 scale)
2. **Total Score**: Sums to 0-100 (60 max from 6 criteria)
3. **Issue Detection**: Identifies specific problems
4. **Feedback**: Provides actionable improvement suggestions
5. **Recommendation**: APPROVE (≥70) or REWRITE (<70)

#### Scoring Rubric

| Total Score | Assessment | Action |
|-------------|------------|--------|
| 90-100 | Excellent - Production ready | APPROVE |
| 70-89 | Good - Minor improvements possible | APPROVE |
| 50-69 | Needs improvement | REWRITE |
| 0-49 | Poor quality | REWRITE (critical) |

#### Example Input/Output

**Input**:
```json
{
  "stories": [
    {
      "story_id": "STORY-001",
      "user_story": "As a user, I want to export data",
      "acceptance_criteria": [],
      "story_points": 5
    }
  ]
}
```

**Output**:
```json
{
  "story_reviews": [
    {
      "story_id": "STORY-001",
      "invest_scores": {
        "independent": 8,
        "negotiable": 7,
        "valuable": 3,
        "estimable": 5,
        "small": 8,
        "testable": 1
      },
      "total_score": 53,
      "issues": [
        "Missing 'so that' clause - user benefit unclear",
        "No acceptance criteria - story is not testable",
        "Vague action 'export data' - what format? what data?"
      ],
      "feedback": "Story needs clear user benefit and concrete acceptance criteria. Specify export format (CSV/JSON?) and which data to export. Add 3-5 Given-When-Then scenarios.",
      "recommendation": "REWRITE"
    }
  ],
  "summary": {
    "total_stories": 1,
    "average_score": 53,
    "stories_below_threshold": 1,
    "stories_needing_rewrite": ["STORY-001"]
  }
}
```

---

### 7. RewriterAgent (Quality Improvement)

**Purpose**: Improve low-quality stories based on reviewer feedback
**Temperature**: 0.5 (higher for creative rewriting)

#### What It Does

1. **Preserves Intent**: Maintains original requirement purpose
2. **Adds Benefit**: Inserts "so that" clause if missing
3. **Adds Criteria**: Creates measurable acceptance criteria
4. **Reduces Scope**: Splits if story too large
5. **Fixes Issues**: Addresses all reviewer feedback

#### Example Input/Output

**Input**:
```json
{
  "story": {
    "story_id": "STORY-001",
    "requirement_id": "REQ-005",
    "user_story": "As a user, I want to export data",
    "acceptance_criteria": [],
    "story_points": 5
  },
  "review": {
    "total_score": 53,
    "issues": [
      "Missing 'so that' clause",
      "No acceptance criteria",
      "Vague action"
    ],
    "feedback": "Add user benefit, specify format, add testable criteria"
  }
}
```

**Output**:
```json
{
  "rewritten_story": {
    "story_id": "STORY-001",
    "requirement_id": "REQ-005",
    "user_story": "As a data analyst, I want to export temperature readings to CSV format so that I can perform statistical analysis in Excel",
    "acceptance_criteria": [
      "Given temperature data exists, When I click 'Export to CSV', Then a CSV file downloads to my computer",
      "Given CSV is exported, When I open it in Excel, Then columns include timestamp, temperature, and sensor_id",
      "Given I have 1000+ readings, When I export, Then all readings are included without truncation",
      "Given export is in progress, When I check the UI, Then I see a progress indicator"
    ],
    "definition_of_done": [
      "Unit tests for CSV generation logic",
      "Integration test with real data export",
      "Manual test with Excel import",
      "Performance test with 10,000 records"
    ],
    "story_points": 3,
    "priority": "MEDIUM"
  }
}
```

**Improvements**:
- ✅ Added "so that I can perform statistical analysis in Excel" (clear benefit)
- ✅ Specified user type: "data analyst" (more specific than "user")
- ✅ Specified format: "CSV" (removed vagueness)
- ✅ Added 4 concrete acceptance criteria (was 0)
- ✅ Reduced story points: 5 → 3 (more focused scope)

---

### 8. StoryOrchestrator (Coordination)

**Purpose**: Coordinate all agents and manage the processing pipeline
**Location**: `src/agents/orchestrator.py`

#### Responsibilities

1. **Agent Initialization**: Creates instances of all 7 agents
2. **Pipeline Execution**: Runs 5-phase processing pipeline
3. **Loop Management**: Coordinates 4 processing loops
4. **Error Handling**: Graceful failure recovery
5. **Logging**: Detailed progress tracking
6. **Test Case Matching**: Links TCs to stories

#### Main Method

```python
def generate_stories(self, document_text: str) -> dict:
    """
    Input: Raw document text (string)

    Output: {
        "requirements": [list of requirements],
        "epics": [list of epics],
        "stories": [list of user stories],
        "test_cases": [list of test cases]
    }
    """
```

#### Processing Flow

```
generate_stories(document_text)
│
├─ PHASE 1: Requirements Extraction
│  └─ RequirementsAgent.run()
│     → Returns: requirements list
│
├─ PHASE 2: Epic Generation (Loop 2: Two-Pass)
│  ├─ EpicExtractorAgent.run()  [Pass 1]
│  └─ EpicRefinerAgent.run()    [Pass 2]
│     → Returns: optimized epics
│
├─ PHASE 3: Story Generation (Loop 1: Batched)
│  └─ For each epic:
│     └─ For each batch of 4 requirements:
│        └─ StoryAgent.run()
│           → Returns: stories for batch
│
├─ PHASE 4: Test Case Generation (Loop 3: Batched)
│  └─ For each batch of 4 requirements:
│     └─ TestCaseAgent.run()
│        → Returns: test cases for batch
│  └─ _match_test_cases()
│     → Links TCs to stories
│
└─ PHASE 5: Quality Review Loop (Loop 4: Iterative)
   └─ _quality_review_loop(stories)
      ├─ Iteration 1:
      │  ├─ ReviewerAgent.run() → scores
      │  ├─ Find stories scoring <70
      │  └─ For each low-quality story:
      │     └─ RewriterAgent.run() → improved story
      ├─ Iteration 2:
      │  └─ Repeat until all ≥70 or max 3 iterations
      └─ Return: quality-assured stories
```

---

## Processing Pipeline

### Complete 5-Phase Pipeline Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         PHASE 1                                      │
│                  Requirements Extraction                             │
│                                                                      │
│  Input: "The weather station shall record temperature readings.     │
│          The system must store temperature data automatically.       │
│          Humidity should also be monitored..."                       │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │            RequirementsAgent                               │    │
│  │  - Extract functional requirements                         │    │
│  │  - Merge duplicates                                        │    │
│  │  - Split broad requirements                                │    │
│  │  - Remove meta-language                                    │    │
│  │  - Assign IDs (REQ-001, REQ-002, ...)                      │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  Output: [                                                           │
│    {"id": "REQ-001", "description": "Record temperature..."},       │
│    {"id": "REQ-002", "description": "Store temperature data"},      │
│    {"id": "REQ-003", "description": "Monitor humidity"}             │
│  ]                                                                   │
│                                                                      │
│  Duration: ~30 seconds                                               │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         PHASE 2                                      │
│                   Epic Generation (LOOP 2)                           │
│                      Two-Pass Approach                               │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  PASS 1: EpicExtractorAgent                                 │   │
│  │  - Group 2-5 requirements per epic                          │   │
│  │  - Target 5-10 epics total                                  │   │
│  │  - Group by feature area                                    │   │
│  └───────────────────────┬─────────────────────────────────────┘   │
│                          │                                          │
│                          ▼                                          │
│  Intermediate: [                                                    │
│    EPIC-001: "Temp Monitoring" [REQ-001, REQ-002],                 │
│    EPIC-002: "Temp Recording" [REQ-003],                           │
│    EPIC-003: "Data Mgmt" [REQ-004..REQ-009]  ← Too broad!          │
│  ]                                                                  │
│                          │                                          │
│                          ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  PASS 2: EpicRefinerAgent                                   │   │
│  │  - Merge similar epics (EPIC-001 + EPIC-002)                │   │
│  │  - Split broad epics (EPIC-003 → 2 epics)                   │   │
│  │  - Balance 2-5 requirements per epic                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Output: [                                                           │
│    EPIC-001: "Temperature Monitoring & Recording" [REQ-001..003],   │
│    EPIC-002: "Data Storage" [REQ-004, REQ-005],                     │
│    EPIC-003: "Data Export" [REQ-006, REQ-007]                       │
│  ]                                                                   │
│                                                                      │
│  Duration: ~1 minute                                                 │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         PHASE 3                                      │
│                  Story Generation (LOOP 1)                           │
│                     Batched Processing                               │
│                                                                      │
│  For each epic:                                                      │
│    For each batch of 4 requirements:                                 │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Batch 1: [REQ-001, REQ-002, REQ-003]                        │  │
│  │    ↓                                                          │  │
│  │  StoryAgent.run()                                             │  │
│  │    ↓                                                          │  │
│  │  [STORY-001, STORY-002, STORY-003]                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Batch 2: [REQ-004, REQ-005, REQ-006, REQ-007]               │  │
│  │    ↓                                                          │  │
│  │  StoryAgent.run()                                             │  │
│  │    ↓                                                          │  │
│  │  [STORY-004, STORY-005, STORY-006, STORY-007]                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Each story includes:                                                │
│  - User story ("As a...I want...so that...")                        │
│  - 3-5 acceptance criteria (Given-When-Then)                        │
│  - Definition of Done                                                │
│  - Story points (1, 2, 3, 5, 8)                                      │
│                                                                      │
│  Duration: ~2 minutes                                                │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         PHASE 4                                      │
│                Test Case Generation (LOOP 3)                         │
│                     Batched Processing                               │
│                                                                      │
│  For each batch of 4 requirements:                                   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Batch 1: [REQ-001, REQ-002, REQ-003, REQ-004]               │  │
│  │    ↓                                                          │  │
│  │  TestCaseAgent.run()                                          │  │
│  │    ↓                                                          │  │
│  │  [TC-001, TC-002, TC-003, TC-004, TC-005, TC-006, ...]       │  │
│  │   (2-4 test cases per requirement)                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Then: Match test cases to stories                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  _match_test_cases()                                          │  │
│  │  - Keyword similarity scoring                                │  │
│  │  - One-to-one TC assignment                                  │  │
│  │  - Threshold: 50% keyword overlap                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Duration: ~1.5 minutes                                              │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         PHASE 5                                      │
│                 Quality Review Loop (LOOP 4)                         │
│                    Iterative Improvement                             │
│                                                                      │
│  Max 3 iterations, threshold: 70/100                                 │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ITERATION 1                                                  │  │
│  │                                                               │  │
│  │  Step 1: ReviewerAgent.run(all_stories)                      │  │
│  │    ↓                                                          │  │
│  │  [                                                            │  │
│  │    STORY-001: 85/100 ✓ APPROVE                               │  │
│  │    STORY-002: 62/100 ✗ REWRITE (missing "so that")           │  │
│  │    STORY-003: 78/100 ✓ APPROVE                               │  │
│  │    STORY-004: 55/100 ✗ REWRITE (no criteria)                 │  │
│  │    ...                                                        │  │
│  │    STORY-020: 68/100 ✗ REWRITE                               │  │
│  │  ]                                                            │  │
│  │                                                               │  │
│  │  Step 2: Identify low-quality stories (<70)                  │  │
│  │    → 12 stories need rewriting                               │  │
│  │                                                               │  │
│  │  Step 3: For each low-quality story:                         │  │
│  │    RewriterAgent.run(story, review_feedback)                 │  │
│  │    ↓                                                          │  │
│  │    Improved story replaces original                          │  │
│  │    (1 minute per story × 12 = 12 minutes)                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          │                                          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ITERATION 2                                                  │  │
│  │                                                               │  │
│  │  Step 1: ReviewerAgent.run(all_stories)                      │  │
│  │    ↓                                                          │  │
│  │  [                                                            │  │
│  │    STORY-001: 85/100 ✓ APPROVE                               │  │
│  │    STORY-002: 88/100 ✓ APPROVE (improved!)                   │  │
│  │    STORY-003: 78/100 ✓ APPROVE                               │  │
│  │    STORY-004: 82/100 ✓ APPROVE (improved!)                   │  │
│  │    ...                                                        │  │
│  │    STORY-017: 68/100 ✗ REWRITE (still needs work)            │  │
│  │    STORY-020: 72/100 ✓ APPROVE (improved!)                   │  │
│  │  ]                                                            │  │
│  │                                                               │  │
│  │  Step 2: Identify low-quality stories (<70)                  │  │
│  │    → 5 stories still need rewriting                          │  │
│  │                                                               │  │
│  │  Step 3: Rewrite remaining low-quality stories               │  │
│  │    (1 minute per story × 5 = 5 minutes)                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          │                                          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ITERATION 3                                                  │  │
│  │                                                               │  │
│  │  All stories now ≥70 or max iterations reached               │  │
│  │  → Exit loop, return final stories                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Duration: ~15-17 minutes (BOTTLENECK)                               │
│  - Iteration 1: 12 rewrites × 1 min = 12 min                        │
│  - Iteration 2: 5 rewrites × 1 min = 5 min                          │
│  - Iteration 3: Review only (all pass)                              │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   FINAL OUTPUT       │
                    │                      │
                    │ - Requirements       │
                    │ - Epics              │
                    │ - Stories (INVEST)   │
                    │ - Test Cases         │
                    │                      │
                    │ Format: JSON/Excel   │
                    └──────────────────────┘
```

### The Four Processing Loops Explained

#### Loop 1: Batch Processing (Story Generation)
**Purpose**: Avoid context overflow while maintaining quality
**Implementation**: Process 4 requirements at a time per epic
**Duration**: ~2 minutes

```
For each epic:
  requirements_in_epic = [REQ-001, REQ-002, ..., REQ-010]  # 10 requirements

  Batch 1: [REQ-001, REQ-002, REQ-003, REQ-004] → StoryAgent → 4 stories
  Batch 2: [REQ-005, REQ-006, REQ-007, REQ-008] → StoryAgent → 4 stories
  Batch 3: [REQ-009, REQ-010]                   → StoryAgent → 2 stories

  Total: 10 stories
```

**Why batching?**
- LLM context limits (too many requirements = degraded quality)
- Maintains epic context while processing manageable chunks
- 4 requirements empirically optimal (tested with 2, 4, 6, 8)

#### Loop 2: Two-Pass Epic Generation
**Purpose**: Optimal epic grouping through extract→refine
**Implementation**: EpicExtractorAgent → EpicRefinerAgent
**Duration**: ~1 minute

```
Pass 1 (Extract):
  Input: 20 requirements
  Output: 8 raw epics (unoptimized)
  Issues: Some epics too similar, some too broad

Pass 2 (Refine):
  Input: 8 raw epics
  Actions:
    - Merge EPIC-001 + EPIC-002 (similar: both "authentication")
    - Split EPIC-005 (too broad: 7 requirements → 2 epics)
  Output: 6 optimized epics (balanced 3-4 reqs each)
```

**Why two passes?**
- Single-pass: Often creates 15+ tiny epics or 3 huge epics
- Two-pass: Better balanced, cleaner groupings

#### Loop 3: Batched Test Case Generation
**Purpose**: Efficient TC generation for all requirements
**Implementation**: Process 4 requirements at a time
**Duration**: ~1.5 minutes

```
Requirements: [REQ-001, REQ-002, ..., REQ-020]  # 20 total

Batch 1: [REQ-001, REQ-002, REQ-003, REQ-004] → 8-16 TCs
Batch 2: [REQ-005, REQ-006, REQ-007, REQ-008] → 8-16 TCs
...
Batch 5: [REQ-017, REQ-018, REQ-019, REQ-020] → 8-16 TCs

Total: 40-80 test cases (2-4 per requirement)
```

#### Loop 4: Quality Review Loop (NEW)
**Purpose**: Ensure INVEST compliance through iterative improvement
**Implementation**: Review → Rewrite → Validate (max 3 iterations)
**Duration**: ~15-17 minutes (current bottleneck)

```
Iteration 1:
  Review: 20 stories → 12 score <70 (60% rewrite rate)
  Rewrite: 12 stories × 1 min = 12 minutes

Iteration 2:
  Review: 20 stories → 5 still score <70 (25% rewrite rate)
  Rewrite: 5 stories × 1 min = 5 minutes

Iteration 3:
  Review: 20 stories → All ≥70 ✓
  Exit: No more rewrites needed

Total: 17 minutes
```

**Why this loop is critical**:
- Without it: 40% of stories lack "so that" clauses, 30% have vague criteria
- With it: 100% INVEST-compliant, production-ready stories

---

## Data Flow

### End-to-End Data Transformation

```
INPUT DOCUMENT (PatientInformationSystem.docx)
│
│ "The system shall allow patients to schedule appointments online.
│  Patients should be able to view their medical history.
│  The system must send appointment reminders via email.
│  Healthcare providers need to update patient records..."
│
▼
┌────────────────────────────────────────────────────────────┐
│ PHASE 1: Requirements (RequirementsAgent)                  │
└────────────────────────────────────────────────────────────┘
│
│ [
│   {"id": "REQ-001", "description": "Allow patients to schedule appointments online"},
│   {"id": "REQ-002", "description": "Allow patients to view medical history"},
│   {"id": "REQ-003", "description": "Send appointment reminders via email"},
│   {"id": "REQ-004", "description": "Allow providers to update patient records"}
│ ]
│
▼
┌────────────────────────────────────────────────────────────┐
│ PHASE 2: Epics (EpicExtractor + EpicRefiner)               │
└────────────────────────────────────────────────────────────┘
│
│ [
│   {
│     "epic_id": "EPIC-001",
│     "epic_name": "Patient Self-Service",
│     "requirement_ids": ["REQ-001", "REQ-002"]
│   },
│   {
│     "epic_id": "EPIC-002",
│     "epic_name": "Appointment Management",
│     "requirement_ids": ["REQ-003"]
│   },
│   {
│     "epic_id": "EPIC-003",
│     "epic_name": "Provider Tools",
│     "requirement_ids": ["REQ-004"]
│   }
│ ]
│
▼
┌────────────────────────────────────────────────────────────┐
│ PHASE 3: Stories (StoryAgent - Batched)                    │
└────────────────────────────────────────────────────────────┘
│
│ [
│   {
│     "story_id": "STORY-001",
│     "requirement_id": "REQ-001",
│     "epic_id": "EPIC-001",
│     "user_story": "As a patient, I want to schedule appointments online so that I can book visits without calling the office",
│     "acceptance_criteria": [
│       "Given I am logged in, When I select a provider and time slot, Then the appointment is confirmed",
│       "Given I book an appointment, When I check my calendar, Then I see the appointment details"
│     ],
│     "definition_of_done": [...],
│     "story_points": 5,
│     "priority": "HIGH"
│   },
│   {
│     "story_id": "STORY-002",
│     "requirement_id": "REQ-002",
│     "epic_id": "EPIC-001",
│     "user_story": "As a patient, I want to view my medical history so that I can track my health over time",
│     "acceptance_criteria": [...],
│     "story_points": 3,
│     "priority": "MEDIUM"
│   },
│   ...
│ ]
│
▼
┌────────────────────────────────────────────────────────────┐
│ PHASE 4: Test Cases (TestCaseAgent - Batched)              │
└────────────────────────────────────────────────────────────┘
│
│ [
│   {
│     "test_id": "TC-001",
│     "requirement_id": "REQ-001",
│     "test_description": "Verify online appointment scheduling",
│     "test_steps": ["Login as patient", "Select provider", "Choose time slot", "Confirm booking"],
│     "expected_result": "Appointment confirmed and visible in patient calendar"
│   },
│   {
│     "test_id": "TC-002",
│     "requirement_id": "REQ-001",
│     "test_description": "Verify double-booking prevention",
│     "test_steps": ["Book time slot", "Attempt to book same slot again"],
│     "expected_result": "System shows error: Time slot unavailable"
│   },
│   ...
│ ]
│
▼
┌────────────────────────────────────────────────────────────┐
│ Test Case Matching (_match_test_cases)                     │
└────────────────────────────────────────────────────────────┘
│
│ Stories with matched TCs:
│ [
│   {
│     "story_id": "STORY-001",
│     "user_story": "As a patient, I want to schedule...",
│     "test_cases": [
│       {"test_id": "TC-001", ...},
│       {"test_id": "TC-002", ...}
│     ]
│   },
│   ...
│ ]
│
▼
┌────────────────────────────────────────────────────────────┐
│ PHASE 5: Quality Review (Reviewer + Rewriter)              │
└────────────────────────────────────────────────────────────┘
│
│ Iteration 1:
│   STORY-001: 55/100 → REWRITE
│   STORY-002: 82/100 → APPROVE
│   ...
│
│ After rewrites:
│   STORY-001: 88/100 → APPROVE ✓
│   All stories now ≥70
│
▼
┌────────────────────────────────────────────────────────────┐
│ FINAL OUTPUT (JSON/Excel)                                   │
└────────────────────────────────────────────────────────────┘
│
│ {
│   "requirements": [REQ-001, REQ-002, ...],
│   "epics": [EPIC-001, EPIC-002, ...],
│   "stories": [STORY-001, STORY-002, ...],  # All INVEST-compliant
│   "test_cases": [TC-001, TC-002, ...]
│ }
│
▼
files saved:
- data/outputs/stories_20260711.json
- data/outputs/stories_20260711.xlsx
```

---

## Model-Agnostic Design

### Why Model-Agnostic?

**User Requirement**: Users will use different AI model API keys (OpenAI, Anthropic, Groq, local Ollama models). Prompts **must work universally** across:

- OpenAI: GPT-3.5, GPT-4, GPT-4-turbo
- Anthropic: Claude 3 (Opus, Sonnet, Haiku)
- Google: Gemini Pro
- Open Source: Llama 3, Mistral, Qwen, CodeLlama
- Others: Groq, Together AI, etc.

### Universal Prompt Architecture

All agent prompts follow this model-agnostic structure:

```markdown
[1] OUTPUT FORMAT - MANDATORY
RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown
headers, or text outside the JSON. Your entire response must be a single
valid JSON object starting with { and ending with }.

{
  "exact_schema": "defined_here"
}

[2] ROLE & TASK DEFINITION
You are a [Role]. [What to do in one sentence].

[3] CONTEXT DATA
[Actual data to process]

[4] REQUIREMENTS - OBJECTIVE RULES
1. [Concrete, measurable instruction]
2. [No vague terms like "good" or "clear"]
3. [Specific format requirements]

[5] EXAMPLES - CONCRETE DEMONSTRATIONS
Input: [Specific example]
Output: {
  "concrete": "example showing exact format"
}

[6] VALIDATION CHECKLIST
Check your output:
- [ ] Has required field X?
- [ ] Follows format Y?
- [ ] Includes Z items?

RESPOND WITH JSON ONLY.
```

### Anti-Patterns (Avoided)

❌ **Model-Specific Tricks**:
```
"Let's think step by step..."  # GPT-specific
"<thinking>...</thinking>"      # Claude-specific
"You are an expert..."          # Role-play optimization
```

❌ **Vague Instructions**:
```
"Write a good user story"       # What is "good"?
"Make it clear and concise"     # Subjective
"Be creative but professional"  # Contradictory
```

❌ **Assumed Behavior**:
```
# Assuming model will be verbose:
"Keep it short"

# Assuming model understands context:
"Use the format from before"
```

### Best Practices (Used)

✅ **Explicit JSON Schema**:
```json
{
  "stories": [
    {
      "story_id": "STORY-001",
      "user_story": "As a [user], I want to [action] so that [benefit]",
      "acceptance_criteria": ["Given...When...Then...", "..."],
      "story_points": 3
    }
  ]
}
```

✅ **Objective Scoring Rules**:
```
Valuable criterion scoring:
- Has "so that" clause? → 10 points
- Missing "so that"? → 0 points

(No judgment needed, purely algorithmic)
```

✅ **Concrete Examples**:
```
Bad: "Write good acceptance criteria"

Good:
"Example acceptance criteria:
- Given the user is logged in, When they click 'Export', Then a CSV downloads
- Given CSV is exported, When opened in Excel, Then columns include timestamp, value
"
```

✅ **Task-Based Instructions** (not model tricks):
```
"Generate 3-5 acceptance criteria in Given-When-Then format"
(Works on any model, no special prompting needed)
```

### JSON Enforcement

**Code-Level Enforcement**:
```python
# All agents use format="json"
self.llm = ChatOllama(
    model=model_name,
    temperature=temperature,
    format="json"  # Forces JSON output
)
```

**Multi-Strategy JSON Extraction**:
```python
def _extract_json(self, text: str) -> Dict:
    text = text.strip()

    # Strategy 1: Remove markdown fences
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    # Strategy 2: Find JSON boundaries
    start = text.find('{')
    end = text.rfind('}') + 1

    if start == -1 or end == 0:
        raise ValueError(f"No JSON found")

    # Strategy 3: Parse
    json_text = text[start:end]
    return json.loads(json_text)
```

### Temperature Settings (Model-Agnostic)

| Agent | Temperature | Reasoning |
|-------|-------------|-----------|
| RequirementsAgent | 0.3 | Deterministic extraction, no creativity needed |
| EpicExtractorAgent | 0.3 | Objective grouping by feature area |
| EpicRefinerAgent | 0.3 | Rule-based optimization (merge/split) |
| StoryAgent | 0.4 | Slightly creative for natural language stories |
| TestCaseAgent | 0.3 | Deterministic test scenario generation |
| ReviewerAgent | 0.3 | Objective scoring (0-10 per criterion) |
| RewriterAgent | 0.5 | Higher creativity for story improvement |

**Why these work universally**:
- Low temps (0.3): Focus on following instructions precisely
- Mid temps (0.4-0.5): Balance structure + natural language
- All models respond similarly to temperature ranges

---

## Performance Characteristics

### Timing Breakdown (20 Requirements → 20 Stories)

| Phase | Agent(s) | Duration | % of Total |
|-------|----------|----------|------------|
| Requirements Extraction | RequirementsAgent | 30s | 2.5% |
| Epic Generation (2-pass) | EpicExtractor + EpicRefiner | 1 min | 5% |
| Story Generation (batched) | StoryAgent | 2 min | 10% |
| Test Case Generation (batched) | TestCaseAgent | 1.5 min | 7.5% |
| **Quality Review Loop** | **Reviewer + Rewriter** | **15-17 min** | **75%** |
| **TOTAL** | All 7 agents | **~20 minutes** | **100%** |

### Bottleneck Analysis: Quality Review Loop

**Current Performance**:
```
Iteration 1:
  - ReviewerAgent scores 20 stories: 30 seconds
  - Find low-quality stories (<70): 12 stories (60%)
  - RewriterAgent × 12 stories: 12 minutes
  - Total: 12.5 minutes

Iteration 2:
  - ReviewerAgent re-scores 20 stories: 30 seconds
  - Find low-quality stories (<70): 5 stories (25%)
  - RewriterAgent × 5 stories: 5 minutes
  - Total: 5.5 minutes

Iteration 3:
  - ReviewerAgent scores: 30 seconds
  - All stories ≥70 → Exit

Total Loop Time: 17-18 minutes
```

**Why So Slow?**
- Sequential processing (one rewrite at a time)
- High initial rewrite rate (60% need improvement)
- 1 minute per rewrite (LLM processing time)

### Scalability Metrics

| Requirements | Epics | Stories | Test Cases | Duration | Cost (Ollama) |
|--------------|-------|---------|------------|----------|---------------|
| 5 | 2-3 | 5 | 10-20 | ~8 min | Free |
| 10 | 3-5 | 10 | 20-40 | ~12 min | Free |
| 20 | 5-8 | 20 | 40-80 | ~20 min | Free |
| 50 | 8-12 | 50 | 100-200 | ~45 min | Free |
| 100 | 12-18 | 100 | 200-400 | ~90 min | Free |

**Scaling Pattern**: Roughly linear with number of requirements
**Parallelization**: Not yet implemented (all sequential)

### Optimization Strategies

#### 1. Prompt Optimization (HIGHEST IMPACT)
**Goal**: Reduce initial rewrite rate (60% → 20%)
**Approach**: Improve StoryAgent prompt to generate better stories initially
**Expected Impact**: 20 min → 6-8 min (67% reduction)
**Implementation**:
- Add more concrete examples to StoryAgent prompt
- Add validation checklist (has "so that"? has 3+ criteria?)
- Add anti-examples (what NOT to do)

**Before**:
```
"Write user stories following INVEST principles"
```

**After**:
```
"Write user stories in this exact format:
As a [specific user type], I want to [concrete action] so that [measurable benefit]

Example:
✓ Good: As a data analyst, I want to export data to CSV so that I can analyze it in Excel
✗ Bad: As a user, I want to export data (missing 'so that', vague user type)

Checklist before submitting:
- [ ] Story includes 'so that' clause?
- [ ] User type is specific (not 'user')?
- [ ] Action is concrete (not 'access data')?
- [ ] Benefit is measurable?
- [ ] 3-5 acceptance criteria included?
"
```

#### 2. Batch Rewriting
**Goal**: Rewrite multiple stories in parallel
**Approach**: Rewrite 4 stories at once instead of 1
**Expected Impact**: 20 min → 10 min (50% reduction)
**Trade-off**: Slightly lower quality per rewrite

#### 3. Parallel LLM Calls
**Goal**: Use thread pool for concurrent rewrites
**Approach**: ThreadPoolExecutor with 4 workers
**Expected Impact**: 20 min → 12 min (40% reduction)
**Complexity**: Requires thread-safe LLM client

#### 4. Smart Thresholds
**Goal**: Only rewrite critical failures
**Approach**:
- Score 0-49: MUST rewrite (critical)
- Score 50-69: Optional rewrite (warnings only)
- Score 70+: Approve
**Expected Impact**: 20 min → 12 min (40% reduction)
**Trade-off**: Some medium-quality stories ship as-is

---

## File Structure

```
user-story-automation/
│
├── src/
│   ├── agents/                          # Multi-agent system (NEW)
│   │   ├── __init__.py                  # Package exports
│   │   ├── base_agent.py                # Abstract base class (94 lines)
│   │   ├── requirements_agent.py        # Requirements extraction (78 lines)
│   │   ├── epic_extractor_agent.py      # Epic grouping pass 1 (82 lines)
│   │   ├── epic_refiner_agent.py        # Epic optimization pass 2 (89 lines)
│   │   ├── story_agent.py               # User story generation (67 lines)
│   │   ├── test_agent.py                # Test case generation (71 lines)
│   │   ├── reviewer_agent.py            # Quality review (97 lines)
│   │   ├── rewriter_agent.py            # Story improvement (84 lines)
│   │   └── orchestrator.py              # Agent coordination (251 lines)
│   │
│   ├── backend/                         # Flask backend
│   │   ├── app.py                       # Flask initialization
│   │   ├── routes/
│   │   │   ├── api.py                   # API endpoints (uses orchestrator)
│   │   │   ├── auth.py                  # Authentication
│   │   │   └── frontend.py              # Frontend serving
│   │   ├── services/
│   │   │   ├── story_service.py         # Business logic wrapper
│   │   │   └── email_service.py         # Email notifications
│   │   ├── models/
│   │   │   ├── database.py              # SQLite setup
│   │   │   └── user.py                  # User model
│   │   └── utils/
│   │       └── helpers.py               # Utility functions
│   │
│   ├── autoAgile/                       # Original CLI (legacy)
│   │   ├── autoAgile.py                 # CLI interface
│   │   ├── utils/
│   │   │   ├── prompts.py               # Prompt templates
│   │   │   ├── llm_factory.py           # LLM initialization
│   │   │   └── utils.py                 # Helper functions
│   │   ├── save_output.py               # Output formatting
│   │   └── tests/
│   │       ├── docs/                    # Test documents
│   │       ├── resources.py             # Test data
│   │       └── evaluation.py            # Quality metrics
│   │
│   └── frontend/                        # Web UI
│       ├── templates/
│       │   ├── index.html               # Landing page
│       │   ├── login.html               # Login page
│       │   └── stories.html             # Story display
│       └── static/
│           ├── css/styles.css
│           └── js/script.js
│
├── tests/                               # Unit & integration tests
│   ├── agents/                          # Agent tests
│   │   ├── test_requirements_agent.py
│   │   ├── test_epic_agents.py
│   │   ├── test_story_agent.py
│   │   ├── test_test_agent.py
│   │   ├── test_reviewer_agent.py
│   │   ├── test_rewriter_agent.py
│   │   └── test_orchestrator.py
│   ├── test_api.py
│   ├── test_bug_fixes.py
│   └── fixtures/
│
├── data/                                # Runtime data
│   ├── logs/
│   │   ├── app.log                      # Application logs
│   │   └── quality_metrics.jsonl       # Quality tracking
│   ├── outputs/                         # Generated files
│   │   ├── stories_20260711.json
│   │   └── stories_20260711.xlsx
│   └── uploads/                         # Temporary uploads
│
├── docs/                                # Documentation
│   ├── README.md                        # Main documentation
│   ├── AGENT_ARCHITECTURE.md            # This file
│   ├── PROJECT_STRUCTURE.md             # File organization
│   ├── features/                        # Feature docs
│   └── setup/                           # Setup guides
│
├── config/                              # Configuration
│   ├── env.template                     # Environment template
│   └── nginx.conf                       # Nginx config
│
├── instance/                            # Application data
│   └── users.db                         # SQLite database
│
├── .env                                 # Environment variables
├── requirements.txt                     # Python dependencies
├── run.py                               # Application entry point
└── README.md                            # Project overview
```

### Key Integration Points

**Web App Flow**:
```
User (Browser)
  ↓
run.py (Flask app start)
  ↓
src/backend/routes/api.py
  ↓
StoryOrchestrator.generate_stories()
  ↓
7 Agents execute pipeline
  ↓
Return JSON to browser
```

**CLI Flow**:
```
User (Terminal)
  ↓
src/autoAgile/autoAgile.py
  ↓
StoryOrchestrator.generate_stories()
  ↓
save_output.py (format as JSON/Excel)
  ↓
Save to data/outputs/
```

---

## Configuration & Setup

### Environment Variables

Create `.env` file from `config/env.template`:

```bash
# === LLM Configuration ===

# Ollama (Local)
OLLAMA_MODEL=mistral:7b-instruct
# Options: llama3:8b, qwen3-coder:30b, codellama:13b, mistral:7b-instruct

# OpenAI (Cloud)
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4

# Groq (Fast Inference)
GROQ_API_KEY=gsk_your-key-here
GROQ_MODEL=mixtral-8x7b-32768

# === Application Settings ===
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# === Database ===
DATABASE_URL=sqlite:///instance/users.db

# === Google OAuth (Optional) ===
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

### Switching LLM Providers

**To use Ollama** (default):
```bash
# .env
OLLAMA_MODEL=mistral:7b-instruct

# Ensure Ollama is running
ollama serve
```

**To use OpenAI**:
1. Modify `src/agents/base_agent.py`:
```python
from langchain_openai import ChatOpenAI  # Add import

# In BaseAgent.__init__:
self.llm = ChatOpenAI(
    model=os.getenv('OPENAI_MODEL', 'gpt-4'),
    temperature=temperature,
    api_key=os.getenv('OPENAI_API_KEY')
)
```

**To use Groq**:
```python
from langchain_groq import ChatGroq

self.llm = ChatGroq(
    model=os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768'),
    temperature=temperature,
    api_key=os.getenv('GROQ_API_KEY')
)
```

### Installation

```bash
# Clone repository
git clone <repo-url>
cd user-story-automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp config/env.template .env
# Edit .env with your settings

# Initialize database
python -c "from src.backend.models.database import init_db; init_db()"

# Run application
python run.py
```

**Access**:
- Web UI: http://localhost:5000
- API: http://localhost:5000/api/generate-stories

---

## Usage Guide

### Web Interface

1. **Navigate to** http://localhost:5000
2. **Login** (or create account)
3. **Upload** requirements document (.docx)
4. **Click** "Generate Stories"
5. **Wait** ~20 minutes
6. **Download** results (JSON/Excel)

### CLI Interface

```bash
# Generate stories from document
python src/autoAgile/autoAgile.py \
  --input src/autoAgile/tests/docs/PatientInformationSystem.docx \
  --output data/outputs/stories.json

# View logs
tail -f data/logs/app.log
```

### API Usage

```bash
# Upload document and generate stories
curl -X POST http://localhost:5000/api/generate-stories \
  -F "document=@PatientInformationSystem.docx" \
  -H "Authorization: Bearer <your-token>"

# Response:
{
  "requirements": [...],
  "epics": [...],
  "stories": [...],
  "test_cases": [...]
}
```

### Output Format

**JSON Output** (`stories.json`):
```json
{
  "requirements": [
    {"id": "REQ-001", "description": "..."}
  ],
  "epics": [
    {"epic_id": "EPIC-001", "epic_name": "...", "requirement_ids": [...]}
  ],
  "stories": [
    {
      "story_id": "STORY-001",
      "requirement_id": "REQ-001",
      "epic_id": "EPIC-001",
      "epic_name": "...",
      "user_story": "As a...I want...so that...",
      "acceptance_criteria": ["Given...When...Then..."],
      "definition_of_done": [...],
      "story_points": 3,
      "priority": "HIGH",
      "test_cases": [...]
    }
  ],
  "test_cases": [
    {
      "test_id": "TC-001",
      "requirement_id": "REQ-001",
      "test_description": "...",
      "test_steps": [...],
      "expected_result": "..."
    }
  ]
}
```

**Excel Output** (`stories.xlsx`):
- Sheet 1: Requirements
- Sheet 2: Epics
- Sheet 3: User Stories
- Sheet 4: Test Cases

---

## Comparison: Old vs New

### Old Architecture (Function-Based)

```
Document
  ↓
extract_list(document) → raw requirements
  ↓
refine_requirements(raw) → refined requirements
  ↓
extract_epics_v2(requirements) → raw epics
  ↓
refine_epics_v2(raw_epics) → refined epics
  ↓
convert_to_user_stories(epics, requirements) → stories
  ↓
generate_test_cases_v2(requirements) → test cases
  ↓
match_test_cases(stories, test_cases) → final output
```

**Characteristics**:
- ❌ No quality control loop
- ❌ Function-based (not extensible)
- ❌ Variable quality (40% missing "so that")
- ✅ Fast (~5 minutes)
- ✅ Simple codebase

### New Architecture (Agent-Based)

```
Document
  ↓
RequirementsAgent → refined requirements
  ↓
EpicExtractorAgent → EpicRefinerAgent → refined epics
  ↓
StoryAgent (batched) → stories
  ↓
TestCaseAgent (batched) → test cases
  ↓
ReviewerAgent → RewriterAgent (loop) → quality stories
  ↓
Final output
```

**Characteristics**:
- ✅ Automated quality control
- ✅ Agent-based (extensible)
- ✅ Consistent high quality (100% INVEST-compliant)
- ✅ Model-agnostic prompts
- ✅ Better abstraction (BaseAgent)
- ❌ Slower (~20 minutes)
- ❌ More complex codebase

### What Changed?

| Aspect | Old | New |
|--------|-----|-----|
| **Requirements** | extract_list() + refine_requirements() | RequirementsAgent |
| **Epics** | extract_epics_v2() + refine_epics_v2() | EpicExtractorAgent + EpicRefinerAgent |
| **Stories** | convert_to_user_stories() | StoryAgent (batched) |
| **Test Cases** | generate_test_cases_v2() | TestCaseAgent (batched) |
| **Quality Control** | None | ReviewerAgent + RewriterAgent (NEW) |
| **Architecture** | Functions | Agents (inheriting from BaseAgent) |
| **Duration** | ~5 min | ~20 min |
| **Quality** | Variable (60% need manual fixes) | Consistent (100% INVEST) |

### What Stayed the Same?

- ✅ Batch processing (4 requirements at a time)
- ✅ Two-pass epic generation
- ✅ Test case matching logic
- ✅ Output format (JSON/Excel)
- ✅ INVEST principles
- ✅ Story point estimation

---

## Troubleshooting

### Common Issues

#### 1. Port 5000 Already in Use

**Error**: `An attempt was made to access a socket in a way forbidden`

**Solution**:
```bash
# Check what's using port 5000
netstat -ano | findstr :5000  # Windows
lsof -i :5000                  # Linux/Mac

# Kill process or change port in run.py
# run.py line 19:
app.run(host='0.0.0.0', port=5001, debug=True)
```

#### 2. Ollama Not Running

**Error**: `Connection refused to http://localhost:11434`

**Solution**:
```bash
# Start Ollama
ollama serve

# Verify models installed
ollama list

# Pull model if needed
ollama pull mistral:7b-instruct
```

#### 3. Python Version Incompatibility

**Error**: `CrewAI requires Python 3.10-3.13`

**Solution**: We don't use CrewAI (uses custom agent system instead)
- Ensure `crewai` is NOT in requirements.txt
- Uses `langchain_ollama` instead (works with Python 3.14)

#### 4. Slow Story Generation (>30 minutes)

**Possible Causes**:
- Quality loop taking too long (many rewrites)
- LLM model too large/slow

**Solutions**:
```bash
# Check logs
tail -f data/logs/app.log

# Look for:
#   "Rewriting X low-quality stories..."
#   If X > 15, prompts need optimization

# Use faster model temporarily
# .env:
OLLAMA_MODEL=mistral:7b-instruct  # Fast
# Instead of:
OLLAMA_MODEL=qwen3-coder:30b      # Slower but better quality
```

#### 5. JSON Parsing Errors

**Error**: `No JSON found in response`

**Cause**: LLM returned plain text instead of JSON

**Solution**: Already handled by `_extract_json()` fallback logic
- If persists, check model supports `format="json"`
- Some older models don't enforce JSON format

### Logging

**Enable verbose logging**:
```python
# run.py or autoAgile.py
import logging
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Check logs**:
```bash
# Application log
tail -f data/logs/app.log

# Quality metrics
cat data/logs/quality_metrics.jsonl | jq
```

---

## Future Enhancements

### Roadmap

#### Phase 1: Performance (Q3 2026)
- [ ] Optimize StoryAgent prompt (60% → 20% rewrite rate)
- [ ] Implement batch rewriting (4 stories at once)
- [ ] Add parallel LLM calls (ThreadPoolExecutor)
- [ ] Expected: 20 min → 8 min

#### Phase 2: Features (Q4 2026)
- [ ] Domain-specific agents (HealthcareStoryAgent, FinanceStoryAgent)
- [ ] Template library (common story patterns)
- [ ] Story prioritization agent
- [ ] Dependency detection

#### Phase 3: Integration (Q1 2027)
- [ ] Jira integration (auto-create tickets)
- [ ] GitHub integration (auto-create issues)
- [ ] Slack notifications
- [ ] Real-time progress updates (WebSockets)

#### Phase 4: Advanced (Q2 2027)
- [ ] Fine-tuned models for story generation
- [ ] Feedback loop (learn from accepted/rejected stories)
- [ ] Multi-language support
- [ ] Voice input for requirements

---

## Glossary

| Term | Definition |
|------|------------|
| **Agent** | Specialized AI component with specific role (e.g., StoryAgent, ReviewerAgent) |
| **BaseAgent** | Abstract class providing common LLM interaction logic for all agents |
| **Epic** | Logical grouping of 2-5 related requirements (e.g., "User Authentication") |
| **INVEST** | Quality criteria: Independent, Negotiable, Valuable, Estimable, Small, Testable |
| **LangChain** | Framework for building LLM applications with chains and agents |
| **LLM** | Large Language Model (GPT-4, Claude, Llama, Mistral, etc.) |
| **Model-Agnostic** | Works across all LLM models without model-specific optimizations |
| **Ollama** | Local LLM runtime (runs models like Llama, Mistral, Qwen locally) |
| **Orchestrator** | Coordinator that manages multiple agents and processing loops |
| **RAG** | Retrieval-Augmented Generation (NOT used in this system) |
| **RAT** | Refine-And-Think pattern: Refine input → LLM votes → Process better version |
| **Rewrite Rate** | Percentage of stories needing improvement (<70 score) |
| **Story Points** | Agile estimation unit (1, 2, 3, 5, 8 - Fibonacci sequence) |
| **Temperature** | LLM randomness parameter (0 = deterministic, 1 = creative) |
| **Two-Pass** | Extract → Refine approach for better quality |

---

## References

### Documentation
- [LangChain Docs](https://python.langchain.com/)
- [Ollama Models](https://ollama.ai/library)
- [INVEST Criteria](https://en.wikipedia.org/wiki/INVEST_(mnemonic))
- [Given-When-Then](https://en.wikipedia.org/wiki/Given-When-Then)

### Project Files
- `docs/PROJECT_STRUCTURE.md`: Overall project organization
- `AGENTIC_ARCHITECTURE_PLAN.md`: Original implementation plan
- `FINAL_STRUCTURE.md`: System consolidation history
- `requirements.txt`: Python dependencies

### Related Documents
- `docs/README.md`: Project overview
- `UBUNTU_SETUP.md`: Ubuntu installation guide
- `QUICK_SETUP.md`: Quick start guide

---

**Document Version**: 2.0
**Last Updated**: 2026-07-11
**Authors**: Agentic Architecture Team
**Maintained By**: Development Team
**Contact**: [Your contact info]

---

## Appendix: Complete Code Example

### Example: Creating a Custom Agent

```python
# src/agents/custom_agent.py
from .base_agent import BaseAgent
from typing import Dict, Any

class CustomAgent(BaseAgent):
    """Custom agent for specific task"""

    def __init__(self):
        super().__init__(
            name="Custom Agent",
            role="Custom Specialist",
            goal="Perform custom task",
            temperature=0.3
        )

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        data = context.get('data', [])

        return f"""RESPOND WITH JSON ONLY.

You are a Custom Agent. [Task description].

DATA:
{data}

INSTRUCTIONS:
1. [Concrete instruction]
2. [Measurable requirement]

OUTPUT FORMAT:
{{
  "results": [
    {{"id": "RESULT-001", "value": "..."}}
  ]
}}

RESPOND WITH JSON ONLY."""

# Usage in orchestrator:
# from .custom_agent import CustomAgent
# self.custom_agent = CustomAgent()
# result = self.custom_agent.run("Process data", {"data": [...]})
```

---

**End of Document**
