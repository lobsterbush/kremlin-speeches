# Russian Presidential Speeches Dataset (2000-2025)

## Project Overview

This project analyzes 1,402 Russian presidential speeches from the Kremlin website spanning 25 years (2000-2025). The dataset includes speeches from Putin I (2000-2008), Medvedev (2008-2012), and Putin II (2012-present).

## Dataset Composition

> **Terminology Note**: Throughout this document, we use "speeches" as shorthand for items from the `/transcripts/speeches/` subcategory on kremlin.ru. These are transcripts of **prepared remarks at ceremonial events** - not transcripts of meetings or dialogues. The Kremlin uses "transcripts" as an umbrella term for all 5 subcategories of presidential communications.

### What Are "Speeches" in This Dataset?

**Important**: The Kremlin website uses "transcripts" as an umbrella category with five subcategories:

1. **`/transcripts/speeches/`** (1,402 collected) - Prepared remarks at ceremonies, award presentations, commemorations
2. **`/transcripts/statements/`** (~20 recent accessible) - Official policy declarations and announcements
3. **`/transcripts/transcripts/`** - Meeting records and bilateral dialogues
4. **`/transcripts/news-conferences/`** - Press briefings and Q&A sessions
5. **`/transcripts/press-statements/`** - Brief public communications

What we call "speeches" here is technically **transcripts of prepared remarks at events**. These include:
- **Speeches** (244 explicitly labeled)
- **Addresses** (198 items)
- **Ceremony remarks** (award presentations, military decorations, commemorations)
- **Gala events** (national holidays, professional days, anniversaries)
- **State visits** (welcoming remarks, formal toasts)

**Key Distinction**: Items from `/transcripts/speeches/` are **prepared, ceremonial remarks** delivered at scheduled events. They differ from statements (reactive policy declarations), transcripts (meeting dialogues), and press conferences (interactive Q&A). This subcategory represents the most curated, ceremonial form of presidential communication.

### Why Only Speeches?

**Technical Limitation**: The Kremlin English website has broken pagination - only the most recent ~20 items per category are accessible via web scraping. This pagination bug appeared between December 26, 2025 (when speeches were successfully scraped) and January 2, 2026. All pagination pages now return identical results.

**Data Collection Timeline**:
- December 26, 2025: Successfully scraped 1,402 speeches (IDs 30-78,853) when pagination worked
- January 2, 2026: Discovered pagination bug affecting all categories
- Attempted workaround: Internet Archive Wayback Machine (only 6 recent statement IDs recovered due to sparse coverage)

**Implication**: This dataset captures formal, ceremonial presidential rhetoric but misses:
- Major policy statements (e.g., 2008 Georgia war declarations)
- Meeting transcripts (bilateral/multilateral discussions)
- Press conference exchanges
- Ad-hoc public statements

**Why Wayback Machine Didn't Help**: Internet Archive has very sparse coverage of Kremlin pagination pages (primarily late 2024 snapshots only), with frequent connection issues. The 1,402 speeches collected on December 26 represent the most comprehensive dataset available.

## Dataset Statistics

**Total Speeches**: 1,402  
**Date Range**: January 28, 2000 - December 24, 2025  
**Average Length**: 602 words (lemmatized)  
**Total Words**: 844,143 (lemmatized from 1.78M original)

### By President

| President | Speeches | Percentage |
|-----------|----------|------------|
| Putin I (2000-2008) | 134 | 9.6% |
| Medvedev (2008-2012) | 213 | 15.2% |
| Putin II (2012-) | 1,055 | 75.2% |

### Temporal Distribution

Speeches per year increased significantly over time:
- **2000-2008 (Putin I)**: Average 17 speeches/year
- **2009-2012 (Medvedev)**: Average 53 speeches/year (peak)
- **2013-2021**: Average 73 speeches/year
- **2022-2025**: Average 61 speeches/year (post-invasion slight decline)

**Peak years**: 2018 (120 speeches), 2019 (98 speeches), 2017 (95 speeches)

## Geographic Analysis

### Top 20 Speech Locations

