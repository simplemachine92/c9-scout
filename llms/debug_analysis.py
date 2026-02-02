#!/usr/bin/env python3
"""
Debug script to test the team analysis functions with the provided API data.
"""

import json
from collections import defaultdict, Counter
from typing import Dict, List, Any
from clients.series_client.get_completed_series_details import GetCompletedSeriesDetails

# Load the API data you provided
API_DATA = {
  "data": {
    "seriesState": {
      "draftActions": [
        {
          "sequenceNumber": "1",
          "drafter": {
            "id": "97"
          },
          "type": "ban",
          "draftable": {
            "name": "icebox"
          }
        },
        {
          "sequenceNumber": "2",
          "drafter": {
            "id": "81"
          },
          "type": "ban",
          "draftable": {
            "name": "corrode"
          }
        },
        {
          "sequenceNumber": "3",
          "drafter": {
            "id": "97"
          },
          "type": "pick",
          "draftable": {
            "name": "lotus"
          }
        },
        {
          "sequenceNumber": "4",
          "drafter": {
            "id": "81"
          },
          "type": "pick",
          "draftable": {
            "name": "bind"
          }
        },
        {
          "sequenceNumber": "5",
          "drafter": {
            "id": "97"
          },
          "type": "ban",
          "draftable": {
            "name": "sunset"
          }
        },
        {
          "sequenceNumber": "6",
          "drafter": {
            "id": "81"
          },
          "type": "ban",
          "draftable": {
            "name": "ascent"
          }
        },
        {
          "sequenceNumber": "7",
          "drafter": {
            "id": "2819695"
          },
          "type": "pick",
          "draftable": {
            "name": "haven"
          }
        }
      ],
      "valid": True,
      "updatedAt": "2025-08-09T01:08:24.737Z",
      "format": "best-of-3",
      "started": True,
      "finished": True,
      "teams": [
        {
          "name": "MIBR (1)",
          "won": False
        },
        {
          "name": "NRG",
          "won": True
        }
      ],
      "games": [
        {
          "sequenceNumber": 1,
          "segments": [
            {
              "sequenceNumber": 1,
              "teams": [
                {
                  "name": "MIBR (1)",
                  "players": [
                    {
                      "name": "aspas",
                      "headshots": 1,
                      "damageDealt": 101,
                      "damageTaken": 78,
                      "currentArmor": 0,
                      "damageDealtTargets": [
                        {
                          "target": {
                            "name": "body"
                          },
                          "damageAmount": 99,
                          "damageTypes": [
                            {
                              "type": "enemyDamage",
                              "damageAmount": 99,
                              "occurrenceCount": 3
                            }
                          ]
                        },
                        {
                          "target": {
                            "name": "head"
                          },
                          "damageAmount": 2,
                          "damageTypes": [
                            {
                              "type": "enemyDamage",
                              "damageAmount": 2,
                              "occurrenceCount": 1
                            }
                          ]
                        }
                      ],
                      "damageDealtSources": [
                        {
                          "source": {
                            "name": "sheriff"
                          },
                          "damageAmount": 101,
                          "damageTypes": [
                            {
                              "type": "enemyDamage",
                              "damageAmount": 101,
                              "occurrenceCount": 4
                            }
                          ]
                        }
                      ],
                      "firstKill": False,
                      "kills": 2,
                      "killAssistsGiven": 0,
                      "killAssistsReceived": 1,
                      "weaponKills": [
                        {
                          "weaponName": "sheriff",
                          "count": 2
                        }
                      ],
                      "deaths": 0,
                      "objectives": []
                    }
                  ]
                }
              ]
            }
          ],
          "map": {
            "name": "lotus",
            "bounds": {
              "min": {
                "x": 300,
                "y": -5500
              },
              "max": {
                "x": 11000,
                "y": 6550
              }
            }
          },
          "teams": [
            {
              "name": "MIBR (1)",
              "players": [
                {
                  "name": "aspas",
                  "character": {
                    "name": "raze",
                    "id": "raze"
                  },
                  "inventory": {
                    "items": []
                  },
                  "kills": 23,
                  "killAssistsGiven": 4,
                  "killAssistsReceived": 16,
                  "weaponKills": [
                    {
                      "weaponName": "sheriff",
                      "count": 2
                    },
                    {
                      "weaponName": "phantom",
                      "count": 11
                    }
                  ],
                  "deaths": 19,
                  "money": 400,
                  "netWorth": 2000
                }
              ]
            }
          ]
        }
      ]
    }
  }
}

