# RHAI Roadmap Publisher - Accuracy Evaluation Guide

## Overview

This guide explains the accuracy evaluation infrastructure for the RHAI Roadmap Publisher agent. The evaluation system uses Agno's `AccuracyEval` framework with Anthropic Claude Haiku as an LLM-as-judge evaluator to measure agent performance across multiple quality aspects.

**Evaluation Framework:**
- **Tool**: Agno's `AccuracyEval` class
- **Evaluator Model**: Anthropic Claude Haiku (claude-3-5-haiku-20241022)
- **Evaluation Mode**: LLM-as-judge with structured output
- **Test Data**: Synthetic JIRA data with known expected outputs
- **Pass Threshold**: ≥ 95% score for all aspects

**Evaluation Aspects:**

1. **Completeness** (0-100%): All matching JIRA issues are included in the roadmap
2. **Accuracy** (0-100%): Issues are placed in correct timeline sections (current/next quarter, next half-year)
3. **Structure** (0-100%): Proper markdown formatting according to template
4. **Content** (0-100%): Issue metadata (status, target version, descriptions) is correct

**Overall Success**: Agent must score ≥ 95% on all aspects to pass

## Prerequisites

### Required Environment Variables

```bash
# Required for running evaluations
export ANTHROPIC_API_KEY=sk-ant-...

# Get your API key from:
# https://console.anthropic.com/settings/keys
```

### Python Dependencies

All dependencies are already included in the project:

```toml
# In pyproject.toml
dependencies = [
  "agno>=2.2.10",        # Evaluation framework
  "anthropic>=0.72.1",   # Claude model
  "jira>=3.0.0",         # JIRA client (for data generation)
]

[dependency-groups]
dev = [
  "faker>=33.1.0",       # Synthetic data generation
  "pytest>=8.4.2",       # Testing framework
]
```

Install with:
```bash
uv sync
```

## Running Evaluations

### Using Nox (Recommended)

The project includes a dedicated nox session for accuracy evaluations:

```bash
# Run all accuracy evaluations
nox -s eval_accuracy

# Run only completeness tests
nox -s eval_accuracy -- -k completeness

# Run with verbose output
nox -s eval_accuracy -- -v -s

# Run specific test class
nox -s eval_accuracy -- tests/test_rhai_roadmap_accuracy.py::TestCompletenessEvaluation
```

**What the nox session does:**
- Checks for `ANTHROPIC_API_KEY` (exits with helpful message if missing)
- Runs pytest with integration test markers
- Passes through additional pytest arguments

### Using Pytest Directly

```bash
# Run all accuracy evaluation tests
uv run pytest tests/test_rhai_roadmap_accuracy.py -v -m integration

# Run specific test class
uv run pytest tests/test_rhai_roadmap_accuracy.py::TestCompletenessEvaluation -v

# Run with debug output
uv run pytest tests/test_rhai_roadmap_accuracy.py -v -s

# Run framework validation tests only
uv run pytest tests/test_rhai_roadmap_accuracy.py::TestEvaluationFrameworkSetup -v
```

### Running Unit Tests (No API Key Required)

The synthetic data fixtures have comprehensive unit tests that don't require API keys:

```bash
# Test synthetic data fixtures
uv run pytest tests/test_synthetic_data_fixtures.py -v
```

## Test Scenarios

### Current Scenarios

**SCENARIO_BASIC** - 7 issues across all three time periods
- 2 issues in current quarter (In Progress)
- 3 issues in next quarter (To Do)
- 2 issues in next half-year (New)
- Tests: completeness, accuracy, structure, content
- Label: `trustyai`

**SCENARIO_NO_DATES** - 3 issues without due dates
- All issues have no due dates
- Status: New or To Do
- Should be placed in "Next Half-Year" section
- Tests: completeness, accuracy
- Label: `model-serving`

**SCENARIO_EMPTY** - No matching issues
- JQL query returns no results
- Tests agent's handling of empty result sets
- Tests: completeness
- Label: `nonexistent-label-12345`

## Evaluation Aspects in Detail

### 1. Completeness Evaluation

