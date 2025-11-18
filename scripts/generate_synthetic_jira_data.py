"""
Generate synthetic JIRA data for testing RHAI Roadmap Publisher accuracy evaluations.

This script connects to JIRA, fetches real issues, anonymizes sensitive information,
and exports them as Python test fixtures.

Usage:
    python scripts/generate_synthetic_jira_data.py \\
        --project RHAISTRAT \\
        --labels "trustyai" \\
        --output tests/fixtures/scenario_trustyai.py

Environment Variables:
    JIRA_API_TOKEN: JIRA personal access token
    JIRA_SERVER_URL: JIRA server URL (default: https://issues.redhat.com)
    JIRA_USERNAME: JIRA username (optional, for basic auth)
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from faker import Faker
from jira import JIRA

# Initialize Faker for generating realistic synthetic data
fake = Faker()


class JiraDataAnonymizer:
    """Anonymize JIRA data while preserving structure and relationships."""

    def __init__(self, seed: int = 42):
        """Initialize anonymizer with consistent seed for reproducibility.

        Args:
            seed: Random seed for Faker (default: 42 for reproducibility)
        """
        Faker.seed(seed)
        self.fake = Faker()
        self.user_mapping: dict[str, str] = {}  # Real username -> Synthetic username
        self.key_mapping: dict[str, str] = {}  # Real key -> Synthetic key
        self.key_counter = 1

    def anonymize_user(self, real_username: str | None) -> str | None:
        """Convert real username to consistent synthetic username.

        Args:
            real_username: Real JIRA username

        Returns:
            Synthetic username (e.g., "User_A", "User_B")
        """
        if real_username is None:
            return None

        if real_username not in self.user_mapping:
            # Generate synthetic username
            user_id = chr(65 + len(self.user_mapping))  # A, B, C, ...
            self.user_mapping[real_username] = f"User_{user_id}"

        return self.user_mapping[real_username]

    def anonymize_key(self, real_key: str, project: str = "SYNTHETIC") -> str:
        """Convert real JIRA key to synthetic key.

        Args:
            real_key: Real JIRA key (e.g., "RHAISTRAT-123")
            project: Synthetic project prefix (default: "SYNTHETIC")

        Returns:
            Synthetic JIRA key (e.g., "SYNTHETIC-001")
        """
        if real_key not in self.key_mapping:
            synthetic_key = f"{project}-{self.key_counter:03d}"
            self.key_mapping[real_key] = synthetic_key
            self.key_counter += 1

        return self.key_mapping[real_key]

    def anonymize_text(self, text: str | None, preserve_structure: bool = True) -> str:
        """Anonymize text content while optionally preserving structure.

        Args:
            text: Original text
            preserve_structure: If True, preserve sentence count and approximate length

        Returns:
            Anonymized text
        """
        if not text:
            return ""

        if preserve_structure:
            # Split into sentences and generate similar-length synthetic text
            sentences = text.split(". ")
            synthetic_sentences = []

            for sentence in sentences:
                # Generate synthetic sentence of similar length
                word_count = len(sentence.split())
                synthetic_sentence = " ".join(self.fake.words(nb=max(3, word_count)))
                synthetic_sentences.append(synthetic_sentence.capitalize())

            return ". ".join(synthetic_sentences) + "."
        else:
            # Simple replacement with Lorem Ipsum
            return self.fake.text(max_nb_chars=len(text))


def fetch_jira_issues(
    jira_client: JIRA,
    project: str,
    labels: list[str] | None = None,
    max_results: int = 50,
) -> list[Any]:
    """Fetch JIRA issues matching criteria.

    Args:
        jira_client: JIRA client instance
        project: JIRA project key
        labels: List of labels to filter by (optional)
        max_results: Maximum number of issues to fetch

    Returns:
        List of JIRA Issue objects
    """
    # Build JQL query
    jql_parts = [f"project = {project}"]

    if labels:
        label_conditions = " OR ".join([f'labels = "{label}"' for label in labels])
        jql_parts.append(f"({label_conditions})")

    # Order by creation date for consistent results
    jql = " AND ".join(jql_parts) + " ORDER BY created DESC"

    print(f"Fetching issues with JQL: {jql}")

    # Fetch issues with all relevant fields
    issues = jira_client.search_issues(
        jql,
        maxResults=max_results,
        fields=[
            "summary",
            "description",
            "status",
            "priority",
            "assignee",
            "reporter",
            "created",
            "updated",
            "components",
            "labels",
            "customfield_12311240",  # Target Version
            "customfield_12315948",  # Product Manager
            "duedate",
        ],
    )

    print(f"Fetched {len(issues)} issues")
    return issues


def convert_issue_to_dict(issue: Any, anonymizer: JiraDataAnonymizer) -> dict[str, Any]:
    """Convert JIRA Issue object to anonymized dictionary.

    Args:
        issue: JIRA Issue object
        anonymizer: JiraDataAnonymizer instance

    Returns:
        Dictionary with anonymized issue data
    """
    # Extract basic fields
    summary = getattr(issue.fields, "summary", "")
    description = getattr(issue.fields, "description", "")
    status = getattr(issue.fields.status, "name", "Unknown") if hasattr(issue.fields, "status") else "Unknown"
    priority = getattr(issue.fields.priority, "name", "Unknown") if hasattr(issue.fields, "priority") else "Unknown"

    # Extract user fields
    assignee = None
    if hasattr(issue.fields, "assignee") and issue.fields.assignee:
        assignee = getattr(issue.fields.assignee, "displayName", None)

    reporter = None
    if hasattr(issue.fields, "reporter") and issue.fields.reporter:
        reporter = getattr(issue.fields.reporter, "displayName", None)

    # Extract dates
    created_date = getattr(issue.fields, "created", None)
    updated_date = getattr(issue.fields, "updated", None)
    due_date = getattr(issue.fields, "duedate", None)

    # Extract components
    components = []
    if hasattr(issue.fields, "components"):
        components = [c.name for c in issue.fields.components]

    # Extract labels
    labels = getattr(issue.fields, "labels", [])

    # Extract custom fields
    target_version = None
    if hasattr(issue.fields, "customfield_12311240") and issue.fields.customfield_12311240:
        if isinstance(issue.fields.customfield_12311240, list):
            target_version = [v for v in issue.fields.customfield_12311240]
        else:
            target_version = [issue.fields.customfield_12311240]

    product_manager = None
    if hasattr(issue.fields, "customfield_12315948") and issue.fields.customfield_12315948:
        product_manager = getattr(issue.fields.customfield_12315948, "displayName", None)

    # Anonymize
    return {
        "key": anonymizer.anonymize_key(issue.key),
        "summary": anonymizer.anonymize_text(summary, preserve_structure=True),
        "description": anonymizer.anonymize_text(description, preserve_structure=True),
        "status": status,  # Keep status as-is
        "priority": priority,  # Keep priority as-is
        "assignee": anonymizer.anonymize_user(assignee),
        "reporter": anonymizer.anonymize_user(reporter),
        "created_date": created_date,
        "updated_date": updated_date,
        "due_date": due_date,
        "components": components,  # Keep components as-is
        "labels": labels,  # Keep labels as-is
        "target_version": target_version,
        "product_manager": anonymizer.anonymize_user(product_manager),
    }


def export_to_python_fixture(
    issues: list[dict[str, Any]],
    output_path: Path,
    scenario_name: str,
    labels: list[str] | None = None,
) -> None:
    """Export anonymized issues as Python test fixture.

    Args:
        issues: List of anonymized issue dictionaries
        output_path: Path to output file
        scenario_name: Name of the scenario (e.g., "SCENARIO_BASIC")
        labels: Original labels used in query
    """
    # Generate fixture content
    content = [
        '"""Synthetic JIRA data for RHAI Roadmap Publisher accuracy evaluations.',
        "",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Issues count: {len(issues)}",
        '"""',
        "",
        "from dataclasses import dataclass",
        "from typing import Any",
        "",
        "",
        "@dataclass",
        "class JiraSyntheticIssue:",
        '    """Represents a synthetic JIRA issue for testing."""',
        "",
        "    key: str",
        "    summary: str",
        "    description: str",
        "    status: str",
        "    priority: str",
        "    assignee: str | None",
        "    reporter: str | None",
        "    created_date: str | None",
        "    updated_date: str | None",
        "    due_date: str | None",
        "    components: list[str]",
        "    labels: list[str]",
        "    target_version: list[str] | None",
        "    product_manager: str | None",
        "",
        "",
        "@dataclass",
        "class JiraScenario:",
        '    """Represents a test scenario with JIRA data and expected output."""',
        "",
        "    name: str",
        "    jql_query: str",
        "    labels: list[str]",
        "    issues: list[JiraSyntheticIssue]",
        "    expected_output: str | None = None",
        "",
        "",
        f"# Scenario: {scenario_name}",
        f"{scenario_name} = JiraScenario(",
        f'    name="{scenario_name}",',
    ]

    # Add JQL query
    if labels:
        label_str = " OR ".join([f'labels = "{label}"' for label in labels])
        content.append(f'    jql_query="project IN (RHAISTRAT, RHOAISTRAT) AND ({label_str}) ORDER BY duedate ASC",')
    else:
        content.append('    jql_query="project IN (RHAISTRAT, RHOAISTRAT) ORDER BY duedate ASC",')

    # Add labels
    if labels:
        content.append(f"    labels={labels!r},")
    else:
        content.append("    labels=[],")

    # Add issues
    content.append("    issues=[")

    for issue in issues:
        content.append("        JiraSyntheticIssue(")
        content.append(f'            key="{issue["key"]}",')
        content.append(f"            summary={issue['summary']!r},")
        content.append(f"            description={issue['description']!r},")
        content.append(f'            status="{issue["status"]}",')
        content.append(f'            priority="{issue["priority"]}",')
        content.append(f"            assignee={issue['assignee']!r},")
        content.append(f"            reporter={issue['reporter']!r},")
        content.append(f"            created_date={issue['created_date']!r},")
        content.append(f"            updated_date={issue['updated_date']!r},")
        content.append(f"            due_date={issue['due_date']!r},")
        content.append(f"            components={issue['components']!r},")
        content.append(f"            labels={issue['labels']!r},")
        content.append(f"            target_version={issue['target_version']!r},")
        content.append(f"            product_manager={issue['product_manager']!r},")
        content.append("        ),")

    content.append("    ],")
    content.append("    expected_output=None,  # To be filled in manually based on agent output")
    content.append(")")

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(content))
    print(f"\n✅ Fixture written to: {output_path}")
    print(f"   Issues: {len(issues)}")
    print("   Next step: Review and add expected_output markdown")