def analyze_team_series_data(series_details: List[Any], target_team_name: str) -> Dict[str, Any]:
    """
    Analyze collective series data for a team and return comprehensive player statistics.
    """
    if not series_details:
        return {
            'team_analysis': {
                'least_favorite_map': None,
                'map_ban_counts': {}
            },
            'player_analysis': {}
        }

    # Initialize data structures for aggregation
    team_map_bans = Counter()
    player_stats = defaultdict(lambda: {
        'total_rounds': 0,
        'pistol_rounds': 0,
        'pistol_armor_buys': 0,
        'total_damage_dealt': 0,
        'total_damage_taken': 0,
        'total_headshots': 0,
        'total_assists_given': 0,
        'total_assists_received': 0,
        'total_capture_ultimate_orb': 0,
        'weapon_usage': Counter(),
        'series_played': 0
    })

    for series in series_details:
        if not hasattr(series, 'series_state') or not series.series_state:
            print(f"Series missing series_state: {series}")
            continue

        print(f"Processing series with {len(series.series_state.draft_actions)} draft actions")

        # Analyze draft actions for map bans
        for draft_action in series.series_state.draft_actions:
            print(f"Processing draft action: type={draft_action.type}, drafter={getattr(draft_action.drafter, 'id', 'None') if draft_action.drafter else 'None'}")
            if draft_action.type == "ban" and draft_action.drafter and hasattr(draft_action.drafter, 'id'):
                # For simplicity, we'll count all bans - in a real implementation,
                # you'd need to cross-reference drafter IDs with team rosters
                # For now, assume the bans we see are from the target team
                if draft_action.draftable and draft_action.draftable.name:
                    team_map_bans[draft_action.draftable.name] += 1
                    print(f"Added ban for {draft_action.draftable.name}")

        # Analyze each game in the series
        for game in series.series_state.games:
            print(f"Processing game {game.sequenceNumber} with {len(game.segments)} segments")

            # Analyze segments (rounds) for pistol performance
            for segment in game.segments:
                print(f"Processing segment {segment.sequenceNumber}")
                # Pistol rounds are typically sequenceNumber 1 (first round of each half)
                is_pistol_round = segment.sequence_number == 1

                for team in segment.teams:
                    print(f"Processing team {team.name}")
                    if team.name != target_team_name:
                        continue

                    print(f"Found target team {target_team_name} with {len(team.players)} players")

                    for player in team.players:
                        print(f"Processing player {player.name}")
                        # Check if this is a Valorant player by checking for Valorant-specific fields
                        if hasattr(player, 'damageDealt') and hasattr(player, 'headshots'):
                            player_name = player.name
                            player_stats[player_name]['total_rounds'] += 1
                            player_stats[player_name]['series_played'] += 1

                            print(f"Player {player_name}: rounds={player_stats[player_name]['total_rounds']}")

                            if is_pistol_round:
                                player_stats[player_name]['pistol_rounds'] += 1
                                # Check if player bought armor (currentArmor > 0 at start of round)
                                armor_value = getattr(player, 'currentArmor', 0)
                                if armor_value > 0:
                                    player_stats[player_name]['pistol_armor_buys'] += 1
                                    print(f"Player {player_name} bought armor on pistol round")

                            # Aggregate stats from segment data
                            damage_dealt = getattr(player, 'damageDealt', 0)
                            damage_taken = getattr(player, 'damageTaken', 0)
                            headshots = getattr(player, 'headshots', 0)
                            assists_given = getattr(player, 'killAssistsGiven', 0)
                            assists_received = getattr(player, 'killAssistsReceived', 0)

                            player_stats[player_name]['total_damage_dealt'] += damage_dealt
                            player_stats[player_name]['total_damage_taken'] += damage_taken
                            player_stats[player_name]['total_headshots'] += headshots
                            player_stats[player_name]['total_assists_given'] += assists_given
                            player_stats[player_name]['total_assists_received'] += assists_received

                            print(f"Player {player_name} stats: damage_dealt={damage_dealt}, headshots={headshots}")

                            # Count captureUltimateOrb objectives
                            if hasattr(player, 'objectives'):
                                for objective in player.objectives:
                                    if objective.type == "captureUltimateOrb":
                                        player_stats[player_name]['total_capture_ultimate_orb'] += objective.completionCount
                                        print(f"Player {player_name} captured ultimate orb")

                            # Track weapon usage from segments
                            if hasattr(player, 'weaponKills'):
                                for weapon_kill in player.weaponKills:
                                    if weapon_kill.weaponName and weapon_kill.count:
                                        player_stats[player_name]['weapon_usage'][weapon_kill.weaponName] += weapon_kill.count
                                        print(f"Player {player_name} weapon: {weapon_kill.weaponName} x{weapon_kill.count}")

            # Also aggregate weapon data from game-level stats (more reliable)
            for game_team in game.teams:
                if game_team.name != target_team_name:
                    continue

                for game_player in game_team.players:
                    player_name = game_player.name
                    if player_name not in player_stats:
                        continue

                    if hasattr(game_player, 'weaponKills'):
                        for weapon_kill in game_player.weaponKills:
                            if weapon_kill.weaponName and weapon_kill.count:
                                player_stats[player_name]['weapon_usage'][weapon_kill.weaponName] += weapon_kill.count
                                print(f"Game-level weapon for {player_name}: {weapon_kill.weaponName} x{weapon_kill.count}")

    # Process final statistics
    most_common_bans = team_map_bans.most_common()
    least_favorite_map = None
    if most_common_bans:
        # Get the map with the most bans (actually least favorite since they ban it most)
        least_favorite_map = most_common_bans[0][0]

    analysis_result = {
        'team_analysis': {
            'least_favorite_map': least_favorite_map,
            'map_ban_counts': dict(team_map_bans)
        },
        'player_analysis': {}
    }

    # Calculate averages and final stats for each player
    for player_name, stats in player_stats.items():
        if stats['total_rounds'] == 0:
            continue

        analysis_result['player_analysis'][player_name] = {
            'series_played': stats['series_played'],
            'total_rounds': stats['total_rounds'],
            'pistol_round_performance': {
                'pistol_rounds_played': stats['pistol_rounds'],
                'armor_buy_rate': (stats['pistol_armor_buys'] / stats['pistol_rounds'] * 100) if stats['pistol_rounds'] > 0 else 0
            },
            'preferred_weapon': stats['weapon_usage'].most_common(1)[0][0] if stats['weapon_usage'] and stats['weapon_usage'].most_common(1) else None,
            'total_headshots': stats['total_headshots'],
            'total_capture_ultimate_orb': stats['total_capture_ultimate_orb'],
            'avg_damage_dealt_per_round': stats['total_damage_dealt'] / stats['total_rounds'],
            'avg_damage_taken_per_round': stats['total_damage_taken'] / stats['total_rounds'],
            'total_assists_received': stats['total_assists_received'],
            'total_assists_given': stats['total_assists_given'],
            'weapon_breakdown': dict(stats['weapon_usage'])
        }

    return analysis_result

