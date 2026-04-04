# AI-Powered CAD System (MCP + Eyeshot)

This repository contains the hackathon prototype for an AI-driven CAD application utilizing the Model Context Protocol (MCP) and devDept Eyeshot SDK.

## Architecture layers:

1. **frontend:** React + Three.js interface combining a Chat Assistant with a 3D Canvas.
2. **backend-mcp:** Python FastAPI server handling the MCP routing logic and tool execution.
3. **llm-service:** Python FastAPI server responsible for talking to the LLM (Gemini/GPT) to map natural language to CAD operations.
4. **cad-engine:** C# ASP.NET Core server utilizing the devDept Eyeshot SDK to perform CAD operations headlessly.
5. **shared:** A set of common schemas mapping commands across the layer divides.

## Setup

1. Copy `.env.example` to `.env`.
2. Assign your secret keys:
   - `GEMINI_API_KEY`: Your Gemini API key from Google AI Studio.
   - `EYESHOT_LICENSE_KEY`: Your Eyeshot production license key.
3. **IMPORTANT**: NEVER commit your `.env` file to the repository. It is already included in `.gitignore` to prevent accidental credential leaks.

## Requirements

- Node.js (for the frontend)
- Python 3.10+ (for MCP and LLM services)
- .NET 8 SDK (for the CAD engine)

## Command Flow example
- Prompt: "Load the sample.step model"
- MCP router sends to LLM service.
- LLM Service returns: `{"action": "load_model", "file_path": "sample.step"}`
- MCP router dispatches HTTP POST to CAD Engine with payload.
- CAD Engine executes the command and yields the modified state.