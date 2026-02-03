# Valorant Team Scout

A Streamlit-based application for scouting Valorant teams using the GRID API and OpenAI for strategic analysis.

## Features

- **Team Search**: Locate any Valorant team in the GRID database.
- **Performance Analysis**: Aggregates data from recent series (up to 12 months) including:
    - **Map Strategy**: Win rates, pick/ban frequencies, and agent preferences per map.
    - **Player Performance**: Detailed weapon usage, kill/death statistics by side (Attacker/Defender), aggression factors, and headshot ratios.
    - **Tactical Insights**: Ultimate orb capture priority and identification of "Agents to Deny" based on opponent impact.
- **AI-Powered Summary**: Generates strategic "how to beat" reports using OpenAI's GPT models.
- **Interactive Chat**: Ask specific questions about the gathered team data via an integrated AI analyst.

## Setup & Installation

### 1. Environment Setup

Create a `.env` file in the root directory with your API keys:

```env
API_KEY=your_grid_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

*(Note: If you have an `environment` folder, you might want to use the python/pip located in `environment/bin/`)*

### 3. Generate GraphQL Clients

The project uses `ariadne-codegen` to generate typed Python clients for the GRID GraphQL API based on queries defined in `query_files/`.

Run the generation script:

```bash
python utilities/generate_client.py
```

This script:
1. Runs `ariadne-codegen` to generate clients in the `clients/` directory.
2. Runs `utilities/fix_nullable_fields.py` to ensure Optional fields in Pydantic models are correctly initialized with `default=None`.

## Usage

Run the Streamlit application:

```bash
streamlit run main.py
```

1. **Search**: Enter a team name (e.g., "LOUD", "Fnatic") and click **Search Team**.
2. **Scout**: Select how many months of history to analyze and click **Scout Team**.
3. **Analyze**: Review the generated metrics, AI summary, and use the chat interface to dig deeper into the data.

## Project Structure

- `main.py`: The main Streamlit application and analysis logic.
- `clients/`: Generated GraphQL clients for different GRID services.
- `query_files/`: GraphQL `.graphql` files defining the data to be fetched.
- `utilities/generate_client.py`: Utility script to regenerate API clients.
- `utilities/fix_nullable_fields.py`: Post-processor for generated Pydantic models.