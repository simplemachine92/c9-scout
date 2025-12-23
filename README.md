# Esports Intelligence Gathering with GraphQL API

This guide demonstrates how to use the GRID GraphQL API to gather comprehensive intelligence on esports organizations and their opponents. The API provides access to tournament data, team rosters, player information, and match schedules.

## Table of Contents

- [Finding Upcoming Matches for an Organization](#finding-upcoming-matches-for-an-organization)
- [Finding Opponent Rosters](#finding-opponent-rosters)
- [Gathering Opposition Intelligence](#gathering-opposition-intelligence)
- [API Schema Overview](#api-schema-overview)
- [Authentication & Permissions](#authentication--permissions)

## Finding Upcoming Matches for an Organization

To find upcoming matches for a specific organization, you need to:

1. First identify the organization's teams
2. Query for series (matches) involving those teams with future scheduled dates

### Example: Get Upcoming Matches for Cloud9

```graphql
query GetUpcomingMatches($organizationName: String!) {
  # Step 1: Find the organization and its teams
  organizations(filter: { name: { equals: $organizationName } }) {
    edges {
      node {
        id
        name
        teams {
          id
          name
          nameShortened
        }
      }
    }
  }
}

# Variables
{
  "organizationName": "Cloud9"
}
```

### Example: Get All Upcoming Series

```graphql
query GetUpcomingSeries {
  allSeries(
    first: 20
    orderBy: StartTimeScheduled
    orderDirection: ASC
    filter: {
      startTimeScheduled: {
        gte: "2025-12-23T00:00:00Z"  # Current date/time
      }
      types: [ESPORTS]  # Only competitive matches
    }
  ) {
    edges {
      node {
        id
        startTimeScheduled
        type
        format {
          name
          nameShortened
        }
        tournament {
          id
          name
          startDate
          endDate
          prizePool {
            amount
          }
          venueType
        }
        teams {
          baseInfo {
            id
            name
            organization {
              id
              name
            }
          }
        }
        streams {
          url
        }
      }
    }
  }
}
```

## Finding Opponent Rosters

Once you have identified the opposing teams from match data, you can gather their roster information.

### Get Team Details

```graphql
query GetTeamDetails($teamId: ID!) {
  team(id: $teamId) {
    id
    name
    nameShortened
    title {
      id
      name
    }
    organization {
      id
      name
    }
    colorPrimary
    colorSecondary
    logoUrl
  }
}
```

### Get Team Players

```graphql
query GetTeamPlayers($teamId: ID!) {
  players(
    first: 20
    filter: {
      teamIdFilter: { id: $teamId }
    }
  ) {
    edges {
      node {
        id
        nickname
        roles {
          id
          name
          title {
            id
            name
          }
        }
        team {
          id
          name
          organization {
            id
            name
          }
        }
        # Note: Some fields may require authentication
        # fullName
        # age
        # nationality { code name }
      }
    }
  }
}
```

### Example: Complete Opponent Intelligence Query

```graphql
query GetOpponentIntelligence($opponentTeamId: ID!) {
  # Get team basic info
  team(id: $opponentTeamId) {
    id
    name
    nameShortened
    title {
      id
      name
    }
    organization {
      id
      name
    }
    colorPrimary
    colorSecondary
    logoUrl
  }

  # Get all players for this team
  players(
    first: 20
    filter: {
      teamIdFilter: { id: $opponentTeamId }
    }
  ) {
    edges {
      node {
        id
        nickname
        roles {
          id
          name
          title {
            id
            name
          }
        }
        imageUrl
        # Restricted fields (may require auth):
        # fullName
        # age
        # nationality { code name }
      }
    }
  }
}
```

## Gathering Opposition Intelligence

For comprehensive opposition analysis, combine match data with team and player intelligence.

### Complete Intelligence Report Query

```graphql
query GenerateIntelligenceReport($opponentTeamIds: [ID!]!) {
  # Get upcoming matches against these opponents
  allSeries(
    first: 50
    filter: {
      teamIds: { in: $opponentTeamIds }
      startTimeScheduled: {
        gte: "2025-12-23T00:00:00Z"
      }
      types: [ESPORTS]
    }
    orderBy: StartTimeScheduled
    orderDirection: ASC
  ) {
    edges {
      node {
        id
        startTimeScheduled
        format {
          name
        }
        tournament {
          name
          prizePool {
            amount
          }
        }
        teams {
          baseInfo {
            id
            name
            organization {
              name
            }
          }
        }
      }
    }
  }

  # Get detailed team information
  teams(
    first: 10
    filter: {
      id: { in: $opponentTeamIds }
    }
  ) {
    edges {
      node {
        id
        name
        title {
          name
        }
        organization {
          name
        }
        colorPrimary
        colorSecondary
        logoUrl
      }
    }
  }
}
```

### VALORANT-Specific Intelligence

For VALORANT matches, focus on series with VALORANT as the title:

```graphql
query GetValorantMatches($teamIds: [ID!]!) {
  allSeries(
    first: 20
    filter: {
      teamIds: { in: $teamIds }
      titleIds: { in: ["1"] }  # VALORANT title ID
      startTimeScheduled: {
        gte: "2025-12-23T00:00:00Z"
      }
    }
    orderBy: StartTimeScheduled
    orderDirection: ASC
  ) {
    edges {
      node {
        id
        startTimeScheduled
        format {
          name  # BO3, BO5, etc.
        }
        tournament {
          name
          # VALORANT-specific: default site setups might be in tournament descriptions
        }
        teams {
          baseInfo {
            name
            organization {
              name
            }
          }
        }
        players {
          id
          nickname
          roles {
            name  # Duelist, Controller, Sentinel, Initiator
          }
        }
      }
    }
  }
}
```

## API Schema Overview

### Key Types

- **`Organization`**: Represents esports organizations (Cloud9, G2 Esports, etc.)
- **`Team`**: Represents specific teams within organizations
- **`Player`**: Individual players with roles and team affiliations
- **`Series`**: Individual matches or series of games
- **`Tournament`**: Collections of series with shared context

### Important Relationships

- Organizations contain multiple Teams
- Teams contain multiple Players
- Tournaments contain multiple Series
- Series involve 2+ Teams and their Players

### Available Filters

- **DateTime filters**: `gte`, `lte` for time ranges
- **ID filters**: `in` for multiple IDs, `equals` for single values
- **String filters**: `contains`, `equals` for text matching
- **Series types**: `ESPORTS`, `SCRIM`, `COMPETITIVE`, `LOOPFEED`

## Authentication & Permissions

Some fields require authentication or have restricted access:

### Restricted Fields
- `Player.fullName`
- `Player.age`
- `Player.nationality`
- `Team.rating`

### Public Fields
- `Player.nickname`
- `Player.roles`
- `Player.team`
- `Team.name`
- `Team.organization`
- `Series.startTimeScheduled`
- `Series.teams`

### Getting Access
If you need access to restricted fields, contact the API provider for authentication credentials.

## Usage Tips

1. **Pagination**: Use `first`/`after` or `last`/`before` for large result sets
2. **Filtering**: Combine multiple filters for precise queries
3. **Sorting**: Use `orderBy` and `orderDirection` for chronological results
4. **Batch Queries**: Combine multiple queries in a single request
5. **Error Handling**: Check for permission errors and adjust queries accordingly

## Common Query Patterns

### Find All Teams in a Tournament
```graphql
query GetTournamentTeams($tournamentId: ID!) {
  tournament(id: $tournamentId) {
    name
    teams {
      id
      name
      organization {
        name
      }
    }
  }
}
```

### Find Players by Role
```graphql
query GetPlayersByRole($roleName: String!) {
  players(
    first: 20
    filter: {
      roles: {
        name: { equals: $roleName }
      }
    }
  ) {
    edges {
      node {
        nickname
        team {
          name
        }
      }
    }
  }
}
```

### Monitor Team Activity
```graphql
query MonitorTeamActivity($teamId: ID!) {
  allSeries(
    first: 10
    filter: {
      teamIds: { in: [$teamId] }
      startTimeScheduled: {
        gte: "2025-01-01T00:00:00Z"
        lte: "2025-12-31T23:59:59Z"
      }
    }
    orderBy: StartTimeScheduled
    orderDirection: DESC
  ) {
    edges {
      node {
        startTimeScheduled
        tournament {
          name
        }
        teams {
          baseInfo {
            name
          }
        }
      }
    }
  }
}
```
