import os
import asyncio
import streamlit as st
from datetime import datetime, timedelta
from dotenv import load_dotenv
from clients.central_client.client import CentralDbClient
from clients.central_client.fragments import TeamFields, SeriesFields
from clients.series_client.client import SeriesClient

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Initialize the client
def get_central_client():
    return CentralDbClient(
        url="https://api-op.grid.gg/central-data/graphql",
        headers={"x-api-key": API_KEY}
    )

def get_series_client():
    return SeriesClient(
        url="https://api-op.grid.gg/live-data-feed/series-state/graphql",
        headers={"x-api-key": API_KEY}
    )

# Cached analysis functions (defined at module level for proper caching)
@st.cache_data
def analyze_map_preferences(_series_details, _target_team_id, _months_back):
    """Analyze map ban/pick preferences from draft actions for target team"""
    from collections import Counter

    map_bans = Counter()
    map_picks = Counter()
    total_actions = 0

    for series in _series_details:
        # Only analyze Valorant series
        if (not series.series_state or
            not hasattr(series.series_state, 'title') or
            not series.series_state.title or
            not hasattr(series.series_state.title, 'name_shortened') or
            series.series_state.title.name_shortened != "val"):
            continue

        if not hasattr(series.series_state, 'draft_actions'):
            continue

        for draft_action in series.series_state.draft_actions:
            # Check if this action was by the target team
            if (hasattr(draft_action, 'drafter') and draft_action.drafter and
                hasattr(draft_action.drafter, 'id') and
                str(draft_action.drafter.id) == str(_target_team_id)):

                total_actions += 1

                if hasattr(draft_action, 'type') and hasattr(draft_action, 'draftable'):
                    action_type = draft_action.type
                    map_name = draft_action.draftable.name if hasattr(draft_action.draftable, 'name') else None

                    if map_name:
                        if action_type == "ban":
                            map_bans[map_name] += 1
                        elif action_type == "pick":
                            map_picks[map_name] += 1

    # Calculate preferences
    most_banned = map_bans.most_common(5) if map_bans else []
    most_picked = map_picks.most_common(5) if map_picks else []
    least_banned = list(reversed(map_bans.most_common()))[:5] if map_bans else []

    return {
        'total_actions': total_actions,
        'map_bans': dict(map_bans),
        'map_picks': dict(map_picks),
        'most_banned_maps': most_banned,
        'most_picked_maps': most_picked,
        'least_banned_maps': least_banned,
        'total_bans': sum(map_bans.values()),
        'total_picks': sum(map_picks.values())
    }

@st.cache_data
def analyze_map_characters(_series_details, _target_team_name, _months_back):
    """For each map, count how often the target team played each character (agent) on that map"""
    from collections import defaultdict, Counter

    # map_name -> character_name -> count (games played)
    map_characters = defaultdict(Counter)

    for series in _series_details:
        if (not series.series_state or
            not hasattr(series.series_state, 'title') or
            not series.series_state.title or
            not hasattr(series.series_state.title, 'name_shortened') or
            series.series_state.title.name_shortened != "val"):
            continue
        if not series.series_state.games:
            continue

        for game in series.series_state.games:
            map_name = None
            if hasattr(game, 'map') and game.map and hasattr(game.map, 'name'):
                map_name = game.map.name
            if not map_name:
                continue

            for team in game.teams:
                if not hasattr(team, 'name'):
                    continue
                if (team.name != _target_team_name and
                    not team.name.startswith(_target_team_name) and
                    _target_team_name not in team.name):
                    continue

                for player in team.players:
                    if hasattr(player, 'character') and player.character and hasattr(player.character, 'name'):
                        char_name = player.character.name
                        if char_name:
                            map_characters[map_name][char_name] += 1
                break  # only one matching team per game

    # Convert to map_name -> list of (character, count) sorted by count desc
    result = {}
    for map_name, char_counts in map_characters.items():
        result[map_name] = char_counts.most_common()
    return result

