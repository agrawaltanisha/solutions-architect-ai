#  Solutions Architect AI

An autonomous multi-agent system that transforms any system design prompt into a
full **Technical Design Document** with a rendered architecture diagram.

## 🚀 Live Demo
> Deploy your own using the instructions below.

## 🤖 How It Works
User Prompt
│
▼
Agent 1: Requirement Analyst  →  Functional & Non-Functional Requirements
│
▼
Agent 2: Diagrammer  →  Calls MCP Mermaid Server  →  Architecture Diagram
│
▼
Agent 3: Critic  →  Risk Assessment + SPOF Detection
│
SPOF?
YES → loop back to Agent 2 (max 3 revisions)
NO  → Final Document
## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph |
| LLM | Groq Cloud FREE API (Llama 3.3 70B) |
| Diagram Tool | MCP Mermaid Server (custom) |
| Backend | Flask |
| Frontend | HTML + CSS + Mermaid.js |
| Tunnel | ngrok |

## ⚡ Quickstart

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/solutions-architect-ai
cd solutions-architect-ai
```

### 2. Install dependencies
```bash
pip install flask flask-cors groq langgraph nest_asyncio
```

### 3. Set your API key
```bash
export GROQ_API_KEY=your_groq_key_here
```
Get a free key at [console.groq.com](https://console.groq.com) — no credit card needed.

### 4. Run the app
```bash
python app.py
```
Then open [http://localhost:5000](http://localhost:5000)

## 🎯 Example Prompts

- Design Amazon's e-commerce platform
- Design Netflix's video streaming system
- Design Uber's ride hailing app
- Design WhatsApp's messaging system
- Design a food delivery app like Swiggy

## 📁 Project Structure
solutions-architect-ai/
├── app.py                  # Flask backend + all 3 agents + LangGraph pipeline
├── templates/
│   └── index.html          # Frontend UI with Mermaid diagram rendering
├── .gitignore
└── README.md
## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Free API key from console.groq.com |


## 📄 License
MIT
