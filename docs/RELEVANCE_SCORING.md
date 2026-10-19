# Relevance Scoring Algorithm

This document details the multi-signal relevance scoring algorithm used in the SourceCrate browser UI to rank academic papers.

## Overview

The relevance scoring system uses a **research-based weighted combination** of multiple signals, drawing from best practices established by:
- **Google Scholar** (citations as dominant factor)
- **PubMed Best Match** (150+ signals, title weighting)
- **BM25 algorithm** (text relevance)
- **2025 hybrid retrieval systems** (8-12% accuracy improvement)

## Final Score Formula

```
Final Score = (
  Base Text Relevance × 40% +
  Citation Impact × 35% +
  Title Match × 15% +
  Recency Factor × 5% +
  Quality Signals × 5%
)
```

**Range**: 0.0 to 1.0 (displayed as 0-100%)

---

## Component Formulas

### 1. Base Text Relevance (40% weight)

**Source**: Backend BM25-based scoring from search API

**Formula**: `paper.relevance_score` (passed from backend)

**Default**: 0.5 if not provided

**Purpose**: Captures query-document text similarity using probabilistic information retrieval

---

### 2. Citation Impact (35% weight)

**Implementation**: `calculateCitationImpact(citations)`

**Formula**:
```javascript
if (citations <= 0) return 0;

citationImpact = log₁₀(citations + 1) / log₁₀(10000)
```

**Scaling Examples**:
| Citations | Impact Score | Percentage |
|-----------|--------------|------------|
| 0         | 0.00         | 0%         |
| 1         | 0.08         | 8%         |
| 10        | 0.25         | 25%        |
| 100       | 0.50         | 50%        |
| 1,000     | 0.75         | 75%        |
| 10,000    | 1.00         | 100%       |

**Rationale**:
- **Logarithmic scaling** handles extreme values better than linear
- Google Scholar research shows citations are the dominant ranking factor
- Prevents 10,000+ citation papers from dominating results
- Gives diminishing returns to additional citations (realistic impact assessment)

**Magic Number**: `10000` = maximum citation threshold for normalization

---

### 3. Title Match Boost (15% weight)

**Implementation**: `calculateTitleMatchBoost(title, query)`

**Formula**:
```javascript
normalizedTitle = title.toLowerCase().replace(/[^\w\s]/g, ' ')
normalizedQuery = query.toLowerCase().replace(/[^\w\s]/g, ' ')

queryTerms = normalizedQuery.split(/\s+/).filter(term => term.length > 2)

matchingTerms = queryTerms.filter(term =>
  normalizedTitle.includes(term)
).length

titleMatchScore = matchingTerms / queryTerms.length
```

**Examples**:
| Query | Title | Score |
|-------|-------|-------|
| "machine learning" | "Introduction to Machine Learning" | 1.0 (2/2 terms) |
| "neural networks deep" | "Deep Neural Networks for Vision" | 1.0 (3/3 terms) |
| "covid vaccine efficacy" | "COVID-19 Vaccine Study" | 0.67 (2/3 terms) |

**Rationale**:
- PubMed and Google Scholar weight title matches heavily
- Users often search for specific papers by title keywords
- Terms in title have higher semantic importance than in abstract

**Magic Number**: `2` = minimum term length to filter short words (of, in, the, etc.)

---

### 4. Recency Factor (5% weight)

**Implementation**: `calculateRecencyFactor(year)`

**Formula** (Exponential Decay):
```javascript
currentYear = new Date().getFullYear()
yearsOld = currentYear - year

if (yearsOld < 0) return 1.0  // Future papers (edge case)
if (!year) return 0.5          // Unknown year default

recencyScore = exp(-0.1386 × yearsOld)
```

**Decay Constant**: `0.1386 = ln(2) / 5`
- **Half-life**: 5 years
- Papers lose 50% of recency boost every 5 years

**Examples**:
| Publication Year | Years Old | Recency Score | Percentage |
|------------------|-----------|---------------|------------|
| 2025             | 0         | 1.00          | 100%       |
| 2024             | 1         | 0.87          | 87%        |
| 2020             | 5         | 0.50          | 50%        |
| 2015             | 10        | 0.25          | 25%        |
| 2010             | 15        | 0.13          | 13%        |
| 2005             | 20        | 0.06          | 6%         |

**Rationale**:
- Recent papers get slight boost for emerging research
- Exponential decay reflects realistic impact decline over time
- 5-year half-life balances novelty vs. established knowledge
- Older classics still rank well due to high citation impact (35% weight)