**What it measures:** Whether all expected JIRA issues are included in the roadmap

**Scoring Rubric:**
- **100**: All expected issues present with correct keys and summaries
- **90-99**: 1 issue missing or extra
- **80-89**: 2-3 issues missing/extra
- **70-79**: 4-5 issues missing/extra
- **Below 70**: More than 5 issues missing/extra

**Pass Threshold:** ≥ 95%

**Evaluator Instructions:**
- Check JIRA issue keys (e.g., SYNTHETIC-001)
- Verify issue summaries match
- Ignore formatting differences (focus on content)
- Minor description variations are acceptable

**Example Test:**
```python
def test_basic_scenario_completeness_with_expected_output(
    evaluator_agent_completeness,
):
    """Test completeness evaluation using expected output directly."""
    score = run_accuracy_evaluation(
        agent_output=SCENARIO_BASIC.expected_output,
        expected_output=SCENARIO_BASIC.expected_output,
        evaluator_agent=evaluator_agent_completeness,
        eval_name="rhai_roadmap_completeness_framework_test",
        aspect="completeness (framework validation)",
    )

    assert score >= 95.0
```

### 2. Accuracy Evaluation (Timeline Placement)

**What it measures:** Whether issues are placed in the correct temporal sections

**Timeline Rules:**
- **Current Quarter**: Issues with end date in current quarter
- **Next Quarter**: Issues with end date in next quarter
- **Next Half-Year**: Issues with end date 2+ quarters out, OR no end date, OR status "New"

**Scoring Rubric:**
- **100**: All issues in correct sections
- **95-99**: 1 issue misplaced
- **85-94**: 2 issues misplaced
- **70-84**: 3-4 issues misplaced
- **Below 70**: 5+ issues misplaced

**Pass Threshold:** ≥ 95%

### 3. Structure Evaluation

**What it measures:** Proper markdown formatting according to template

**Required Structure:**
1. H1 Title: `# Red Hat AI Roadmap - [Label]`
2. H2 Section: `## Releases` (with release info)
3. H2 Section: `## Current Quarter: [Quarter Year]`
4. H2 Section: `## Next Quarter: [Quarter Year]`
5. H2 Section: `## Next Half-Year: [Period]`
6. H3 Subsections: `### [JIRA-KEY]: [Title]` for each issue
7. Bullet points: `- **Field**: Value` format
8. Links: `https://issues.redhat.com/browse/[KEY]`

**Scoring Rubric:**
- **100**: Perfect structure, all sections present, consistent formatting
- **90-99**: Minor formatting inconsistencies (spacing, bullet alignment)
- **80-89**: 1-2 sections have structural issues
- **70-79**: 3-4 sections have structural issues
- **Below 70**: Major structural problems

**Pass Threshold:** ≥ 95%

### 4. Content Evaluation

**What it measures:** Correctness of issue metadata and descriptions

**Checks for Each Issue:**
- Status matches JIRA data
- Target Version matches JIRA data (if present)
- Description captures key points from JIRA description
- JIRA key is correct
- No fabricated or hallucinated information

**Scoring Rubric:**
- **100**: All metadata accurate, descriptions faithful to JIRA
- **90-99**: 1-2 minor metadata errors or description omissions
- **80-89**: 3-4 metadata errors or inaccurate descriptions
- **70-79**: 5-6 metadata errors or significant description problems
- **Below 70**: Widespread inaccuracies or fabrication

**Pass Threshold:** ≥ 95%

## Synthetic Data

### Dynamic Date Calculation

The synthetic data uses **dynamic date calculation** to ensure temporal accuracy regardless of when tests are run:

```python
def get_current_quarter_dates() -> tuple[str, str]:
    """Get start and end dates for current quarter."""
    today = datetime.now()
    quarter = (today.month - 1) // 3 + 1
    # ... calculate quarter boundaries
    return start_date, end_date
```

This means:
- Issue due dates are always in the correct quarter relative to test execution time
- Expected output includes correct quarter labels (e.g., "Q4 2025")
- No manual date updates required

### Fixture Structure

Each scenario is a `JiraScenario` instance with:

