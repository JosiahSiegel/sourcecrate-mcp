"""
Unit tests for fuzzy paper matching functionality.
Tests paper deduplication, similarity scoring, and metadata merging.
"""

from source_crate.utils.fuzzy_matching import FuzzyPaperMatcher, MatchScore


class TestFuzzyPaperMatcher:
    """Test suite for FuzzyPaperMatcher class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = FuzzyPaperMatcher()

    def test_normalize_title(self):
        """Test title normalization functionality."""
        # Test basic normalization
        title = "The Machine Learning: A Comprehensive Analysis"
        expected = "machine learning comprehensive analysis"
        assert self.matcher.normalize_title(title) == expected

        # Test punctuation removal
        title = "Deep Learning, Neural Networks & AI: Review!"
        expected = "deep learning neural networks ai review"
        assert self.matcher.normalize_title(title) == expected

        # Test empty title
        assert self.matcher.normalize_title("") == ""

    def test_normalize_author_name(self):
        """Test author name normalization."""
        # Test basic name
        author = "Dr. John Smith Jr."
        expected = "john smith"
        assert self.matcher.normalize_author_name(author) == expected

        # Test with titles
        author = "Prof. Mary Johnson PhD"
        expected = "mary johnson"
        assert self.matcher.normalize_author_name(author) == expected

        # Test empty name
        assert self.matcher.normalize_author_name("") == ""

    def test_extract_author_list(self):
        """Test author list extraction from various formats."""
        # Test string format
        authors = "John Smith, Jane Doe and Bob Wilson"
        expected = ["john smith", "jane doe", "bob wilson"]
        assert self.matcher.extract_author_list(authors) == expected

        # Test list of dicts format
        authors = [
            {"name": "John Smith"},
            {"full_name": "Jane Doe"},
            {"name": "Bob Wilson"},
        ]
        expected = ["john smith", "jane doe", "bob wilson"]
        assert self.matcher.extract_author_list(authors) == expected

        # Test list of strings
        authors = ["John Smith", "Jane Doe", "Bob Wilson"]
        expected = ["john smith", "jane doe", "bob wilson"]
        assert self.matcher.extract_author_list(authors) == expected

        # Test empty list
        assert self.matcher.extract_author_list([]) == []

    def test_calculate_title_similarity(self):
        """Test title similarity calculation."""
        # Test identical titles
        title1 = "Machine Learning in Healthcare"
        title2 = "Machine Learning in Healthcare"
        similarity = self.matcher.calculate_title_similarity(title1, title2)
        assert similarity == 1.0

        # Test similar titles
        title1 = "Deep Learning for Image Recognition"
        title2 = "Deep Learning for Computer Vision"
        similarity = self.matcher.calculate_title_similarity(title1, title2)
        assert 0.5 < similarity < 1.0

        # Test completely different titles
        title1 = "Machine Learning Applications"
        title2 = "Quantum Physics Fundamentals"
        similarity = self.matcher.calculate_title_similarity(title1, title2)
        assert similarity < 0.5

        # Test empty titles
        similarity = self.matcher.calculate_title_similarity("", "")
        assert similarity == 0.0

    def test_calculate_author_similarity(self):
        """Test author list similarity calculation."""
        # Test identical authors
        authors1 = ["John Smith", "Jane Doe"]
        authors2 = ["John Smith", "Jane Doe"]
        similarity = self.matcher.calculate_author_similarity(authors1, authors2)
        assert similarity == 1.0

        # Test partial overlap
        authors1 = ["John Smith", "Jane Doe", "Bob Wilson"]
        authors2 = ["John Smith", "Alice Brown"]
        similarity = self.matcher.calculate_author_similarity(authors1, authors2)
        assert 0.2 < similarity < 0.8  # 1 common author out of 4 unique

        # Test no overlap
        authors1 = ["John Smith", "Jane Doe"]
        authors2 = ["Alice Brown", "Bob Wilson"]
        similarity = self.matcher.calculate_author_similarity(authors1, authors2)
        assert similarity == 0.0

        # Test empty lists
        similarity = self.matcher.calculate_author_similarity([], [])
        assert similarity == 0.0

    def test_calculate_year_similarity(self):
        """Test publication year similarity calculation."""
        # Test identical years
        similarity = self.matcher.calculate_year_similarity(2023, 2023)
        assert similarity == 1.0

        # Test close years (1 year difference)
        similarity = self.matcher.calculate_year_similarity(2023, 2024)
        assert similarity == 0.8

        # Test 2 year difference
        similarity = self.matcher.calculate_year_similarity(2023, 2025)
        assert similarity == 0.6

        # Test distant years
        similarity = self.matcher.calculate_year_similarity(2023, 2020)
        assert similarity == 0.0

        # Test missing years
        similarity = self.matcher.calculate_year_similarity(None, 2023)
        assert similarity == 0.5

    def test_calculate_doi_similarity(self):
        """Test DOI similarity calculation."""
        # Test identical DOIs
        doi1 = "10.1234/example.doi"
        doi2 = "10.1234/example.doi"
        similarity = self.matcher.calculate_doi_similarity(doi1, doi2)
        assert similarity == 1.0

        # Test DOIs with different formats
        doi1 = "https://doi.org/10.1234/example.doi"
        doi2 = "10.1234/example.doi"
        similarity = self.matcher.calculate_doi_similarity(doi1, doi2)
        assert similarity == 1.0

        # Test different DOIs
        doi1 = "10.1234/example.doi1"
        doi2 = "10.1234/example.doi2"
        similarity = self.matcher.calculate_doi_similarity(doi1, doi2)
        assert similarity == 0.0

        # Test empty DOIs
        similarity = self.matcher.calculate_doi_similarity("", "")
        assert similarity == 0.0

    def test_calculate_match_score(self):
        """Test comprehensive match score calculation."""
        # Test identical papers
        paper1 = {
            "title": "Machine Learning in Healthcare",
            "authors": ["John Smith", "Jane Doe"],
            "year": 2023,
            "doi": "10.1234/example.doi",
        }
        paper2 = {
            "title": "Machine Learning in Healthcare",
            "authors": ["John Smith", "Jane Doe"],
            "year": 2023,
            "doi": "10.1234/example.doi",
        }

        score = self.matcher.calculate_match_score(paper1, paper2)
        assert isinstance(score, MatchScore)
        assert score.overall_score == 1.0
        assert score.confidence == "high"

        # Matching DOI remains authoritative when sources use different titles.
        paper2["title"] = "Machine Learning for Healthcare Applications"
        score = self.matcher.calculate_match_score(paper1, paper2)
        assert score.overall_score == 1.0
        assert score.confidence in ["high", "medium"]

        # Test different papers
        paper2 = {
            "title": "Quantum Computing Fundamentals",
            "authors": ["Alice Brown", "Bob Wilson"],
            "year": 2020,
            "doi": "10.5678/different.doi",
        }
        score = self.matcher.calculate_match_score(paper1, paper2)
        assert score.overall_score < 0.5
        assert score.confidence == "low"

    def test_find_duplicates(self):
        """Test duplicate detection in paper lists."""
        papers = [
            {
                "title": "Machine Learning in Healthcare",
                "authors": ["John Smith", "Jane Doe"],
                "year": 2023,
            },
            {
                "title": "Machine Learning for Healthcare",  # Similar title
                "authors": ["John Smith", "Jane Doe"],
                "year": 2023,
            },
            {
                "title": "Quantum Computing Basics",
                "authors": ["Alice Brown"],
                "year": 2022,
            },
        ]

        duplicates = self.matcher.find_duplicates(papers)

        # Should find the first two papers as duplicates
        assert len(duplicates) == 1
        assert len(duplicates[0]) == 2
        assert 0 in duplicates[0] and 1 in duplicates[0]

    def test_merge_duplicate_papers(self):
        """Test merging of duplicate papers."""
        papers = [
            {
                "title": "Machine Learning in Healthcare",
                "authors": ["John Smith"],
                "abstract": "Short abstract",
                "source": "arxiv",
            },
            {
                "title": "Machine Learning for Healthcare Applications",  # Longer title
                "authors": ["John Smith", "Jane Doe"],  # More authors
                "abstract": "This is a much longer and more detailed abstract with more information",
                "source": "pubmed",
                "doi": "10.1234/example.doi",
            },
        ]

        merged = self.matcher.merge_duplicate_papers(papers)

        # Should use the longer title
        assert "Applications" in merged["title"]

        # Should merge authors
        assert len(merged["authors"]) == 2
        assert "John Smith" in [str(author) for author in merged["authors"]]
        assert "Jane Doe" in [str(author) for author in merged["authors"]]

        # Should use the longer abstract
        assert len(merged["abstract"]) > 50

        # Should include DOI
        assert merged["doi"] == "10.1234/example.doi"

        # Should track merged sources
        assert merged["_merged_sources"] == ["arxiv", "pubmed"]
        assert merged["_merged_count"] == 2

    def test_deduplicate_papers(self):
        """Test full deduplication process."""
        papers = [
            {
                "title": "Machine Learning in Healthcare",
                "authors": ["John Smith"],
                "source": "arxiv",
            },
            {
                "title": "Machine Learning for Healthcare",  # Duplicate
                "authors": ["John Smith"],
                "source": "pubmed",
            },
            {
                "title": "Quantum Computing Basics",
                "authors": ["Alice Brown"],
                "source": "arxiv",
            },
            {
                "title": "Deep Learning Applications",
                "authors": ["Bob Wilson"],
                "source": "crossref",
            },
        ]

        deduplicated = self.matcher.deduplicate_papers(papers)

        # Should reduce from 4 to 3 papers (2 duplicates merged)
        assert len(deduplicated) == 3

        # Should have one merged paper with both sources
        merged_papers = [p for p in deduplicated if "_merged_sources" in p]
        assert len(merged_papers) == 1
        assert "arxiv" in merged_papers[0]["_merged_sources"]
        assert "pubmed" in merged_papers[0]["_merged_sources"]

    def test_empty_inputs(self):
        """Test handling of empty inputs."""
        # Empty paper list
        assert self.matcher.find_duplicates([]) == []
        assert self.matcher.deduplicate_papers([]) == []

        # Single paper
        papers = [{"title": "Single Paper", "authors": ["Author"]}]
        assert self.matcher.find_duplicates(papers) == []
        assert self.matcher.deduplicate_papers(papers) == papers

    def test_strict_mode(self):
        """Test strict mode functionality."""
        strict_matcher = FuzzyPaperMatcher(strict_mode=True)
        regular_matcher = FuzzyPaperMatcher(strict_mode=False)

        # Strict mode should have higher threshold
        assert strict_matcher.match_threshold > regular_matcher.match_threshold
