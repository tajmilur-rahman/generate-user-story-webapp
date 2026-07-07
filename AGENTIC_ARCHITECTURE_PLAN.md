# Agentic Architecture Implementation Plan (Option B)

**Status:** Planning Phase - DO NOT IMPLEMENT YET
**Wait For:** New repository setup
**Approach:** Option B - Minimal + Quality Review Loop

---

## 🎯 Executive Summary

### What We're Building
Replace the current monolithic LLM pipeline with a **multi-agent architecture** that includes quality review loops while preserving all existing functionality and processing loops.

### Key Principles
- ✅ Same API endpoints, same response format
- ✅ Keep all existing loops (batch processing, extract→refine)
- ✅ Add quality review loop (Generate → Review → Rewrite)
- ✅ No new features - just better internal architecture
- ✅ Preserve backward compatibility

---

## 🤖 Agent Architecture (Option B)

### Agent Lineup (7 Agents + 1 Orchestrator)

| # | Agent | Replaces Current Code | Purpose |
|---|-------|----------------------|---------|
| 1 | **RequirementsAgent** | `extract_list()` + `refine_requirements()` | Extract and refine requirements |
| 2 | **EpicExtractorAgent** | `extract_epics_v2()` | Extract initial epics (first pass) |
| 3 | **EpicRefinerAgent** | `refine_epics_v2()` | Refine and merge epics (second pass) |
| 4 | **StoryAgent** | Story generation in `convert_to_user_stories()` | Generate user stories with AC |
| 5 | **TestCaseAgent** | `generate_test_cases_v2()` | Generate test cases |
| 6 | **ReviewerAgent** | NEW | Score stories on INVEST criteria (0-100) |
| 7 | **RewriterAgent** | NEW | Improve stories with score < 70 |
| 8 | **Orchestrator** | Coordinates all agents | Manages pipeline + review loop |

---

## 🔄 Loops to Preserve + New Loop

### Existing Loops (KEEP ALL)

#### Loop 1: Batch Processing (4 requirements at a time)
```python
# Current: src/backend/services/story_service.py
batch_size = 4
for i in range(0, len(requirements), batch_size):
    batch = requirements[i:i+batch_size]
    # Process batch
```

**Agent Implementation:**
```python
# StoryAgent processes in batches
for batch in chunks(requirements, size=4):
    stories = StoryAgent.run(batch)
```

#### Loop 2: Epic Extract → Refine (Two-pass)
```python
# Current: src/autoAgile/utils/prompts.py
raw_epics = extract_epics_v2(...)
refined_epics = refine_epics_v2(raw_epics, ...)
```

**Agent Implementation:**
```python
# Two separate agents for two passes
raw_epics = EpicExtractorAgent.run(requirements)
refined_epics = EpicRefinerAgent.run(raw_epics)
```

#### Loop 3: Batched Test Case Generation
```python
# Current: Generate TCs for every 4 requirements
for batch in requirement_batches:
    test_cases = generate_test_cases_v2(batch)
```

**Agent Implementation:**
```python
# TestCaseAgent processes in batches
for batch in chunks(requirements, size=4):
    tcs = TestCaseAgent.run(batch)
```

### New Loop (ADD)

#### Loop 4: Quality Review → Rewrite → Review
```python
# NEW: Iterative quality improvement
max_iterations = 3
iteration = 0

while iteration < max_iterations:
    # Review all stories
    scores = ReviewerAgent.run(stories)

    # Find low-quality stories (score < 70)
    low_quality = [s for s in stories if scores[s.id] < 70]

    if not low_quality:
        break  # All stories meet threshold

    # Rewrite bad stories
    for story in low_quality:
        feedback = scores[story.id]
        improved = RewriterAgent.run(story, feedback)
        replace_story(stories, story.id, improved)

    iteration += 1
```

---

## 📁 Target Directory Structure