def _is_target_team(team_name, target_name):
    if not team_name or not target_name:
        return False
    return (
        team_name == target_name or
        team_name.startswith(target_name) or
        target_name in team_name
    )

@st.cache_data
def analyze_opponent_character_impact(_series_details, _target_team_name, _months_back):
    """
    When the opponent plays a character, how well do they perform (kills, damage)?
    Returns characters to prioritize denying, ranked by opponent performance when playing them.
    """
    from collections import defaultdict

    # character -> { games_played: int, total_kills: int, total_damage: int, total_rounds: int }
    char_stats = defaultdict(lambda: {"games_played": 0, "total_kills": 0, "total_damage": 0, "total_rounds": 0})

    for series in _series_details:
        if (not series.series_state or
            not hasattr(series.series_state, "title") or
            not series.series_state.title or
            getattr(series.series_state.title, "name_shortened", None) != "val"):
            continue
        if not series.series_state.games:
            continue

        for game in series.series_state.games:
            if not game.teams or len(game.teams) < 2:
                continue

            # Identify opponent team (the one that isn't the scouted team)
            opponent_team = None
            for t in game.teams:
                if not hasattr(t, "name"):
                    continue
                if not _is_target_team(t.name, _target_team_name):
                    opponent_team = t
                    break
            if not opponent_team or not hasattr(opponent_team, "players"):
                continue

            # Opponent player -> character name in this game
            player_to_char = {}
            for p in opponent_team.players:
                if hasattr(p, "name") and hasattr(p, "character") and p.character and hasattr(p.character, "name"):
                    player_to_char[p.name] = p.character.name
            if not player_to_char:
                continue

            # Sum kills and damage per opponent player from segments (this game)
            player_kills = defaultdict(int)
            player_damage = defaultdict(int)
            for segment in getattr(game, "segments", []) or []:
                for seg_team in getattr(segment, "teams", []) or []:
                    if not hasattr(seg_team, "name") or _is_target_team(seg_team.name, _target_team_name):
                        continue
                    for seg_player in getattr(seg_team, "players", []) or []:
                        pname = getattr(seg_player, "name", None)
                        if pname is None:
                            continue
                        player_kills[pname] += getattr(seg_player, "kills", 0) or 0
                        player_damage[pname] += getattr(seg_player, "damage_dealt", 0) or 0
                    break  # one opponent team per segment
            rounds_this_game = len(getattr(game, "segments", []) or [])

            for pname, char_name in player_to_char.items():
                k = player_kills[pname]
                d = player_damage[pname]
                char_stats[char_name]["games_played"] += 1
                char_stats[char_name]["total_kills"] += k
                char_stats[char_name]["total_damage"] += d
                char_stats[char_name]["total_rounds"] += rounds_this_game

    # Build ranked list: (character, games_played, avg_kills_per_game, avg_damage_per_round)
    result = []
    for char_name, s in char_stats.items():
        g = s["games_played"]
        if g == 0:
            continue
        avg_kills = s["total_kills"] / g
        total_rounds = s["total_rounds"] or 1
        avg_damage_per_round = s["total_damage"] / total_rounds
        result.append({
            "character": char_name,
            "games_played": g,
            "avg_kills_per_game": round(avg_kills, 1),
            "avg_damage_per_round": round(avg_damage_per_round, 0),
            "total_kills": s["total_kills"],
            "total_damage": s["total_damage"],
            "total_rounds": s["total_rounds"],
        })
    # Sort by impact: avg kills per game (primary), then avg damage per round
    result.sort(key=lambda x: (x["avg_kills_per_game"], x["avg_damage_per_round"]), reverse=True)
    return result

