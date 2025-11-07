# Contributing to Spring-Ready Python

Thanks for considering contributing! This library is intentionally simple and focused.

## Philosophy

- **Keep it simple** - No over-engineering
- **Match Spring Boot behavior** - Fail-fast, retry logic, etc.
- **Own implementation** - No hidden dependencies
- **Well-tested** - Every feature needs tests
- **Clear documentation** - Examples for everything

## Development Setup

```bash
# Clone the repo
git clone https://github.com/tcivie/spring_ready_python.git
cd spring_ready_python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,all]"

# Run tests
pytest tests/

# Run example
python example.py
```

## Making Changes

1. **Fork the repository**
2. **Create a branch** - `git checkout -b feature/my-feature`
3. **Write tests** - Tests go in `tests/`
4. **Make changes** - Keep it focused
5. **Run tests** - `pytest tests/`
6. **Update docs** - If adding features
7. **Submit PR** - Describe what and why

## Code Style

- Use type hints where it makes sense
- Follow PEP 8 (but don't be annoying about it)
- Keep functions small and focused
- Comment the "why", not the "what"
- Match Spring Boot naming conventions where possible

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=spring_ready --cov-report=html

# Run specific test
pytest tests/test_basic.py::TestRetry
```

## What We're Looking For

✅ **Bug fixes** - Always welcome  
✅ **Better error messages** - Help users debug  
✅ **Performance improvements** - If measurable  
✅ **Documentation fixes** - Typos, clarity, examples  
✅ **More tests** - Increase coverage  

## What We're NOT Looking For

❌ **New frameworks** - FastAPI only for now  
❌ **Complex features** - Keep it simple  
❌ **Breaking changes** - Unless absolutely necessary  
❌ **Dependencies** - Avoid adding new ones  
❌ **Runtime config refresh** - Out of scope  

## Questions?

Open an issue first if you're unsure whether a feature fits.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
