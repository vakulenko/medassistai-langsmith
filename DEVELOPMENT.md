# Development Guide - LangSmith Studio Debugging

This guide explains how to develop and debug the MedAssistAI agent using LangSmith Studio.

## Quick Start

### 1. Setup

```bash
pip install -r requirements.txt
```

Create `.env` with your API keys:
```env
GOOGLE_API_KEY=your_key
LANGSMITH_API_KEY=your_key
```

### 2. Start Debug Mode

```bash
python debug.py
```

Or on Windows:
```bash
debug.bat
```

The server starts on http://127.0.0.1:2024

### 3. Open LangSmith Studio

Go to https://smith.langchain.com

Your agent appears automatically - no configuration needed!

## Development Workflow

1. **Edit your agent**: Modify `graph.py`, `state.py`, or other modules
2. **Watch hot-reload**: Changes appear instantly in Studio
3. **Test in Studio**: Use the playground to test your agent
4. **Debug execution**: Click on traces to see LLM calls, prompts, responses
5. **Monitor performance**: See latency, tokens, and execution flow

## What Gets Traced

Every request shows:
- ✅ Intent detection (what the user wants)
- ✅ Information extraction (collected data)
- ✅ LLM prompts and responses
- ✅ Response generation
- ✅ Execution flow with timing
- ✅ Any errors or exceptions

## Files

| File | Purpose |
|------|---------|
| `debug.py` | Start development server |
| `debug.bat` | Windows launcher |
| `langgraph.json` | LangGraph configuration |
| `graph.py` | Agent definition |
| `state.py` | State models |
| `config.py` | Configuration |

## Troubleshooting

### Debug script won't start

Check dependencies:
```bash
pip install --upgrade langgraph-cli[inmem]
```

### No traces appear in Studio

1. Verify `LANGSMITH_API_KEY` is in `.env`
2. Check internet connection
3. Refresh Studio page

### Server crashes

Check output for error messages and verify:
- `.env` file exists
- `langgraph.json` is valid
- `graph.py` has no syntax errors

## Tips for Development

✅ **Keep terminal visible** - See server logs for debugging  
✅ **Use Studio playground** - Test your agent directly  
✅ **Monitor traces** - Watch what your agent is doing  
✅ **Edit code** - Changes hot-reload automatically  
✅ **Check LLM calls** - See exact prompts and responses  

## Next: Run the Chatbot

Once development is done, run the Streamlit UI:

```bash
streamlit run app.py
```

This connects to your agent for real conversations.

## Learn More

- LangGraph: https://langchain-ai.github.io/langgraph/
- LangSmith Studio: https://smith.langchain.com/docs
- LangChain: https://langchain.com

