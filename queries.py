# GraphQL Queries and Constants for GRID Esports Scouting

from gql import gql
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the variables using os.getenv()
# It is good practice to provide default values in case a variable is not set
GRAPHQL_ENDPOINT = os.getenv("GRAPHQL_ENDPOINT", "https://your-grid-endpoint.com/graphql")
API_KEY = os.getenv("API_KEY")

# Default scouting parameters
DEFAULT_DAYS_BACK = 30
DEFAULT_SERIES_LIMIT = 50

# GraphQL Query: Get recent series for a specific team
GET_TEAM_RECENT_SERIES = gql("""
query GetTeamRecentSeries($teamId: ID!, $startDate: String!, $endDate: String!, $limit: Int!) {
  allSeries(
    first: $limit
    filter: {
      teamIds: { in: [$teamId] }
      startTimeScheduled: {
        gte: $startDate
        lte: $endDate
      }
      types: [ESPORTS]
    }
    orderBy: StartTimeScheduled
    orderDirection: DESC
  ) {
    edges {
      node {
        id
        title {
          id
          name
        }
        teams {
          baseInfo {
            id
            name
          }
          scoreAdvantage
        }
        startTimeScheduled
      }
    }
  }
}
""")

# GraphQL Query: Get detailed series info including players for composition analysis
GET_SERIES_WITH_PLAYERS = gql("""
query GetSeriesWithPlayers($teamId: ID!, $startDate: String!, $endDate: String!, $limit: Int!) {
  allSeries(
    first: $limit
    filter: {
      teamIds: { in: [$teamId] }
      startTimeScheduled: {
        gte: $startDate
        lte: $endDate
      }
      types: [ESPORTS]
    }
    orderBy: StartTimeScheduled
    orderDirection: DESC
  ) {
    edges {
      node {
        id
        title {
          id
          name
        }
        players {
          id
          nickname
          roles {
            name
          }
          team {
            id
            name
          }
        }
        startTimeScheduled
      }
    }
  }
}
""")

# GraphQL Query: Get basic team information
GET_TEAM_INFO = gql("""
query GetTeamInfo($teamId: ID!) {
  team(id: $teamId) {
    id
    name
    logoUrl
    rating
  }
}
""")

# GraphQL Query: Search for teams by name
SEARCH_TEAMS = gql("""
query SearchTeams($nameFilter: String!, $limit: Int!) {
  teams(
    first: $limit
    filter: {
      name: { contains: $nameFilter }
    }
  ) {
    edges {
      node {
        id
        name
        logoUrl
      }
    }
  }
}
""")
