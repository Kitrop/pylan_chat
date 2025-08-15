# 🚀 CI/CD Setup Guide for LANChat

## Overview
This project includes a comprehensive CI/CD pipeline that automatically:
- ✅ Lints and checks code quality
- ✅ Runs tests on multiple Python versions and platforms
- ✅ Builds executables for Windows, macOS, and Linux
- ✅ Performs security scans
- ✅ Creates releases with artifacts
- ✅ Updates dependencies automatically

## Quick Start

### 1. Repository Setup
1. Push your code to GitHub
2. Enable GitHub Actions in your repository settings
3. Set up branch protection rules for `main` branch

### 2. Required Secrets
Add these secrets in your GitHub repository settings:

```bash
# For releases (optional)
GITHUB_TOKEN  # Automatically available

# For deployment (if needed)
DEPLOY_KEY    # SSH key for deployment
DEPLOY_HOST   # Deployment server hostname
DEPLOY_USER   # Deployment server username
```

### 3. Branch Protection Rules
Set up branch protection for `main`:
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Require pull request reviews before merging
- ✅ Include administrators in restrictions

## Pipeline Stages

### 🔍 Lint & Quality Check
- **Tools**: flake8, isort, mypy, pylint
- **Trigger**: Every push and PR
- **Duration**: ~2-3 minutes

### 🧪 Testing
- **Platforms**: Ubuntu, Windows, macOS
- **Python Versions**: 3.9, 3.10, 3.11, 3.12
- **Coverage**: Codecov integration
- **Duration**: ~10-15 minutes

### 🔨 Building
- **Platforms**: Windows (.exe), macOS (binary), Linux (binary)
- **Tool**: PyInstaller
- **Artifacts**: Uploaded to GitHub Actions
- **Duration**: ~5-10 minutes per platform

### 🔒 Security Scan
- **Tools**: Bandit, Safety
- **Schedule**: Weekly + on PR
- **Reports**: JSON and text formats
- **Duration**: ~2-3 minutes

### 🚀 Release
- **Trigger**: GitHub release creation
- **Assets**: All platform executables
- **Duration**: ~5 minutes

## Local Development

### Install Development Dependencies
```bash
pip install -e ".[dev]"
```

### Run Tests Locally
```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_main.py

# GUI tests only
pytest -m gui
```

### Code Quality Checks
```bash
# Format code
isort .

# Lint code
flake8 .
pylint **/*.py

# Type checking
mypy .

# Security scan
bandit -r .
safety check
```

### Build Locally
```bash
# Windows
python scripts/build_windows.py

# macOS
python scripts/build_macos.py

# Linux
python scripts/build_linux.py
```

## Configuration Files

### `.github/workflows/ci-cd.yml`
Main CI/CD pipeline with all stages.

### `.github/workflows/security.yml`
Security scanning workflow.

### `.github/dependabot.yml`
Automatic dependency updates.

### `pyproject.toml`
Modern Python project configuration.

### `.flake8`
Code linting configuration.

### `pytest.ini`
Testing configuration.

## Troubleshooting

### Common Issues

#### 1. Tests Failing
```bash
# Check test output
pytest -v

# Run specific failing test
pytest tests/test_main.py::TestServiceController::test_init -v
```

#### 2. Build Failures
```bash
# Check PyInstaller logs
python scripts/build_windows.py --debug

# Verify dependencies
pip install -r requirements.txt
```

#### 3. Linting Errors
```bash
# Auto-fix formatting
isort .

# Check specific files
flake8 main.py
```

### Performance Optimization

#### 1. Cache Dependencies
The pipeline uses GitHub Actions cache for:
- Python packages
- PyInstaller cache
- Build artifacts

#### 2. Parallel Execution
- Tests run in parallel across platforms
- Builds run in parallel for different platforms
- Security scans run independently

#### 3. Conditional Execution
- GUI tests only run on Linux
- Release creation only on release events
- Security scans scheduled weekly

## Customization

### Add New Test
1. Create test file in `tests/`
2. Follow naming convention: `test_*.py`
3. Use pytest fixtures and markers
4. Add to appropriate test category

### Modify Build Process
1. Edit `scripts/build_*.py` files
2. Update PyInstaller parameters
3. Test locally before pushing

### Add New Platform
1. Add platform to matrix in CI/CD
2. Create build script
3. Update release assets upload

### Custom Dependencies
1. Add to `pyproject.toml`
2. Update `requirements.txt`
3. Test in CI/CD pipeline

## Monitoring

### GitHub Actions Dashboard
- View all workflow runs
- Check specific job logs
- Download artifacts
- Monitor performance

### Code Coverage
- Integrated with Codecov
- Coverage reports in PRs
- Historical coverage tracking

### Security Alerts
- Automatic vulnerability scanning
- Dependency update notifications
- Security report artifacts

## Best Practices

### 1. Commit Messages
```
feat: add new chat feature
fix: resolve file upload issue
docs: update README
test: add GUI tests
ci: update workflow
```

### 2. Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `hotfix/*`: Critical fixes

### 3. Pull Requests
- Use provided template
- Add tests for new features
- Update documentation
- Request reviews

### 4. Releases
- Use semantic versioning
- Create GitHub releases
- Include changelog
- Tag releases properly

## Support

For issues with the CI/CD pipeline:
1. Check GitHub Actions logs
2. Review configuration files
3. Test locally first
4. Create issue with detailed information

## Contributing

When contributing to the CI/CD setup:
1. Test changes locally
2. Update documentation
3. Follow existing patterns
4. Add appropriate tests
