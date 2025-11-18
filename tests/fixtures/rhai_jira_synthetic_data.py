"""Synthetic JIRA data for RHAI Roadmap Publisher accuracy evaluations.

This module contains pre-generated synthetic JIRA data for testing the RHAI Roadmap
Publisher agent's accuracy. Each scenario represents a different test case with
known inputs and expected outputs.

Generated: 2025-11-15
"""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class JiraSyntheticIssue:
    """Represents a synthetic JIRA issue for testing."""

    key: str
    summary: str
    description: str
    status: str
    priority: str
    assignee: str | None
    reporter: str | None
    created_date: str | None
    updated_date: str | None
    due_date: str | None  # End date for timeline placement
    components: list[str]
    labels: list[str]
    target_version: list[str] | None
    product_manager: str | None


@dataclass
class JiraScenario:
    """Represents a test scenario with JIRA data and expected output."""

    name: str
    description: str
    jql_query: str
    labels: list[str]
    issues: list[JiraSyntheticIssue]
    expected_output: str | None = None


def get_current_quarter_dates() -> tuple[str, str]:
    """Get start and end dates for current quarter.

    Returns:
        Tuple of (start_date, end_date) in ISO format
    """
    today = datetime.now()
    quarter = (today.month - 1) // 3 + 1
    year = today.year

    # Quarter start month
    start_month = (quarter - 1) * 3 + 1
    start_date = datetime(year, start_month, 1)

    # Quarter end month
    end_month = quarter * 3
    if end_month == 12:
        end_date = datetime(year, 12, 31)
    else:
        end_date = datetime(year, end_month + 1, 1) - timedelta(days=1)

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def get_next_quarter_dates() -> tuple[str, str]:
    """Get start and end dates for next quarter.

    Returns:
        Tuple of (start_date, end_date) in ISO format
    """
    today = datetime.now()
    quarter = (today.month - 1) // 3 + 1
    year = today.year

    # Next quarter
    next_quarter = quarter + 1
    next_year = year
    if next_quarter > 4:
        next_quarter = 1
        next_year += 1

    # Quarter start month
    start_month = (next_quarter - 1) * 3 + 1
    start_date = datetime(next_year, start_month, 1)

    # Quarter end month
    end_month = next_quarter * 3
    if end_month == 12:
        end_date = datetime(next_year, 12, 31)
    else:
        end_date = datetime(next_year, end_month + 1, 1) - timedelta(days=1)

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def get_half_year_dates() -> tuple[str, str]:
    """Get start and end dates for next half-year (2 quarters after next quarter).

    Returns:
        Tuple of (start_date, end_date) in ISO format
    """
    today = datetime.now()
    quarter = (today.month - 1) // 3 + 1
    year = today.year

    # Two quarters ahead
    target_quarter = quarter + 2
    target_year = year
    if target_quarter > 4:
        target_quarter = target_quarter - 4
        target_year += 1

    # Start of target quarter
    start_month = (target_quarter - 1) * 3 + 1
    start_date = datetime(target_year, start_month, 1)

    # End is 6 months later (2 full quarters)
    end_date = start_date + timedelta(days=180)

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


# Get dynamic quarter dates for scenarios
current_q_start, current_q_end = get_current_quarter_dates()
next_q_start, next_q_end = get_next_quarter_dates()
half_year_start, half_year_end = get_half_year_dates()

# Calculate midpoint dates for issues
current_q_mid = (
    datetime.fromisoformat(current_q_start) + (datetime.fromisoformat(current_q_end) - datetime.fromisoformat(current_q_start)) / 2
).strftime("%Y-%m-%d")

next_q_mid = (
    datetime.fromisoformat(next_q_start) + (datetime.fromisoformat(next_q_end) - datetime.fromisoformat(next_q_start)) / 2
).strftime("%Y-%m-%d")

half_year_mid = (
    datetime.fromisoformat(half_year_start) + (datetime.fromisoformat(half_year_end) - datetime.fromisoformat(half_year_start)) / 2
).strftime("%Y-%m-%d")


# =============================================================================
# Scenario 1: Basic Scenario - Issues across all three time periods
# =============================================================================

