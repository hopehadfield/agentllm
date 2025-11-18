# RHAI Roadmap Publisher - Accuracy Evaluation Implementation Plan

## Overview

- **Goal**: Implement comprehensive accuracy evaluations for the RHAI Roadmap Publisher agent using Agno's accuracy evaluation framework
- **Type**: Testing Infrastructure / Quality Assurance
- **Components Affected**:
  - New: `tests/test_rhai_roadmap_accuracy.py` (evaluation tests)
  - New: `tests/fixtures/rhai_jira_synthetic_data.py` (synthetic JIRA data)
  - New: `scripts/generate_synthetic_jira_data.py` (data anonymization script)
  - New: `docs/rhai_roadmap_evaluation_guide.md` (evaluation documentation)
- **Priority**: High - Establishes quality baseline and reusable patterns for agent evaluation

## Requirements

### Functional Requirements

1. **Accuracy Evaluation Framework**
   - Use Agno's `AccuracyEval` class to measure agent performance
   - Use Anthropic Claude Haiku as the LLM-as-judge evaluator
   - Support multiple isolated test scenarios (each test can run independently)
   - Require `ANTHROPIC_API_KEY` environment variable for evaluations

2. **Evaluation Aspects** (separate scores for each)
   - **Completeness**: All matching JIRA issues are included in the roadmap (0-100%)
   - **Accuracy**: Issues placed in correct timeline sections (current/next quarter, next half-year) (0-100%)
   - **Structure**: Proper markdown formatting according to template (0-100%)
   - **Content**: Issue metadata (status, target version, descriptions) is correct (0-100%)
   - **Overall Score**: Average of all aspect scores (must be ≥ 95% to pass)

3. **Test Scenarios** (start small, expand progressively)
   - **Phase 1 - Basic Scenarios**:
     - Single label with issues across all three time periods
     - Issues without end dates (should go to "Next Half-Year")
     - Issues with "New" status (should go to "Next Half-Year")
   - **Phase 2 - Edge Cases**:
     - Label with no matching issues (should report no results)
     - Issues at quarter boundaries (edge date testing)
     - Multiple labels/components in single query
   - **Phase 3 - Complex Scenarios**:
     - Mixed status issues (New, In Progress, Done)
     - Various target versions across time periods
     - Cross-project queries (RHAISTRAT + RHOAISTRAT)

4. **Synthetic Test Data**
   - Python script to anonymize real JIRA data
   - Preserve structure: key, summary, description, status, priority, dates, labels, components
   - Anonymize: usernames, specific product details, sensitive information
   - Store as Python fixtures (dict/dataclass structures)
   - Enable deterministic, reproducible tests

### Non-Functional Requirements

1. **Testability**
   - Each evaluation scenario runs independently
   - No inter-test dependencies
   - Clear pass/fail criteria (95% threshold)
   - Fast execution (< 30s per evaluation scenario)

2. **Maintainability**
   - Reusable evaluation patterns for other agents
   - Clear documentation of methodology
   - Easy to add new test scenarios
   - Separation of concerns (data, evaluation logic, assertions)

3. **Integration**
   - Mark as integration tests (`@pytest.mark.integration`)
   - Separate nox session for accuracy evaluations
   - CI/CD compatible (can skip if API key not available)
   - Local development friendly

## Architecture Alignment

### Existing Components to Use

1. **RHAI Roadmap Publisher Agent** (`src/agentllm/agents/rhai_roadmap_publisher.py`)
   - Lines 23-346: Complete agent implementation
   - Lines 115-297: System prompt with roadmap generation instructions
   - Already has toolkit configs: GoogleDrive, Jira, SystemPromptExtension, RHAIToolkit

2. **Test Patterns** (`tests/test_demo_agent.py`)
   - Lines 1-100: Pytest fixtures for shared_db, token_storage
   - Test structure and organization patterns
   - Model parameter testing patterns

3. **Agno Framework**
   - `agno.evals.AccuracyEval` - Evaluation class
   - `agno.models.anthropic.Claude` - Anthropic model integration
   - Agent execution and response handling

4. **Existing Toolkits**
   - `JiraTools` (`src/agentllm/tools/jira_toolkit.py`) - For mocking JIRA responses
   - `JiraIssueData` model (lines 29-48) - Data structure for JIRA issues

### New Components Required

1. **Synthetic Data Generator** (`scripts/generate_synthetic_jira_data.py`)
   - **Purpose**: Convert real JIRA data to anonymized test fixtures
   - **Rationale**: Enable realistic, reproducible tests without exposing sensitive data
   - **Key Features**:
     - Connect to JIRA API (using credentials)
     - Fetch sample issues across different projects, labels, statuses
     - Anonymize usernames, descriptions, summaries
     - Preserve dates, structure, labels, components
     - Export as Python dataclass/dict structures