**Magic Numbers**:
- `0.1386` = decay constant for 5-year half-life
- `5` = years for half-life (tunable parameter)
- `0.5` = default score for unknown publication year

---

### 5. Quality Signals (5% weight)

**Implementation**: `calculateQualitySignals(paper)`

**Formula**:
```javascript
qualityScore = 0

// Multi-source bonus
mergedCount = paper._merged_count || 1
multiSourceBonus = min(0.1 × mergedCount, 0.5)
qualityScore += multiSourceBonus

// Open access bonus
if (paper.is_open_access) {
  qualityScore += 0.5
}

return min(1.0, qualityScore)
```

**Components**:

#### Multi-Source Bonus:
- Each source adds 0.1 to quality score
- **Capped at 0.5** (5 or more sources)
- Papers from multiple databases indicate higher reliability

**Examples**:
| Sources | Bonus | Notes |
|---------|-------|-------|
| 1       | 0.1   | Single source |
| 2       | 0.2   | Verified by 2 databases |
| 3       | 0.3   | Strong verification |
| 5+      | 0.5   | Maximum (capped) |

#### Open Access Bonus:
- **+0.5** for open access papers
- Promotes accessibility and reproducibility

**Total Quality Examples**:
| Scenario | Calculation | Score |
|----------|-------------|-------|
| 1 source, paywalled | 0.1 + 0.0 | 0.1 |
| 1 source, open access | 0.1 + 0.5 | 0.6 |
| 3 sources, paywalled | 0.3 + 0.0 | 0.3 |
| 5 sources, open access | 0.5 + 0.5 | 1.0 |

**Magic Numbers**:
- `0.1` = bonus per additional source
- `0.5` = maximum multi-source bonus (5 sources)
- `0.5` = open access bonus
- `1.0` = maximum total quality score (capped)

---

## Complete Scoring Example

### Paper A: Recent High-Impact Open Access
- **Query**: "transformer neural networks"
- **Title**: "Attention Is All You Need: Transformers"
- **Citations**: 50,000
- **Year**: 2024
- **Sources**: 4 (arXiv, Semantic Scholar, CrossRef, Google Scholar)
- **Open Access**: Yes
- **Base Relevance**: 0.85 (high text match from backend)

**Calculation**:
```
Citation Impact = log₁₀(50001) / log₁₀(10000) = 1.17 → 1.0 (capped)
  → 1.0 × 0.35 = 0.35

Title Match = 3/3 terms matched = 1.0
  → 1.0 × 0.15 = 0.15

Recency = exp(-0.1386 × 1) = 0.87
  → 0.87 × 0.05 = 0.04

Quality = min((0.1 × 4) + 0.5, 1.0) = 0.9
  → 0.9 × 0.05 = 0.045

Base = 0.85 × 0.40 = 0.34

Final Score = 0.35 + 0.15 + 0.04 + 0.045 + 0.34 = 0.925 (93%)
```

### Paper B: Classic Highly-Cited
- **Query**: "machine learning algorithms"
- **Title**: "Statistical Learning Theory"
- **Citations**: 8,500
- **Year**: 1998
- **Sources**: 2 (CrossRef, Google Scholar)
- **Open Access**: No
- **Base Relevance**: 0.70

**Calculation**:
```
Citation Impact = log₁₀(8501) / log₁₀(10000) = 0.96
  → 0.96 × 0.35 = 0.34

Title Match = 1/3 terms ("learning")
  → 0.33 × 0.15 = 0.05

Recency = exp(-0.1386 × 27) = 0.03
  → 0.03 × 0.05 = 0.002

Quality = (0.1 × 2) + 0.0 = 0.2
  → 0.2 × 0.05 = 0.01

Base = 0.70 × 0.40 = 0.28

Final Score = 0.34 + 0.05 + 0.002 + 0.01 + 0.28 = 0.682 (68%)
```

**Comparison**: Paper A ranks higher due to title match, recency, and open access, despite Paper B having more citations.

---

## Relevance Threshold

### Default: 35% (Permanent)

**Magic Number**: `35` = minimum relevance percentage

**Behavior**:
- Papers below 35% relevance are filtered out
- **Automatic fallback**: If no papers meet 35%, threshold drops to 0% for that search only
- Resets to 35% on next search

**Implementation**:
```javascript
let relevanceThreshold = 35; // Permanent default

// In renderStreamingResults():
if (filteredResults.length === 0 && relevanceThreshold === 35) {
  console.log('No results at 35% relevance, falling back to 0%');
  relevanceThreshold = 0;
  filteredResults = applyFilters(streamingResults);
}
```