SCENARIO_BASIC = JiraScenario(
    name="SCENARIO_BASIC",
    description="Basic scenario with 7 issues distributed across current quarter, next quarter, and next half-year",
    jql_query='project IN (RHAISTRAT, RHOAISTRAT) AND labels = "trustyai" ORDER BY duedate ASC',
    labels=["trustyai"],
    issues=[
        # Current Quarter - 2 issues
        JiraSyntheticIssue(
            key="SYNTHETIC-001",
            summary="Implement bias detection framework",
            description="Create comprehensive bias detection system. Enable automated fairness analysis. Support multiple bias metrics.",
            status="In Progress",
            priority="High",
            assignee="User_A",
            reporter="User_B",
            created_date="2024-10-15T10:30:00+00:00",
            updated_date="2025-11-10T14:22:00+00:00",
            due_date=current_q_mid,
            components=["TrustyAI"],
            labels=["trustyai", "bias-detection"],
            target_version=["RHOAI 2.16"],
            product_manager="User_C",
        ),
        JiraSyntheticIssue(
            key="SYNTHETIC-002",
            summary="Add explainability visualizations dashboard",
            description="Develop visualization components. Support LIME SHAP explanations. Interactive dashboard interface.",
            status="In Progress",
            priority="Medium",
            assignee="User_A",
            reporter="User_C",
            created_date="2024-11-01T09:15:00+00:00",
            updated_date="2025-11-12T16:45:00+00:00",
            due_date=current_q_end,
            components=["TrustyAI"],
            labels=["trustyai", "explainability"],
            target_version=["RHOAI 2.16"],
            product_manager="User_C",
        ),
        # Next Quarter - 3 issues
        JiraSyntheticIssue(
            key="SYNTHETIC-003",
            summary="Integrate fairness metrics monitoring",
            description="Continuous fairness monitoring system. Real-time metric tracking. Alert generation capabilities.",
            status="To Do",
            priority="High",
            assignee="User_D",
            reporter="User_B",
            created_date="2024-11-05T11:20:00+00:00",
            updated_date="2025-11-08T13:30:00+00:00",
            due_date=next_q_start,
            components=["TrustyAI", "Monitoring"],
            labels=["trustyai", "monitoring"],
            target_version=["RHOAI 2.17"],
            product_manager="User_C",
        ),
        JiraSyntheticIssue(
            key="SYNTHETIC-004",
            summary="Support custom bias mitigation strategies",
            description="Enable user-defined mitigation techniques. Pluggable strategy framework. Configuration management interface.",
            status="To Do",
            priority="Medium",
            assignee="User_E",
            reporter="User_C",
            created_date="2024-11-10T14:45:00+00:00",
            updated_date="2025-11-11T10:15:00+00:00",
            due_date=next_q_mid,
            components=["TrustyAI"],
            labels=["trustyai", "mitigation"],
            target_version=["RHOAI 2.17"],
            product_manager="User_C",
        ),
        JiraSyntheticIssue(
            key="SYNTHETIC-005",
            summary="Enhance model card generation automation",
            description="Automated model documentation. Comprehensive metadata capture. Standard format compliance.",
            status="To Do",
            priority="Low",
            assignee=None,
            reporter="User_B",
            created_date="2024-11-12T08:30:00+00:00",
            updated_date="2025-11-13T09:20:00+00:00",
            due_date=next_q_end,
            components=["TrustyAI", "Documentation"],
            labels=["trustyai", "model-cards"],
            target_version=["RHOAI 2.17"],
            product_manager="User_C",
        ),
        # Next Half-Year - 2 issues
        JiraSyntheticIssue(
            key="SYNTHETIC-006",
            summary="Advanced counterfactual explanation engine",
            description="Generate counterfactual explanations. Support diverse data types. Optimization algorithms implementation.",
            status="New",
            priority="Medium",
            assignee=None,
            reporter="User_F",
            created_date="2024-11-15T12:00:00+00:00",
            updated_date="2025-11-14T15:30:00+00:00",
            due_date=half_year_mid,
            components=["TrustyAI", "Explainability"],
            labels=["trustyai", "explainability", "advanced"],
            target_version=["RHOAI 2.18"],
            product_manager="User_C",
        ),
        JiraSyntheticIssue(
            key="SYNTHETIC-007",
            summary="Multi-stakeholder fairness framework",
            description="Support competing fairness definitions. Stakeholder preference management. Trade-off analysis tools.",
            status="New",
            priority="Low",
            assignee=None,
            reporter="User_G",
            created_date="2024-11-18T10:45:00+00:00",
            updated_date="2025-11-14T11:10:00+00:00",
            due_date=half_year_end,
            components=["TrustyAI"],
            labels=["trustyai", "fairness"],
            target_version=["RHOAI 2.19"],
            product_manager="User_C",
        ),
    ],
    expected_output=f"""# Red Hat AI Roadmap - TrustyAI

## Releases

For the upcoming periods, the target versions are scheduled as follows:
- **Current Quarter**: RHOAI 2.16
- **Next Quarter**: RHOAI 2.17
- **Next Half-Year**: RHOAI 2.18, RHOAI 2.19

## Current Quarter: Q{(datetime.now().month - 1) // 3 + 1} {datetime.now().year}

### SYNTHETIC-001: Implement bias detection framework
- **Status**: In Progress
- **Target Version**: RHOAI 2.16
- **Description**: Create comprehensive bias detection system for automated fairness analysis
- **Link**: https://issues.redhat.com/browse/SYNTHETIC-001

### SYNTHETIC-002: Add explainability visualizations dashboard
- **Status**: In Progress
- **Target Version**: RHOAI 2.16
- **Description**: Develop visualization components supporting LIME and SHAP explanations
- **Link**: https://issues.redhat.com/browse/SYNTHETIC-002

## Next Quarter: Q{((datetime.now().month - 1) // 3 + 2) % 4 or 4} {datetime.now().year if (datetime.now().month - 1) // 3 + 2 <= 4 else datetime.now().year + 1}

### SYNTHETIC-003: Integrate fairness metrics monitoring
- **Status**: To Do
- **Target Version**: RHOAI 2.17
- **Description**: Continuous fairness monitoring with real-time tracking and alerts
- **Link**: https://issues.redhat.com/browse/SYNTHETIC-003

### SYNTHETIC-004: Support custom bias mitigation strategies
- **Status**: To Do
- **Target Version**: RHOAI 2.17
- **Description**: Enable user-defined mitigation techniques with pluggable framework
- **Link**: https://issues.redhat.com/browse/SYNTHETIC-004

### SYNTHETIC-005: Enhance model card generation automation
- **Status**: To Do
- **Target Version**: RHOAI 2.17
- **Description**: Automated model documentation with comprehensive metadata capture
- **Link**: https://issues.redhat.com/browse/SYNTHETIC-005

## Next Half-Year: {((datetime.now().month - 1) // 3 + 2) % 2 + 1}H {datetime.now().year + 1 if (datetime.now().month - 1) // 3 + 2 > 4 else datetime.now().year}

### SYNTHETIC-006: Advanced counterfactual explanation engine
- **Status**: New
- **Target Version**: RHOAI 2.18
- **Strategic Focus**: Generate counterfactual explanations supporting diverse data types
- **Link**: https://issues.redhat.com/browse/SYNTHETIC-006

### SYNTHETIC-007: Multi-stakeholder fairness framework
- **Status**: New
- **Target Version**: RHOAI 2.19
- **Strategic Focus**: Support competing fairness definitions with trade-off analysis
- **Link**: https://issues.redhat.com/browse/SYNTHETIC-007
""",
)