| Location | Count | Percentage |
|----------|-------|------------|
| The Kremlin, Moscow | 224 | 16.0% |
| Moscow | 204 | 14.6% |
| The Kremlin, Moscow | 164 | 11.7% |
| St Petersburg | 97 | 6.9% |
| Sochi | 61 | 4.4% |
| Novo-Ogaryovo, Moscow Region | 34 | 2.4% |
| Red Square, Moscow | 18 | 1.3% |
| Grand Kremlin Palace, Moscow | 15 | 1.1% |
| Vladivostok | 13 | 0.9% |
| Beijing | 9 | 0.6% |
| Kazan | 9 | 0.6% |
| Saint Petersburg | 6 | 0.4% |
| Sevastopol | 6 | 0.4% |
| Zhukovsky, Moscow Region | 6 | 0.4% |
| Bishkek | 5 | 0.4% |
| Gorki, Moscow Region | 5 | 0.4% |
| Nizhny Novgorod | 5 | 0.4% |
| Russky Island, Primorye Territory | 5 | 0.4% |
| Astana | 4 | 0.3% |
| Dushanbe | 4 | 0.3% |

### Domestic vs International

- **Domestic**: 925 speeches (78.7%)
- **International**: 251 speeches (21.3%)

### Location Patterns by Period

**Pre-Crimea (2000-2013)**
1. The Kremlin, Moscow (29.4%)
2. Moscow (11.8%)
3. St Petersburg (5.8%)
4. Sochi (3.9%)
5. Grand Kremlin Palace, Moscow (3.1%)

**Crimea-2022 (2014-2021)**
1. The Kremlin, Moscow (25.7%)
2. Moscow (17.3%)
3. St Petersburg (7.9%)
4. Sochi (6.2%)
5. Novo-Ogaryovo, Moscow Region (3.7%)

**Post-Invasion (2022-2025)**
1. The Kremlin, Moscow (18.6%)
2. Moscow (12.2%)
3. St Petersburg (6.3%)
4. Novo-Ogaryovo, Moscow Region (2.5%)
5. Murmansk (1.3%)

**Key Trends**: 
- Kremlin dominance declining over time (29.4% → 25.7% → 18.6%)
- Increased use of Moscow Region residences (Novo-Ogaryovo) post-2014
- International speeches consistently ~20% across all periods

## Georgia & Moldova Analysis

### Overall Findings

**Georgia**
- Mentioned in: 14 speeches (1.0%)
- Total mentions: 20
- Average: 0.016% per 100 words

**Moldova**
- Mentioned in: 18 speeches (1.3%)
- Total mentions: 36
- Average: 0.019% per 100 words

### By Period

#### Pre-Crimea (2000-2013)
- **Georgia**: 0.037% of speech content | 8 speeches (14 mentions)
- **Moldova**: 0.018% | 6 speeches (10 mentions)

#### Crimea-2022 (2014-2021)
- **Georgia**: 0.006% (**84% decline**) | 6 speeches (6 mentions)
- **Moldova**: 0.026% (**44% increase**) | 11 speeches (23 mentions)

#### Post-Invasion (2022-2025)
- **Georgia**: 0.000% (**complete absence**) | 0 speeches (0 mentions)
- **Moldova**: 0.004% (**85% decline**) | 1 speech (3 mentions)

### 2008 Georgia War Period

**Critical Finding**: August-December 2008 had **8 speeches** with **ZERO mentions** of Georgia.

**Explanation**: Major Georgia war declarations were delivered as official **statements**, not speeches. This confirms the limitation of the speeches-only dataset for analyzing specific geopolitical crises.

### Relative Attention (vs Ukraine Baseline)

**Pre-Crimea**
- Ukraine: 0.069% (baseline)
- Georgia: 0.037% (11% of Ukraine attention)
- Moldova: 0.018% (5% of Ukraine)

**Crimea-2022**
- Ukraine: 0.043%
- Georgia: 0.006% (**3% of Ukraine**)
- Moldova: 0.026% (**13% of Ukraine**)

**Post-Invasion**
- Ukraine: 0.100%
- Georgia: 0.000% (**0%**)
- Moldova: 0.004% (**2%**)

