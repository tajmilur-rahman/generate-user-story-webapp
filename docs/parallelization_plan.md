# Multi-Agent Architecture Parallelization Plan

## Current Performance Analysis

### Bottlenecks Identified

**Phase 3 (Story Generation)**: ~2-3 minutes
- Sequential epic processing (5 epics)
- Sequential batch processing within each epic (4 batches/epic)
- Total: 20 sequential LLM calls at ~5-8 seconds each

**Phase 4 (Test Case Generation)**: ~30-40 seconds
- Sequential batch processing
- Total: 5 sequential LLM calls

**Phase 5 (Review Loop)**: ~1-2 minutes
- Sequential story rewrites
- Total: 10-15 sequential LLM calls per iteration

**Total Pipeline Time**: 5-7 minutes for a typical document

---

## Parallelization Strategy

### 1. PARALLEL EPIC PROCESSING (Highest Impact)

**Speedup**: 5x faster (5 epics in parallel vs sequential)

**Implementation**: Use `ThreadPoolExecutor` to process all epics concurrently

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)

class StoryOrchestrator:
    def __init__(self, max_workers=5):
        self.max_workers = max_workers  # Parallel threads for LLM calls
        # ... existing init code ...

    def _process_single_epic(self, epic, requirements):
        """Process one epic with all its batches (sequential batches within epic)"""
        epic_reqs = [r for r in requirements if r["id"] in epic["requirement_ids"]]
        logger.info(f"  Processing epic: {epic['epic_name']} ({len(epic_reqs)} requirements)")

        stories = []
        batch_size = 4

        for i in range(0, len(epic_reqs), batch_size):
            batch = epic_reqs[i:i+batch_size]

            story_result = self.story_agent.run(
                f"Generate stories for batch {i//batch_size + 1}",
                {"requirements_batch": batch, "epic": epic}
            )

            if story_result["success"]:
                batch_stories = story_result["output"]["stories"]
                # Add epic context
                for s in batch_stories:
                    s["epic_id"] = epic["epic_id"]
                    s["epic_name"] = epic["epic_name"]
                stories.extend(batch_stories)

        return stories

    def generate_stories(self, document_text: str) -> dict:
        # ... existing Phase 1 and Phase 2 code ...

        # PHASE 3: Story Generation (PARALLEL EPICS)
        logger.info("\n[PHASE 3] Generating Stories (Parallel Epics)...")
        all_stories = []

        # Process epics in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all epic processing tasks
            future_to_epic = {
                executor.submit(self._process_single_epic, epic, requirements): epic
                for epic in epics
            }

            # Collect results as they complete
            for future in as_completed(future_to_epic):
                epic = future_to_epic[future]
                try:
                    stories = future.result()
                    all_stories.extend(stories)
                    logger.info(f"  ✓ Completed epic: {epic['epic_name']} ({len(stories)} stories)")
                except Exception as e:
                    logger.error(f"  ✗ Epic {epic['epic_name']} failed: {e}")

        logger.info(f"✓ Generated {len(all_stories)} stories")

        # ... rest of pipeline ...
```

**Benefits**:
- 5 epics process simultaneously
- ~5x speedup in Phase 3 (2-3 min → 30-40 sec)
- Safe: Each epic is independent
- Production-ready: ThreadPoolExecutor handles errors gracefully

---

### 2. PARALLEL BATCH PROCESSING (Medium Impact)

**Speedup**: 4x faster (process 4 batches in parallel)

**Challenge**: Global TC numbering requires sequential processing OR pre-calculation

**Solution A: Pre-calculate TC ranges (Recommended)**

```python
def _calculate_tc_ranges(self, requirements, batch_size=4):
    """Pre-calculate starting TC numbers for each batch"""
    tc_ranges = []
    current_tc = 1

    for i in range(0, len(requirements), batch_size):
        batch = requirements[i:i+batch_size]
        # Estimate: 2.5 TCs per requirement (average of 2-4)
        estimated_tcs = len(batch) * 2.5
        tc_ranges.append({
            'batch_idx': i,
            'batch': batch,
            'starting_tc': current_tc
        })
        current_tc += int(estimated_tcs)

    return tc_ranges

def _process_tc_batch(self, batch_info):
    """Process one test case batch"""
    tc_result = self.test_agent.run(
        f"Generate test cases for batch",
        {
            "requirements_batch": batch_info['batch'],
            "starting_tc_number": batch_info['starting_tc']
        }
    )

    if tc_result["success"]:
        return tc_result["output"]["test_cases"]
    return []

# In generate_stories():
# PHASE 4: Test Case Generation (PARALLEL BATCHES)
logger.info("\n[PHASE 4] Generating Test Cases (Parallel Batches)...")

# Pre-calculate TC ranges
tc_ranges = self._calculate_tc_ranges(requirements, batch_size=4)

all_test_cases = []

# Process batches in parallel
with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
    future_to_batch = {
        executor.submit(self._process_tc_batch, batch_info): batch_info
        for batch_info in tc_ranges
    }

    for future in as_completed(future_to_batch):
        try:
            test_cases = future.result()
            all_test_cases.extend(test_cases)
        except Exception as e:
            logger.error(f"  ✗ Batch failed: {e}")