def main():
    """Main entry point for synthetic data generation."""
    parser = argparse.ArgumentParser(description="Generate synthetic JIRA data for RHAI Roadmap Publisher evaluations")
    parser.add_argument(
        "--project",
        required=True,
        help="JIRA project key (e.g., RHAISTRAT)",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        help='JIRA labels to filter by (e.g., "trustyai" "modelmesh")',
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of issues to fetch (default: 50)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output path for Python fixture file",
    )
    parser.add_argument(
        "--scenario-name",
        default="SCENARIO",
        help="Name for the scenario constant (default: SCENARIO)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for anonymization (default: 42)",
    )

    args = parser.parse_args()

    # Check environment variables
    jira_token = os.getenv("JIRA_API_TOKEN")
    jira_server = os.getenv("JIRA_SERVER_URL", "https://issues.redhat.com")
    jira_username = os.getenv("JIRA_USERNAME")

    if not jira_token:
        print("❌ Error: JIRA_API_TOKEN environment variable not set")
        print("\nSet your JIRA personal access token:")
        print("  export JIRA_API_TOKEN=your_token_here")
        sys.exit(1)

    print(f"🔍 Connecting to JIRA: {jira_server}")

    # Connect to JIRA
    try:
        if jira_username:
            jira_client = JIRA(server=jira_server, basic_auth=(jira_username, jira_token))
        else:
            jira_client = JIRA(server=jira_server, token_auth=jira_token)

        print("✅ Connected to JIRA")
    except Exception as e:
        print(f"❌ Failed to connect to JIRA: {e}")
        sys.exit(1)

    # Fetch issues
    try:
        issues = fetch_jira_issues(
            jira_client,
            project=args.project,
            labels=args.labels,
            max_results=args.max_results,
        )
    except Exception as e:
        print(f"❌ Failed to fetch issues: {e}")
        sys.exit(1)

    if not issues:
        print("⚠️  No issues found matching criteria")
        sys.exit(0)

    # Anonymize issues
    print(f"\n🔒 Anonymizing {len(issues)} issues...")
    anonymizer = JiraDataAnonymizer(seed=args.seed)
    anonymized_issues = [convert_issue_to_dict(issue, anonymizer) for issue in issues]

    # Export to fixture
    export_to_python_fixture(
        anonymized_issues,
        output_path=args.output,
        scenario_name=args.scenario_name,
        labels=args.labels,
    )

    print("\n✨ Done!")
    print("\nNext steps:")
    print(f"1. Review the generated fixture: {args.output}")
    print("2. Run the agent with this scenario to generate expected output")
    print("3. Add the expected output markdown to the fixture's expected_output field")
    print("4. Create test cases using this fixture in tests/test_rhai_roadmap_accuracy.py")


if __name__ == "__main__":
    main()