2. **Synthetic Data Fixtures** (`tests/fixtures/rhai_jira_synthetic_data.py`)
   - **Purpose**: Provide pre-generated test data for evaluation scenarios
   - **Rationale**: Deterministic tests, no external dependencies during test execution
   - **Structure**:
     - Scenario 1: Basic roadmap (5-7 issues across quarters)
     - Scenario 2: Issues without dates (3 issues)
     - Scenario 3: Empty result set (no matching issues)
     - Scenario 4: Quarter boundary dates (4 issues)
     - Each scenario includes: input (JQL query, labels), JIRA response data, expected output

3. **Accuracy Evaluation Tests** (`tests/test_rhai_roadmap_accuracy.py`)
   - **Purpose**: Execute accuracy evaluations for each scenario
   - **Rationale**: Automated quality assurance, regression prevention
   - **Structure**:
     - Pytest class per evaluation aspect (Completeness, Accuracy, Structure, Content)
     - Each test method = one scenario
     - Use pytest fixtures for agent setup and data
     - Mock JIRA responses using synthetic data
     - Execute agent with mocked data
     - Run Agno AccuracyEval with Claude Haiku evaluator
     - Assert score ≥ 95%

4. **Evaluation Documentation** (`docs/rhai_roadmap_evaluation_guide.md`)
   - **Purpose**: Guide for understanding, running, and extending evaluations
   - **Rationale**: Maintainability, knowledge transfer, reusability
   - **Contents**:
     - Overview of evaluation framework
     - How to run evaluations locally
     - How to add new scenarios
     - Interpreting evaluation results
     - Troubleshooting common issues
     - Extending to other agents

## Implementation Approach

### Phase 1: Synthetic Data Infrastructure

**Goal**: Create the foundation for reproducible testing with realistic data

#### Step 1.1: Create Synthetic Data Generator Script

**File**: `scripts/generate_synthetic_jira_data.py`

**Implementation**:
```python
# Core functionality:
# 1. Accept JIRA credentials via environment variables
# 2. Accept query parameters (projects, labels, date ranges)
# 3. Fetch issues via JIRA REST API
# 4. Anonymize fields:
#    - Replace usernames with "User_A", "User_B", etc.
#    - Replace issue keys with synthetic keys (SYNTHETIC-001, etc.)
#    - Anonymize summaries/descriptions while preserving structure
#    - Keep dates, labels, components, status unchanged
# 5. Export as Python code (dataclass definitions)

# Key libraries:
# - jira (Python JIRA client)
# - faker (for realistic synthetic data)
# - pathlib (file operations)
```

**Key Features**:
- CLI interface: `python scripts/generate_synthetic_jira_data.py --project RHAISTRAT --labels "trustyai" --output tests/fixtures/scenario_trustyai.py`
- Preserve temporal relationships (dates relative to "today")
- Generate expected output markdown as well
- Include metadata for verification

**Testing Strategy**:
- Manual testing with real JIRA credentials
- Verify output format matches JiraIssueData structure
- Confirm anonymization (no real usernames/keys in output)

#### Step 1.2: Generate Initial Synthetic Data Fixtures

**File**: `tests/fixtures/rhai_jira_synthetic_data.py`

**Implementation**:
```python
# Structure:
# - SCENARIO_BASIC: 7 issues across 3 quarters
#   - 2 in current quarter
#   - 3 in next quarter
#   - 2 in next half-year
# - SCENARIO_NO_DATES: 3 issues without end dates
# - SCENARIO_EMPTY: JQL that returns no results
# - SCENARIO_QUARTER_BOUNDARY: Issues at Q boundaries
#
# Each scenario contains:
# - jql_query: str
# - labels: list[str]
# - jira_response: list[JiraIssueData]
# - expected_output: str (markdown)
# - expected_completeness: float (0-1)
# - expected_accuracy: float (0-1)
```

**Key Design Decisions**:
- Use dataclasses for type safety
- Include detailed comments explaining each scenario
- Provide helper functions to convert to mock responses
- Store expected outputs as multiline strings

**Testing Strategy**:
- Import fixtures in test file, verify structure
- Ensure all required fields present
- Validate dates are sensible (parseable, logical quarters)

### Phase 2: Evaluation Framework Setup

**Goal**: Implement core evaluation infrastructure with Agno + Anthropic Claude

#### Step 2.1: Create Base Evaluation Test Structure

**File**: `tests/test_rhai_roadmap_accuracy.py`