def main():
    print("=== Debug Analysis Script ===")

    # Create a mock series object from the API data
    try:
        # Parse the API data into our Pydantic model
        series_data = API_DATA["data"]
        series = GetCompletedSeriesDetails.model_validate(series_data)

        print(f"Successfully parsed series data")
        print(f"Series has {len(series.series_state.draft_actions)} draft actions")
        print(f"Series has {len(series.series_state.games)} games")

        # Test the analysis function
        target_team = "MIBR (1)"
        print(f"\nAnalyzing team: {target_team}")

        result = analyze_team_series_data([series], target_team)

        print("\n=== RESULTS ===")
        print("Team Analysis:")
        print(f"  Least Favorite Map: {result['team_analysis']['least_favorite_map']}")
        print(f"  Map Ban Counts: {result['team_analysis']['map_ban_counts']}")

        print("\nPlayer Analysis:")
        for player_name, stats in result['player_analysis'].items():
            print(f"\n{player_name}:")
            print(f"  Series Played: {stats['series_played']}")
            print(f"  Total Rounds: {stats['total_rounds']}")
            print(f"  Pistol Rounds: {stats['pistol_round_performance']['pistol_rounds_played']}")
            print(f"  Armor Buy Rate: {stats['pistol_round_performance']['armor_buy_rate']:.1f}%")
            print(f"  Preferred Weapon: {stats['preferred_weapon']}")
            print(f"  Total Headshots: {stats['total_headshots']}")
            print(f"  Ultimate Orbs: {stats['total_capture_ultimate_orb']}")
            print(f"  Avg Damage Dealt: {stats['avg_damage_dealt_per_round']:.1f}")
            print(f"  Avg Damage Taken: {stats['avg_damage_taken_per_round']:.1f}")
            print(f"  Assists Given: {stats['total_assists_given']}")
            print(f"  Assists Received: {stats['total_assists_received']}")
            print(f"  Weapon Breakdown: {stats['weapon_breakdown']}")

    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()