# =============================================================================
# Scenario 2: Issues Without Dates - Should go to "Next Half-Year"
# =============================================================================

SCENARIO_NO_DATES = JiraScenario(
    name="SCENARIO_NO_DATES",
    description="Scenario with issues that have no due dates or 'New' status",
    jql_query='project IN (RHAISTRAT, RHOAISTRAT) AND labels = "model-serving" AND (duedate IS EMPTY OR status = "New") ORDER BY created DESC',
    labels=["model-serving"],
    issues=[
        JiraSyntheticIssue(
            key="SYNTHETIC-101",
            summary="Implement auto-scaling for model servers",
            description="Dynamic resource allocation. Load-based scaling policies. Performance optimization.",
            status="New",
            priority="High",
            assignee=None,
            reporter="User_H",
            created_date="2024-11-01T09:00:00+00:00",
            updated_date="2025-11-10T10:30:00+00:00",
            due_date=None,  # No due date
            components=["ModelServing"],
            labels=["model-serving", "scalability"],
            target_version=None,
            product_manager="User_I",
        ),
        JiraSyntheticIssue(
            key="SYNTHETIC-102",
            summary="Add multi-model batching support",
            description="Batch inference optimization. Request aggregation logic. Latency reduction techniques.",
            status="New",
            priority="Medium",
            assignee=None,
            reporter="User_I",
            created_date="2024-11-05T14:20:00+00:00",
            updated_date="2025-11-11T11:45:00+00:00",
            due_date=None,  # No due date
            components=["ModelServing", "Performance"],
            labels=["model-serving", "batching"],
            target_version=None,
            product_manager="User_I",
        ),
        JiraSyntheticIssue(
            key="SYNTHETIC-103",
            summary="Support GPU sharing across models",
            description="Efficient GPU utilization. Resource partitioning strategies. Multi-tenant serving architecture.",
            status="To Do",
            priority="Medium",
            assignee="User_J",
            reporter="User_H",
            created_date="2024-11-08T16:00:00+00:00",
            updated_date="2025-11-12T13:00:00+00:00",
            due_date=None,  # No due date
            components=["ModelServing", "Infrastructure"],
            labels=["model-serving", "gpu"],
            target_version=None,
            product_manager="User_I",
        ),
    ],
    expected_output=f"""# Red Hat AI Roadmap - Model Serving

## Releases

For the upcoming periods, the target versions are scheduled as follows:
- **Current Quarter**: No releases scheduled
- **Next Quarter**: No releases scheduled
- **Next Half-Year**: To be determined

## Next Half-Year: {((datetime.now().month - 1) // 3 + 2) % 2 + 1}H {datetime.now().year + 1 if (datetime.now().month - 1) // 3 + 2 > 4 else datetime.now().year}

### SYNTHETIC-101: Implement auto-scaling for model servers
- **Status**: New
- **Strategic Focus**: Dynamic resource allocation with load-based scaling policies
- **Link**: https://issues.redhat.com/browse/SYNTHETIC-101

### SYNTHETIC-102: Add multi-model batching support
- **Status**: New
- **Strategic Focus**: Batch inference optimization for latency reduction
- **Link**: https://issues.redhat.com/browse/SYNTHETIC-102

### SYNTHETIC-103: Support GPU sharing across models
- **Status**: To Do
- **Strategic Focus**: Efficient GPU utilization with multi-tenant architecture
- **Link**: https://issues.redhat.com/browse/SYNTHETIC-103

**Note**: All issues lack specific target dates and are planned for future development.
""",
)