**Implementation**:
```python
# Pytest structure:
#
# Fixtures:
# - evaluator_model: Claude Haiku via Agno
# - rhai_agent: RHAIRoadmapPublisher instance with mocked JIRA
# - mock_jira_search: Fixture that returns synthetic data
#
# Test Classes (one per evaluation aspect):
# - TestCompletenessEvaluation
#   - test_basic_scenario_completeness
#   - test_no_dates_scenario_completeness
#   - test_empty_scenario_completeness
#
# - TestAccuracyEvaluation
#   - test_basic_scenario_accuracy
#   - test_quarter_boundary_accuracy
#
# - TestStructureEvaluation
#   - test_basic_scenario_structure
#   - test_markdown_formatting
#
# - TestContentEvaluation
#   - test_basic_scenario_content
#   - test_metadata_correctness
#
# Helper Functions:
# - run_accuracy_eval(agent, scenario, aspect, expected_output)
# - create_evaluator_instructions(aspect_name)
# - assert_score_threshold(result, min_score=0.95)
```

**Key Design Decisions**:
- Use `pytest.mark.integration` for all eval tests
- Skip tests if `ANTHROPIC_API_KEY` not set
- Each test is independent (can run in isolation)
- Clear naming: `test_{scenario}_{aspect}`
- Separate evaluator instructions per aspect

**Dependencies**:
```python
import os
import pytest
from unittest.mock import patch, MagicMock
from agno.evals import AccuracyEval
from agno.models.anthropic import Claude
from agentllm.agents.rhai_roadmap_publisher import RHAIRoadmapPublisher
from tests.fixtures.rhai_jira_synthetic_data import (
    SCENARIO_BASIC, SCENARIO_NO_DATES, SCENARIO_EMPTY
)
```

#### Step 2.2: Implement Evaluator Model Configuration

**Implementation**:
```python
@pytest.fixture
def evaluator_model():
    """Claude Haiku model for LLM-as-judge evaluation."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    return Claude(
        id="claude-3-5-haiku-20241022",  # Haiku model
        api_key=api_key,
    )

@pytest.fixture
def evaluator_agent_completeness(evaluator_model):
    """Evaluator agent for completeness scoring."""
    from agno.agent import Agent

    instructions = [
        "You are evaluating roadmap completeness.",
        "Compare the agent's roadmap output to the expected output.",
        "Score from 0-100 based on:",
        "- All expected JIRA issues are present (key, summary)",
        "- No issues are missing",
        "- No extra issues are included",
        "Return ONLY a number from 0-100."
    ]

    return Agent(
        model=evaluator_model,
        instructions=instructions,
    )
```

**Rationale**:
- Separate evaluator agents for each aspect (different instructions)
- Use Claude Haiku (cost-effective, fast)
- Clear scoring rubrics in instructions
- Fail fast if API key missing

#### Step 2.3: Implement JIRA Mocking Infrastructure

**Implementation**:
```python
@pytest.fixture
def mock_jira_client(scenario_data):
    """Mock JIRA client that returns synthetic data for searches."""
    mock_jira = MagicMock()

    # Mock search_issues to return scenario data
    def mock_search(jql, maxResults=None, fields=None):
        # Convert scenario JiraIssueData to JIRA Issue objects
        return [create_mock_jira_issue(issue) for issue in scenario_data.jira_response]

    mock_jira.search_issues.side_effect = mock_search
    return mock_jira

def create_mock_jira_issue(issue_data: JiraIssueData):
    """Convert JiraIssueData to mock JIRA Issue object."""
    mock_issue = MagicMock()
    mock_issue.key = issue_data.key
    mock_issue.fields.summary = issue_data.summary
    mock_issue.fields.description = issue_data.description
    # ... map all fields
    return mock_issue
```

**Rationale**:
- Avoid external JIRA API calls during tests
- Full control over responses
- Fast, deterministic tests
- Use unittest.mock for patching

### Phase 3: Implement Basic Evaluation Scenarios

**Goal**: Start with simple, isolated scenarios to validate the framework

#### Step 3.1: Completeness Evaluation - Basic Scenario

**Test**: `test_basic_scenario_completeness`

**Implementation**:
```python
@pytest.mark.integration
class TestCompletenessEvaluation:

    def test_basic_scenario_completeness(
        self,
        rhai_agent,
        evaluator_agent_completeness,
        mock_jira_client
    ):
        """Evaluate completeness for basic scenario with issues across all quarters."""
        # Arrange
        scenario = SCENARIO_BASIC
        user_id = "eval-test-user"
        user_message = f"Create a roadmap for label '{scenario.labels[0]}'"

        # Mock JIRA client to return scenario data
        with patch("agentllm.tools.jira_toolkit.JIRA", return_value=mock_jira_client):
            # Act: Run agent
            agent_output = rhai_agent.run(user_message, user_id=user_id)

            # Create AccuracyEval
            evaluation = AccuracyEval(
                name="rhai_roadmap_completeness_basic",
                agent=rhai_agent,
                evaluator_agent=evaluator_agent_completeness,
                input=user_message,
                expected_output=scenario.expected_output,
                num_iterations=1,
            )

            # Run evaluation (sync)
            result = evaluation.run_with_output(
                output=str(agent_output.content)
            )

            # Assert
            assert result.avg_score >= 95.0, (
                f"Completeness score {result.avg_score} below threshold 95.0"
            )
```

