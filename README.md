# CrewAI Task Orchestration Backend

This backend API orchestrates CrewAI agents for task execution with chat functionality.

## Features

- Agent metadata management
- Dynamic tool creation from database
- Task status management
- Chat history preservation
- Asynchronous task processing

## API Endpoints

- `POST /process-task` - Process a task message
- `GET /task-status/{task_id}` - Get task status
- `GET /health` - Health check

## Environment Variables

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase service key
- `OPENAI_API_KEY` - Your OpenAI API key
- `GROQ_API_KEY` - Your Groq API key (optional)

## Deployment

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables
3. Run: `python main.py`