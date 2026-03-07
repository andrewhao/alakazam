# Tech Stack: Alakazam

## Core Language & Package Management
- **Python (>=3.10)**: Leveraging modern async features and type hinting for a robust, performant core.
- **uv**: The preferred choice for ultra-fast dependency management, environment isolation, and project execution.

## CLI & User Interface
- **Click**: For a powerful, modular, and well-structured CLI interface.
- **Rich**: For high-signal, visually engaging terminal output, progress bars, and formatted data tables.

## Data & Validation
- **Pydantic (v2)**: Providing high-performance data validation and configuration management.
- **PyYAML**: For flexible, user-friendly configuration file support.

## Document & File Processing
- **pypdf**: For efficient PDF content extraction and metadata analysis.
- **aiofiles**: For non-blocking asynchronous file operations, essential for high-performance batch processing.

## AI & Intelligence
- **Anthropic (Claude)**, **OpenAI (GPT)** & **Google (Gemini)**: Multi-model support for intelligent document analysis.
- **Google Generative AI SDK**: For official Gemini model integration.
- **Plugin Architecture**: Modular design allows for the seamless addition of new AI analyzers and naming strategies.

## Development & Quality Assurance
- **Hatchling**: Modern, standards-compliant build backend and package manager.
- **pytest**: The primary test framework, utilizing `pytest-asyncio` for async tests.
- **Mypy**: For strict static type checking to ensure code correctness and safety.
- **Ruff & Black**: For ultra-fast linting and consistent, automated code formatting.
- **uv (Execution)**: Used to run tests, linters, and the application itself to ensure environment consistency.