**Expected Behavior**:
- Agent receives user message requesting roadmap
- JIRA search returns synthetic data (7 issues)
- Agent generates markdown roadmap
- Evaluator compares to expected output
- Score ≥ 95% (all 7 issues present)

**Success Criteria**:
- Test passes with score ≥ 95%
- Clear error message if fails
- Runs in < 30 seconds

#### Step 3.2: Accuracy Evaluation - Basic Scenario

**Test**: `test_basic_scenario_accuracy`

**Implementation**:
```python
@pytest.mark.integration
class TestAccuracyEvaluation:

    def test_basic_scenario_accuracy(
        self,
        rhai_agent,
        evaluator_agent_accuracy,
        mock_jira_client
    ):
        """Evaluate timeline placement accuracy for basic scenario."""
        # Similar structure to completeness test
        # Different evaluator agent with accuracy-focused instructions

        # Evaluator instructions:
        instructions = [
            "You are evaluating roadmap timeline accuracy.",
            "Check if issues are in the correct time period:",
            "- Current Quarter: Issues with end date in current quarter",
            "- Next Quarter: Issues with end date in next quarter",
            "- Next Half-Year: Issues with end date 2 quarters out, OR no dates, OR status 'New'",
            "Score from 0-100 based on correct placement.",
            "Return ONLY a number from 0-100."
        ]
```

**Expected Behavior**:
- 2 issues in "Current Quarter" section (correct dates)
- 3 issues in "Next Quarter" section (correct dates)
- 2 issues in "Next Half-Year" section (correct dates)
- Score ≥ 95% for correct placement

#### Step 3.3: Structure Evaluation - Basic Scenario

**Test**: `test_basic_scenario_structure`

**Implementation**:
```python
@pytest.mark.integration
class TestStructureEvaluation:

    def test_basic_scenario_structure(
        self,
        rhai_agent,
        evaluator_agent_structure,
        mock_jira_client
    ):
        """Evaluate markdown structure and formatting."""
        # Evaluator instructions:
        instructions = [
            "You are evaluating roadmap markdown structure.",
            "Check for required sections and formatting:",
            "- H1 title: '# Red Hat AI Roadmap - [Label]'",
            "- H2 sections: '## Releases', '## Current Quarter', '## Next Quarter', '## Next Half-Year'",
            "- H3 subsections for each issue: '### [KEY]: [Title]'",
            "- Bullet points for metadata: '- **Status**: ...', '- **Target Version**: ...'",
            "- Links in correct format: 'https://issues.redhat.com/browse/[KEY]'",
            "Score from 0-100 based on structure compliance.",
            "Return ONLY a number from 0-100."
        ]
```

**Expected Behavior**:
- Proper markdown hierarchy (H1, H2, H3)
- Required sections present
- Consistent bullet formatting
- JIRA links in expected format
- Score ≥ 95% for proper structure

#### Step 3.4: Content Evaluation - Basic Scenario

**Test**: `test_basic_scenario_content`

**Implementation**:
```python
@pytest.mark.integration
class TestContentEvaluation:

    def test_basic_scenario_content(
        self,
        rhai_agent,
        evaluator_agent_content,
        mock_jira_client
    ):
        """Evaluate correctness of issue metadata and descriptions."""
        # Evaluator instructions:
        instructions = [
            "You are evaluating roadmap content accuracy.",
            "Verify issue metadata is correct:",
            "- Status matches JIRA data",
            "- Target Version matches JIRA data",
            "- Description captures key points from JIRA",
            "- JIRA key is correct",
            "Score from 0-100 based on metadata accuracy.",
            "Return ONLY a number from 0-100."
        ]
```

**Expected Behavior**:
- Status fields match JIRA data
- Target versions correct
- Descriptions summarize JIRA descriptions
- No fabricated data
- Score ≥ 95% for accurate content

### Phase 4: Expand to Edge Cases and Complex Scenarios

**Goal**: Comprehensive coverage including error conditions and complex queries

#### Step 4.1: Issues Without Dates Scenario

**Test**: `test_no_dates_scenario_completeness` + `test_no_dates_scenario_accuracy`

**Scenario**: 3 issues with no end dates or "New" status

**Expected Behavior**:
- All 3 issues placed in "Next Half-Year" section
- Note in roadmap about missing dates
- Completeness: all 3 issues present
- Accuracy: all in correct section (Next Half-Year)

#### Step 4.2: Empty Result Set Scenario

**Test**: `test_empty_scenario_completeness`

**Scenario**: JQL query returns no matching issues

**Expected Behavior**:
- Agent reports "No issues found for label X"
- Suggests alternative labels or actions
- Completeness: 100% (correctly reports empty result)
- No fabricated issues