@st.cache_data
def analyze_player_weapons(_series_details, _target_team_name, _months_back):
    """Analyze player weapon preferences from detailed series data for target team only"""
    from collections import defaultdict, Counter

    player_weapons = defaultdict(Counter)  # player_name -> weapon -> total_kills
    player_series_count = defaultdict(int)  # player_name -> series_played
    # player_name -> side -> {'kills': int, 'rounds': int}
    def _side_dict():
        return defaultdict(lambda: {'kills': 0, 'rounds': 0})
    player_kills_by_side = defaultdict(_side_dict)
    # player_name -> {'total_damage_dealt': int, 'rounds': int} (per-round from segments)
    player_damage_dealt = defaultdict(lambda: {'total_damage_dealt': 0, 'rounds': 0})

    for series in _series_details:
        # Only analyze Valorant series
        if (not series.series_state or
            not hasattr(series.series_state, 'title') or
            not series.series_state.title or
            not hasattr(series.series_state.title, 'name_shortened') or
            series.series_state.title.name_shortened != "val"):
            continue

        if not series.series_state.games:
            continue

        # First pass: collect all players from target team in this series
        series_players = set()
        for game in series.series_state.games:
            # Check game-level teams
            for team in game.teams:
                if hasattr(team, 'name') and (
                    team.name == _target_team_name or
                    team.name.startswith(_target_team_name) or
                    _target_team_name in team.name
                ):
                    for player in team.players:
                        series_players.add(player.name)

            # Check segment-level teams
            for segment in game.segments:
                for team in segment.teams:
                    if hasattr(team, 'name') and (
                        team.name == _target_team_name or
                        team.name.startswith(_target_team_name) or
                        _target_team_name in team.name
                    ):
                        for player in team.players:
                            series_players.add(player.name)

        # Count this series for all players who participated
        for player_name in series_players:
            player_series_count[player_name] += 1

        # Second pass: collect weapon data (only for players we know participated)
        for game in series.series_state.games:
            # Get weapon data from game-level player stats (more reliable)
            for team in game.teams:
                if hasattr(team, 'name') and (
                    team.name == _target_team_name or
                    team.name.startswith(_target_team_name) or
                    _target_team_name in team.name
                ):
                    for player in team.players:
                        player_name = player.name
                        # Only collect weapon data for players who participated in this series
                        if player_name in series_players:
                            if hasattr(player, 'weapon_kills'):
                                for weapon_kill in player.weapon_kills:
                                    if weapon_kill.weapon_name and weapon_kill.count:
                                        player_weapons[player_name][weapon_kill.weapon_name] += weapon_kill.count

            # Also check segment-level data for additional weapon info and side-based kills
            for segment in game.segments:
                for team in segment.teams:
                    if hasattr(team, 'name') and (
                        team.name == _target_team_name or
                        team.name.startswith(_target_team_name) or
                        _target_team_name in team.name
                    ):
                        side = (getattr(team, 'side', None) or '').lower()
                        if side not in ('attacker', 'defender'):
                            side = None

                        for player in team.players:
                            player_name = player.name
                            # Only collect for players who participated in this series
                            if player_name in series_players:
                                if hasattr(player, 'weapon_kills'):
                                    for weapon_kill in player.weapon_kills:
                                        if weapon_kill.weapon_name and weapon_kill.count:
                                            player_weapons[player_name][weapon_kill.weapon_name] += weapon_kill.count
                                # Track kills by side (segment-level has side per round)
                                if side and hasattr(player, 'kills'):
                                    player_kills_by_side[player_name][side]['kills'] += player.kills
                                    player_kills_by_side[player_name][side]['rounds'] += 1
                                # Track damage dealt per round (segment-level has damageDealt per round)
                                if hasattr(player, 'damage_dealt'):
                                    player_damage_dealt[player_name]['total_damage_dealt'] += player.damage_dealt
                                    player_damage_dealt[player_name]['rounds'] += 1

    # Calculate preferred weapons and side stats for each player
    player_analysis = {}
    for player_name, weapon_counts in player_weapons.items():
        total_kills = sum(weapon_counts.values())
        if total_kills > 0:
            # Get top 3 weapons
            top_weapons = weapon_counts.most_common(3)

            # Average kills per side
            side_stats = {}
            for side in ('attacker', 'defender'):
                data = player_kills_by_side[player_name][side]
                kills = data['kills']
                rounds = data['rounds']
                side_stats[side] = {
                    'kills': kills,
                    'rounds': rounds,
                    'avg_kills': round(kills / rounds, 2) if rounds > 0 else 0.0
                }

            # Damage dealt (per-round from segments)
            dmg = player_damage_dealt[player_name]
            total_dmg = dmg['total_damage_dealt']
            rounds_with_dmg = dmg['rounds']
            avg_damage_dealt_per_round = round(total_dmg / rounds_with_dmg, 1) if rounds_with_dmg > 0 else 0.0

            player_analysis[player_name] = {
                'series_played': player_series_count[player_name],
                'total_kills': total_kills,
                'preferred_weapon': top_weapons[0][0] if top_weapons else None,
                'preferred_weapon_kills': top_weapons[0][1] if top_weapons else 0,
                'weapon_breakdown': dict(top_weapons),
                'all_weapons': dict(weapon_counts),
                'kills_by_side': side_stats,
                'total_damage_dealt': total_dmg,
                'rounds_with_damage_data': rounds_with_dmg,
                'avg_damage_dealt_per_round': avg_damage_dealt_per_round
            }

    return {
        'total_players_analyzed': len(player_analysis),
        'player_analysis': player_analysis
    }

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

