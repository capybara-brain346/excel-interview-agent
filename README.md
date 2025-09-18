# Excel Interview Agent

A sophisticated multi-agent technical interview system designed to conduct structured Excel interviews with automated evaluation using LangGraph and Google Gemini AI.

## 📋 Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 1GB free space

### API Requirements

- **Google Gemini API Key**: Required for LLM evaluation and question generation
  - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Free tier available with usage limits

## 🛠️ Installation

### Method 1: Using uv (Recommended)

1. **Install uv** (if not already installed):

   ```bash
   # On macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd excel-interview-agent
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

### Method 2: Using pip

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd excel-interview-agent
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Method 3: Using conda

1. **Create a conda environment**:

   ```bash
   conda create -n excel-interview python=3.11
   conda activate excel-interview
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

### Environment Setup

1. **Copy the environment template**:

   ```bash
   cp env.example .env
   ```

2. **Edit the `.env` file** with your configuration:

   ```bash
   # Required: Google Gemini API Key
   GOOGLE_API_KEY=your_google_api_key_here

   # Optional: Customize model settings
   GOOGLE_MODEL=gemini-1.5-flash
   TEMPERATURE=0.1
   ```

### API Key Setup

1. **Get Google Gemini API Key**:

   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account
   - Create a new API key
   - Copy the key to your `.env` file

2. **Verify API Key**:
   - Ensure the key is valid and has appropriate permissions
   - Check your API usage limits in Google AI Studio

## 🚀 Running the Application

### Basic Usage

**Using uv**:

```bash
uv run python app.py
```

**Using pip**:

```bash
python app.py
```

### Advanced Options

The application supports several command-line options:

```bash
python app.py [OPTIONS]

Options:
  --mock              Use mock evaluator instead of LLM (for testing)
  --port PORT         Port to run the Gradio app on (default: 7860)
  --host HOST         Host to run the Gradio app on (default: 127.0.0.1)
  --share             Create a public link for the Gradio app
  --log-level LEVEL   Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
```

### Common Usage Examples

**Local development**:

```bash
python app.py --log-level DEBUG
```

**Public sharing**:

```bash
python app.py --share --host 0.0.0.0
```

**Custom port**:

```bash
python app.py --port 8080
```

**Mock mode (no API key required)**:

```bash
python app.py --mock
```

## 🌐 Accessing the Application

Once started, the application will be available at:

- **Local**: http://127.0.0.1:7860
- **Network**: http://[your-ip]:7860 (if using --host 0.0.0.0)
- **Public**: A shareable link will be provided (if using --share)

## 📱 Using the Interface

1. **Start Interview**:

   - Check the consent checkbox
   - Optionally enable LLM evaluation
   - Click "Start Interview"

2. **Conduct Interview**:

   - Respond to questions in the chat interface
   - Use "Submit Response" to send your answers
   - Use "End Interview Early" if needed

3. **View Results**:
   - Click "Get Report" after completing the interview
   - Download PDF report using "Download PDF Report"

## 🔧 Development Setup

### Project Structure

```
excel-interview-agent/
├── src/
│   ├── interview_engine/     # Core interview logic
│   │   ├── engine.py         # Main interview engine
│   │   ├── evaluator.py      # LLM evaluation logic
│   │   ├── question_generator.py  # Dynamic question generation
│   │   ├── reporter.py       # Report generation
│   │   ├── persistence.py    # Session persistence
│   │   └── models.py         # Data models
│   └── ui/
│       └── gradio_app.py     # Gradio web interface
├── app.py                    # Main application entry point
├── pyproject.toml           # Project configuration
├── requirements.txt         # Python dependencies
└── env.example             # Environment template
```

### Development Dependencies

Install development dependencies:

```bash
# Using uv
uv sync --dev

# Using pip
pip install -r requirements-dev.txt  # if available
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src
```

## 🐛 Troubleshooting

### Common Issues

**1. API Key Not Working**

```
Error: Failed to start interview: Invalid API key
```

- Verify your Google API key is correct
- Check if the API key has proper permissions
- Ensure you're not hitting rate limits

**2. Port Already in Use**

```
Error: Port 7860 is already in use
```

- Use a different port: `python app.py --port 8080`
- Kill the process using the port: `lsof -ti:7860 | xargs kill -9`

**3. Module Import Errors**

```
ModuleNotFoundError: No module named 'src'
```

- Ensure you're running from the project root directory
- Activate your virtual environment
- Reinstall dependencies

**4. Gradio Interface Not Loading**

- Check if all dependencies are installed correctly
- Try running with `--log-level DEBUG` for more information
- Ensure your firewall allows the port

**5. PDF Generation Issues**

```
Error generating PDF report
```

- Check if reportlab is installed correctly
- Ensure you have write permissions in the sessions directory
- Try running with elevated permissions if needed

### Debug Mode

Run with debug logging for detailed information:

```bash
python app.py --log-level DEBUG
```

### Logs

Application logs are saved to `interview_app.log` in the project directory.

## 📚 API Reference

### Environment Variables

| Variable         | Required | Default            | Description                 |
| ---------------- | -------- | ------------------ | --------------------------- |
| `GOOGLE_API_KEY` | Yes      | -                  | Google Gemini API key       |
| `GOOGLE_MODEL`   | No       | `gemini-1.5-flash` | Model to use for generation |
| `TEMPERATURE`    | No       | `0.1`              | Model temperature setting   |

### Command Line Options

| Option        | Type    | Default   | Description        |
| ------------- | ------- | --------- | ------------------ |
| `--mock`      | Flag    | False     | Use mock evaluator |
| `--port`      | Integer | 7860      | Server port        |
| `--host`      | String  | 127.0.0.1 | Server host        |
| `--share`     | Flag    | False     | Create public link |
| `--log-level` | String  | INFO      | Logging level      |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `python -m pytest`
5. Commit changes: `git commit -m "Add feature"`
6. Push to branch: `git push origin feature-name`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Search existing issues in the repository
3. Create a new issue with detailed information
4. Include logs and error messages when reporting bugs

## 🔄 Updates

To update the application:

```bash
git pull origin main
uv sync  # or pip install -r requirements.txt
```

---

**Note**: This application requires an active internet connection for LLM evaluation and question generation.