**Rationale**:
- 35% balances quality vs. quantity
- Lower than 45% to be more inclusive
- Automatic fallback prevents "no results" scenarios
- User cannot manually adjust (simplifies UX)

---

## Weight Rationale

### Why These Weights?

| Component | Weight | Justification |
|-----------|--------|---------------|
| Base Text Relevance | 40% | Primary signal from backend BM25; proven algorithm |
| Citation Impact | 35% | Google Scholar research: citations are dominant factor |
| Title Match | 15% | PubMed approach: title matches highly predictive |
| Recency | 5% | Small boost for recent work, doesn't override quality |
| Quality Signals | 5% | Bonus for verification, accessibility |

**Total**: 100%

**Research Support**:
- Google Scholar: Citation counts highest weighted factor (empirical study with 1.3M+ articles)
- PubMed Best Match: Uses 150+ signals with title match as key factor
- BM25: Text relevance foundational in information retrieval
- Hybrid systems: Combining signals achieves 8-12% better accuracy vs. single-signal

---

## Magic Numbers Summary

| Number | Purpose | Location | Rationale |
|--------|---------|----------|-----------|
| `0.40` | Base text weight | Final formula | BM25 primary signal |
| `0.35` | Citation weight | Final formula | Google Scholar dominant factor |
| `0.15` | Title match weight | Final formula | PubMed high predictive value |
| `0.05` | Recency weight | Final formula | Small boost for novelty |
| `0.05` | Quality weight | Final formula | Bonus for verification |
| `10000` | Citation normalization | Citation impact | Maximum realistic citations |
| `0.1386` | Decay constant | Recency factor | ln(2)/5 for 5-year half-life |
| `5` | Half-life years | Recency factor | Balance novelty vs. classics |
| `0.5` | Unknown year default | Recency factor | Neutral score |
| `2` | Min term length | Title match | Filter short words |
| `0.1` | Per-source bonus | Quality signals | Each additional source |
| `0.5` | Max multi-source | Quality signals | Cap at 5 sources |
| `0.5` | Open access bonus | Quality signals | Accessibility boost |
| `35` | Min relevance % | Threshold | Balance quality/quantity |

---

## Performance Characteristics

### Computational Complexity
- **Per paper**: O(1) - constant time scoring
- **Title matching**: O(n × m) where n = query terms, m = title words
- **Overall**: O(N) for N papers - linear scaling

### Expected Improvements vs. Simple Citation Boost
- **Better ranking of classics**: Logarithmic prevents extreme domination
- **Boosts recent breakthroughs**: Recency decay rewards novelty
- **Prioritizes exact matches**: Title matching surfaces target papers
- **Rewards comprehensive coverage**: Multi-source bonus indicates quality
- **Promotes open science**: Open access bonus encourages accessibility

---

## References

### Academic Research
1. **Google Scholar Ranking**: "Google Scholar's Ranking Algorithm: The Impact of Citation Counts (An Empirical Study)" - IEEE Conference Publication
2. **PubMed Best Match**: "Best Match: New relevance search for PubMed" - PMC
3. **BM25 Algorithm**: "Practical BM25 - Part 2: The BM25 Algorithm and its Variables" - Elastic Blog
4. **Hybrid Retrieval 2025**: "A hybrid retrieval system combining BM25 with semantic similarity" - Universidad de los Andes

### Implementation
- File: `js/processing-poc.js` in the neighboring `sourcecrate` repository
- Functions:
  - `calculateCitationImpact()` (lines 465-471)
  - `calculateTitleMatchBoost()` (lines 480-498)
  - `calculateRecencyFactor()` (lines 507-519)
  - `calculateQualitySignals()` (lines 527-543)
  - `calculateOptimalRelevance()` (lines 556-585)

---

## Future Tuning Considerations

### Adjustable Parameters
If relevance quality needs tuning, consider adjusting:

1. **Weights** (must sum to 1.0):
   - Increase citation weight for citation-focused domains
   - Increase title weight for known-item searches
   - Increase recency for fast-moving fields (AI, COVID research)

2. **Magic Numbers**:
   - Citation threshold (currently 10,000) - adjust for field norms
   - Half-life years (currently 5) - reduce for fast-moving fields
   - Relevance threshold (currently 35%) - balance quality vs. quantity

3. **Fallback Behavior**:
   - Currently automatic 35% → 0%
   - Could implement stepped reduction (35% → 25% → 15% → 0%)

### A/B Testing Recommendations
- Track click-through rate on top results
- Measure user dwell time per paper
- Compare relevance scores to user bookmarks/downloads
- Gather feedback on result quality vs. quantity
