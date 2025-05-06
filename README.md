# integrations

Common utilities enabling interaction with specific tools.

## Installation

### pip install from source

```bash
pip install git+https://github.com/BuckyI/integrations.git


# or:
git clone https://github.com/BuckyI/integrations.git
cd integrations
pip install .

# install optional dependencies:
pip install "integrations[notion,llm] @ git+https://github.com/BuckyI/integrations.git"
```

### add to `requirements.txt`

```txt
integrations @ git+https://github.com/BuckyI/integrations.git
integrations[notion] @ git+https://github.com/BuckyI/integrations.git  # with optional dependencies
```

`pip install -r requirements.txt` to install.

### add to `pyproject.toml`

```toml
[project]
dependencies = ["integrations"]

[tool.uv.sources]
integrations = { git = "https://github.com/BuckyI/integrations.git" }

[tool.poetry.dependencies]
integrations = { git = "https://github.com/BuckyI/integrations.git" }
```

If you use uv:

```bash
pip install uv
uv pip install -r pyproject.toml
```

Note by default, the minimum dependencies are installed. Refer to `[project.optional-dependencies]` section in `pyproject.toml` to determine your settings.

```toml
dependencies = ["integrations[notion,llm]"]
```