#### Step 4.3: Quarter Boundary Scenario

**Test**: `test_quarter_boundary_accuracy`

**Scenario**: Issues with end dates at exact quarter boundaries

**Expected Behavior**:
- Issues on last day of Q1 → Current Quarter
- Issues on first day of Q2 → Next Quarter
- Boundary logic is correct
- Accuracy: 100% for boundary cases

#### Step 4.4: Complex Multi-Project Scenario

**Test**: `test_multi_project_scenario_completeness`

**Scenario**: Query across RHAISTRAT and RHOAISTRAT projects

**Expected Behavior**:
- Issues from both projects included
- Proper organization by quarter (not by project)
- Completeness: all issues from both projects
- Structure: unified roadmap format

### Phase 5: Documentation and Reusability

**Goal**: Create clear documentation and reusable patterns for future agent evaluations

#### Step 5.1: Create Evaluation Guide

**File**: `docs/rhai_roadmap_evaluation_guide.md`

**Structure**:
```markdown
# RHAI Roadmap Publisher - Accuracy Evaluation Guide

## Overview
[Purpose, methodology, evaluation aspects]

## Running Evaluations

### Prerequisites
- ANTHROPIC_API_KEY environment variable
- Python dependencies installed (uv sync)

### Commands
```bash
# Run all accuracy evaluations
nox -s eval-accuracy

# Run specific evaluation class
uv run pytest tests/test_rhai_roadmap_accuracy.py::TestCompletenessEvaluation -v

# Run single test scenario
uv run pytest tests/test_rhai_roadmap_accuracy.py::TestCompletenessEvaluation::test_basic_scenario_completeness -v
```

## Evaluation Aspects

### Completeness (0-100%)
[What it measures, how it's scored, examples]

### Accuracy (0-100%)
[Timeline placement logic, scoring rubric]

### Structure (0-100%)
[Markdown format requirements, scoring criteria]

### Content (0-100%)
[Metadata correctness, description quality]

## Adding New Scenarios

### Step 1: Generate Synthetic Data
```bash
python scripts/generate_synthetic_jira_data.py \
  --project RHAISTRAT \
  --labels "new-feature" \
  --output tests/fixtures/scenario_new_feature.py
```

### Step 2: Create Test Cases
[Code template for new test]

### Step 3: Run and Validate
[Verification checklist]

## Troubleshooting

### Low Scores
[Common causes, debugging steps]

### API Key Issues
[How to set ANTHROPIC_API_KEY, testing API access]

### Timeout Errors
[Increasing timeouts, model selection]

## Extending to Other Agents

### Reusable Patterns
- Synthetic data generation
- Mock infrastructure
- Evaluator agent configuration
- Aspect-based evaluation structure

### Adapting the Framework
[Step-by-step guide to apply to new agent types]
```

#### Step 5.2: Add Nox Session for Evaluations

**File**: `noxfile.py`

**Addition**:
```python
@nox.session(venv_backend="none")
def eval_accuracy(session):
    """Run accuracy evaluations for RHAI Roadmap Publisher.

    Requires ANTHROPIC_API_KEY environment variable.

    Examples:
        nox -s eval-accuracy                    # All evaluations
        nox -s eval-accuracy -- -k completeness # Only completeness tests
    """
    import os
    import sys

    # Check for ANTHROPIC_API_KEY
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("\n💡 Set your Anthropic API key:")
        print("   export ANTHROPIC_API_KEY=sk-ant-...")
        print("   Or add to .env file")
        sys.exit(1)

    print("✅ ANTHROPIC_API_KEY configured")
    print("🧪 Running accuracy evaluations...\n")

    args = [
        "uv", "run", "pytest",
        "tests/test_rhai_roadmap_accuracy.py",
        "-v",
        "--tb=short",
        "-m", "integration"
    ]

    # Pass through additional pytest arguments
    if session.posargs:
        args.extend(session.posargs)

    session.run(*args, external=True)
```

**Rationale**:
- Easy-to-remember command: `nox -s eval-accuracy`
- Clear error if API key missing
- Supports pytest arguments for filtering
- Marked as integration tests

## Testing Strategy

### Unit Testing (Synthetic Data & Infrastructure)

**File**: `tests/test_synthetic_data_fixtures.py`

```python
def test_scenario_basic_structure():
    """Verify SCENARIO_BASIC has all required fields."""
    assert SCENARIO_BASIC.jql_query
    assert SCENARIO_BASIC.labels
    assert len(SCENARIO_BASIC.jira_response) == 7
    assert SCENARIO_BASIC.expected_output

def test_scenario_basic_date_distribution():
    """Verify issues distributed across quarters."""
    # 2 current, 3 next, 2 half-year
    # Assert based on end dates

def test_jira_issue_data_conversion():
    """Test helper functions convert correctly."""
    issue = SCENARIO_BASIC.jira_response[0]
    mock_issue = create_mock_jira_issue(issue)
    assert mock_issue.key == issue.key
```

