"""Unit tests for synthetic JIRA data fixtures.

These tests validate the structure and integrity of the synthetic data used
for RHAI Roadmap Publisher accuracy evaluations.
"""

from datetime import datetime

import pytest

from tests.fixtures.rhai_jira_synthetic_data import (
    SCENARIO_BASIC,
    SCENARIO_EMPTY,
    SCENARIO_NO_DATES,
    JiraScenario,
    JiraSyntheticIssue,
    get_scenario_by_name,
    list_all_scenarios,
)


class TestScenarioStructure:
    """Test that scenarios have correct structure and required fields."""

    def test_scenario_basic_structure(self):
        """Verify SCENARIO_BASIC has all required fields."""
        assert SCENARIO_BASIC.name == "SCENARIO_BASIC"
        assert SCENARIO_BASIC.description
        assert SCENARIO_BASIC.jql_query
        assert SCENARIO_BASIC.labels == ["trustyai"]
        assert len(SCENARIO_BASIC.issues) == 7
        assert SCENARIO_BASIC.expected_output is not None
        assert len(SCENARIO_BASIC.expected_output) > 0

    def test_scenario_no_dates_structure(self):
        """Verify SCENARIO_NO_DATES has all required fields."""
        assert SCENARIO_NO_DATES.name == "SCENARIO_NO_DATES"
        assert SCENARIO_NO_DATES.description
        assert SCENARIO_NO_DATES.jql_query
        assert SCENARIO_NO_DATES.labels == ["model-serving"]
        assert len(SCENARIO_NO_DATES.issues) == 3
        assert SCENARIO_NO_DATES.expected_output is not None

    def test_scenario_empty_structure(self):
        """Verify SCENARIO_EMPTY has all required fields."""
        assert SCENARIO_EMPTY.name == "SCENARIO_EMPTY"
        assert SCENARIO_EMPTY.description
        assert SCENARIO_EMPTY.jql_query
        assert SCENARIO_EMPTY.labels == ["nonexistent-label-12345"]
        assert len(SCENARIO_EMPTY.issues) == 0
        assert SCENARIO_EMPTY.expected_output is not None


class TestScenarioBasicDataDistribution:
    """Test that SCENARIO_BASIC has correct temporal distribution."""

    def test_basic_has_current_quarter_issues(self):
        """Verify SCENARIO_BASIC has issues in current quarter."""
        current_q_issues = [issue for issue in SCENARIO_BASIC.issues if issue.key in ["SYNTHETIC-001", "SYNTHETIC-002"]]
        assert len(current_q_issues) == 2
        assert all(issue.due_date is not None for issue in current_q_issues)

    def test_basic_has_next_quarter_issues(self):
        """Verify SCENARIO_BASIC has issues in next quarter."""
        next_q_issues = [issue for issue in SCENARIO_BASIC.issues if issue.key in ["SYNTHETIC-003", "SYNTHETIC-004", "SYNTHETIC-005"]]
        assert len(next_q_issues) == 3
        assert all(issue.due_date is not None for issue in next_q_issues)

    def test_basic_has_half_year_issues(self):
        """Verify SCENARIO_BASIC has issues in next half-year."""
        half_year_issues = [issue for issue in SCENARIO_BASIC.issues if issue.key in ["SYNTHETIC-006", "SYNTHETIC-007"]]
        assert len(half_year_issues) == 2
        assert all(issue.due_date is not None for issue in half_year_issues)

    def test_basic_issue_statuses_are_realistic(self):
        """Verify SCENARIO_BASIC has realistic status progression."""
        # Current quarter: In Progress
        assert SCENARIO_BASIC.issues[0].status == "In Progress"
        assert SCENARIO_BASIC.issues[1].status == "In Progress"

        # Next quarter: To Do
        assert SCENARIO_BASIC.issues[2].status == "To Do"
        assert SCENARIO_BASIC.issues[3].status == "To Do"
        assert SCENARIO_BASIC.issues[4].status == "To Do"

        # Next half-year: New
        assert SCENARIO_BASIC.issues[5].status == "New"
        assert SCENARIO_BASIC.issues[6].status == "New"

    def test_basic_has_target_versions(self):
        """Verify SCENARIO_BASIC issues have target versions."""
        for issue in SCENARIO_BASIC.issues:
            assert issue.target_version is not None
            assert len(issue.target_version) > 0
            # Verify RHOAI version format
            assert any("RHOAI" in version for version in issue.target_version)


class TestScenarioNoDatesValidation:
    """Test that SCENARIO_NO_DATES has issues without dates."""

    def test_all_issues_have_no_due_date(self):
        """Verify all issues in SCENARIO_NO_DATES have no due date."""
        for issue in SCENARIO_NO_DATES.issues:
            assert issue.due_date is None

    def test_all_issues_are_new_or_todo(self):
        """Verify all issues are New or To Do status."""
        for issue in SCENARIO_NO_DATES.issues:
            assert issue.status in ["New", "To Do"]

    def test_no_target_versions(self):
        """Verify issues have no target versions."""
        for issue in SCENARIO_NO_DATES.issues:
            assert issue.target_version is None


class TestScenarioEmptyValidation:
    """Test that SCENARIO_EMPTY has no issues."""

    def test_empty_has_no_issues(self):
        """Verify SCENARIO_EMPTY has no issues."""
        assert len(SCENARIO_EMPTY.issues) == 0

    def test_empty_expected_output_explains_no_results(self):
        """Verify expected output explains no results."""
        assert "No issues found" in SCENARIO_EMPTY.expected_output
        assert "nonexistent-label-12345" in SCENARIO_EMPTY.expected_output