async def get_series_details(series_ids: list[str]):
    """Get detailed series data including player stats"""
    client = get_series_client()

    tasks = []
    for series_id in series_ids:
        tasks.append(client.get_completed_series_details(id=series_id))

    try:
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        print(f"DEBUG: Got {len(responses)} responses from API")

        # Filter out exceptions and None responses
        valid_responses = []
        for i, response in enumerate(responses):
            series_id = series_ids[i] if i < len(series_ids) else "unknown"

            if isinstance(response, Exception):
                print(f"DEBUG: Series {series_id} failed with exception: {response}")
                continue  # Skip failed requests
            elif response is None:
                print(f"DEBUG: Series {series_id} returned None")
                continue  # Skip None responses
            else:
                print(f"DEBUG: Series {series_id} response type: {type(response)}")
                print(f"DEBUG: Series {series_id} has series_state attr: {hasattr(response, 'series_state')}")
                if hasattr(response, 'series_state'):
                    print(f"DEBUG: Series {series_id} series_state is None: {response.series_state is None}")
                    if response.series_state:
                        print(f"DEBUG: Series {series_id} has games: {len(response.series_state.games) if hasattr(response.series_state, 'games') else 'no games attr'}")

                # Be more lenient - accept any response that isn't clearly broken
                if response is not None and not isinstance(response, Exception):
                    valid_responses.append(response)
                    print(f"DEBUG: Series {series_id} accepted (even if no series_state)")
                    # Debug: show what attributes the response has
                    attrs = [attr for attr in dir(response) if not attr.startswith('_')]
                    print(f"DEBUG: Series {series_id} attributes: {attrs}")
                else:
                    print(f"DEBUG: Series {series_id} rejected - None or exception")

        print(f"DEBUG: Returning {len(valid_responses)} valid responses")
        return valid_responses

    except Exception as e:
        print(f"Error getting series details: {e}")
        return []


# Streamlit UI
st.title("Team & Series Lookup")
st.write("Search for a team and view their recent series")

# Step 1: Team Search
st.subheader("Step 1: Enter Opponent Name")
team_name = st.text_input("Enter team name:", placeholder="e.g., LOUD, Cloud9, G2 Esports")

# Initialize session state to store the team and series
if 'selected_team' not in st.session_state:
    st.session_state.selected_team = None
if 'series_list' not in st.session_state:
    st.session_state.series_list = None

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

