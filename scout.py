from gql import Client
from gql.transport.requests import RequestsHTTPTransport
import datetime
from collections import defaultdict, Counter
from typing import List, Dict, Set, Tuple
from queries import (
    GRAPHQL_ENDPOINT,
    API_KEY,
    DEFAULT_DAYS_BACK,
    DEFAULT_SERIES_LIMIT,
    GET_TEAM_RECENT_SERIES,
    GET_SERIES_WITH_PLAYERS
)

def create_client():
    """Create and return a GQL client for the GRID GraphQL API"""
    headers = {
        "Content-type": "application/json",
    }

    # Add API key to headers if available
    if API_KEY:
        headers["X-API-Key"] = API_KEY

    transport = RequestsHTTPTransport(
        url=GRAPHQL_ENDPOINT,
        use_json=True,
        headers=headers
    )
    return Client(transport=transport, fetch_schema_from_transport=True)

def get_team_recent_series(client, team_id: str, days_back: int = DEFAULT_DAYS_BACK, limit: int = DEFAULT_SERIES_LIMIT) -> List[Dict]:
    """Get recent series where a team participated"""
    # Calculate date range
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days_back)

    variables = {
        "teamId": team_id,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "limit": limit
    }

    result = client.execute(GET_TEAM_RECENT_SERIES, variable_values=variables)
    return [edge['node'] for edge in result['allSeries']['edges']]

def get_opponent_agent_compositions(client, opponent_team_ids: List[str], days_back: int = DEFAULT_DAYS_BACK) -> Dict[str, Dict[str, int]]:
    """Get agent compositions for opponent teams from their recent matches"""
    # Get series for all opponent teams
    all_series = []
    for team_id in opponent_team_ids:
        result = client.execute(GET_SERIES_WITH_PLAYERS, variable_values={
            "teamId": team_id,
            "startDate": (datetime.datetime.now() - datetime.timedelta(days=days_back)).isoformat(),
            "endDate": datetime.datetime.now().isoformat(),
            "limit": 30  # Get more series for better composition analysis
        })
        all_series.extend([edge['node'] for edge in result['allSeries']['edges']])

    # Analyze agent compositions per opponent team
    team_compositions = defaultdict(lambda: defaultdict(int))

    for series in all_series:
        # Group players by team for this series
        team_players = defaultdict(list)
        for player in series['players']:
            if player['team']:
                team_players[player['team']['id']].append(player)

        # Count agent roles for each team in this series
        for team_id, players in team_players.items():
            if team_id in opponent_team_ids:
                role_counts = Counter()
                for player in players:
                    for role in player['roles']:
                        role_counts[role['name']] += 1

                # Create a composition signature based on role distribution
                sorted_roles = sorted(role_counts.items())
                composition_key = " + ".join([f"{count}x{role}" for role, count in sorted_roles])
                team_compositions[team_id][composition_key] += 1

    return dict(team_compositions)

def extract_opponent_teams(series_list: List[Dict], exclude_team_id: str) -> Set[Tuple[str, str]]:
    """Extract unique opponent teams from a list of series"""
    opponent_teams = set()
    for series in series_list:
        for team_participant in series['teams']:
            team_info = team_participant['baseInfo']
            if team_info['id'] != exclude_team_id:
                opponent_teams.add((team_info['id'], team_info['name']))
    return opponent_teams

def display_opponent_compositions(compositions: Dict[str, Dict[str, int]], opponent_teams: Set[Tuple[str, str]], days_back: int):
    """Display the agent composition analysis for each opponent team"""
    print("\n" + "=" * 60)
    print("🎯 Analyzing opponent agent compositions...")
    print("=" * 60)

    for team_id_opp, team_name in sorted(opponent_teams, key=lambda x: x[1]):
        print(f"\n🏹 {team_name} Agent Compositions (Last {days_back} days):")

        if team_id_opp in compositions:
            team_comps = compositions[team_id_opp]
            if team_comps:
                # Sort by frequency
                sorted_comps = sorted(team_comps.items(), key=lambda x: x[1], reverse=True)
                total_matches = sum(team_comps.values())
                for comp, count in sorted_comps:
                    percentage = (count / total_matches) * 100
                    print(".1f")
            else:
                print("  📝 No composition data available")
        else:
            print("  📝 No recent matches found")

def scout_team_opponents(target_team_id: str = "1", target_team_name: str = "Cloud9", days_back: int = DEFAULT_DAYS_BACK):
    """Main scouting function to analyze a team's upcoming opponents"""
    client = create_client()

    try:
        print(f"🔍 Scouting {target_team_name}'s opponents from the last {days_back} days...")
        print("=" * 60)

        # Step 1: Get team's recent series to find opponents
        team_series = get_team_recent_series(client, target_team_id, days_back)

        if not team_series:
            print(f"❌ No recent {target_team_name} matches found.")
            return

        # Extract unique opponent teams
        opponent_teams = extract_opponent_teams(team_series, target_team_id)

        if not opponent_teams:
            print("❌ No opponent teams found.")
            return

        print(f"📊 Found {len(opponent_teams)} opponent teams from {len(team_series)} recent matches:")
        for team_id_opp, team_name in sorted(opponent_teams, key=lambda x: x[1]):
            print(f"  • {team_name} (ID: {team_id_opp})")

        # Step 2: Analyze each opponent's recent agent compositions
        opponent_ids = [team_id for team_id, _ in opponent_teams]
        compositions = get_opponent_agent_compositions(client, opponent_ids, days_back)

        # Step 3: Display results
        display_opponent_compositions(compositions, opponent_teams, days_back)

        print("\n" + "=" * 60)
        print("✅ Scouting complete!")

    except Exception as e:
        print(f"❌ Error during scouting: {str(e)}")
        print("💡 Make sure your GraphQL endpoint URL and authentication are correct.")

if __name__ == "__main__":
    # Scout Cloud9's opponents (default team ID "1")
    scout_team_opponents()