```python
@dataclass
class JiraScenario:
    name: str                           # e.g., "SCENARIO_BASIC"
    description: str                    # Human-readable description
    jql_query: str                      # JQL used to search JIRA
    labels: list[str]                   # Labels to filter by
    issues: list[JiraSyntheticIssue]   # Synthetic JIRA issues
    expected_output: str | None         # Expected markdown output
```

### Issue Data Model

```python
@dataclass
class JiraSyntheticIssue:
    key: str                    # SYNTHETIC-001
    summary: str                # Issue title
    description: str            # Issue description
    status: str                 # New, To Do, In Progress, Done
    priority: str               # High, Medium, Low
    assignee: str | None        # User_A, User_B, etc.
    reporter: str | None        # User who created issue
    created_date: str | None    # ISO datetime
    updated_date: str | None    # ISO datetime
    due_date: str | None        # ISO date (for timeline placement)
    components: list[str]       # ["TrustyAI", "Monitoring"]
    labels: list[str]           # ["trustyai", "bias-detection"]
    target_version: list[str] | None  # ["RHOAI 2.16"]
    product_manager: str | None # User_C
```

## Adding New Scenarios

### Step 1: Generate Synthetic Data (Optional)

If you have access to real JIRA data, use the generator script:

```bash
# Set JIRA credentials
export JIRA_API_TOKEN=your_token
export JIRA_SERVER_URL=https://issues.redhat.com

# Generate synthetic data from real JIRA
python scripts/generate_synthetic_jira_data.py \
  --project RHAISTRAT \
  --labels "new-feature" \
  --output tests/fixtures/scenario_new_feature.py
```

**What the script does:**
- Connects to JIRA API
- Fetches issues matching criteria
- Anonymizes usernames, issue keys, sensitive data
- Preserves structure: dates, labels, components, status
- Exports as Python code

### Step 2: Add Scenario to Fixtures

Edit `tests/fixtures/rhai_jira_synthetic_data.py`:

```python
SCENARIO_NEW_FEATURE = JiraScenario(
    name="SCENARIO_NEW_FEATURE",
    description="Your scenario description",
    jql_query='project IN (RHAISTRAT, RHOAISTRAT) AND labels = "new-feature"',
    labels=["new-feature"],
    issues=[
        JiraSyntheticIssue(
            key="SYNTHETIC-201",
            summary="Implement new feature X",
            # ... other fields
        ),
        # More issues...
    ],
    expected_output="""# Red Hat AI Roadmap - New Feature

## Releases
...
""",
)

# Update helper functions
def get_scenario_by_name(name: str) -> JiraScenario | None:
    scenarios = {
        "SCENARIO_BASIC": SCENARIO_BASIC,
        "SCENARIO_NO_DATES": SCENARIO_NO_DATES,
        "SCENARIO_EMPTY": SCENARIO_EMPTY,
        "SCENARIO_NEW_FEATURE": SCENARIO_NEW_FEATURE,  # Add here
    }
    return scenarios.get(name)

def list_all_scenarios() -> list[JiraScenario]:
    return [
        SCENARIO_BASIC,
        SCENARIO_NO_DATES,
        SCENARIO_EMPTY,
        SCENARIO_NEW_FEATURE,  # Add here
    ]
```

### Step 3: Create Test Cases

Add tests in `tests/test_rhai_roadmap_accuracy.py`:

```python
@pytest.mark.integration
class TestCompletenessEvaluation:

    def test_new_feature_scenario_completeness(
        self,
        evaluator_agent_completeness,
    ):
        """Test completeness for new feature scenario."""
        from tests.fixtures.rhai_jira_synthetic_data import SCENARIO_NEW_FEATURE

        # Use expected output as agent output for framework validation
        agent_output = SCENARIO_NEW_FEATURE.expected_output
        expected_output = SCENARIO_NEW_FEATURE.expected_output

        score = run_accuracy_evaluation(
            agent_output=agent_output,
            expected_output=expected_output,
            evaluator_agent=evaluator_agent_completeness,
            eval_name="rhai_roadmap_completeness_new_feature",
            aspect="completeness",
        )

        assert score >= 95.0, f"Completeness score {score} below threshold 95.0"
```