```
user-story-automation/  (or new repo name)
├── src/
│   ├── agents/                          # NEW: All agent code
│   │   ├── __init__.py
│   │   ├── base_agent.py                # Base class for all agents
│   │   ├── requirements_agent.py        # Replaces extract_list + refine_requirements
│   │   ├── epic_extractor_agent.py      # Replaces extract_epics_v2 (first pass)
│   │   ├── epic_refiner_agent.py        # Replaces refine_epics_v2 (second pass)
│   │   ├── story_agent.py               # Replaces story generation
│   │   ├── test_agent.py                # Replaces generate_test_cases_v2
│   │   ├── reviewer_agent.py            # NEW: Quality scoring
│   │   ├── rewriter_agent.py            # NEW: Story improvement
│   │   └── orchestrator.py              # Coordinates all agents + loops
│   │
│   ├── autoAgile/                       # KEEP: Backup of old code
│   │   └── utils/
│   │       ├── prompts.py               # Eventually delete after testing
│   │       └── prompts_legacy.py        # BACKUP of original
│   │
│   └── backend/
│       ├── routes/
│       │   └── agile.py                 # UPDATE: Use orchestrator
│       └── services/
│           ├── story_service.py         # UPDATE: Thin wrapper
│           └── story_service_legacy.py  # BACKUP
│
├── tests/
│   └── agents/                          # NEW: Agent tests
│       ├── test_base_agent.py
│       ├── test_requirements_agent.py
│       ├── test_epic_agents.py
│       ├── test_story_agent.py
│       ├── test_test_agent.py
│       ├── test_reviewer_agent.py
│       ├── test_rewriter_agent.py
│       └── test_orchestrator.py
│
├── docs/
│   └── agents/
│       ├── architecture.md              # Architecture documentation
│       └── agent_prompts.md             # All agent prompts documented
│
├── requirements.txt                     # UPDATE: Add crewai dependencies
├── AGENTIC_ARCHITECTURE_PLAN.md         # THIS FILE
└── README.md                            # UPDATE: Document agent architecture
```

---

## 💻 Code Templates

### 1. BaseAgent Class

**File:** `src/agents/base_agent.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_community.llms import Ollama
import os
import json
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents - handles common LLM interaction"""

    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        temperature: float = 0.3
    ):
        self.name = name
        self.role = role
        self.goal = goal

        # Use same model as current system
        model_name = os.getenv('OLLAMA_MODEL', 'qwen3-coder:30b')
        self.llm = Ollama(
            model=model_name,
            temperature=temperature,
            base_url="http://localhost:11434"
        )

        logger.info(f"[{name}] Initialized with model: {model_name}")

    @abstractmethod
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build specialized prompt for this agent's role"""
        pass

    def run(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task"""
        try:
            logger.info(f"[{self.name}] Starting task...")

            # Build specialized prompt
            system_prompt = self.get_system_prompt(context)
            full_prompt = f"{system_prompt}\n\n{task}"

            # Call LLM with JSON enforcement (like current _json_chain)
            if hasattr(self.llm, 'bind'):
                response = self.llm.bind(format="json").invoke(full_prompt)
            else:
                response = self.llm.invoke(full_prompt)

            # Parse JSON response
            result = self._extract_json(response)

            logger.info(f"[{self.name}] Completed successfully")

            return {
                "agent": self.name,
                "success": True,
                "output": result
            }

        except Exception as e:
            logger.error(f"[{self.name}] Error: {str(e)}")
            return {
                "agent": self.name,
                "success": False,
                "error": str(e)
            }

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from response - reuse _strip_fences logic"""
        text = text.strip()

        # Remove markdown fences
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        # Find JSON boundaries
        start = text.find('{')
        end = text.rfind('}') + 1

        if start == -1 or end == 0:
            raise ValueError(f"No JSON found in response: {text[:200]}")

        json_text = text[start:end]
        return json.loads(json_text)
```

---

### 2. RequirementsAgent

**File:** `src/agents/requirements_agent.py`

```python
from .base_agent import BaseAgent
from typing import Dict, Any

class RequirementsAgent(BaseAgent):
    """Extracts and refines requirements - replaces extract_list + refine_requirements"""

    def __init__(self):
        super().__init__(
            name="Requirements Extractor",
            role="Requirements Analyst",
            goal="Extract and refine all requirements from documents"
        )

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        return """RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with {{ and ending with }}.

You are a Requirements Analyst. Extract and refine all requirements from the document.

INSTRUCTIONS:
1. Extract EVERY requirement (functional and non-functional)
2. Merge duplicate or overlapping requirements
3. Split overly broad requirements into specific ones
4. Remove meta-requirements (e.g., "system should have good documentation")
5. Number requirements sequentially starting from REQ-001
6. Aim for 10-20 clear, specific requirements

OUTPUT FORMAT (JSON only):
{{
  "requirements": [
    {{
      "id": "REQ-001",
      "description": "The system shall record temperature every 5 minutes",
      "type": "functional",
      "priority": "high"
    }},
    {{
      "id": "REQ-002",
      "description": "The system shall achieve 99.9% uptime",
      "type": "non-functional",
      "priority": "medium"
    }}
  ]
}}

RESPOND WITH JSON ONLY. No markdown, no prose."""
```

