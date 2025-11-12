# Python Upgrade Guide: macOS

**When to Upgrade**: Before starting Phase 5 development (or now if you want to align with project requirements)

**Current Status**: Python 3.9.6 (system Python)  
**Required**: Python 3.11+  
**Recommended**: Python 3.12 (latest stable)

---

## Option 1: Homebrew (Recommended for macOS)

### Step 1: Install Homebrew (if not installed)
```bash
# Check if Homebrew is installed
which brew

# If not installed, run:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Python 3.12
```bash
# Install Python 3.12
brew install python@3.12

# Verify installation
python3.12 --version
# Should show: Python 3.12.x
```

### Step 3: Update PATH (Optional but Recommended)
Add to your `~/.zshrc` (since you're using zsh):
```bash
# Add Homebrew Python to PATH (if not already there)
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Or for Intel Macs:
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Step 4: Verify Python 3.12 is Default
```bash
# Check which python3 points to
which python3
python3 --version

# If it still shows 3.9, you can create an alias or use python3.12 explicitly
```

---

## Option 2: pyenv (Recommended for Multiple Python Versions)

### Step 1: Install pyenv
```bash
# Install pyenv via Homebrew
brew install pyenv

# Add to ~/.zshrc
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# Reload shell
source ~/.zshrc
```

### Step 2: Install Python 3.12
```bash
# Install Python 3.12
pyenv install 3.12.0

# Set as global default (optional)
pyenv global 3.12.0

# Or set for this project only
cd /Users/nosenfield/Desktop/GauntletAI/Week-5-Flourish/vocabulator
pyenv local 3.12.0
```

### Step 3: Verify
```bash
python3 --version
# Should show: Python 3.12.0
```

---

## Option 3: Use Python 3.12 Directly (Quickest)

If you just want to get started quickly without changing system Python:

```bash
# Install Python 3.12 via Homebrew
brew install python@3.12

# Use python3.12 explicitly for this project
cd /Users/nosenfield/Desktop/GauntletAI/Week-5-Flourish/vocabulator
python3.12 -m venv venv
source venv/bin/activate
```

---

## After Upgrading: Set Up Project

### Step 1: Create Virtual Environment with Python 3.12
```bash
cd /Users/nosenfield/Desktop/GauntletAI/Week-5-Flourish/vocabulator

# Remove old venv if it exists (optional)
rm -rf venv

# Create new venv with Python 3.12
python3.12 -m venv venv
# Or if python3.12 is your default:
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify Python version in venv
python --version
# Should show: Python 3.12.x
```

### Step 2: Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Step 3: Verify Setup
```bash
# Run setup verification
python -m pytest tests/test_setup.py -v

# Run all standalone tests
python -m pytest tests/unit/ -v -m "not aws and not openai"
```

---

## Verification Checklist

After upgrading, verify everything works:

```bash
# 1. Check Python version
python3 --version
# Expected: Python 3.12.x (or 3.11.x minimum)

# 2. Check virtual environment Python
source venv/bin/activate
python --version
# Expected: Python 3.12.x (or 3.11.x minimum)

# 3. Verify dependencies installed
pip list | grep -E "(fastapi|pydantic|pytest)"

# 4. Run tests
pytest tests/unit/test_api_models.py -v

# 5. Check code quality tools
python -m black --version
python -m ruff --version
python -m mypy --version
```

---

## Troubleshooting

### Issue: `python3` still points to 3.9
**Solution**: Use `python3.12` explicitly or update PATH:
```bash
# Check where python3.12 is installed
which python3.12

# Create alias (add to ~/.zshrc)
alias python3='/opt/homebrew/bin/python3.12'  # For Apple Silicon
# or
alias python3='/usr/local/bin/python3.12'     # For Intel Macs
```

### Issue: Virtual environment uses wrong Python
**Solution**: Recreate venv with correct Python:
```bash
deactivate  # If venv is active
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
```

### Issue: `pip` command not found
**Solution**: Use `python3 -m pip` instead:
```bash
python3.12 -m pip install -r requirements.txt
```

---

## Recommended Approach for This Project

**Best Option**: Use **pyenv** with project-local Python version

**Why?**
- Keeps system Python untouched
- Easy to switch versions per project
- Works well with virtual environments
- No PATH conflicts

**Quick Setup**:
```bash
# Install pyenv
brew install pyenv

# Add to ~/.zshrc
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Install and use Python 3.12
pyenv install 3.12.0
cd /Users/nosenfield/Desktop/GauntletAI/Week-5-Flourish/vocabulator
pyenv local 3.12.0

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## When to Upgrade

**Upgrade Now If:**
- ✅ Starting Phase 5 development
- ✅ Want to align with project requirements
- ✅ Want better performance (3.11+ is 10-60% faster)
- ✅ Want longer support (3.9 EOL is Oct 2025)

**Can Wait If:**
- ⏸️ Just testing/exploring the codebase
- ⏸️ Current setup works for your needs
- ⏸️ Waiting for team alignment

---

## Next Steps After Upgrade

1. ✅ Verify Python 3.12 is installed
2. ✅ Create new virtual environment
3. ✅ Install all dependencies
4. ✅ Run test suite to verify everything works
5. ✅ Update any CI/CD configs if needed
6. ✅ Document Python version in team docs

---

**Note**: The project code works on Python 3.9+ (tests pass), but 3.11+ is recommended for:
- Performance (10-60% faster)
- Security updates (3.9 EOL Oct 2025)
- AWS Lambda support (3.11+)
- Better error messages

