# Git Workflow Strategy for FeedIT

## Branching Model
- `main`: Production-ready code only.
- `develop`: Integration branch for features.
- `feature/*`: Feature branches from `develop`.
- `hotfix/*`: Urgent patches off `main`.

## Commit Guidelines
- Use conventional commits: `feat:`, `fix:`, `docs:`, etc.
- Write clear, concise commit messages.

## Pull Request Process
- One PR per feature or fix.
- At least one review required before merge.
- Resolve merge conflicts proactively.

## CI/CD Integration
- GitHub Actions automatically runs tests and linters.
- Security scanning via Bandit, Grype, and ZAP post-deploy.

## Tagging & Releases
- Tags follow semantic v