# Step 2: Select time period for scouting
if st.session_state.selected_team:
    team = st.session_state.selected_team
    
    # Step 2: Select time period for scouting
    st.divider()
    st.subheader("Step 2: Select Analysis Period")
    
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
                # Store series in session state
                st.session_state.series_list = series_list

            else:
                st.session_state.series_list = None
                st.error("No series data available.")

    # Scout team button
    if st.button("Scout Team", type="primary"):
        # Clear cached analysis results when starting a new scout
        analyze_player_weapons.clear()
        analyze_map_preferences.clear()
        analyze_map_characters.clear()
        analyze_opponent_character_impact.clear()
        asyncio.run(find_series())

    # Analysis Section (appears when we have series data)
    if st.session_state.series_list:
        series_list = st.session_state.series_list

        # Automatic Weapon Analysis (runs immediately after finding series)
        st.divider()
        with st.spinner("Analyzing team"):
            # Get series IDs and fetch detailed data
            series_ids = [str(s.id) for s in series_list if hasattr(s, 'id') and s.id]

            if series_ids:
                # Get detailed series data
                detailed_series = asyncio.run(get_series_details(series_ids))  # Analyze all available series

                if detailed_series:
                    # Pass months_back directly as cache parameter
                    weapon_analysis = analyze_player_weapons(detailed_series, team.name, months_back)
                    map_analysis = analyze_map_preferences(detailed_series, team.id, months_back)
                    map_characters = analyze_map_characters(detailed_series, team.name, months_back)
                    opponent_impact = analyze_opponent_character_impact(detailed_series, team.name, months_back)

                    # Show team performance analysis
                    if weapon_analysis['player_analysis'] or map_analysis['total_actions'] > 0:
                        st.subheader(f"🎯 {team.name} - Performance Analysis")
                        st.info(f"Analyzed {len(detailed_series)} series from the selected time period")

                        # Show summary metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Players", weapon_analysis['total_players_analyzed'])
                        with col2:
                            total_kills = sum(stats['total_kills'] for stats in weapon_analysis['player_analysis'].values())
                            st.metric("Total Kills", total_kills)
                        with col3:
                            st.metric("Map Actions", map_analysis['total_actions'])
                        with col4:
                            st.metric("Maps Banned", map_analysis['total_bans'])

                        st.divider()

                        # Map Preferences Section
                        if map_analysis['total_actions'] > 0:
                            st.subheader("🗺️ Map Preferences")

                            map_col1, map_col2 = st.columns(2)

                            with map_col1:
                                st.write("**Most Banned Maps:**")
                                if map_analysis['most_banned_maps']:
                                    for map_name, count in map_analysis['most_banned_maps']:
                                        st.write(f"• {map_name}: {count} bans")
                                else:
                                    st.write("*No ban data available*")

                            with map_col2:
                                st.write("**Most Picked Maps:**")
                                if map_analysis['most_picked_maps']:
                                    for map_name, count in map_analysis['most_picked_maps']:
                                        st.write(f"• {map_name}: {count} picks")
                                else:
                                    st.write("*No pick data available*")

                            # Show detailed map stats in expandable section
                            with st.expander("📊 Detailed Map Statistics"):
                                if map_analysis['map_bans']:
                                    st.write("**Ban Frequency:**")
                                    ban_data = [{"Map": map_name, "Bans": count}
                                              for map_name, count in map_analysis['map_bans'].items()]
                                    ban_data.sort(key=lambda x: x['Bans'], reverse=True)
                                    st.dataframe(ban_data, use_container_width=True)

                                if map_analysis['map_picks']:
                                    st.write("**Pick Frequency:**")
                                    pick_data = [{"Map": map_name, "Picks": count}
                                               for map_name, count in map_analysis['map_picks'].items()]
                                    pick_data.sort(key=lambda x: x['Picks'], reverse=True)
                                    st.dataframe(pick_data, use_container_width=True)

                            # Characters by map: click a map to see preferred agents on that map
                            if map_characters:
                                st.write("**Characters by map** — expand a map to see which agents the team plays there:")
                                for map_name in sorted(map_characters.keys()):
                                    chars = map_characters[map_name]
                                    if not chars:
                                        continue
                                    total_picks = sum(c for _, c in chars)
                                    with st.expander(f"🗺️ {map_name} ({total_picks} agent picks)"):
                                        for char_name, count in chars:
                                            st.write(f"• **{char_name}**: {count}")

                            st.divider()

                        # Opponent character impact: which agents to deny (show whenever we have data)
                        if opponent_impact:
                            st.subheader("🚫 Characters to deny")
                            st.caption("When the opponent plays these agents they perform best. Consider banning or first-picking to deny them.")
                            for i, row in enumerate(opponent_impact[:10], 1):
                                with st.expander(f"**{i}. {row['character']}** — {row['games_played']} games, {row['avg_kills_per_game']} avg kills/game"):
                                    st.metric("Avg kills per game", row["avg_kills_per_game"])
                                    st.metric("Avg damage per round", f"{row['avg_damage_per_round']:.0f}")
                                    st.caption(f"Total: {row['total_kills']} kills, {row['total_damage']} damage over {row['total_rounds']} rounds")
                            st.divider()

                        # Weapon Analysis Section
                        if weapon_analysis['player_analysis']:
                            st.subheader("🔫 Weapon Preferences")

                        # Sort players by series played
                        sorted_players = sorted(
                            weapon_analysis['player_analysis'].items(),
                            key=lambda x: x[1]['series_played'],
                            reverse=True
                        )

                        for player_name, stats in sorted_players[:10]:  # Show top 10 players
                            with st.expander(f"🎯 {player_name} (Series: {stats['series_played']})"):
                                col_a, col_b = st.columns(2)

                                with col_a:
                                    st.metric("Preferred Weapon",
                                             stats['preferred_weapon'] or "Unknown")
                                    st.metric("Kills with Preferred",
                                             stats['preferred_weapon_kills'])
                                    st.metric("Avg Damage Dealt / Round",
                                             stats.get('avg_damage_dealt_per_round', 0))
                                    if stats.get('rounds_with_damage_data'):
                                        st.caption(f"Over {stats['rounds_with_damage_data']} rounds")

                                with col_b:
                                    st.metric("Total Kills", stats['total_kills'])
                                    st.write("**Top Weapons:**")
                                    for weapon, kills in list(stats['weapon_breakdown'].items())[:3]:
                                        st.write(f"• {weapon}: {kills} kills")

                                # Average kills per side (attacker / defender)
                                if stats.get('kills_by_side'):
                                    st.subheader("📊 Kills by Side")
                                    side_data = stats['kills_by_side']
                                    side_col1, side_col2 = st.columns(2)
                                    with side_col1:
                                        att = side_data.get('attacker', {})
                                        st.metric("Attacker — Avg Kills/Round", att.get('avg_kills', 0))
                                        st.caption(f"{att.get('kills', 0)} kills in {att.get('rounds', 0)} rounds")
                                    with side_col2:
                                        def_ = side_data.get('defender', {})
                                        st.metric("Defender — Avg Kills/Round", def_.get('avg_kills', 0))
                                        st.caption(f"{def_.get('kills', 0)} kills in {def_.get('rounds', 0)} rounds")

                                # Show full weapon breakdown in expandable section
                                with st.expander("Full Weapon Breakdown"):
                                    weapon_data = []
                                    for weapon, kills in stats['all_weapons'].items():
                                        weapon_data.append({"Weapon": weapon, "Kills": kills})

                                    weapon_data.sort(key=lambda x: x['Kills'], reverse=True)
                                    st.dataframe(weapon_data, use_container_width=True)
                    else:
                        st.warning("No player weapon data available for analysis")
                else:
                    st.error("Unable to fetch detailed series data for weapon analysis")
            else:
                st.error("No valid series IDs found for weapon analysis")

# Add some helpful information
with st.sidebar:
    st.header("About")
    st.write("This app queries the GRID API to find team information and recent series data.")
    
    st.subheader("How to Use")
    st.write("1. Enter a team name and click 'Search Team'")
    st.write("2. Select analysis period and click 'Scout Team'")
    st.write("3. View comprehensive Valorant performance insights")
    
    st.subheader("Example Teams")
    st.code("LOUD\nFnatic\nT1\nG2 Esports")