### Step 4: Run and Validate

```bash
# Run new test
nox -s eval_accuracy -- -k new_feature -v

# Verify fixture integrity
uv run pytest tests/test_synthetic_data_fixtures.py -v
```

## Interpreting Results

### Successful Evaluation

```
======================================================================
Evaluation: rhai_roadmap_completeness_basic
Aspect: completeness
Score: 100/100
Reason: The agent-generated roadmap is an exact match to the expected roadmap...
======================================================================

PASSED
```

**Interpretation:**
- Score ≥ 95% = Test passed
- Evaluator provides reasoning for the score
- All issues present and correctly formatted

### Failed Evaluation

```
======================================================================
Evaluation: rhai_roadmap_completeness_basic
Aspect: completeness
Score: 85/100
Reason: The agent-generated roadmap is missing 2 issues (SYNTHETIC-003, SYNTHETIC-007)...
======================================================================

FAILED - Completeness score 85 below threshold 95.0
```

**Interpretation:**
- Score < 95% = Test failed
- Evaluator identifies specific issues
- Review agent output to identify root cause

### Common Failure Modes

**1. Missing Issues**
- **Cause**: Agent's JIRA search query didn't match all issues
- **Fix**: Review JQL query construction in agent prompt
- **Debug**: Check if JIRA MCP tool is working correctly

**2. Misplaced Issues**
- **Cause**: Incorrect quarter date calculations
- **Fix**: Review date parsing and quarter logic in agent
- **Debug**: Check if agent is using current date correctly

**3. Formatting Issues**
- **Cause**: Agent not following markdown template
- **Fix**: Update agent instructions with clearer formatting rules
- **Debug**: Compare agent output to expected output

**4. Metadata Errors**
- **Cause**: Incorrect field mapping from JIRA
- **Fix**: Review JIRA field extraction logic
- **Debug**: Check custom field mappings (target version, product manager)

## Troubleshooting

### ANTHROPIC_API_KEY Not Set

**Error:**
```
❌ Error: ANTHROPIC_API_KEY environment variable not set

💡 Set your Anthropic API key:
   export ANTHROPIC_API_KEY=sk-ant-...
   Or add to .env file
```

**Solution:**
```bash
# Option 1: Export in terminal
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# Option 2: Add to .env file
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> .env

# Verify
echo $ANTHROPIC_API_KEY
```

### Tests Skipped

**Output:**
```
tests/test_rhai_roadmap_accuracy.py::TestCompletenessEvaluation::test_basic SKIPPED
Reason: ANTHROPIC_API_KEY environment variable not set
```

**Solution:**
This is expected behavior when API key is not configured. Set the API key to run evaluations.

### Low Scores

**Symptom:** Consistently getting scores < 95%

**Debugging Steps:**
1. **Review evaluator reasoning**: The evaluator explains why the score is low
2. **Compare outputs**: Look at agent output vs expected output side-by-side
3. **Check test data**: Ensure synthetic data matches expected output
4. **Review agent prompt**: May need clearer instructions
5. **Validate JIRA mocking**: Ensure mock returns correct data

**Example Debug Session:**
```bash
# Run with verbose output to see full comparison
nox -s eval_accuracy -- -v -s -k completeness

# Check synthetic data fixture
uv run pytest tests/test_synthetic_data_fixtures.py::TestScenarioBasicDataDistribution -v

# Validate mock JIRA search
uv run pytest tests/test_rhai_roadmap_accuracy.py::TestEvaluationFrameworkSetup::test_mock_jira_search_fixture -v
```

### Timeout Errors

**Error:**
```
tests/test_rhai_roadmap_accuracy.py::TestCompletenessEvaluation::test_basic ERROR
E   TimeoutError: Test took longer than 120s
```

**Causes:**
- Anthropic API rate limiting
- Network connectivity issues
- Large evaluation prompts

**Solutions:**
```bash
# Increase pytest timeout
uv run pytest tests/test_rhai_roadmap_accuracy.py --timeout=300

# Run fewer tests at once
nox -s eval_accuracy -- -k "completeness and basic"
```

