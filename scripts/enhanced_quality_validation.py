#!/usr/bin/env python3
"""
Enhanced Quality Validation Framework
Addresses issue 3.2 - Content Quality Validation from COMPREHENSIVE_ISSUE_RESOLUTION.md

Validates:
- Result relevance to queries
- Content completeness (title, authors, abstract)
- PDF availability claims
- Source-specific quality thresholds
- Cross-disciplinary routing quality
"""

import asyncio
import sys
import time
from typing import Any, Dict, List, Optional


class QualityValidator:
    """Enhanced validator for content quality and relevance"""

    def __init__(self):
        self.quality_tests = {
            "machine learning": {
                "relevance_keywords": [
                    "machine",
                    "learning",
                    "neural",
                    "algorithm",
                    "AI",
                    "artificial",
                    "deep",
                    "model",
                ],
                "irrelevant_keywords": [
                    "cooking",
                    "recipe",
                    "music",
                    "art",
                    "literature",
                ],
                "expected_domains": [
                    "computer science",
                    "artificial intelligence",
                    "data science",
                ],
                "min_completeness_score": 0.7,
            },
            "diabetes treatment": {
                "relevance_keywords": [
                    "diabetes",
                    "diabetic",
                    "insulin",
                    "glucose",
                    "glycemic",
                    "treatment",
                    "therapy",
                ],
                "irrelevant_keywords": [
                    "poetry",
                    "music",
                    "art",
                    "literature",
                    "cooking",
                ],
                "expected_domains": ["medicine", "endocrinology", "health"],
                "min_completeness_score": 0.8,
            },
            "AI in healthcare": {  # Cross-disciplinary test
                "relevance_keywords": [
                    "AI",
                    "artificial",
                    "intelligence",
                    "machine",
                    "learning",
                    "health",
                    "medical",
                    "clinical",
                ],
                "irrelevant_keywords": ["cooking", "music", "art", "literature"],
                "expected_domains": [
                    "computer science",
                    "medicine",
                    "health informatics",
                ],
                "min_completeness_score": 0.7,
                "cross_disciplinary": True,
            },
        }

    async def run_quality_validation(self) -> Dict[str, Any]:
        """Run comprehensive content quality validation"""
        print("🎯 Enhanced Quality Validation Starting...")
        print("=" * 50)

        results = {
            "timestamp": time.time(),
            "tests": [],
            "overall_quality_score": 0.0,
            "status": "UNKNOWN",
        }

        # Test each quality dimension
        for query, criteria in self.quality_tests.items():
            print(f"📝 Testing quality for: '{query}'")
            test_result = await self._test_query_quality(query, criteria)
            results["tests"].append(test_result)

        # Calculate overall quality score
        passed_tests = sum(1 for test in results["tests"] if test["passed"])
        total_tests = len(results["tests"])
        results["overall_quality_score"] = (
            passed_tests / total_tests if total_tests > 0 else 0
        )

        # Determine status
        if results["overall_quality_score"] >= 0.8:
            results["status"] = "PASS"
            print(
                f"\n✅ Quality validation passed ({results['overall_quality_score']:.1%})"
            )
        else:
            results["status"] = "FAIL"
            print(
                f"\n❌ Quality validation failed ({results['overall_quality_score']:.1%})"
            )

        return results

    async def _test_query_quality(
        self, query: str, criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test quality for a specific query"""
        test_result = {
            "query": query,
            "passed": False,
            "relevance_score": 0.0,
            "completeness_score": 0.0,
            "pdf_availability_score": 0.0,
            "cross_disciplinary_score": 0.0,
            "issues": [],
        }

        try:
            sys.path.insert(0, ".")
            from paperez_mcp import server

            # Get results
            result = await asyncio.wait_for(
                server.browse_papers.fn(query, limit=5), timeout=15.0
            )

            if not result or len(result) == 0:
                test_result["issues"].append("No results returned")
                return test_result

            papers = result[0].get("results", [])
            if len(papers) == 0:
                test_result["issues"].append("No papers in results")
                return test_result

            # Test relevance
            test_result["relevance_score"] = self._calculate_relevance_score(
                papers, criteria
            )

            # Test completeness
            test_result["completeness_score"] = self._calculate_completeness_score(
                papers
            )

            # Test PDF availability
            test_result["pdf_availability_score"] = (
                self._calculate_pdf_availability_score(papers)
            )

            # Test cross-disciplinary quality if applicable
            if criteria.get("cross_disciplinary", False):
                test_result["cross_disciplinary_score"] = (
                    self._calculate_cross_disciplinary_score(result[0], criteria)
                )

            # Overall pass/fail determination
            min_completeness = criteria.get("min_completeness_score", 0.7)
            if (
                test_result["relevance_score"] >= 0.6
                and test_result["completeness_score"] >= min_completeness
                and test_result["pdf_availability_score"] >= 0.3
            ):  # Some PDFs should be available
                test_result["passed"] = True
            else:
                test_result["issues"].append(f"Quality thresholds not met")

            print(
                f"  Relevance: {test_result['relevance_score']:.2f}, Completeness: {test_result['completeness_score']:.2f}, PDF: {test_result['pdf_availability_score']:.2f}"
            )

        except Exception as e:
            test_result["issues"].append(f"Quality test error: {str(e)}")

        return test_result

    def _calculate_relevance_score(
        self, papers: List[Dict], criteria: Dict[str, Any]
    ) -> float:
        """Calculate how relevant the results are to the query"""
        if not papers:
            return 0.0

        relevant_keywords = criteria.get("relevance_keywords", [])
        irrelevant_keywords = criteria.get("irrelevant_keywords", [])

        total_score = 0.0
        for paper in papers:
            paper_score = 0.0
            text_to_check = (
                f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
            )

            # Positive scoring for relevant keywords
            relevant_matches = sum(
                1 for keyword in relevant_keywords if keyword.lower() in text_to_check
            )
            paper_score += (
                relevant_matches / len(relevant_keywords) if relevant_keywords else 0
            )

            # Negative scoring for irrelevant keywords
            irrelevant_matches = sum(
                1 for keyword in irrelevant_keywords if keyword.lower() in text_to_check
            )
            paper_score -= irrelevant_matches * 0.5  # Penalty for irrelevant content

            total_score += max(0, min(1, paper_score))  # Clamp between 0 and 1

        return total_score / len(papers)

    def _calculate_completeness_score(self, papers: List[Dict]) -> float:
        """Calculate how complete the metadata is"""
        if not papers:
            return 0.0

        total_score = 0.0
        for paper in papers:
            completeness = 0.0

            # Required fields
            if paper.get("title"):
                completeness += 0.4
            if paper.get("authors"):
                completeness += 0.3
            if paper.get("abstract"):
                completeness += 0.2
            if paper.get("year"):
                completeness += 0.1

            total_score += completeness

        return total_score / len(papers)

    def _calculate_pdf_availability_score(self, papers: List[Dict]) -> float:
        """Calculate PDF availability rate"""
        if not papers:
            return 0.0

        pdf_available = 0
        for paper in papers:
            if (
                paper.get("pdf_url")
                or paper.get("open_access_pdf")
                or paper.get("url", "").endswith(".pdf")
            ):
                pdf_available += 1

        return pdf_available / len(papers)

    def _calculate_cross_disciplinary_score(
        self, result: Dict, criteria: Dict[str, Any]
    ) -> float:
        """Calculate cross-disciplinary routing quality"""
        sources_used = result.get("sources_used", [])

        # For cross-disciplinary queries, expect multiple different source types
        source_diversity = len(set(sources_used))

        # Look for evidence of cross-disciplinary sources
        has_stem_source = any(source in sources_used for source in ["arxiv", "ieee"])
        has_medical_source = any(
            source in sources_used for source in ["pubmed", "pubmed_central"]
        )
        has_general_source = any(
            source in sources_used for source in ["semantic_scholar", "crossref"]
        )

        diversity_score = min(
            1.0, source_diversity / 3.0
        )  # Expect at least 3 different sources
        type_coverage = (
            has_stem_source + has_medical_source + has_general_source
        ) / 3.0

        return (diversity_score + type_coverage) / 2.0


async def main():
    """Run enhanced quality validation"""
    import time

    validator = QualityValidator()
    results = await validator.run_quality_validation()

    # Exit with appropriate code
    if results["status"] == "PASS":
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
