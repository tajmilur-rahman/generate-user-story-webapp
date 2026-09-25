from .requirements_agent import RequirementsAgent
from .epic_extractor_agent import EpicExtractorAgent
from .epic_refiner_agent import EpicRefinerAgent
from .story_agent import StoryAgent
from .test_agent import TestCaseAgent
from .reviewer_agent import ReviewerAgent
from .rewriter_agent import RewriterAgent
from .grounding import assess_grounding
from .invest_checks import evaluate_stories, summarise_scores
from difflib import SequenceMatcher
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import logging
import time
import json
import os
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Every generated story opens with the same persona clause, e.g.
# "As a weather station operator, I want to ...". That boilerplate is ~40
# characters of pure overlap, which inflates character-level similarity
# between completely unrelated stories. Strip it before comparing.
_STORY_PREFIX_RE = re.compile(
    r"^\s*as\s+an?\s+[^,]{0,80},\s*i\s+want(?:\s+to)?\s*", re.IGNORECASE)


def _story_core(text):
    """Return the story text with its persona boilerplate removed."""
    if not text:
        return ""
    return _STORY_PREFIX_RE.sub("", text).strip()

class ParallelStoryOrchestrator:
    """
    Parallel version of StoryOrchestrator using ThreadPoolExecutor

    Performance improvements:
    - Parallel epic processing (5x speedup in Phase 3)
    - Parallel story rewrites (8x speedup in Phase 5)
    - Parallel test case batches (4x speedup in Phase 4)

    Expected total speedup: 8-10x (25 min → 2-3 min)
    """

    def __init__(self, max_workers=None):
        """
        Initialize orchestrator with parallel execution capability

        Args:
            max_workers: Maximum parallel workers (default: 5 for optimal GPU utilization)
        """
        self.requirements_agent = RequirementsAgent()
        self.epic_extractor = EpicExtractorAgent()
        self.epic_refiner = EpicRefinerAgent()
        self.story_agent = StoryAgent()
        self.test_agent = TestCaseAgent()
        self.reviewer_agent = ReviewerAgent()
        self.rewriter_agent = RewriterAgent()

        # Default to 5 workers (good balance for single GPU)
        self.max_workers = max_workers or 5

        # Partial failures are collected here rather than only logged, so a run
        # that lost an epic is distinguishable from a complete one. Guarded by a
        # lock because worker threads append concurrently.
        self.failures = []
        self._failures_lock = Lock()

        # Set per run by generate_stories()
        self.run_id = None
        self.run_dir = None
        self.completed_phases = []

        logger.info(f"ParallelStoryOrchestrator initialized with {self.max_workers} workers")

    def deduplicate_requirements(self, requirements):
        """
        Deduplicate requirements by semantic similarity.

        Args:
            requirements: List of requirement dictionaries

        Returns:
            List of unique requirements (duplicates removed)
        """
        if not requirements or not isinstance(requirements, list):
            return requirements

        unique = []
        duplicates_found = []

        for req in requirements:
            if not req or not isinstance(req, dict):
                continue

            description = req.get('description', '')
            if not description:
                unique.append(req)
                continue

            is_duplicate = False
            for existing in unique:
                existing_desc = existing.get('description', '')
                similarity = SequenceMatcher(None, description.lower(), existing_desc.lower()).ratio()
                # SequenceMatcher scores CHARACTER overlap, not meaning. At 0.60
                # genuinely distinct requirements were being discarded -- e.g.
                # "Collect pressure readings periodically" scored 0.63 against
                # "Collect temperature readings every minute", and wind direction
                # scored 0.86 against wind speed. Only near-identical wording
                # should count as a duplicate. 0.90 specifically: "Collect wind
                # direction readings periodically" scores 0.857 against the wind
                # SPEED requirement, and those are different measurements.
                if similarity > 0.90:
                    is_duplicate = True
                    duplicates_found.append((description, existing_desc, similarity))
                    logger.info(f"🔍 Duplicate requirement detected ({similarity:.1%} similar)")
                    logger.info(f"   Skipping: {description[:80]}...")
                    logger.info(f"   Kept:     {existing_desc[:80]}...")
                    break

            if not is_duplicate:
                unique.append(req)

        if duplicates_found:
            logger.info(f"✅ Removed {len(duplicates_found)} duplicate requirements ({len(requirements)} → {len(unique)})")

        return unique

    def deduplicate_stories(self, stories):
        """
        Deduplicate stories by title + description similarity.

        Args:
            stories: List of story dictionaries

        Returns:
            List of unique stories (duplicates removed)
        """
        if not stories or not isinstance(stories, list):
            return stories

        unique = []
        duplicates_found = []

        for story in stories:
            if not isinstance(story, dict):
                continue

            title = story.get('user_story', '')
            description = story.get('acceptance_criteria', [])
            desc_text = ' '.join(description) if isinstance(description, list) else str(description)

            if not title and not desc_text:
                unique.append(story)
                continue

            requirement_id = str(story.get('requirement_id', '') or '').strip()

            is_duplicate = False
            for existing in unique:
                # BLOCKING: two stories that implement different requirements are
                # not duplicates, whatever their wording. Surface similarity
                # cannot decide this -- measured on real output, distinct stories
                # ("record temperature readings" vs "record pressure readings")
                # score HIGHER than a genuinely reworded duplicate, so no
                # threshold separates them. Restricting comparison to stories
                # that share a requirement removes the whole failure class by
                # construction. Stories with no requirement id are still compared,
                # since nothing distinguishes them.
                existing_requirement_id = str(
                    existing.get('requirement_id', '') or '').strip()
                if (requirement_id and existing_requirement_id
                        and requirement_id != existing_requirement_id):
                    continue

                existing_title = existing.get('user_story', '')
                existing_desc = existing.get('acceptance_criteria', [])
                existing_desc_text = ' '.join(existing_desc) if isinstance(existing_desc, list) else str(existing_desc)

                # Compare the story bodies with the shared persona prefix removed,
                # otherwise every story looks ~50-68% alike on boilerplate alone.
                title_sim = SequenceMatcher(
                    None, _story_core(title).lower(),
                    _story_core(existing_title).lower()).ratio()

                # Check description similarity
                desc_sim = SequenceMatcher(None, desc_text.lower(), existing_desc_text.lower()).ratio()

                # Require BOTH signals to agree. The previous `title_sim > 0.5 or
                # desc_sim > 0.7` dropped stories whose descriptions were only 3.5%
                # similar -- i.e. entirely different work -- on title overlap alone.
                # A near-identical title still counts on its own.
                if (title_sim > 0.75 and desc_sim > 0.60) or title_sim > 0.92:
                    is_duplicate = True
                    duplicates_found.append((title, existing_title, max(title_sim, desc_sim)))
                    logger.info(f"🔍 Duplicate story detected (title: {title_sim:.1%}, desc: {desc_sim:.1%})")
                    logger.info(f"   Skipping: {title[:60]}...")
                    logger.info(f"   Kept:     {existing_title[:60]}...")
                    break

            if not is_duplicate:
                unique.append(story)

        if duplicates_found:
            logger.info(f"✅ Removed {len(duplicates_found)} duplicate stories ({len(stories)} → {len(unique)})")

        return unique

    def _checkpoint(self, phase, payload):
        """
        Persist one phase's output as soon as it completes.

        GPU time is the expensive resource in this pipeline. Holding every
        intermediate result in memory until the final step means a bug in the
        last 2% discards a multi-minute run -- which is exactly what happened
        twice before this was added. Writing each phase as it lands turns a
        total loss into a recoverable one, and doubles as an audit trail.

        Never raises: a checkpoint failure must not take down a good run.

        Args:
            phase: Phase name, used as the filename
            payload: JSON-serialisable phase output
        """
        if not self.run_dir:
            return

        self.completed_phases.append(phase)
        try:
            os.makedirs(self.run_dir, exist_ok=True)
            path = os.path.join(self.run_dir, f"{phase}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            logger.info(f"  [CHECKPOINT] {phase} -> {path}")
        except Exception as e:
            logger.warning(f"  [CHECKPOINT] Could not persist {phase}: {e}")

    def _record_failure(self, phase, detail, error):
        """
        Record a partial failure so it can be reported to the caller.

        Args:
            phase: Pipeline phase name
            detail: What was being processed (epic name, batch, story id)
            error: Error description
        """
        with self._failures_lock:
            self.failures.append({
                "phase": phase,
                "detail": detail,
                "error": str(error)
            })
        logger.error(f"  ✗ [{phase}] {detail}: {error}")

    def _process_single_epic(self, epic, requirements):
        """
        Process one epic with all its batches (sequential batches within epic)

        Args:
            epic: Epic dictionary
            requirements: Full requirements list

        Returns:
            List of stories for this epic
        """
        epic_reqs = [r for r in requirements if r["id"] in epic["requirement_ids"]]
        logger.info(f"  [PARALLEL] Processing epic: {epic['epic_name']} ({len(epic_reqs)} requirements)")

        stories = []
        batch_size = 4

        for i in range(0, len(epic_reqs), batch_size):
            batch = epic_reqs[i:i+batch_size]

            story_result = self.story_agent.run(
                f"Generate stories for batch {i//batch_size + 1}",
                {"requirements_batch": batch, "epic": epic}
            )

            if not story_result["success"]:
                self._record_failure(
                    "stories", f"epic {epic['epic_name']} batch {i//batch_size + 1}",
                    story_result.get("error", "unknown")
                )
                continue

            if story_result["success"]:
                batch_stories = story_result["output"]["stories"]
                # Add epic context.
                #
                # Each epic is a separate Story Writer call with no starting
                # number, so every epic independently numbers its stories from
                # STORY-001. Left alone those IDs collide across the parallel
                # workers: the review loop keys stories by story_id, so most
                # stories become unreachable and a single rewrite overwrites
                # every story sharing the ID. Namespace the ID by epic, which
                # stays unique without any cross-thread counter.
                for offset, s in enumerate(batch_stories, start=len(stories) + 1):
                    s["epic_id"] = epic["epic_id"]
                    s["epic_name"] = epic["epic_name"]
                    s["story_id"] = f"{epic['epic_id']}-STORY-{offset:03d}"
                stories.extend(batch_stories)

        logger.info(f"  [PARALLEL] ✓ Completed epic: {epic['epic_name']} ({len(stories)} stories)")
        return stories

    def _process_tc_batch(self, batch_info):
        """
        Process one test case batch

        Args:
            batch_info: Dictionary with 'batch' and 'starting_tc' keys

        Returns:
            List of test cases
        """
        tc_result = self.test_agent.run(
            f"Generate test cases for batch",
            {
                "requirements_batch": batch_info['batch'],
                "starting_tc_number": batch_info['starting_tc']
            }
        )

        if tc_result["success"]:
            test_cases = tc_result["output"]["test_cases"]
            logger.info(f"  [PARALLEL] ✓ Generated {len(test_cases)} test cases (starting TC{batch_info['starting_tc']})")
            return test_cases

        self._record_failure(
            "test_cases", f"batch starting TC{batch_info['starting_tc']}",
            tc_result.get("error", "unknown")
        )
        return []

    def _assign_test_case_ids(self, batch_results, requirements):
        """
        Flatten parallel batch results and assign test case IDs centrally.

        Model-authored IDs are ignored entirely rather than parsed. The previous
        implementation sorted on int(test_id.replace('TC', '')), so a single
        malformed ID from any batch -- 'tc1', 'TC_1', 'TC01-A', or a missing key
        -- raised and destroyed a completed multi-minute run. Nothing the model
        writes should be able to do that.

        Ordering is by requirement position then batch position, so the same
        input yields the same IDs regardless of thread completion order.

        Args:
            batch_results: Mapping of batch position -> list of test cases
            requirements: Requirements in document order

        Returns:
            Flat list of test cases with sequential TC IDs
        """
        req_order = {req["id"]: idx for idx, req in enumerate(requirements)}
        flattened = []

        for batch_pos in sorted(batch_results):
            for within_batch, tc in enumerate(batch_results[batch_pos]):
                if not isinstance(tc, dict):
                    continue
                # Unknown requirement ids sort last rather than crashing
                sort_key = (
                    req_order.get(tc.get("requirement_id"), len(req_order)),
                    batch_pos,
                    within_batch
                )
                flattened.append((sort_key, tc))

        flattened.sort(key=lambda pair: pair[0])

        ordered = []
        for idx, (_, tc) in enumerate(flattened, start=1):
            tc["test_id"] = f"TC{idx}"
            ordered.append(tc)

        return ordered

    def _calculate_tc_ranges(self, requirements, batch_size=4):
        """
        Pre-calculate starting TC numbers for each batch

        Args:
            requirements: List of requirements
            batch_size: Number of requirements per batch

        Returns:
            List of batch info dictionaries
        """
        tc_ranges = []
        current_tc = 1

        for i in range(0, len(requirements), batch_size):
            batch = requirements[i:i+batch_size]
            # Estimate: 3 TCs per requirement (average of 2-4)
            estimated_tcs = len(batch) * 3
            tc_ranges.append({
                'batch_idx': i,
                'batch': batch,
                'starting_tc': current_tc
            })
            current_tc += estimated_tcs

        return tc_ranges

    def _review_batch(self, batch):
        """
        Review one batch of stories.

        Args:
            batch: List of story dictionaries

        Returns:
            List of review dictionaries (empty on failure)
        """
        result = self.reviewer_agent.run(
            "Review and score all stories",
            {"stories": batch}
        )

        if not result["success"]:
            logger.error(f"    [PARALLEL] ✗ Review batch of {len(batch)} failed")
            return []

        reviews = result["output"].get("story_reviews", [])
        logger.info(f"    [PARALLEL] ✓ Reviewed {len(reviews)} stories")
        return reviews

    def _rewrite_single_story(self, story, review):
        """
        Rewrite one story

        Args:
            story: Story dictionary
            review: Review dictionary with scores and feedback

        Returns:
            Improved story or None on failure
        """
        story_id = story.get('story_id', 'unknown')
        score = review.get('total_score', 0)

        logger.info(f"    [PARALLEL] Rewriting {story_id} (score: {score}/100)...")

        rewrite_result = self.rewriter_agent.run(
            f"Rewrite {story_id}",
            {"story": story, "review": review}
        )

        if rewrite_result["success"]:
            logger.info(f"    [PARALLEL] ✓ Rewritten {story_id}")
            improved = rewrite_result["output"]["rewritten_story"]
            # The rewriter returns fresh story text and may drop or invent the
            # identity fields. Carry the originals over so the story stays
            # attached to its epic and keeps the ID the review loop matches on.
            if isinstance(improved, dict):
                for field in ("story_id", "epic_id", "epic_name", "requirement_id"):
                    if field in story:
                        improved[field] = story[field]
            return improved

        logger.error(f"    [PARALLEL] ✗ Rewrite failed for {story_id}")
        return None

    def generate_stories(self, document_text: str) -> dict:
        """Main pipeline with parallel execution"""

        start_time = time.time()

        # Reset per-run state: the orchestrator may be reused across requests.
        with self._failures_lock:
            self.failures = []

        self.run_id = (
            f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        )
        self.run_dir = os.path.join(
            os.getenv('RUN_ARTIFACT_DIR', os.path.join('data', 'runs')),
            self.run_id
        )
        self.completed_phases = []
        logger.info(f"Run ID: {self.run_id}")

        logger.info("=" * 60)
        logger.info("Starting PARALLEL Agentic Story Generation Pipeline")
        logger.info(f"Workers: {self.max_workers}")
        logger.info("=" * 60)

        # PHASE 1: Requirements Extraction
        phase_start = time.time()
        logger.info("\n[PHASE 1] Extracting Requirements...")
        req_result = self.requirements_agent.run(
            "Extract and refine all requirements",
            {"document": document_text}
        )

        if not req_result["success"]:
            raise Exception(f"Requirements extraction failed: {req_result.get('error')}")

        requirements = req_result["output"]["requirements"]
        logger.info(f"✓ Extracted {len(requirements)} requirements ({time.time() - phase_start:.1f}s)")

        # DEDUPLICATION: Remove duplicate requirements by semantic similarity
        logger.info("\n[DEDUPLICATION] Checking for duplicate requirements...")
        requirements = self.deduplicate_requirements(requirements)
        logger.info(f"✓ Final requirement count: {len(requirements)}")
        self._checkpoint("01_requirements", requirements)

        # PHASE 2: Epic Generation (LOOP 2 - Extract → Refine)
        phase_start = time.time()
        logger.info("\n[PHASE 2] Generating Epics (Two-Pass)...")

        # Pass 1: Extract
        epic_extract_result = self.epic_extractor.run(
            "Extract initial epics",
            {"requirements": requirements}
        )

        if not epic_extract_result["success"]:
            raise Exception("Epic extraction failed")

        raw_epics = epic_extract_result["output"]["epics"]
        logger.info(f"✓ Extracted {len(raw_epics)} raw epics")

        # Pass 2: Refine
        epic_refine_result = self.epic_refiner.run(
            "Refine and merge epics",
            {"raw_epics": raw_epics, "requirements": requirements}
        )

        if not epic_refine_result["success"]:
            raise Exception("Epic refinement failed")

        epics = epic_refine_result["output"]["epics"]
        logger.info(f"✓ Refined to {len(epics)} final epics ({time.time() - phase_start:.1f}s)")
        self._checkpoint("02_epics", epics)

        # PHASE 3: Story Generation (PARALLEL EPICS) ⚡
        phase_start = time.time()
        logger.info(f"\n[PHASE 3] Generating Stories (PARALLEL - {self.max_workers} workers)...")
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
                except Exception as e:
                    self._record_failure("stories", f"epic {epic['epic_name']}", e)

        logger.info(f"✓ Generated {len(all_stories)} stories ({time.time() - phase_start:.1f}s)")

        # DEDUPLICATION: Remove duplicate stories by title/description similarity
        logger.info("\n[DEDUPLICATION] Checking for duplicate stories...")
        all_stories = self.deduplicate_stories(all_stories)
        logger.info(f"✓ Final story count: {len(all_stories)}")

        # GROUNDING REPORT: note vocabulary that does not occur in the source.
        #
        # Reporting only -- nothing is removed. A ratio was measured not to
        # separate fabricated stories from genuine ones (a fabrication scored
        # 44% against a genuine story's 29%, because fabrications reuse the
        # document's framing and only the subject is invented), so no verdict
        # is asserted. The absent vocabulary is what a reader can act on:
        # "humidity" missing from a weather specification is obvious.
        for story in all_stories:
            report = assess_grounding(
                f"{story.get('title', '')} {story.get('user_story', '')}",
                document_text)
            story["grounding"] = report
            if report["unsupported_terms"]:
                logger.info(
                    f"  ℹ Not in source document ({report['score']:.0%} of terms "
                    f"found): {', '.join(report['unsupported_terms'][:6])} "
                    f"-- {story.get('user_story', '')[:60]}"
                )

        self._checkpoint("03_stories", all_stories)

        # PHASE 4: Test Case Generation (PARALLEL BATCHES) ⚡
        phase_start = time.time()
        logger.info(f"\n[PHASE 4] Generating Test Cases (PARALLEL - {self.max_workers} workers)...")

        # Pre-calculate TC ranges
        tc_ranges = self._calculate_tc_ranges(requirements, batch_size=4)
        all_test_cases = []

        # Process batches in parallel. Results are keyed by batch position, not
        # appended on arrival, so ordering never depends on which thread
        # finishes first.
        batch_results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_batch = {
                executor.submit(self._process_tc_batch, batch_info): pos
                for pos, batch_info in enumerate(tc_ranges)
            }

            for future in as_completed(future_to_batch):
                pos = future_to_batch[future]
                try:
                    batch_results[pos] = future.result()
                except Exception as e:
                    self._record_failure("test_cases", f"batch {pos}", e)

        all_test_cases = self._assign_test_case_ids(batch_results, requirements)

        logger.info(f"✓ Generated {len(all_test_cases)} test cases ({time.time() - phase_start:.1f}s)")
        self._checkpoint("04_test_cases", all_test_cases)

        # Match TCs to stories
        all_stories = self._match_test_cases(all_stories, all_test_cases)

        # PHASE 5: Quality Review Loop (PARALLEL REWRITES) ⚡
        phase_start = time.time()
        logger.info(f"\n[PHASE 5] Quality Review Loop (PARALLEL - {self.max_workers} workers)...")
        all_stories = self._quality_review_loop(all_stories)
        logger.info(f"✓ Quality review complete ({time.time() - phase_start:.1f}s)")
        self._checkpoint("05_reviewed_stories", all_stories)

        total_time = time.time() - start_time

        self._log_summary(total_time)

        return {
            "run_id": self.run_id,
            "requirements": requirements,
            "epics": epics,
            "stories": all_stories,
            "test_cases": all_test_cases,
            "execution_time": total_time,
            "failures": list(self.failures),
            "partial": bool(self.failures)
        }

    def _log_summary(self, total_time):
        """
        Report the total run time.

        Per-phase timings and deduplication counts are already logged inline as
        each phase completes, so this reports only the final figure.

        Args:
            total_time: Total pipeline wall-clock time in seconds
        """
        if total_time < 60:
            elapsed = f"{total_time:.1f}s"
        else:
            elapsed = f"{int(total_time // 60)}m {total_time % 60:04.1f}s"

        logger.info("\n" + "=" * 62)
        logger.info(f"Pipeline complete in {elapsed}")
        logger.info("=" * 62)

    def _quality_review_loop(self, stories: list) -> list:
        """LOOP 4: Iterative quality improvement with PARALLEL rewrites"""

        max_iterations = 3
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"\n  Review Iteration {iteration}/{max_iterations}")

            # Deterministic INVEST checks first. They are free, unbiased and
            # cannot return a false pass, so anything they can decide should
            # not cost a model call.
            rubric = evaluate_stories(stories)
            rubric_scores = [r["score"] for r in rubric.values()]
            rubric_dist = summarise_scores(rubric_scores)
            logger.info(
                f"  Rubric scores: mean={rubric_dist['mean']} "
                f"min={rubric_dist['min']} max={rubric_dist['max']}"
            )
            for story_id, outcome in rubric.items():
                if outcome["issues"]:
                    logger.info(
                        f"    {story_id}: {outcome['score']}/100 - "
                        f"{'; '.join(outcome['issues'][:2])}"
                    )

            # Review in PARALLEL batches. A single call scoring every story was
            # the serial bottleneck of this phase (~22% of total runtime), and
            # its prompt grew without bound as the story count rose, risking
            # truncated or degraded scoring on larger documents.
            review_batch_size = 4
            batches = [stories[i:i + review_batch_size]
                       for i in range(0, len(stories), review_batch_size)]

            story_reviews = []
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self._review_batch, b) for b in batches]
                for future in as_completed(futures):
                    try:
                        story_reviews.extend(future.result())
                    except Exception as e:
                        self._record_failure("review", "review batch", e)

            if not story_reviews:
                logger.error("  Review failed, skipping quality loop")
                break

            scores = [r.get("total_score", 0)
                      for r in story_reviews if isinstance(r, dict)]
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0

            # Log the distribution, not just the mean. A judge returning the
            # same number for every story is indistinguishable from a genuinely
            # uniform batch if you only print the average -- which is how a
            # constant 93/100 went unquestioned across runs.
            dist = summarise_scores(scores)
            logger.info(
                f"  Judge scores: mean={dist['mean']} median={dist['median']} "
                f"min={dist['min']} max={dist['max']} "
                f"distinct={dist['distinct_values']}/{dist['count']}"
            )
            if dist["count"] > 2 and dist["distinct_values"] == 1:
                logger.warning(
                    f"  ⚠ Judge returned {dist['mean']} for all "
                    f"{dist['count']} stories -- the model score is not "
                    f"discriminating. Set REVIEWER_MODEL to a different model."
                )

            logger.info(f"  Average INVEST Score: {avg_score}/100")

            # Find stories needing improvement
            low_quality = []
            for review in story_reviews:
                if not isinstance(review, dict):
                    continue
                judge_score = review.get("total_score", 0)
                rubric_score = rubric.get(review.get("story_id"), {}).get("score", 100)

                # Either gate can send a story back. The rubric catches what the
                # judge is too generous to fail; the judge catches what no rule
                # can express.
                if judge_score < 70 or rubric_score < 70:
                    review.setdefault("issues", [])
                    review["issues"] = list(review["issues"]) + rubric.get(
                        review.get("story_id"), {}).get("issues", [])
                    low_quality.append(review)

            if not low_quality:
                logger.info(
                    "  ✓ All stories meet quality threshold (≥70) on both the "
                    "deterministic rubric and the model judge"
                )
                break

            logger.info(f"  ↻ Rewriting {len(low_quality)} low-quality stories IN PARALLEL...")

            # PARALLEL REWRITES ⚡
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
                        self._record_failure(
                            "rewrite", f"story {review.get('story_id', '?')}", e)

            # Replace improved stories
            for i, story in enumerate(stories):
                if story.get("story_id") in improved_stories:
                    stories[i] = improved_stories[story["story_id"]]

        if iteration == max_iterations:
            logger.warning(f"  ⚠ Reached max iterations without full convergence")

        return stories

    def _match_test_cases(self, stories: list, test_cases: list) -> list:
        """Match TCs to stories - reuses existing similarity logic"""
        # Import the similarity function from existing code. The package is
        # rooted at src/, so the path is backend.services -- not src.backend.
        try:
            from backend.services.story_service import _tc_similarity
        except ImportError:
            # Fallback to simple keyword matching
            logger.warning("Could not import _tc_similarity, using fallback matching")
            _tc_similarity = self._simple_similarity

        claimed_tc_groups = set()

        for story in stories:
            story_text = story.get("user_story", "")
            best_match = None
            best_score = 0.0

            for tc in test_cases:
                if tc["test_id"] in claimed_tc_groups:
                    continue

                tc_text = f"{tc.get('test_description', '')} {' '.join(tc.get('test_steps', []))}"
                similarity = _tc_similarity(story_text, tc_text)

                # 0.35 matches the threshold story_service uses for the same
                # comparison. At 0.5 a story and its test case almost never
                # cleared the bar, so stories came back with no test cases.
                if similarity > best_score and similarity >= 0.35:
                    best_score = similarity
                    best_match = tc

            if best_match:
                story["test_cases"] = [best_match]
                claimed_tc_groups.add(best_match["test_id"])
            else:
                story["test_cases"] = []

        return stories

    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Simple keyword-based similarity (fallback)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0