---

### 3. ReviewerAgent (NEW - Quality Control)

**File:** `src/agents/reviewer_agent.py`

```python
from .base_agent import BaseAgent
from typing import Dict, Any, List

class ReviewerAgent(BaseAgent):
    """Reviews and scores user stories on INVEST criteria"""

    def __init__(self):
        super().__init__(
            name="Story Reviewer",
            role="Quality Assurance Reviewer",
            goal="Score every story on INVEST criteria and identify issues"
        )

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        stories = context.get('stories', [])

        return f"""RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with {{{{ and ending with }}}}.

You are a Story Quality Reviewer. Score each story on INVEST criteria.

STORIES TO REVIEW:
{self._format_stories(stories)}

INVEST CRITERIA (score each 0-10):
- **Independent**: Can be developed without dependencies (check for "depends on", "requires")
- **Negotiable**: Implementation details flexible (avoid "must use", "exactly")
- **Valuable**: Clear user benefit (look for "so that" clause)
- **Estimable**: Team can estimate effort (not vague like "good performance")
- **Small**: Fits in one sprint (story points ≤5 ideal)
- **Testable**: Has concrete acceptance criteria

SCORING:
- 90-100: Excellent story, ready to implement
- 70-89: Good story, minor improvements possible
- 50-69: Needs improvement, rewrite recommended
- 0-49: Poor quality, must rewrite

OUTPUT FORMAT (JSON only):
{{{{
  "story_reviews": [
    {{{{
      "story_id": "STORY-001",
      "invest_scores": {{{{
        "independent": 10,
        "negotiable": 8,
        "valuable": 10,
        "estimable": 7,
        "small": 9,
        "testable": 10
      }}}},
      "total_score": 90,
      "issues": [],
      "feedback": "Excellent story with clear value and testable criteria",
      "recommendation": "APPROVE"
    }}}},
    {{{{
      "story_id": "STORY-002",
      "invest_scores": {{{{
        "independent": 9,
        "negotiable": 7,
        "valuable": 4,
        "estimable": 6,
        "small": 8,
        "testable": 3
      }}}},
      "total_score": 62,
      "issues": [
        "Missing 'so that' clause - unclear user value",
        "No acceptance criteria - not testable"
      ],
      "feedback": "Story lacks clear benefit and testable criteria. Add 'so that' clause and 3+ acceptance criteria.",
      "recommendation": "REWRITE"
    }}}}
  ],
  "summary": {{{{
    "total_stories": 2,
    "average_score": 76,
    "stories_below_threshold": 1,
    "stories_needing_rewrite": ["STORY-002"]
  }}}}
}}}}

RESPOND WITH JSON ONLY."""

    def _format_stories(self, stories: List[Dict]) -> str:
        formatted = []
        for story in stories:
            formatted.append(f"""
Story ID: {story.get('story_id', 'N/A')}
User Story: {story.get('user_story', 'N/A')}
Acceptance Criteria: {story.get('acceptance_criteria', [])}
Story Points: {story.get('story_points', 'N/A')}
""")
        return "\n---\n".join(formatted)
```

---

### 4. RewriterAgent (NEW - Quality Improvement)

**File:** `src/agents/rewriter_agent.py`