### Integration Testing (Accuracy Evaluations)

**Covered by main test file**: `tests/test_rhai_roadmap_accuracy.py`

- Each test scenario is an integration test
- End-to-end: synthetic data → agent execution → evaluation → score
- Tests marked with `@pytest.mark.integration`

### Manual Testing

**Synthetic Data Generation**:
```bash
# Test with real JIRA (requires credentials)
export JIRA_API_TOKEN=...
export JIRA_SERVER_URL=https://issues.redhat.com
python scripts/generate_synthetic_jira_data.py \
  --project RHAISTRAT \
  --labels "trustyai" \
  --output /tmp/test_scenario.py

# Verify output
cat /tmp/test_scenario.py
```

**Evaluation Execution**:
```bash
# Run single evaluation
ANTHROPIC_API_KEY=sk-ant-... \
  uv run pytest tests/test_rhai_roadmap_accuracy.py::TestCompletenessEvaluation::test_basic_scenario_completeness -v -s

# Check logs for detailed output
tail -f tmp/agno_handler.log
```

## Files to Create/Modify

### New Files

1. **`scripts/generate_synthetic_jira_data.py`**
   - Purpose: Anonymize real JIRA data for test fixtures
   - ~200 lines
   - Dependencies: jira, faker

2. **`tests/fixtures/rhai_jira_synthetic_data.py`**
   - Purpose: Pre-generated synthetic JIRA data for scenarios
   - ~400 lines (data-heavy)
   - Contains: 5-7 scenario definitions with expected outputs

3. **`tests/test_rhai_roadmap_accuracy.py`**
   - Purpose: Accuracy evaluation test suite
   - ~600 lines
   - Structure: 4 test classes (Completeness, Accuracy, Structure, Content)

4. **`docs/rhai_roadmap_evaluation_guide.md`**
   - Purpose: Comprehensive guide for evaluations
   - ~300 lines
   - Audience: Developers, QA, future maintainers

5. **`tests/test_synthetic_data_fixtures.py`**
   - Purpose: Unit tests for synthetic data infrastructure
   - ~150 lines
   - Validates fixture structure and helper functions

### Modified Files

1. **`noxfile.py`**
   - Change: Add `eval_accuracy` session (lines ~500-530)
   - Purpose: Easy CLI access to evaluations

2. **`pyproject.toml`**
   - Change: Add `faker` to dev dependencies
   - Lines: ~55-60 (dependency-groups.dev)

3. **`.env.example`**
   - Change: Add `ANTHROPIC_API_KEY` with example
   - Purpose: Document required environment variable

4. **`CLAUDE.md`**
   - Change: Add section on "Accuracy Evaluations" (after "Testing")
   - Purpose: Reference new evaluation infrastructure

## Dependencies & Prerequisites

### Python Packages

**New Dependencies**:
- `faker` - Realistic synthetic data generation (already have `anthropic>=0.72.1`)

**Existing Dependencies** (already in project):
- `agno>=2.2.10` - Evaluation framework
- `anthropic>=0.72.1` - Claude model access
- `jira>=3.0.0` - JIRA client for data generation
- `pytest>=8.4.2` - Testing framework

### Environment Variables

**Required for Evaluations**:
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude Haiku evaluator