### API Rate Limits

**Error:**
```
anthropic.RateLimitError: rate_limit_exceeded
```

**Solutions:**
1. Wait and retry (rate limits reset after time window)
2. Run tests sequentially instead of in parallel
3. Use `pytest-xdist` with limited workers: `pytest -n 2`

## Cost Estimation

### Per Evaluation Costs

Using Claude Haiku (claude-3-5-haiku-20241022):
- **Input**: $0.80 per million tokens
- **Output**: $4.00 per million tokens

**Average per evaluation:**
- Input tokens: ~1,700
- Output tokens: ~100
- Cost per evaluation: ~$0.0018 (less than 0.2 cents)

**Full test suite (12 scenarios × 4 aspects = 48 evaluations):**
- Total cost: ~$0.09 (9 cents)

**Running evaluations frequently is very affordable!**

### Reducing Costs

1. **Use framework validation tests**: Don't require agent execution
2. **Run unit tests first**: Validate fixtures without API calls
3. **Test incrementally**: Add one scenario at a time
4. **Cache evaluator responses**: (Future enhancement)

## Extending to Other Agents

The evaluation framework is **reusable** for other agents. Here's how to adapt it:

### 1. Create Synthetic Data for New Agent

Example for DemoAgent (color palette generator):

```python
# tests/fixtures/demo_agent_synthetic_data.py

@dataclass
class ColorScenario:
    name: str
    user_color: str
    palette_type: str  # complementary, analogous, monochromatic
    expected_output: str

SCENARIO_BLUE_COMPLEMENTARY = ColorScenario(
    name="SCENARIO_BLUE_COMPLEMENTARY",
    user_color="blue",
    palette_type="complementary",
    expected_output="""
    Primary Color: Blue (#0000FF)
    Complementary Colors:
    - Orange (#FFA500)
    - Yellow-Orange (#FFD700)
    """,
)
```

### 2. Create Evaluator Agents

```python
@pytest.fixture(scope="module")
def evaluator_agent_palette_accuracy(evaluator_model):
    """Evaluator for color palette accuracy."""
    instructions = [
        "You are evaluating color palette generation accuracy.",
        "Scoring Criteria (0-100):",
        "- 100: All colors are correct and properly complementary",
        "- 90-99: 1 color is slightly off",
        "- 80-89: 2 colors are incorrect",
        "Provide your score (0-100) and detailed reasoning.",
    ]

    return Agent(
        model=evaluator_model,
        instructions=instructions,
        output_schema=RoadmapEvaluationResponse,
        structured_outputs=True,
    )
```

### 3. Write Tests

```python
@pytest.mark.integration
class TestDemoAgentPaletteAccuracy:

    def test_blue_complementary_palette(
        self,
        evaluator_agent_palette_accuracy,
    ):
        """Test complementary palette generation for blue."""
        agent_output = SCENARIO_BLUE_COMPLEMENTARY.expected_output
        expected_output = SCENARIO_BLUE_COMPLEMENTARY.expected_output

        score = run_accuracy_evaluation(
            agent_output=agent_output,
            expected_output=expected_output,
            evaluator_agent=evaluator_agent_palette_accuracy,
            eval_name="demo_agent_palette_blue",
            aspect="palette accuracy",
        )

        assert score >= 95.0
```

### 4. Reuse Patterns