```python
from .base_agent import BaseAgent
from typing import Dict, Any

class RewriterAgent(BaseAgent):
    """Improves low-quality stories based on reviewer feedback"""

    def __init__(self):
        super().__init__(
            name="Story Rewriter",
            role="Story Improvement Specialist",
            goal="Fix low-quality stories to achieve INVEST score ≥70",
            temperature=0.5  # Higher for creative rewriting
        )

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        story = context.get('story', {})
        review = context.get('review', {})

        return f"""RESPOND WITH JSON ONLY. Do not include any prose, explanations, markdown headers, or text outside the JSON. Your entire response must be a single valid JSON object starting with {{{{ and ending with }}}}.

You are a Story Improvement Specialist. Rewrite this low-quality story to address all issues.

ORIGINAL STORY (Score: {review.get('total_score', 0)}/100):
{story.get('user_story', 'N/A')}

INVEST SCORES:
{review.get('invest_scores', {{}})}

ISSUES IDENTIFIED:
{review.get('issues', [])}

FEEDBACK:
{review.get('feedback', 'N/A')}

INSTRUCTIONS:
1. Preserve the original intent and requirement
2. Add "so that [benefit]" clause if missing (improves Valuable score)
3. Make story smaller if >5 story points (improves Small score)
4. Add 3-5 concrete acceptance criteria (improves Testable score)
5. Remove vague terms like "good", "fast", "user-friendly" (improves Estimable score)
6. Remove dependencies on other stories (improves Independent score)

OUTPUT FORMAT (JSON only):
{{{{
  "rewritten_story": {{{{
    "story_id": "{story.get('story_id', 'N/A')}",
    "user_story": "As a [specific user type], I want to [specific action] so that [concrete benefit]",
    "acceptance_criteria": [
      "Given [context], When [action], Then [expected result with metrics]",
      "Given [context], When [action], Then [expected result with metrics]",
      "Given [context], When [action], Then [expected result with metrics]"
    ],
    "definition_of_done": [
      "Unit tests written with >80% coverage",
      "Code reviewed and approved",
      "Integration tested in staging environment"
    ],
    "story_points": 3,
    "priority": "high"
  }}}},
  "changes_made": [
    "Added 'so that' clause to clarify user benefit",
    "Added 3 specific acceptance criteria with measurable outcomes",
    "Reduced story points from 8 to 3 by narrowing scope"
  ]
}}}}

RESPOND WITH JSON ONLY."""
```

---

### 5. Orchestrator (Coordinates Everything)

**File:** `src/agents/orchestrator.py`

