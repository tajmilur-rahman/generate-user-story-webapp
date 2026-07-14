from .requirements_agent import RequirementsAgent
from .epic_extractor_agent import EpicExtractorAgent
from .epic_refiner_agent import EpicRefinerAgent
from .story_agent import StoryAgent
from .test_agent import TestCaseAgent
from .reviewer_agent import ReviewerAgent
from .rewriter_agent import RewriterAgent
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

        if not req_result["success"]:
            raise Exception(f"Requirements extraction failed: {req_result.get('error')}")

        requirements = req_result["output"]["requirements"]
        logger.info(f"✓ Extracted {len(requirements)} requirements")

        # PHASE 2: Epic Generation (LOOP 2 - Extract → Refine)
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

        # PHASE 4: Test Case Generation (LOOP 3 - Batched with Global TC Numbering)
        logger.info("\n[PHASE 4] Generating Test Cases (Batched)...")
        all_test_cases = []
        batch_size = 4
        current_tc_number = 1  # Global TC numbering starts at 1

        for i in range(0, len(requirements), batch_size):
            batch = requirements[i:i+batch_size]

            tc_result = self.test_agent.run(
                f"Generate test cases for batch {i//batch_size + 1}",
                {
                    "requirements_batch": batch,
                    "starting_tc_number": current_tc_number  # Pass current TC number
                }
            )

            if tc_result["success"]:
                batch_test_cases = tc_result["output"]["test_cases"]
                all_test_cases.extend(batch_test_cases)
                # Update TC number for next batch (assuming 2-3 TCs per requirement)
                current_tc_number += len(batch_test_cases)

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
                story = next((s for s in stories if s["story_id"] == story_id), None)

                if not story:
                    continue

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
        # Import the similarity function from existing code
        try:
            from src.backend.services.story_service import _tc_similarity
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

                if similarity > best_score and similarity >= 0.5:
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
