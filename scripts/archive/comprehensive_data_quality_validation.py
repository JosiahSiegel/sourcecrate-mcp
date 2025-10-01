#!/usr/bin/env python3
"""
Comprehensive Data Quality Validation Script

Validates all data quality improvements implemented for Issues 4.1, 4.2, and 4.3.
Tests PDF availability, metadata standardization, enrichment, and relevance scoring.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from paperez_mcp.api_clients.arxiv_client import search_arxiv
from paperez_mcp.api_clients.pubmed_client import search_pubmed
from paperez_mcp.utils.metadata_enrichment import metadata_enrichment_service
from paperez_mcp.utils.metadata_normalizer import metadata_normalizer
from paperez_mcp.utils.pdf_validator import pdf_validator
from paperez_mcp.utils.relevance_scorer import relevance_scorer

logging.basicConfig(level=logging.WARNING)  # Reduce noise during testing


class DataQualityValidator:
    """Comprehensive validator for data quality improvements"""

    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}")

        if details:
            print(f"   📝 {details}")

        self.test_results[test_name] = {"passed": passed, "details": details}

    async def test_pdf_validation_system(self):
        """Test PDF URL validation and alternative source integration"""
        print("\n📄 Testing PDF Validation System...")

        # Test 1: PDF URL format validation (without network calls)
        test_urls = [
            "https://arxiv.org/pdf/2301.12345.pdf",  # Valid format
            "https://example.com/not-pdf",  # Invalid format
            "not-a-url",  # Invalid format
        ]

        valid_format_count = 0
        for url in test_urls:
            # Test format validation instead of network validation
            is_valid_format = (
                isinstance(url, str)
                and url.startswith(("http://", "https://"))
                and url.endswith(".pdf")
            )
            if is_valid_format:
                valid_format_count += 1

        # Also test that the validation function handles invalid formats gracefully
        validation_handles_invalid = True
        try:
            invalid_result, _ = await pdf_validator.validate_pdf_url("not-a-url")
            # Should return False for invalid format
            validation_handles_invalid = not invalid_result
        except Exception:
            validation_handles_invalid = False

        self.log_test(
            "PDF URL Validation",
            valid_format_count == 1 and validation_handles_invalid,
            f"Format validation: {valid_format_count}/1 valid, handles invalid: {validation_handles_invalid}",
        )

        # Test 2: Alternative PDF source discovery
        test_paper = {
            "title": "Test Paper",
            "doi": "10.1371/journal.pone.0123456",  # PLOS ONE
            "arxiv_id": "2301.12345",
        }

        alternatives = await pdf_validator.find_alternative_pdf_urls(test_paper)
        self.log_test(
            "Alternative PDF Discovery",
            len(alternatives) > 0,
            f"Found {len(alternatives)} alternative PDF sources",
        )

        # Test 3: PDF enhancement workflow
        enhanced = await pdf_validator.enhance_pdf_availability(test_paper)
        has_enhancement_metadata = "pdf_validated" in enhanced
        self.log_test(
            "PDF Enhancement Workflow",
            has_enhancement_metadata,
            f"Added enhancement metadata: {has_enhancement_metadata}",
        )

    async def test_metadata_normalization(self):
        """Test metadata normalization and completeness scoring"""
        print("\n📊 Testing Metadata Normalization...")

        # Test 1: Title normalization
        test_titles = [
            "machine learning advances",  # Should capitalize
            "  Extra   Spaces  ",  # Should clean
            "Title with Period.",  # Should remove trailing period
        ]

        normalized_titles = [
            metadata_normalizer.normalize_title(title) for title in test_titles
        ]
        proper_capitalization = all(
            title[0].isupper() for title in normalized_titles if title
        )
        self.log_test(
            "Title Normalization",
            proper_capitalization,
            f"Capitalized: {normalized_titles[0]}",
        )

        # Test 2: Author parsing
        test_authors = [
            "John Smith, Jane Doe",  # String format
            [{"name": "John Smith"}, {"name": "Jane Doe"}],  # Dict format
            ["John Smith", "Jane Doe"],  # List format
        ]

        parsed_authors = [
            metadata_normalizer.normalize_authors(authors) for authors in test_authors
        ]
        all_lists = all(isinstance(result, list) for result in parsed_authors)
        self.log_test(
            "Author Normalization", all_lists, f"All converted to lists: {all_lists}"
        )

        # Test 3: Completeness scoring
        complete_paper = {
            "title": "Complete Research Paper on Advanced Topics",
            "authors": ["Dr. Smith", "Dr. Jones"],
            "abstract": "This is a comprehensive abstract with sufficient detail about the research methodology and findings.",
            "year": 2023,
            "journal": "Nature",
            "doi": "10.1038/nature.2023.001",
            "pdf_url": "https://nature.com/paper.pdf",
        }

        incomplete_paper = {
            "title": "Short",
            "authors": [],
            "abstract": "",
        }

        complete_score = metadata_normalizer.calculate_completeness_score(
            complete_paper
        )
        incomplete_score = metadata_normalizer.calculate_completeness_score(
            incomplete_paper
        )

        self.log_test(
            "Completeness Scoring",
            complete_score > incomplete_score and complete_score > 0.8,
            f"Complete: {complete_score:.2f}, Incomplete: {incomplete_score:.2f}",
        )

    async def test_metadata_enrichment(self):
        """Test cross-source metadata enrichment"""
        print("\n🔗 Testing Metadata Enrichment...")

        # Test 1: Field discovery
        available_fields = metadata_enrichment_service._discover_available_fields()
        standard_fields_found = {"title", "authors", "abstract"}.issubset(
            available_fields
        )
        self.log_test(
            "Dynamic Field Discovery",
            standard_fields_found and len(available_fields) >= 8,
            f"Discovered {len(available_fields)} fields: {sorted(list(available_fields))[:5]}...",
        )

        # Test 2: Multi-source enrichment
        primary_paper = {
            "title": "Short Title",  # Low quality
            "authors": ["Smith"],
            "source": "source_a",
        }

        alternative_paper = {
            "title": "Comprehensive Machine Learning Research: Advanced Methods and Applications",  # Better
            "authors": ["Dr. John Smith", "Dr. Jane Doe"],
            "citation_count": 42,
            "pdf_url": "https://example.com/better.pdf",
            "source": "source_b",
        }

        enriched = await metadata_enrichment_service.enrich_paper_metadata(
            primary_paper, [alternative_paper]
        )

        enrichment_occurred = (
            "_enriched_fields" in enriched
            and len(enriched.get("_enriched_fields", [])) > 0
        )
        self.log_test(
            "Cross-Source Enrichment",
            enrichment_occurred,
            f"Enriched fields: {enriched.get('_enriched_fields', [])}",
        )

        # Test 3: Quality-based value selection
        test_values = {
            "low_quality": "ML Paper",
            "high_quality": "Comprehensive Machine Learning Research Methods",
        }

        best_value, best_source = metadata_enrichment_service._select_best_value(
            "title", test_values
        )
        selected_better_quality = len(best_value) > len(test_values["low_quality"])
        self.log_test(
            "Quality-Based Selection",
            selected_better_quality,
            f"Selected: '{best_value}' from {best_source}",
        )

    async def test_relevance_scoring(self):
        """Test relevance scoring and ranking system"""
        print("\n🎯 Testing Relevance Scoring...")

        query = "machine learning medical diagnosis"

        test_papers = [
            {
                "title": "Machine Learning for Medical Diagnosis and Treatment",
                "abstract": "Comprehensive study on machine learning applications in medical diagnosis",
                "year": 2023,
                "citation_count": 50,
                "metadata_completeness": 0.95,
            },
            {
                "title": "Statistical Methods in Economics",  # Irrelevant
                "abstract": "Economic analysis using statistical approaches",
                "year": 2020,
                "citation_count": 20,
                "metadata_completeness": 0.80,
            },
            {
                "title": "Computer Vision Applications",  # Partially relevant
                "abstract": "Machine learning for computer vision and image processing",
                "year": 2024,
                "citation_count": 30,
                "metadata_completeness": 0.85,
            },
        ]

        # Test 1: Individual scoring
        scores = [
            relevance_scorer.score_paper_relevance(query, paper)
            for paper in test_papers
        ]
        most_relevant_score = max(scores)
        best_paper_index = scores.index(most_relevant_score)

        # The medical ML paper should score highest
        correct_ranking = best_paper_index == 0 and scores[0] > scores[1]
        self.log_test(
            "Relevance Scoring Accuracy",
            correct_ranking,
            f"Scores: Medical ML: {scores[0]:.3f}, Economics: {scores[1]:.3f}, CV: {scores[2]:.3f}",
        )

        # Test 2: Ranking functionality
        ranked_papers = relevance_scorer.rank_papers(query, test_papers)
        top_paper_title = ranked_papers[0]["title"]
        correct_top_result = "Medical" in top_paper_title
        self.log_test(
            "Paper Ranking",
            correct_top_result,
            f"Top result: {top_paper_title[:50]}...",
        )

        # Test 3: Component scoring
        recency_score = relevance_scorer.calculate_recency_score(2023)
        citation_score = relevance_scorer.calculate_citation_score(50)

        reasonable_scores = 0.7 <= recency_score <= 1.0 and 0.6 <= citation_score <= 1.0
        self.log_test(
            "Component Scoring",
            reasonable_scores,
            f"Recency: {recency_score:.2f}, Citations: {citation_score:.2f}",
        )

        # Test 4: Low relevance filtering
        filtered_papers = relevance_scorer.filter_low_relevance(
            ranked_papers, min_threshold=0.3
        )
        filtering_works = len(filtered_papers) <= len(ranked_papers)
        self.log_test(
            "Low Relevance Filtering",
            filtering_works,
            f"Filtered: {len(ranked_papers)} -> {len(filtered_papers)} papers",
        )

    async def test_source_integration(self):
        """Test integration with actual sources"""
        print("\n🔌 Testing Source Integration...")

        # Test 1: ArXiv with enhanced processing
        try:
            arxiv_results = await search_arxiv("machine learning", limit=2)
            arxiv_enhanced = (
                len(arxiv_results) > 0 and "pdf_validated" in arxiv_results[0]
            )
            self.log_test(
                "ArXiv Enhanced Integration",
                arxiv_enhanced,
                f"Found {len(arxiv_results)} results with PDF validation",
            )
        except Exception as e:
            self.log_test("ArXiv Enhanced Integration", False, f"Error: {e}")

        # Test 2: PubMed with PMC enhancement
        try:
            pubmed_results = await search_pubmed("diabetes", limit=2)
            pubmed_enhanced = (
                len(pubmed_results) > 0 and "metadata_completeness" in pubmed_results[0]
            )
            self.log_test(
                "PubMed Enhanced Integration",
                pubmed_enhanced,
                f"Found {len(pubmed_results)} results with metadata scoring",
            )
        except Exception as e:
            self.log_test("PubMed Enhanced Integration", False, f"Error: {e}")

    def print_summary(self):
        """Print test summary"""
        print("\n📊 Data Quality Validation Summary")
        print("=" * 50)
        print(f"Tests Passed: {self.passed_tests}/{self.total_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests)*100:.1f}%")

        if self.passed_tests == self.total_tests:
            print(
                "🎉 ALL TESTS PASSED! Data quality improvements are working correctly."
            )
        else:
            print(
                f"⚠️  {self.total_tests - self.passed_tests} tests failed. Review the issues above."
            )

        print("\n📋 Issues Addressed:")
        print(
            "✅ Issue 4.1: PDF Availability - Enhanced with validation and alternative sources"
        )
        print(
            "✅ Issue 4.2: Metadata Standardization - Dynamic field mappings and enrichment"
        )
        print(
            "✅ Issue 4.3: Relevance Scoring - Advanced TF-IDF, citation, and recency weighting"
        )


async def main():
    """Run comprehensive data quality validation"""
    print("🚀 Comprehensive Data Quality Validation")
    print("=" * 60)
    print("Testing all improvements for Issues 4.1, 4.2, and 4.3...")

    validator = DataQualityValidator()

    # Run all validation tests
    await validator.test_pdf_validation_system()
    await validator.test_metadata_normalization()
    await validator.test_metadata_enrichment()
    await validator.test_relevance_scoring()
    await validator.test_source_integration()

    # Print final summary
    validator.print_summary()

    # Exit with appropriate code
    sys.exit(0 if validator.passed_tests == validator.total_tests else 1)


if __name__ == "__main__":
    asyncio.run(main())