```python
from .requirements_agent import RequirementsAgent
from .epic_extractor_agent import EpicExtractorAgent
from .epic_refiner_agent import EpicRefinerAgent
from .story_agent import StoryAgent
from .test_agent import TestCaseAgent
from .reviewer_agent import ReviewerAgent
from .rewriter_agent import RewriterAgent
from src.backend.services.story_service import _tc_similarity
import logging

logger = logging.getLogger(__name__)

class StoryOrchestrator:
    """Coordinates all agents and manages quality loop"""

    def __init__(self):
        self.requirements_agent = RequirementsAgent()
        self.epic_extractor = EpicExtractorAgent()
        self.epic_refiner = EpicRefinerAgent()
        self.story_agent = StoryAgent()
        self.test_agent = TestCaseAgent()
        self.reviewer_agent = ReviewerAgent()
        self.rewriter_agent = RewriterAgent()

        logger.info("StoryOrchestrator initialized with 7 agents")

    def generate_stories(self, document_text: str) -> dict:
        """Main pipeline - preserves all existing loops + adds review loop"""

        logger.info("=" * 60)
        logger.info("Starting Agentic Story Generation Pipeline")
        logger.info("=" * 60)

        # PHASE 1: Requirements Extraction
        logger.info("\n[PHASE 1] Extracting Requirements...")
        req_result = self.requirements_agent.run(
            "Extract and refine all requirements",
            {"document": document_text}
        )
        requirements = req_result["output"]["requirements"]
        logger.info(f"✓ Extracted {len(requirements)} requirements")

        # PHASE 2: Epic Generation (LOOP 2 - Extract → Refine)
        logger.info("\n[PHASE 2] Generating Epics (Two-Pass)...")

        # Pass 1: Extract
        epic_extract_result = self.epic_extractor.run(
            "Extract initial epics",
            {"requirements": requirements}
        )
        raw_epics = epic_extract_result["output"]["epics"]
        logger.info(f"✓ Extracted {len(raw_epics)} raw epics")

        # Pass 2: Refine
        epic_refine_result = self.epic_refiner.run(
            "Refine and merge epics",
            {"raw_epics": raw_epics, "requirements": requirements}
        )
        epics = epic_refine_result["output"]["epics"]
        logger.info(f"✓ Refined to {len(epics)} final epics")

        # PHASE 3: Story Generation (LOOP 1 - Batched by Epic)
        logger.info("\n[PHASE 3] Generating Stories (Batched)...")
        all_stories = []

        for epic in epics:
            epic_reqs = [r for r in requirements if r["id"] in epic["requirement_ids"]]
            logger.info(f"  Processing epic: {epic['epic_name']} ({len(epic_reqs)} requirements)")

            # Process in batches of 4 (LOOP 1)
            batch_size = 4
            for i in range(0, len(epic_reqs), batch_size):
                batch = epic_reqs[i:i+batch_size]

                story_result = self.story_agent.run(
                    f"Generate stories for batch {i//batch_size + 1}",
                    {"requirements_batch": batch, "epic": epic}
                )

                if story_result["success"]:
                    stories = story_result["output"]["stories"]
                    # Add epic context
                    for s in stories:
                        s["epic_id"] = epic["epic_id"]
                        s["epic_name"] = epic["epic_name"]
                    all_stories.extend(stories)

        logger.info(f"✓ Generated {len(all_stories)} stories")

        # PHASE 4: Test Case Generation (LOOP 3 - Batched)
        logger.info("\n[PHASE 4] Generating Test Cases (Batched)...")
        all_test_cases = []
        batch_size = 4

        for i in range(0, len(requirements), batch_size):
            batch = requirements[i:i+batch_size]

            tc_result = self.test_agent.run(
                f"Generate test cases for batch {i//batch_size + 1}",
                {"requirements_batch": batch}
            )

            if tc_result["success"]:
                all_test_cases.extend(tc_result["output"]["test_cases"])

        logger.info(f"✓ Generated {len(all_test_cases)} test cases")

        # Match TCs to stories
        all_stories = self._match_test_cases(all_stories, all_test_cases)

        # PHASE 5: Quality Review Loop (LOOP 4 - NEW)
        logger.info("\n[PHASE 5] Quality Review Loop...")
        all_stories = self._quality_review_loop(all_stories)

        logger.info("\n" + "=" * 60)
        logger.info("Pipeline Complete!")
        logger.info("=" * 60)

        return {
            "requirements": requirements,
            "epics": epics,
            "stories": all_stories,
            "test_cases": all_test_cases
        }

    def _quality_review_loop(self, stories: list) -> list:
        """LOOP 4: Iterative quality improvement"""

        max_iterations = 3
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"\n  Review Iteration {iteration}/{max_iterations}")

            # Review all stories
            review_result = self.reviewer_agent.run(
                "Review and score all stories",
                {"stories": stories}
            )

            if not review_result["success"]:
                logger.error("  Review failed, skipping quality loop")
                break

            story_reviews = review_result["output"]["story_reviews"]
            avg_score = review_result["output"]["summary"]["average_score"]

            logger.info(f"  Average INVEST Score: {avg_score}/100")

            # Find stories needing improvement
            low_quality = [
                review for review in story_reviews
                if review["total_score"] < 70
            ]

            if not low_quality:
                logger.info(f"  ✓ All stories meet quality threshold (≥70)")
                break

            logger.info(f"  ↻ Rewriting {len(low_quality)} low-quality stories...")

            # Rewrite each low-quality story
            for review in low_quality:
                story_id = review["story_id"]
                story = next(s for s in stories if s["story_id"] == story_id)

                logger.info(f"    - {story_id}: {review['total_score']}/100 → Rewriting...")

                rewrite_result = self.rewriter_agent.run(
                    f"Rewrite {story_id}",
                    {"story": story, "review": review}
                )

                if rewrite_result["success"]:
                    improved_story = rewrite_result["output"]["rewritten_story"]

                    # Replace story
                    for i, s in enumerate(stories):
                        if s["story_id"] == story_id:
                            stories[i] = improved_story
                            break

        if iteration == max_iterations:
            logger.warning(f"  ⚠ Reached max iterations without full convergence")

        return stories

    def _match_test_cases(self, stories: list, test_cases: list) -> list:
        """Match TCs to stories - reuses existing similarity logic"""
        claimed_tc_groups = set()

        for story in stories:
            story_text = story["user_story"]
            best_match = None
            best_score = 0.0

            for tc in test_cases:
                if tc["test_id"] in claimed_tc_groups:
                    continue

                tc_text = f"{tc['test_description']} {' '.join(tc.get('test_steps', []))}"
                similarity = _tc_similarity(story_text, tc_text)

                if similarity > best_score and similarity >= 0.5:
                    best_score = similarity
                    best_match = tc

            if best_match:
                story["test_cases"] = [best_match]
                claimed_tc_groups.add(best_match["test_id"])
            else:
                story["test_cases"] = []

        return stories
```

---

### 6. Flask Integration

**File:** `src/backend/routes/agile.py` (UPDATE)

