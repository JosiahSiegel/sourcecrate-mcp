# PaperezMCP Configuration Directory

This directory contains the category-organized configuration system for PaperezMCP. Each research domain has its own YAML file making it easy to see which areas need more sources.

## Research Category Files

### 🔬 **Scientific Research**
- **`scientific.yaml`** - STEM fields, preprints, general academic (4 sources)
  - ✅ Well covered: CrossRef, Semantic Scholar, arXiv, DOAJ
  - ⚠️ **GAPS**: IEEE Xplore, ACM, OpenAlex, physics/chemistry/math databases

### 🏥 **Medical & Biomedical**
- **`medical.yaml`** - Medical, clinical, life sciences (4 sources)
  - ✅ Well covered: PubMed, PMC, Europe PMC, ClinicalTrials
  - ⚠️ **GAPS**: Psychology, nursing, pharmacy, medical device research

### 💼 **Business & Economics**
- **`business.yaml`** - Business, finance, management (1 source, SSRN disabled)
  - 🚨 **CRITICAL**: Only 2 general sources (CrossRef, Semantic Scholar)
  - ⚠️ **MASSIVE GAPS**: RePEc, NBER, business school repos, finance databases

### 📚 **Historical & Archives**
- **`historical.yaml`** - Historical documents, government archives (2 sources)
  - ⚠️ **MAJOR GAPS**: Federal Register, National Archives, Library of Congress
  - Note: HathiTrust disabled (no keyword search API)

### 👥 **Social Sciences**
- **`social-sciences.yaml`** - Psychology, sociology, education (0 dedicated sources)
  - 🚨 **CRITICAL**: NO DEDICATED SOURCES AT ALL
  - ⚠️ **MASSIVE GAPS**: PsycINFO, SAGE, education databases, sociology sources

### 🎨 **Humanities**
- **`humanities.yaml`** - Literature, philosophy, arts (0 dedicated sources)
  - 🚨 **CRITICAL**: NO DEDICATED SOURCES AT ALL
  - ⚠️ **MASSIVE GAPS**: JSTOR, Project MUSE, MLA Bibliography, art databases

### ⚖️ **Legal Research**
- **`legal.yaml`** - Legal research, case law (0 dedicated sources)
  - 🚨 **CRITICAL**: NO DEDICATED SOURCES AT ALL
  - ⚠️ **MASSIVE GAPS**: HeinOnline, legal databases, court opinions

### 🏛️ **Government & Policy**
- **`government.yaml`** - Government documents, policy research (0 dedicated sources)
  - 🚨 **CRITICAL**: NO DEDICATED SOURCES AT ALL
  - ⚠️ **MAJOR GAPS**: Federal Register, GovInfo, think tanks, international orgs

### ⚙️ **Core Configuration**
- **`base.yaml`** - Core settings, routing, performance configuration

## Gap Analysis Summary

### ✅ **Well Covered**
- Scientific/STEM research (4 sources)
- Medical/biomedical research (4 sources)

### 🚨 **CRITICAL GAPS** (Zero dedicated sources)
- Social Sciences (psychology, education, sociology)
- Humanities (literature, philosophy, arts)
- Legal Research (case law, legal scholarship)
- Government/Policy (federal documents, think tanks)

### ⚠️ **MAJOR GAPS** (Under-resourced)
- Business/Economics (severely limited)
- Historical Research (limited working sources)

## Adding Sources to Categories

To add sources to any category, simply edit the appropriate YAML file:

```yaml
# Example: Adding a new source to medical.yaml
sources:
  new_medical_source:
    name: new_medical_source
    type: http_api
    enabled: true
    config:
      description: New medical database
      base_url: https://api.example.com
      # ... configuration

categories:
  medical:
    sources:
      - pubmed
      - pubmed_central
      - europe_pmc
      - clinicaltrials
      - new_medical_source  # Add to category
```

## Priority Implementation Order

1. **HIGH PRIORITY**: OpenAlex (covers multiple gaps)
2. **HIGH PRIORITY**: Social sciences sources (PsycINFO alternatives)
3. **HIGH PRIORITY**: Business sources (RePEc, NBER)
4. **MEDIUM PRIORITY**: Legal sources (open access legal databases)
5. **MEDIUM PRIORITY**: Government sources (Federal Register, GovInfo)
6. **MEDIUM PRIORITY**: Humanities sources (open access alternatives)

This organization makes it immediately clear which research domains need attention!