**Required for Data Generation** (optional, only for creating new fixtures):
- `JIRA_API_TOKEN` - JIRA personal access token
- `JIRA_SERVER_URL` - JIRA instance URL (e.g., https://issues.redhat.com)
- `JIRA_USERNAME` - JIRA username (optional, for basic auth)

### External Services

- **Anthropic API** - Claude Haiku model for LLM-as-judge evaluation
  - Cost: ~$0.001 per evaluation (very low)
  - Rate limits: Standard Anthropic API limits

## Risks & Mitigations

### Risk: Evaluation Costs

**Description**: Running many evaluations could incur Anthropic API costs

**Mitigation**:
- Use Claude Haiku (cheapest model: $0.25/1M input tokens, $1.25/1M output)
- Estimated cost per eval: < $0.01
- Total for full suite (~12 tests): < $0.15
- Cache evaluator agents where possible
- Document expected costs in guide

### Risk: Non-Deterministic Scores

**Description**: LLM evaluators may give slightly different scores on repeated runs

**Mitigation**:
- Set temperature=0 for evaluator models (deterministic)
- Use clear, objective scoring rubrics
- Allow small variance (e.g., 94.5% still fails if threshold is 95%)
- Document expected score ranges
- Consider averaging multiple runs for critical scenarios

### Risk: Synthetic Data Staleness

**Description**: Real JIRA structure changes, synthetic data becomes unrealistic

**Mitigation**:
- Version synthetic data files (include generation date)
- Document real JIRA query used to generate each scenario
- Re-generate fixtures quarterly
- Add validation tests for fixture structure

### Risk: Test Maintenance Burden

**Description**: Many scenarios = many tests to maintain

**Mitigation**:
- Start small (Phase 1: 3 scenarios, ~6 tests)
- Expand incrementally (Phases 2-3: add as needed)
- Reusable fixtures and helper functions
- Clear documentation for adding new scenarios
- Consider parameterized tests for similar scenarios

### Risk: JIRA Mock Complexity

**Description**: Mocking JIRA responses accurately is complex

**Mitigation**:
- Use VCR cassettes as reference (if available)
- Generate mocks from real JIRA responses (via script)
- Comprehensive fixture validation tests
- Document mock structure and assumptions

### Risk: Agent Changes Break Evaluations

**Description**: Updates to agent prompt or logic change output format

**Mitigation**:
- Version expected outputs with agent version
- Update fixtures when agent changes intentionally
- Failing evals indicate regression (desired!)
- Separate structure tests from content tests (format vs. logic)

## Timeline Estimate

### Phase 1: Synthetic Data Infrastructure (~2-3 days)
- Day 1: Implement data generation script (4-6 hours)
- Day 1-2: Generate initial fixtures for 3 scenarios (2-4 hours)
- Day 2: Unit tests for fixtures (2-3 hours)

### Phase 2: Evaluation Framework (~3-4 days)
- Day 3: Set up base test structure, fixtures, mocks (4-6 hours)
- Day 4: Implement evaluator model configuration (3-4 hours)
- Day 4-5: JIRA mocking infrastructure (4-6 hours)

### Phase 3: Basic Scenarios (~3-4 days)
- Day 6: Completeness evaluation + basic scenario (3-4 hours)
- Day 6-7: Accuracy evaluation + basic scenario (4-5 hours)
- Day 7: Structure evaluation + basic scenario (3-4 hours)
- Day 8: Content evaluation + basic scenario (3-4 hours)

### Phase 4: Edge Cases (~2-3 days)
- Day 9: No dates scenario (2-3 hours)
- Day 9: Empty result scenario (2-3 hours)
- Day 10: Quarter boundary scenario (3-4 hours)
- Day 10: Multi-project scenario (3-4 hours)

### Phase 5: Documentation (~1-2 days)
- Day 11: Evaluation guide (4-6 hours)
- Day 11: Nox session, examples (2-3 hours)
- Day 12: Final review, polish, testing (3-4 hours)

**Total Estimated Time**: 11-16 days (2-3 weeks)

**Critical Path**:
1. Synthetic data generation (blocks everything)
2. Evaluation framework setup (blocks all scenarios)
3. Basic scenarios (validates framework)
4. Edge cases and docs (can be parallelized)

## Success Criteria

### Functional Success

- ✅ All basic scenario tests pass with score ≥ 95%
- ✅ All edge case tests pass with score ≥ 95%
- ✅ Each test can run independently
- ✅ Tests complete in < 30s per scenario
- ✅ Synthetic data generation script works with real JIRA
- ✅ At least 12 evaluation scenarios implemented (3 per aspect)

### Quality Success

- ✅ Comprehensive documentation in `docs/rhai_roadmap_evaluation_guide.md`
- ✅ Reusable patterns documented for other agents
- ✅ Clear error messages when evaluations fail
- ✅ Code follows existing project conventions (ruff, pytest patterns)
- ✅ All fixtures have validation unit tests

### Integration Success

- ✅ Nox session `eval-accuracy` works end-to-end
- ✅ Tests properly marked with `@pytest.mark.integration`
- ✅ Skip gracefully if `ANTHROPIC_API_KEY` not set
- ✅ Compatible with CI/CD (can run in automated pipeline)
- ✅ No external dependencies during test execution (JIRA mocked)

### Reusability Success

- ✅ Framework applicable to other agents (DemoAgent, ReleaseManager)
- ✅ Clear guide for adding new scenarios
- ✅ Synthetic data generation generalizes to other JIRA projects
- ✅ Evaluator agent patterns reusable for different evaluation types

## Next Steps After Implementation

1. **Apply to Other Agents**
   - Adapt framework for ReleaseManager agent
   - Create evaluations for DemoAgent (simpler scenarios)

2. **Expand Scenario Coverage**
   - Add scenarios for different labels (TrustyAI, ModelMesh, etc.)
   - Test error handling (JIRA API failures, malformed data)
   - Performance scenarios (large result sets, 50+ issues)

3. **CI/CD Integration**
   - Add eval-accuracy to GitHub Actions workflow
   - Set up nightly evaluation runs
   - Track score trends over time

4. **Advanced Evaluations**
   - Multi-turn conversations (follow-up questions)
   - User feedback incorporation
   - Comparative evaluations (different model versions)

5. **Monitoring & Alerting**
   - Track evaluation scores in metrics system
   - Alert on score degradation
   - Dashboard for evaluation trends

---

## Appendix: Example Evaluation Output

```
============================= test session starts ==============================
collecting ... collected 12 items

tests/test_rhai_roadmap_accuracy.py::TestCompletenessEvaluation::test_basic_scenario_completeness
Running AccuracyEval: rhai_roadmap_completeness_basic
Evaluator: Claude Haiku (claude-3-5-haiku-20241022)
Input: "Create a roadmap for label 'trustyai'"
Expected: [7 issues across 3 quarters]
Agent Output: [Generated markdown roadmap]
Score: 98.0/100
PASSED                                                                  [  8%]

tests/test_rhai_roadmap_accuracy.py::TestAccuracyEvaluation::test_basic_scenario_accuracy
Running AccuracyEval: rhai_roadmap_accuracy_basic
Score: 96.5/100
PASSED                                                                  [ 16%]

tests/test_rhai_roadmap_accuracy.py::TestStructureEvaluation::test_basic_scenario_structure
Running AccuracyEval: rhai_roadmap_structure_basic
Score: 100.0/100
PASSED                                                                  [ 25%]

tests/test_rhai_roadmap_accuracy.py::TestContentEvaluation::test_basic_scenario_content
Running AccuracyEval: rhai_roadmap_content_basic
Score: 95.5/100
PASSED                                                                  [ 33%]

...

======================== 12 passed in 180.45s (3m 0s) =========================
```

## Appendix: Evaluator Agent Instructions Templates

### Completeness Evaluator
```
You are evaluating the completeness of a RHAI roadmap document.

Your task is to compare the agent's generated roadmap to the expected roadmap and score how completely all issues are included.

Scoring Criteria (0-100):
- 100: All expected JIRA issues present with correct keys and summaries
- 90-99: 1 issue missing or 1 extra issue present
- 80-89: 2-3 issues missing/extra
- 70-79: 4-5 issues missing/extra
- Below 70: More than 5 issues missing/extra

Important:
- Check JIRA issue keys (e.g., RHAISTRAT-123)
- Verify issue summaries match
- Ignore formatting differences (focus on content)
- Minor description variations are acceptable

Return ONLY a number from 0 to 100.
```

### Accuracy Evaluator
```
You are evaluating the timeline accuracy of a RHAI roadmap document.

Your task is to verify that JIRA issues are placed in the correct time period sections.

Timeline Rules:
- Current Quarter: Issues with end date falling in the current quarter
- Next Quarter: Issues with end date in the next quarter
- Next Half-Year: Issues with end date 2+ quarters out, OR no end date, OR status "New"

Scoring Criteria (0-100):
- 100: All issues in correct sections
- 95-99: 1 issue misplaced
- 85-94: 2 issues misplaced
- 70-84: 3-4 issues misplaced
- Below 70: 5+ issues misplaced

Return ONLY a number from 0 to 100.
```

### Structure Evaluator
```
You are evaluating the markdown structure of a RHAI roadmap document.

Your task is to verify proper formatting according to the template.

Required Structure:
1. H1 Title: "# Red Hat AI Roadmap - [Label]"
2. H2 Section: "## Releases" (with release info)
3. H2 Section: "## Current Quarter: [Quarter Year]"
4. H2 Section: "## Next Quarter: [Quarter Year]"
5. H2 Section: "## Next Half-Year: [Period]"
6. H3 Subsections: "### [JIRA-KEY]: [Title]" for each issue
7. Bullet points: "- **Field**: Value" format
8. Links: "https://issues.redhat.com/browse/[KEY]"

Scoring Criteria (0-100):
- 100: Perfect structure, all sections present, consistent formatting
- 90-99: Minor formatting inconsistencies (spacing, bullet alignment)
- 80-89: 1-2 sections have structural issues
- 70-79: 3-4 sections have structural issues
- Below 70: Major structural problems

Return ONLY a number from 0 to 100.
```

### Content Evaluator
```
You are evaluating the content accuracy of a RHAI roadmap document.

Your task is to verify that issue metadata and descriptions are correct.

Check Each Issue For:
- Status matches JIRA data
- Target Version matches JIRA data (if present)
- Description captures key points from JIRA description
- JIRA key is correct
- No fabricated or hallucinated information

Scoring Criteria (0-100):
- 100: All metadata accurate, descriptions faithful to JIRA
- 90-99: 1-2 minor metadata errors or description omissions
- 80-89: 3-4 metadata errors or inaccurate descriptions
- 70-79: 5-6 metadata errors or significant description problems
- Below 70: Widespread inaccuracies or fabrication

Return ONLY a number from 0 to 100.
```
