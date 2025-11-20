"""Backstage contribution helper toolkit."""

from typing import Optional

from agno.tools import Toolkit


class BackstageToolkit(Toolkit):
    """Toolkit for Backstage upstream contribution guidance."""

    def __init__(self, github_token: Optional[str] = None):
        """Initialize BackstageToolkit.

        Args:
            github_token: GitHub PAT for API access (optional for public repos)
        """
        super().__init__(name="backstage_toolkit")
        self.github_token = github_token
        self.register(self.get_contribution_guide)
        self.register(self.check_repo_structure)
        self.register(self.validate_pr_requirements)
        self.register(self.get_development_setup)
        self.register(self.find_good_first_issues)

    def get_contribution_guide(self, repo: str = "backstage") -> str:
        """Get contribution guidelines for Backstage repositories.

        Args:
            repo: Repository name ('backstage' or 'community-plugins')

        Returns:
            Contribution guidelines and best practices
        """
        guides = {
            "backstage": """# Backstage Core Contribution Guide

**Repository**: https://github.com/backstage/backstage

## Key Requirements
1. **CLA**: Sign the Contributor License Agreement
2. **Changesets**: All PRs need changesets (`yarn changeset`)
3. **Tests**: Unit tests required for all changes
4. **Code Style**: ESLint + Prettier (run `yarn lint:all`)
5. **Commits**: Conventional commits preferred

## PR Process
1. Fork and create feature branch
2. Make changes with tests
3. Run `yarn changeset` to document changes
4. Submit PR with clear description
5. Address review feedback
6. Wait for maintainer approval

## Common Mistakes
- Forgetting changeset files
- Not running linters before PR
- Large PRs without prior discussion
- Missing tests for new features

## Resources
- CONTRIBUTING.md: https://github.com/backstage/backstage/blob/master/CONTRIBUTING.md
- Discord: https://discord.gg/backstage
""",
            "community-plugins": """# Backstage Community Plugins Contribution Guide

**Repository**: https://github.com/backstage/community-plugins

## Key Requirements
1. **CLA**: Sign the Contributor License Agreement
2. **Changesets**: Required for all changes
3. **Plugin Structure**: Follow workspaces structure
4. **Documentation**: README.md required for new plugins
5. **Tests**: Unit + integration tests

## Plugin Submission
1. New plugins go in `workspaces/` directory
2. Use plugin template for structure
3. Include comprehensive README
4. Add to plugin catalog
5. Provide working examples

## PR Process
1. Discuss new plugins in Discord first
2. Fork and create branch
3. Develop with tests
4. Add changeset
5. Submit PR with demo/screenshots
6. Respond to reviews

## Common Mistakes
- Not following plugin template
- Missing documentation
- No examples or demos
- Incomplete test coverage

## Resources
- CONTRIBUTING.md: https://github.com/backstage/community-plugins/blob/main/CONTRIBUTING.md
- Plugin Guidelines: Check repo docs
- Discord: https://discord.gg/backstage
""",
        }

        return guides.get(repo, "Unknown repository. Use 'backstage' or 'community-plugins'")

    def check_repo_structure(self, plugin_name: str, repo: str = "community-plugins") -> str:
        """Check if plugin follows correct repository structure.

        Args:
            plugin_name: Name of the plugin (e.g., 'my-plugin')
            repo: Target repository ('backstage' or 'community-plugins')

        Returns:
            Structure validation guidance
        """
        if repo == "community-plugins":
            return f"""# Plugin Structure for '{plugin_name}'

## Expected Structure
```
workspaces/{plugin_name}/
├── plugins/
│   └── {plugin_name}/
│       ├── src/
│       ├── package.json
│       ├── README.md
│       └── tsconfig.json
├── package.json (workspace config)
└── README.md (workspace overview)
```

## Required Files
- ✅ `plugins/{plugin_name}/package.json`: Plugin manifest
- ✅ `plugins/{plugin_name}/README.md`: Documentation
- ✅ `plugins/{plugin_name}/src/index.ts`: Entry point
- ✅ `.changeset/` files: For versioning

## Validation Steps
1. Check package.json has correct name: `@backstage-community/{plugin_name}`
2. Verify exports in src/index.ts
3. Ensure README has setup instructions
4. Confirm tests exist in src/**/*.test.ts
5. Run `yarn install` and `yarn tsc` to verify build

## Next Steps
- Run `yarn lint:all` to check code style
- Run `yarn test` to verify tests pass
- Add changeset: `yarn changeset`
"""
        else:
            return f"""# Core Backstage Structure

Plugins in backstage/backstage follow monorepo structure:
```
plugins/{plugin_name}/
├── src/
├── package.json
├── README.md
└── config.d.ts (if needed)
```

Refer to existing plugins for patterns.
"""

    def validate_pr_requirements(self, has_changeset: bool = False, has_tests: bool = False,
                                 passes_lint: bool = False, repo: str = "backstage") -> str:
        """Validate if PR meets contribution requirements.

        Args:
            has_changeset: Whether changeset files are present
            has_tests: Whether tests are included
            passes_lint: Whether code passes linting
            repo: Target repository

        Returns:
            PR readiness checklist
        """
        status = "✅" if all([has_changeset, has_tests, passes_lint]) else "❌"

        return f"""# PR Readiness Check ({repo})

{status} **Overall Status**: {'Ready' if all([has_changeset, has_tests, passes_lint]) else 'Not Ready'}

## Checklist
- {'✅' if has_changeset else '❌'} **Changeset**: {'Present' if has_changeset else 'MISSING - Run `yarn changeset`'}
- {'✅' if has_tests else '❌'} **Tests**: {'Included' if has_tests else 'MISSING - Add unit tests'}
- {'✅' if passes_lint else '❌'} **Linting**: {'Passing' if passes_lint else 'FAILING - Run `yarn lint:all --fix`'}

## Additional Requirements
- [ ] CLA signed (auto-checked by bot)
- [ ] PR description explains changes
- [ ] Breaking changes documented (if any)
- [ ] Examples/screenshots provided (for UI changes)

## Before Submitting
```bash
# Run these commands
yarn install          # Update dependencies
yarn tsc             # Type check
yarn lint:all        # Lint code
yarn test            # Run tests
yarn changeset       # Add changeset
```

## Common Issues
- **Changeset missing**: PRs won't merge without it
- **Tests failing**: Check `yarn test` output
- **Lint errors**: Run `yarn lint:all --fix` to auto-fix
"""

    def get_development_setup(self, repo: str = "backstage") -> str:
        """Get development environment setup instructions.

        Args:
            repo: Repository name

        Returns:
            Setup instructions
        """
        setups = {
            "backstage": """# Backstage Development Setup

## Prerequisites
- Node.js 18+ (use nvm)
- Yarn 1.22+
- Git

## Setup Steps
```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/backstage.git
cd backstage

# 2. Install dependencies
yarn install

# 3. Build all packages
yarn tsc

# 4. Run tests to verify setup
yarn test

# 5. Start development (optional)
cd packages/app
yarn start
```

## Development Workflow
```bash
# Make changes to plugin/package
cd plugins/my-plugin

# Run tests in watch mode
yarn test --watch

# Type check
yarn tsc

# Lint
yarn lint

# Build
yarn build
```

## Troubleshooting
- **Install fails**: Clear `node_modules` and `yarn.lock`, re-run
- **Build fails**: Check Node.js version (18+)
- **Test fails**: Check if all deps installed

## Resources
- https://backstage.io/docs/getting-started/
""",
            "community-plugins": """# Community Plugins Development Setup

## Prerequisites
- Node.js 18+
- Yarn 1.22+
- Git

## Setup Steps
```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/community-plugins.git
cd community-plugins

# 2. Install dependencies
yarn install

# 3. Build all workspaces
yarn tsc:full

# 4. Navigate to your plugin workspace
cd workspaces/my-plugin

# 5. Run tests
yarn test
```

## Creating New Plugin
```bash
# Use plugin template
yarn new

# Follow prompts to create plugin structure
```

## Development Workflow
```bash
# In workspace directory
yarn test           # Run tests
yarn lint          # Check code style
yarn tsc           # Type check
yarn build         # Build plugin
```

## Troubleshooting
- Clear yarn cache: `yarn cache clean`
- Rebuild: `yarn clean && yarn install`
""",
        }

        return setups.get(repo, "Unknown repository")

    def find_good_first_issues(self, repo: str = "backstage") -> str:
        """Find good first issues for new contributors.

        Args:
            repo: Repository name

        Returns:
            Links and guidance for finding issues
        """
        return f"""# Finding Good First Issues

## GitHub Issue Links
- **{repo} good first issues**: https://github.com/backstage/{repo}/labels/good%20first%20issue
- **Help wanted**: https://github.com/backstage/{repo}/labels/help%20wanted
- **All issues**: https://github.com/backstage/{repo}/issues

## Tips for Choosing
1. **Start small**: Pick issues labeled 'good first issue'
2. **Check activity**: Recent comments = active issue
3. **Ask first**: Comment to claim issue before starting
4. **Read context**: Check linked PRs/discussions

## Where to Get Help
- **Discord**: https://discord.gg/backstage
  - #contributing channel for questions
  - #general for community help
- **GitHub Discussions**: https://github.com/backstage/{repo}/discussions

## Suggested First Contributions
- Documentation improvements
- Test coverage additions
- Bug fixes with clear reproduction
- TypeScript type improvements

## Before Starting
- Comment on issue to indicate you're working on it
- Ask maintainers if approach is acceptable
- Join Discord to discuss if unsure
"""