class TestIssueDataIntegrity:
    """Test integrity and consistency of individual issues."""

    @pytest.mark.parametrize(
        "scenario",
        [SCENARIO_BASIC, SCENARIO_NO_DATES],
        ids=["SCENARIO_BASIC", "SCENARIO_NO_DATES"],
    )
    def test_all_issues_have_required_fields(self, scenario):
        """Verify all issues have required fields populated."""
        for issue in scenario.issues:
            assert issue.key
            assert issue.summary
            assert issue.description
            assert issue.status
            assert issue.priority
            assert issue.reporter  # Reporter is always present
            assert issue.created_date
            assert issue.updated_date
            assert isinstance(issue.components, list)
            assert isinstance(issue.labels, list)
            assert len(issue.labels) > 0  # At least one label

    @pytest.mark.parametrize(
        "scenario",
        [SCENARIO_BASIC, SCENARIO_NO_DATES],
        ids=["SCENARIO_BASIC", "SCENARIO_NO_DATES"],
    )
    def test_keys_are_unique(self, scenario):
        """Verify all issue keys are unique within a scenario."""
        keys = [issue.key for issue in scenario.issues]
        assert len(keys) == len(set(keys))

    @pytest.mark.parametrize(
        "scenario",
        [SCENARIO_BASIC, SCENARIO_NO_DATES],
        ids=["SCENARIO_BASIC", "SCENARIO_NO_DATES"],
    )
    def test_keys_follow_format(self, scenario):
        """Verify issue keys follow SYNTHETIC-XXX format."""
        for issue in scenario.issues:
            assert issue.key.startswith("SYNTHETIC-")
            parts = issue.key.split("-")
            assert len(parts) == 2
            assert parts[1].isdigit()

    @pytest.mark.parametrize(
        "scenario",
        [SCENARIO_BASIC, SCENARIO_NO_DATES],
        ids=["SCENARIO_BASIC", "SCENARIO_NO_DATES"],
    )
    def test_dates_are_parseable(self, scenario):
        """Verify date fields can be parsed as ISO datetime."""
        for issue in scenario.issues:
            if issue.created_date:
                datetime.fromisoformat(issue.created_date.replace("+00:00", ""))
            if issue.updated_date:
                datetime.fromisoformat(issue.updated_date.replace("+00:00", ""))
            if issue.due_date:
                datetime.fromisoformat(issue.due_date)

    def test_basic_dates_are_chronologically_ordered(self):
        """Verify SCENARIO_BASIC issues have dates in temporal order."""
        # Current quarter issues should have earlier due dates than next quarter
        current_q_dates = [datetime.fromisoformat(issue.due_date) for issue in SCENARIO_BASIC.issues[:2]]
        next_q_dates = [datetime.fromisoformat(issue.due_date) for issue in SCENARIO_BASIC.issues[2:5]]
        half_year_dates = [datetime.fromisoformat(issue.due_date) for issue in SCENARIO_BASIC.issues[5:7]]

        # Check temporal ordering
        assert max(current_q_dates) < min(next_q_dates)
        assert max(next_q_dates) < min(half_year_dates)


class TestScenarioExpectedOutputs:
    """Test that expected outputs have correct structure."""

    def test_basic_expected_output_has_required_sections(self):
        """Verify SCENARIO_BASIC expected output has all sections."""
        output = SCENARIO_BASIC.expected_output

        # Check H1 title
        assert "# Red Hat AI Roadmap - TrustyAI" in output

        # Check H2 sections
        assert "## Releases" in output
        assert "## Current Quarter:" in output
        assert "## Next Quarter:" in output
        assert "## Next Half-Year:" in output

    def test_basic_expected_output_has_all_issue_keys(self):
        """Verify expected output mentions all issue keys."""
        output = SCENARIO_BASIC.expected_output

        for issue in SCENARIO_BASIC.issues:
            assert issue.key in output

    def test_basic_expected_output_has_jira_links(self):
        """Verify expected output has JIRA links for all issues."""
        output = SCENARIO_BASIC.expected_output

        for issue in SCENARIO_BASIC.issues:
            expected_link = f"https://issues.redhat.com/browse/{issue.key}"
            assert expected_link in output

    def test_no_dates_expected_output_explains_placement(self):
        """Verify SCENARIO_NO_DATES expected output explains why issues are in half-year."""
        output = SCENARIO_NO_DATES.expected_output

        # Should note lack of dates
        assert "lack specific target dates" in output or "Note" in output

        # Should have all issues
        for issue in SCENARIO_NO_DATES.issues:
            assert issue.key in output


class TestHelperFunctions:
    """Test helper functions for accessing scenarios."""

    def test_get_scenario_by_name(self):
        """Test getting scenarios by name."""
        assert get_scenario_by_name("SCENARIO_BASIC") == SCENARIO_BASIC
        assert get_scenario_by_name("SCENARIO_NO_DATES") == SCENARIO_NO_DATES
        assert get_scenario_by_name("SCENARIO_EMPTY") == SCENARIO_EMPTY
        assert get_scenario_by_name("NONEXISTENT") is None

    def test_list_all_scenarios(self):
        """Test listing all available scenarios."""
        scenarios = list_all_scenarios()
        assert len(scenarios) == 3
        assert SCENARIO_BASIC in scenarios
        assert SCENARIO_NO_DATES in scenarios
        assert SCENARIO_EMPTY in scenarios

    def test_all_scenarios_are_scenario_instances(self):
        """Verify all scenarios are JiraScenario instances."""
        for scenario in list_all_scenarios():
            assert isinstance(scenario, JiraScenario)

    def test_all_issues_are_issue_instances(self):
        """Verify all issues are JiraSyntheticIssue instances."""
        for scenario in list_all_scenarios():
            for issue in scenario.issues:
                assert isinstance(issue, JiraSyntheticIssue)