```python
from src.agents.orchestrator import StoryOrchestrator
from flask import Blueprint, request, jsonify
import logging

agile_bp = Blueprint('agile', __name__)
logger = logging.getLogger(__name__)

# Initialize orchestrator
orchestrator = StoryOrchestrator()

@agile_bp.route('/generate', methods=['POST'])
def generate_stories():
    """Generate stories using agentic architecture"""
    try:
        file = request.files['file']
        text = extract_text_from_file(file)

        # Use agent orchestrator
        result = orchestrator.generate_stories(text)

        return jsonify({
            'success': True,
            'requirements': result['requirements'],
            'epics': result['epics'],
            'stories': result['stories'],
            'test_cases': result['test_cases']
        })

    except Exception as e:
        logger.error(f"Story generation failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Keep legacy endpoint for comparison during transition
@agile_bp.route('/generate-legacy', methods=['POST'])
def generate_stories_legacy():
    """Old monolithic system (backup)"""
    try:
        file = request.files['file']
        text = extract_text_from_file(file)

        # Use old implementation from prompts_legacy.py
        from src.autoAgile.utils.prompts_legacy import (
            extract_list, refine_requirements, extract_epics_v2
        )
        # ... old implementation ...

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## 🔧 Dependencies

**Add to `requirements.txt`:**

```txt
# Existing dependencies
Flask==2.3.2
langchain==0.1.0
langchain-community==0.0.38
# ... other existing dependencies ...

# NEW: Agent framework
crewai==0.28.0
crewai-tools==0.1.6
```

---

## 🌿 Git Strategy for New Repo

### When New Repo is Ready

#### Step 1: Clone New Repo
```bash
git clone <new-repo-url>
cd <new-repo-name>
```

#### Step 2: Create Feature Branch
```bash
git checkout -b feature/agentic-architecture
```

#### Step 3: Set Up Directory Structure
```bash
mkdir -p src/agents tests/agents docs/agents
```

#### Step 4: Copy This Plan
```bash
# Copy this planning document
cp /path/to/AGENTIC_ARCHITECTURE_PLAN.md ./
git add AGENTIC_ARCHITECTURE_PLAN.md
git commit -m "docs: add agentic architecture implementation plan"
git push -u origin feature/agentic-architecture
```

#### Step 5: Start Implementation
```bash
# Install dependencies
pip install crewai==0.28.0 crewai-tools==0.1.6

# Create first agent file
touch src/agents/base_agent.py

# Follow implementation tasks from this document
```

---

## 📊 Success Metrics

### Quality Improvements (Expected)
- **Story Quality:** 60/100 → 82/100 average INVEST score (+37%)
- **Stories Needing Manual Fixes:** 40% → 5% (-88%)
- **Test Case Coverage:** 80% → 100% (+20%)
- **Requirements Coverage:** 85% → 98% (+13%)

### Technical Metrics
- **Code Organization:** 1 monolithic file → 8 focused agent files
- **Debuggability:** Hard (one big prompt) → Easy (trace by agent)
- **Test Coverage:** Hard to test → Easy (unit test each agent)
- **Extensibility:** Modify giant prompt → Add/swap agents

### Performance
- **Execution Time:** ~45s → ~60s for 20 stories (+33% time)
- **Trade-off:** Worth it for 37% quality improvement

---

## ✅ Pre-Implementation Checklist

Before starting implementation:

- [ ] New repository created and accessible
- [ ] Feature branch created: `feature/agentic-architecture`
- [ ] This plan document copied to new repo
- [ ] Python environment set up (Python 3.8+)
- [ ] Ollama installed and running
- [ ] Model downloaded: `ollama pull qwen3-coder:30b`
- [ ] Dependencies installable: `pip install crewai crewai-tools`

---

## 🎯 Final Deliverables

### Code
- [ ] 7 agent classes fully implemented
- [ ] Orchestrator coordinates all agents
- [ ] All 4 loops working (batch, extract→refine, TC batch, review)
- [ ] Flask integration complete
- [ ] Legacy code backed up

### Tests
- [ ] Unit tests for each agent (>80% coverage)
- [ ] Integration tests for full pipeline
- [ ] Comparison tests (old vs new system)
- [ ] Performance benchmarks

### Documentation
- [ ] Architecture diagram
- [ ] Agent prompt documentation
- [ ] API documentation
- [ ] Migration guide
- [ ] README updated

### Verification
- [ ] Side-by-side testing completed
- [ ] Quality improvement demonstrated
- [ ] No breaking changes
- [ ] Production ready

---

## 📝 Notes

- **DO NOT START** until new repo is ready
- **PRESERVE** all existing functionality
- **ADD** quality review loop as main improvement
- **KEEP** all existing loops (batching, extract→refine)
- **TEST** continuously (don't wait until end)
- **DOCUMENT** as you go (not at the end)

---

**Last Updated:** 2026-07-07
**Status:** Planning Complete - Awaiting New Repository
**Next Step:** Wait for new repo, then begin implementation