# =============================================================================
# Scenario 3: Empty Result Set - No matching issues
# =============================================================================

SCENARIO_EMPTY = JiraScenario(
    name="SCENARIO_EMPTY",
    description="Scenario where JQL query returns no issues",
    jql_query='project IN (RHAISTRAT, RHOAISTRAT) AND labels = "nonexistent-label-12345" ORDER BY duedate ASC',
    labels=["nonexistent-label-12345"],
    issues=[],
    expected_output="""No issues found matching the label 'nonexistent-label-12345' in projects RHAISTRAT and RHOAISTRAT.

Please verify:
- The label name is spelled correctly
- Issues with this label exist in the specified projects
- You have permission to view these issues

To explore available labels, you can search JIRA or consult your team's documentation.
""",
)


# =============================================================================
# Helper Functions
# =============================================================================


def get_scenario_by_name(name: str) -> JiraScenario | None:
    """Get a scenario by name.

    Args:
        name: Scenario name (e.g., "SCENARIO_BASIC")

    Returns:
        JiraScenario instance or None if not found
    """
    scenarios = {
        "SCENARIO_BASIC": SCENARIO_BASIC,
        "SCENARIO_NO_DATES": SCENARIO_NO_DATES,
        "SCENARIO_EMPTY": SCENARIO_EMPTY,
    }
    return scenarios.get(name)


def list_all_scenarios() -> list[JiraScenario]:
    """Get all available scenarios.

    Returns:
        List of all JiraScenario instances
    """
    return [
        SCENARIO_BASIC,
        SCENARIO_NO_DATES,
        SCENARIO_EMPTY,
    ]