# Re-number TCs sequentially after collection (cleanup any gaps)
for idx, tc in enumerate(sorted(all_test_cases, key=lambda x: int(x['test_id'].split('-')[1]))):
    tc['test_id'] = f"TC{idx + 1}"

logger.info(f"✓ Generated {len(all_test_cases)} test cases")
```

**Benefits**:
- 4-5 batches process simultaneously
- ~4x speedup in Phase 4 (30-40 sec → 8-10 sec)
- TC numbering preserved with cleanup step

---

### 3. PARALLEL STORY REWRITES (High Impact)

**Speedup**: 5-10x faster (rewrite 5-10 stories in parallel)

```python
def _rewrite_single_story(self, story, review):
    """Rewrite one story"""
    logger.info(f"    - {story['story_id']}: {review['total_score']}/100 → Rewriting...")

    rewrite_result = self.rewriter_agent.run(
        f"Rewrite {story['story_id']}",
        {"story": story, "review": review}
    )

    if rewrite_result["success"]:
        return rewrite_result["output"]["rewritten_story"]
    return None

def _quality_review_loop(self, stories: list) -> list:
    """LOOP 4: Iterative quality improvement (with parallel rewrites)"""

    max_iterations = 3
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"\n  Review Iteration {iteration}/{max_iterations}")

        # Review all stories (sequential - one LLM call)
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

        logger.info(f"  ↻ Rewriting {len(low_quality)} low-quality stories IN PARALLEL...")

        # PARALLEL REWRITES (NEW)
        improved_stories = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Create story lookup
            story_map = {s["story_id"]: s for s in stories}

            # Submit rewrite tasks
            future_to_review = {
                executor.submit(
                    self._rewrite_single_story,
                    story_map[review["story_id"]],
                    review
                ): review
                for review in low_quality
                if review["story_id"] in story_map
            }

            # Collect improved stories
            for future in as_completed(future_to_review):
                review = future_to_review[future]
                try:
                    improved_story = future.result()
                    if improved_story:
                        improved_stories[review["story_id"]] = improved_story
                except Exception as e:
                    logger.error(f"  ✗ Rewrite failed for {review['story_id']}: {e}")

        # Replace improved stories
        for i, story in enumerate(stories):
            if story["story_id"] in improved_stories:
                stories[i] = improved_stories[story["story_id"]]

    if iteration == max_iterations:
        logger.warning(f"  ⚠ Reached max iterations without full convergence")

    return stories
```

**Benefits**:
- 5-10 stories rewrite simultaneously
- ~8x speedup in Phase 5 (1-2 min → 10-20 sec)
- Maintains quality loop integrity

---

### 4. ASYNC LLM CALLS (Advanced - Future Enhancement)

**Speedup**: Additional 20-30% on top of parallelization

**Requirement**: Requires async-compatible LLM library (Ollama supports async)

```python
import asyncio
from langchain_ollama import AsyncChatOllama

