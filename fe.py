import os
import asyncio
import streamlit as st
from datetime import datetime, timedelta
from dotenv import load_dotenv
from clients.central_client.client import CentralDbClient
from clients.central_client.fragments import TeamFields, SeriesFields

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Initialize the client
def get_central_client():
    return CentralDbClient(
        url="https://api-op.grid.gg/central-data/graphql",
        headers={"x-api-key": API_KEY}
    )

async def fetch_team(team_name: str):
    """Fetch team data by exact name"""
    client = get_central_client()
    response = await client.get_team_by_exact_name(team_name)
    
    try:
        team_node = response.teams.edges[0].node
        opponent = TeamFields.model_validate(team_node)
        return opponent
    except (AttributeError, IndexError):
        return None

async def fetch_recent_series(since_date: str, team_id: str):
    """User provides timestamp for how far back they would like to scout"""
    client = get_central_client()
    response = await client.get_all_series_since_date(team_id, since_date)

    try:
        # Check if there are any edges first
        if not response.all_series.edges:
            return []  # Return empty list if no results
            
        # Get all series from the response
        series_list = []
        for edge in response.all_series.edges:
            series_node = edge.node
            validated = SeriesFields.model_validate(series_node)
            series_list.append(validated)
        return series_list
    except (AttributeError, IndexError):
        return []  # Return empty list instead of None

def calculate_date_from_months(months_back: int) -> str:
    """Calculate the date string from months back"""
    from datetime import timezone
    target_date = datetime.now(timezone.utc) - timedelta(days=months_back * 30)
    # Format as ISO 8601 string with timezone: "2024-04-24T15:00:07+00:00"
    # Use +00:00 format (with colon) as used in the working hardcoded query
    return target_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")


# Streamlit UI
st.title("Team & Series Lookup")
st.write("Search for a team and view their recent series")

# Step 1: Team Search
st.subheader("Step 1: Find a Team")
team_name = st.text_input("Enter team name:", placeholder="e.g., LOUD, Cloud9, G2 Esports")

# Initialize session state to store the team
if 'selected_team' not in st.session_state:
    st.session_state.selected_team = None

async def search_team():
    """Async function to search for a team"""
    if team_name:
        with st.spinner("Searching for team..."):
            # Run async function directly (Streamlit handles the event loop)
            team = await fetch_team(team_name)

            if team:
                st.session_state.selected_team = team
                st.success(f"Team found: {team.name if hasattr(team, 'name') else team.id}")
                print(f"Team ID: {team.id}")
            else:
                st.error(f"Team '{team_name}' not found.")
                st.session_state.selected_team = None
    else:
        st.warning("Please enter a team name.")

# Search button
if st.button("Search Team"):
    asyncio.run(search_team())

# Step 2: Display team details and get months back
if st.session_state.selected_team:
    team = st.session_state.selected_team
    
    # Display team information
    st.divider()
    st.subheader("Team Details")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Team ID", team.id)
        if hasattr(team, 'name'):
            st.metric("Name", team.name)
    
    with col2:
        if hasattr(team, 'code'):
            st.metric("Code", team.code)
    
    # Show all available fields
    with st.expander("View All Team Fields"):
        st.json(team.model_dump())
    
    # Step 3: Get months back and fetch series
    st.divider()
    st.subheader("Step 2: Search for Recent Series")
    
    months_back = st.number_input(
        "How many months back to search?",
        min_value=1,
        max_value=12,
        value=3,
        step=1,
        help="Select how many months of historical data to retrieve"
    )
    
    # Display the calculated date
    target_date = datetime.now() - timedelta(days=months_back * 30)
    st.info(f"Will search for series since: {target_date.strftime('%Y-%m-%d')}")
    
    async def find_series():
        """Async function to find series"""
        with st.spinner(f"Fetching series from the last {months_back} month(s)..."):
            # Calculate the date string
            since_date = calculate_date_from_months(months_back)

            # Run async function directly (Streamlit handles the event loop)
            series_list = await fetch_recent_series(since_date, team.id)

            if series_list:
                st.success(f"Found {len(series_list)} series!")

                st.divider()
                st.subheader(f"Series from Last {months_back} Month(s)")

                # Show series in an expandable format
                for i, series in enumerate(series_list, 1):
                    with st.expander(f"Series {i}: {getattr(series, 'id', 'Unknown ID')}"):
                        col1, col2 = st.columns(2)

                        with col1:
                            if hasattr(series, 'id'):
                                st.write(f"**ID:** {series.id}")
                            if hasattr(series, 'title'):
                                st.write(f"**Title:** {series.title}")
                            if hasattr(series, 'startTime'):
                                st.write(f"**Start Time:** {series.startTime}")

                        with col2:
                            if hasattr(series, 'teams'):
                                st.write(f"**Teams:** {series.teams}")
                            if hasattr(series, 'winner'):
                                st.write(f"**Winner:** {series.winner}")

                        # Show all fields
                        st.json(series.model_dump())

                # Optional: Show summary statistics
                st.divider()
                st.metric("Total Series Found", len(series_list))

            else:
                st.session_state.series_list = None
                st.error("No series data available.")

    # Search series button
    if st.button("Find Series"):
        asyncio.run(find_series())

# Add some helpful information
with st.sidebar:
    st.header("About")
    st.write("This app queries the GRID API to find team information and recent series data.")
    
    st.subheader("How to Use")
    st.write("1. Enter a team name and click 'Search Team'")
    st.write("2. Once found, select how many months back to search")
    st.write("3. Click 'Find Series' to see all matches")
    
    st.subheader("Example Teams")
    st.code("LOUD\nFnatic\nT1\nG2 Esports")