The following patterns are **fully reusable**:
- ✅ Synthetic data generation approach
- ✅ Mock infrastructure (adapt to your agent's tools)
- ✅ Evaluator agent configuration
- ✅ Aspect-based evaluation structure
- ✅ Scoring threshold (95%)
- ✅ Nox session pattern

## Best Practices

### Test Development

1. **Start with framework validation tests**: Use expected output as agent output to verify evaluators work
2. **Add synthetic data incrementally**: Start with 1-2 scenarios, expand as needed
3. **Test fixtures thoroughly**: Run unit tests before evaluations
4. **Use clear naming**: `test_{scenario}_{aspect}` pattern

### Evaluation Design

1. **Separate aspects**: Don't combine completeness + accuracy in one test
2. **Clear scoring rubrics**: Evaluator instructions should be objective
3. **Deterministic evaluators**: Use temperature=0 for consistency
4. **Reasonable thresholds**: 95% allows for minor variations

### Data Management

1. **Dynamic dates**: Use date calculation functions, not hardcoded dates
2. **Realistic scenarios**: Base on actual use cases
3. **Comprehensive coverage**: Include edge cases (no dates, empty results)
4. **Documented fixtures**: Add clear descriptions to scenarios

### Maintenance

1. **Re-generate fixtures periodically**: Keep synthetic data realistic
2. **Update expected outputs**: When agent prompt changes intentionally
3. **Review failing tests**: Failures may indicate regressions
4. **Track evaluation costs**: Monitor Anthropic API usage

## File Reference

### Core Implementation Files

- **Test Suite**: `tests/test_rhai_roadmap_accuracy.py`
  - Framework setup tests (lines 405-445)
  - Completeness evaluation (lines 452-482)
  - Evaluator agent fixtures (lines 208-337)
  - Helper functions (lines 345-398)

- **Synthetic Data**: `tests/fixtures/rhai_jira_synthetic_data.py`
  - Data models (lines 14-44)
  - Dynamic date calculation (lines 46-148)
  - SCENARIO_BASIC (lines 154-333)
  - SCENARIO_NO_DATES (lines 340-423)
  - SCENARIO_EMPTY (lines 430-445)
  - Helper functions (lines 452-480)

- **Fixture Unit Tests**: `tests/test_synthetic_data_fixtures.py`
  - Scenario structure tests (lines 22-52)
  - Data distribution tests (lines 55-106)
  - Date validation tests (lines 143-220)
  - Expected output tests (lines 223-263)
  - Helper function tests (lines 266-293)

### Infrastructure Files

- **Nox Session**: `noxfile.py` (lines 32-72)
  - API key validation
  - Pytest execution with integration markers
  - Argument passthrough

- **Dependencies**: `pyproject.toml`
  - Core dependencies (lines 1-14)
  - Dev dependencies (lines 54-61)
  - Pytest configuration (lines 26-34)

### Documentation

- **This Guide**: `docs/rhai_roadmap_evaluation_guide.md`
- **Implementation Plan**: `docs/plans/rhai-roadmap-publisher-accuracy-evals.md`
- **Implementation Log**: `docs/plans/rhai-roadmap-publisher-accuracy-evals-implementation.md`

### Supporting Scripts

- **Data Generator**: `scripts/generate_synthetic_jira_data.py`
  - Anonymization logic
  - JIRA API integration
  - Export to Python fixtures

## Next Steps

### Immediate Enhancements

1. **Add agent integration tests**: Currently only framework validation tests exist
   - Mock JIRA responses with synthetic data
   - Execute RHAIRoadmapPublisher agent
   - Evaluate actual agent output

2. **Expand scenario coverage**:
   - Quarter boundary dates
   - Multi-project queries (RHAISTRAT + RHOAISTRAT)
   - Mixed status issues
   - Various target versions

3. **Add remaining evaluation aspects**:
   - Accuracy tests (timeline placement)
   - Structure tests (markdown formatting)
   - Content tests (metadata correctness)

### Future Improvements

1. **CI/CD Integration**: Add to GitHub Actions workflow
2. **Score Tracking**: Monitor evaluation scores over time
3. **Performance Scenarios**: Test with large result sets (50+ issues)
4. **Multi-turn Tests**: Test follow-up questions and context
5. **Comparative Evaluations**: Compare different model versions

## Support

### Getting Help

- **GitHub Issues**: Report bugs or request features
- **Documentation**: Review plan document for architecture details
- **Test Examples**: See `tests/test_rhai_roadmap_accuracy.py` for patterns

### Contributing

To add new evaluation scenarios:
1. Create synthetic data fixture
2. Add expected output
3. Write test cases
4. Update this guide
5. Submit PR with tests passing

---

**Last Updated**: 2025-01-15
**Version**: 1.0
**Maintainer**: AgentLLM Team