class BaseAgent(ABC):
    def __init__(self, name: str, role: str, goal: str, temperature: float = 0.0):
        self.name = name
        self.role = role
        self.goal = goal

        model_name = os.getenv('OLLAMA_MODEL', 'qwen3-coder:30b')

        # Sync LLM for backward compatibility
        self.llm = ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url="http://localhost:11434",
            format="json"
        )

        # Async LLM for parallel execution
        self.async_llm = AsyncChatOllama(
            model=model_name,
            temperature=temperature,
            base_url="http://localhost:11434",
            format="json"
        )

    async def run_async(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Async version of run() for parallel execution"""
        try:
            logger.info(f"[{self.name}] Starting async task...")

            system_prompt = self.get_system_prompt(context)
            full_prompt = f"{system_prompt}\n\n{task}"

            # Async LLM call
            response = await self.async_llm.ainvoke(full_prompt)

            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)

            result = self._extract_json(response_text)

            logger.info(f"[{self.name}] Completed async task")

            return {
                "agent": self.name,
                "success": True,
                "output": result
            }
        except Exception as e:
            logger.error(f"[{self.name}] Async error: {str(e)}")
            return {
                "agent": self.name,
                "success": False,
                "error": str(e)
            }

# In orchestrator:
async def _process_epics_async(self, epics, requirements):
    """Process all epics in parallel using asyncio"""
    tasks = [
        self._process_single_epic_async(epic, requirements)
        for epic in epics
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_stories = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Epic processing failed: {result}")
        else:
            all_stories.extend(result)

    return all_stories
```

**Benefits**:
- True async I/O (non-blocking)
- Better resource utilization
- Can handle 10+ parallel requests efficiently

---

## 5. HYBRID APPROACH: Parallel Batches within Parallel Epics (Maximum Speed)

**Speedup**: 10-15x overall (Phase 3: 2-3 min → 10-15 sec)

```python
def _process_epic_batches_parallel(self, epic, requirements):
    """Process all batches within an epic in parallel"""
    epic_reqs = [r for r in requirements if r["id"] in epic["requirement_ids"]]
    batch_size = 4

    # Create batches
    batches = [
        epic_reqs[i:i+batch_size]
        for i in range(0, len(epic_reqs), batch_size)
    ]

    stories = []

    # Process batches in parallel (nested parallelization)
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_batch = {
            executor.submit(
                self.story_agent.run,
                f"Generate stories for batch {idx+1}",
                {"requirements_batch": batch, "epic": epic}
            ): batch
            for idx, batch in enumerate(batches)
        }

        for future in as_completed(future_to_batch):
            try:
                story_result = future.result()
                if story_result["success"]:
                    batch_stories = story_result["output"]["stories"]
                    for s in batch_stories:
                        s["epic_id"] = epic["epic_id"]
                        s["epic_name"] = epic["epic_name"]
                    stories.extend(batch_stories)
            except Exception as e:
                logger.error(f"Batch failed: {e}")

    return stories

# In generate_stories():
# PHASE 3: Parallel epics + parallel batches
with ThreadPoolExecutor(max_workers=5) as executor:
    future_to_epic = {
        executor.submit(self._process_epic_batches_parallel, epic, requirements): epic
        for epic in epics
    }

    for future in as_completed(future_to_epic):
        try:
            stories = future.result()
            all_stories.extend(stories)
        except Exception as e:
            logger.error(f"Epic failed: {e}")
```

**Benefits**:
- 5 epics × 4 batches = 20 LLM calls in parallel
- **10-15x speedup** (assumes sufficient GPU/LLM capacity)
- Maximum throughput

**WARNING**: Requires enough LLM capacity to handle 20 concurrent requests!

---

## Performance Comparison

| Phase | Current (Sequential) | Strategy 1 (Parallel Epics) | Strategy 3 (Full Parallel) |
|-------|---------------------|----------------------------|---------------------------|
| **Phase 3** | 2-3 min | 30-40 sec | 10-15 sec |
| **Phase 4** | 30-40 sec | 30-40 sec | 8-10 sec |
| **Phase 5** | 1-2 min | 1-2 min | 10-15 sec |
| **TOTAL** | **5-7 min** | **2.5-3.5 min** | **30-45 sec** |

---

## Recommended Implementation Plan

### Phase 1: Low-Risk Wins (Week 1)
1. **Parallel Epic Processing** (Strategy 1)
   - Add `ThreadPoolExecutor` to Phase 3
   - Extract `_process_single_epic()` method
   - Test with 2-3 workers first, scale to 5

2. **Parallel Story Rewrites** (Strategy 3)
   - Add `ThreadPoolExecutor` to review loop
   - Extract `_rewrite_single_story()` method

**Expected Speedup**: 3-4x overall (5-7 min → 1.5-2 min)

### Phase 2: Advanced Optimization (Week 2)
3. **Parallel Batch Processing** (Strategy 2)
   - Pre-calculate TC ranges
   - Parallelize Phase 4
   - Add TC re-numbering cleanup

**Expected Speedup**: 4-5x overall (5-7 min → 1-1.5 min)

### Phase 3: Maximum Performance (Week 3-4)
4. **Async LLM Calls** (Strategy 4)
   - Migrate to AsyncChatOllama
   - Convert agents to async/await
   - Test with asyncio.gather()

5. **Hybrid Parallel** (Strategy 5)
   - Nested parallelization (epics + batches)
   - Requires LLM capacity testing

**Expected Speedup**: 10-15x overall (5-7 min → 30-45 sec)

---

## Production Considerations

### 1. **LLM Capacity Limits**
- Ollama default: 1 concurrent request
- Need to configure parallel requests:
  ```bash
  # In Ollama config or environment
  OLLAMA_NUM_PARALLEL=5  # Allow 5 concurrent requests
  ```

### 2. **Error Handling**
- Use `try/except` in all worker functions
- Log failures but continue processing
- Collect partial results on failure

### 3. **Resource Monitoring**
- Monitor GPU memory (Ollama loads model once)
- Monitor CPU threads (ThreadPoolExecutor limit)
- Add timeout to prevent hanging (10-15 sec per call)

### 4. **Logging Improvements**
- Add timestamps to see parallel execution
- Log worker thread IDs
- Add progress bars for long operations

---

## Example: Complete Parallel Orchestrator

See `src/agents/orchestrator_parallel.py` (to be created)

```python
# orchestrator_parallel.py
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import time

logger = logging.getLogger(__name__)

class ParallelStoryOrchestrator(StoryOrchestrator):
    """
    Parallel version of StoryOrchestrator with ThreadPoolExecutor

    Improvements:
    - Parallel epic processing (5x speedup)
    - Parallel story rewrites (8x speedup)
    - Parallel batch processing (4x speedup)
    """

    def __init__(self, max_workers=5):
        super().__init__()
        self.max_workers = max_workers

    # ... (all methods from above)
```

---

## Next Steps

1. **Implement Phase 1** (Parallel Epics + Rewrites)
2. **Test with production data** (measure actual speedup)
3. **Configure Ollama** for parallel requests
4. **Monitor GPU/CPU usage**
5. **Iterate to Phase 2/3** based on results

Would you like me to implement the parallel version now?
