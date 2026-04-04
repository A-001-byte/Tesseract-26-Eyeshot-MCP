# AI-Powered CAD System (MCP + Eyeshot)

This repository contains the hackathon prototype for an AI-driven CAD application utilizing the Model Context Protocol (MCP) and devDept Eyeshot SDK.

## Architecture layers:

1. **frontend:** React + Three.js interface combining a Chat Assistant with a 3D Canvas.
2. **backend-mcp:** Python FastAPI server handling the MCP routing logic and tool execution.
3. **llm-service:** Python FastAPI server responsible for talking to the LLM (Gemini/GPT) to map natural language to CAD operations.
4. **cad-engine:** C# ASP.NET Core server utilizing the devDept Eyeshot SDK to perform CAD operations headlessly.
5. **shared:** A set of common schemas mapping commands across the layer divides.

## Setup

1. Copy `.env.example` to `.env` and assign your API keys.
2. Ensure you have Node.js, Python, and .NET installed locally or run via the (forthcoming) Docker definitions.
3. Start the services as per the instructions in their respective folders.

## Command Flow example
- Prompt: "Load the sample.step model"
- MCP router sends to LLM service.
- LLM Service returns: `{"action": "load_model", "file_path": "sample.step"}`
- MCP router dispatches HTTP POST to CAD Engine with payload.
- CAD Engine executes the command and yields the modified state.