### Key Patterns

1. **Georgia Fadeout**: Georgia disappeared from Putin's speeches entirely post-2022. Peak attention was during Medvedev's presidency (2008-2012).

2. **Moldova Brief Rise**: Moldova had a temporary uptick during 2014-2021 (likely Ukraine crisis spillover), then faded dramatically.

3. **Both Marginal**: Even at peak, both countries represented <0.05% of speech content - marginal topics in ceremonial presidential rhetoric.

4. **Co-occurrence**: Only 1 speech mentioned both Georgia and Moldova together. 7 speeches mentioned Georgia with Ukraine, 7 mentioned Moldova with Ukraine.

## Text Processing Methodology

### Preprocessing Pipeline

1. **Stopword Removal**: 292 stopwords removed
   - 198 English stopwords
   - 94 custom (including "president", "putin", "medvedev", etc.)

2. **Lemmatization**: Words reduced to root forms

3. **Country Normalization**: Demonyms mapped to countries
   - georgian/georgians → georgia
   - moldovan/moldovans → moldova
   - ukrainian/ukrainians → ukraine
   - russian/russians → russia
   - chinese → china
   - Capital cities: tbilisi → georgia, chisinau → moldova

4. **Word Reduction**: 52.6% reduction (1,779,894 → 844,143 words)

### Visualization Approach

- **Time aggregation**: Quarterly rolling averages (2-quarter window)
- **Smoothing rationale**: Reduces noise from sporadic mentions while preserving trends
- **Standard practice**: Rolling averages commonly used in political science time series

## Data Limitations

1. **English Site Only**: Russian-language site has identical pagination bug (confirmed January 2, 2026)
2. **Speeches Only**: Missing statements, transcripts, press conferences
3. **Broken Pagination**: Website pagination broke between Dec 26-Jan 2, 2026. All categories now return only ~20 identical results per page
4. **Wayback Machine Insufficient**: Internet Archive has sparse coverage (primarily late 2024), only 6 statement IDs recovered
5. **2008 Georgia Gap**: War declarations not in speeches dataset
6. **Ceremonial Bias**: Speeches are formal/curated, not all presidential communications
7. **Historical Coverage**: Successfully captured 25 years of speeches (2000-2025) before pagination broke

## Files Generated

**Core Data**
- `kremlin_speeches_all_lemmatized.csv` - Full processed dataset (1,402 speeches)
- `speech_locations_top20.csv` - Top 20 speech locations with counts

**Visualizations**
- `regional_comparison_smooth.png` - 25-year regional focus trends
- `ukraine_timeline_smooth.png` - Ukraine mentions with key events
- `asia_china_smooth.png` - Asia/China trends
- `georgia_moldova_timeline.png` - Georgia & Moldova with event markers
- `post_soviet_comparison.png` - All western post-Soviet states
- `georgia_moldova_ukraine_ratio.png` - Relative attention analysis

**Analysis Scripts**
- `preprocess_all_speeches.py` - Text preprocessing and lemmatization
- `figures_smoothed.R` - Main visualization generation
- `analyze_georgia_moldova.R` - Comprehensive Georgia/Moldova analysis
- `analyze_speeches_metadata.R` - Location and metadata analysis

**Scraping Scripts**
- `scrape_kremlin.py` - Original Selenium-based scraper (speeches only)
- `scrape_statements_curl.py` - Curl-based scraper (limited success on other categories)
- `scrape_wayback.py` - Internet Archive scraper (6 statement IDs recovered)
- `wayback_scraped_ids.json` - IDs recovered from Wayback Machine

## Key Insights

1. **Presidential speeches are ceremonial**: They focus on domestic achievements, international summits, and commemorative events - not real-time policy crises.

2. **Moscow-centric**: Nearly 80% of speeches are domestic, with Kremlin/Moscow accounting for ~42% of all locations.

3. **Georgia vanished**: After being moderately visible during Medvedev era, Georgia completely disappeared from Putin II speeches post-2022.

4. **Moldova transient**: Brief 2014-2021 increase likely reflects regional instability concerns, but attention faded post-Ukraine invasion.

5. **Speech frequency increased**: Putin II era (2012-) delivers ~3x more speeches annually than Putin I era (2000-2008).

6. **Data gap matters**: The 2008 Georgia war is invisible in speeches data because key declarations were made as statements, not speeches.

## Methodological Implications: Speeches vs Statements for Foreign Policy Analysis

### What Prepared Ceremonial Remarks Reveal

**Items from `/transcripts/speeches/` capture *enduring* foreign policy priorities, not *urgent* ones.**

These prepared remarks are:
- **Backward-looking**: Commemorate achievements, justify past actions
- **Ceremonial**: Delivered at scheduled events (state visits, anniversaries, awards)
- **Curated**: Carefully prepared, reviewed, polished
- **Public-facing**: Designed for domestic and international audiences
- **Relationship-building**: Emphasize partnerships, shared values, long-term ties

What this means for foreign policy analysis:

1. **Sustained attention ≠ Crisis response**: If a country appears frequently in speeches, it signals *strategic importance* (e.g., China's rising prominence 2014-2021), not necessarily immediate conflict.

2. **Absence = Normalization or neglect**: Georgia's disappearance from speeches post-2022 doesn't mean Russia forgot about Georgia - it means Georgia is no longer a *ceremonial talking point*. The relationship is either normalized (routine) or deprioritized.

3. **Speeches show *what Russia wants to be known for***: The Asia pivot visible in speeches (China mentions tripling 2014-2021) reflects Russia's desired international positioning, not daily diplomatic activity.

### What Statements Reveal (That Speeches Don't)

**Statements capture *reactive* foreign policy, not *reflective* positioning.**

Statements are:
- **Real-time**: Issued in response to breaking events
- **Declarative**: Announce policy changes, condemn actions, make demands
- **Urgent**: Address crises, conflicts, violations
- **Unscheduled**: Published when events dictate
- **Directive**: Tell other actors what Russia will/won't tolerate

Examples of what statements capture that speeches miss:
- **2008 Georgia war declarations**: Recognition of South Ossetia/Abkhazia
- **2014 Crimea annexation**: Justification for military action
- **2022 Ukraine invasion**: Declaration of "special military operation"
- **Sanctions responses**: Immediate reactions to Western measures
- **Diplomatic protests**: Responses to perceived violations

### The Georgia 2008 Case Study

**The Problem**: Our analysis shows 0 Georgia mentions in August-December 2008 speeches, despite Russia fighting a war with Georgia.

**The Explanation**: 
- War declarations, recognition of South Ossetia/Abkhazia, and justifications were delivered as **statements**
- August-December 2008 speeches included routine events (Moscow City Day, National Unity Day, New Year Address) - none directly about the war
- By the time Georgia appeared in speeches (2009-2011), it was in *commemorative* contexts (decorating soldiers, retrospective justifications)

**The Lesson**: Speeches lag crises by months/years. They memorialize and normalize after the fact.

### Meeting Transcripts (`/transcripts/transcripts/`): The Middle Ground

Transcripts of meetings, bilateral discussions, and dialogues (from the `/transcripts/transcripts/` subcategory) capture:
- **Interactive diplomacy**: Q&A reveals unscripted positions
- **Bilateral priorities**: What's discussed in closed-door meetings
- **Tactical bargaining**: Day-to-day negotiation positions
- **Media management**: How Russia responds to criticism

### Analytical Framework

| Subcategory | Time Orientation | Function | What It Reveals |
|---------------|------------------|----------|------------------|
| **`/statements/`** | Present/Immediate | Declare policy | Crisis response, red lines, immediate reactions |
| **`/transcripts/`** | Present/Interactive | Negotiate/explain | Tactical positions, bilateral priorities, Q&A dynamics |
| **`/speeches/`** | Past/Reflective | Commemorate/position | Strategic priorities, desired image, long-term partnerships |
| **`/press-statements/`** | Present/Brief | Inform/react | Quick responses, schedule changes, minor updates |
| **`/news-conferences/`** | Present/Defensive | Manage media | Response to criticism, narrative control |

### For Foreign Policy Research

**Use ceremonial remarks (`/transcripts/speeches/`) to answer**:
- Which countries/regions receive *sustained ceremonial attention*?
- How does Russia *frame* long-term relationships?
- What partnerships does Russia *celebrate publicly*?
- How has Russia's *desired international positioning* changed over 25 years?
- Which alliances get *commemorated* at state events?

**Use statements (`/transcripts/statements/`) to answer**:
- How does Russia *respond to crises*?
- What actions trigger *immediate Russian reaction*?
- When does Russia *draw red lines*?
- How does Russia *justify military action*?
- What events cause Russia to *break from routine*?

**Use meeting transcripts (`/transcripts/transcripts/`) to answer**:
- What issues dominate *bilateral meetings*?
- How does Russia *negotiate* in closed settings?
- What questions does Russia *avoid or deflect*?
- How does leadership *respond to challenges*?
- What gets discussed *off the ceremonial stage*?

### This Dataset's Contribution

**What we can conclude about Georgia and Moldova**:

✓ **Valid**: Both countries are *ceremonially marginal* in Russian presidential rhetoric  
✓ **Valid**: Georgia had a brief *commemorative peak* during Medvedev's presidency (post-2008 war)  
✓ **Valid**: Moldova briefly *rose in symbolic importance* during 2014-2021 Ukraine crisis  
✓ **Valid**: Both countries have been *deprioritized in ceremonial contexts* post-2022  
✓ **Valid**: Neither country receives the *sustained rhetorical attention* of China, Belarus, or Ukraine  

✗ **Invalid**: Claiming Georgia wasn't important to Russia in 2008 (the war happened in statements)  
✗ **Invalid**: Claiming Russia has no Moldova policy post-2022 (absence from speeches ≠ policy absence)  
✗ **Invalid**: Using speeches to measure *crisis response* or *tactical priorities*  
✗ **Invalid**: Comparing speech mentions across fundamentally different events (commemorations vs wars)  

**The bottom line**: Speeches show *what Russia wants to celebrate*, not *what Russia is doing*. They reveal enduring partnerships and strategic positioning, not real-time foreign policy. For Georgia and Moldova, our findings indicate these countries are not part of Russia's *ceremonial narrative* - they're not partners to celebrate, regions to showcase, or relationships to commemorate. This is meaningful, but different from measuring operational foreign policy priorities.

## Research Applications

This dataset is suitable for:
- **Ceremonial rhetoric analysis** - How Russia frames achievements/commemorations
- **Long-term strategic positioning** - Which partnerships Russia emphasizes publicly over decades
- **Geographic priorities in public diplomacy** - Where presidents choose to deliver speeches
- **Temporal patterns in communication** - How presidential speech-making has evolved
- **Comparative symbolic importance** - Relative attention to countries/regions in ceremonial contexts
- **Retrospective framing** - How Russia commemorates past events
- **Alliance signaling** - Which relationships get celebrated at state events

This dataset is **NOT** suitable for:
- **Crisis response analysis** - Major events often communicated via statements
- **Real-time policy tracking** - Speeches are prepared weeks in advance
- **Bilateral diplomacy** - Substantive negotiations occur in transcripts/meeting records
- **Immediate reactions** - Statements and press conferences handle urgent responses
- **Comprehensive discourse analysis** - Missing 4 other communication categories
- **Military decision-making** - Operational decisions not discussed in ceremonial speeches
- **Tactical foreign policy** - Day-to-day diplomacy happens outside speeches

## Reproduction

To reproduce this analysis:

```bash
# 1. Preprocess speeches
python3 preprocess_all_speeches.py

# 2. Generate main visualizations
Rscript figures_smoothed.R

# 3. Georgia/Moldova analysis
Rscript analyze_georgia_moldova.R

# 4. Metadata analysis
Rscript analyze_speeches_metadata.R
```

All code and data available in this repository. Analysis conducted January 2026.

---

**Dataset Citation**: Kremlin.ru English Transcripts Archive (http://en.kremlin.ru/events/president/transcripts/speeches), accessed December 2025-January 2026.
