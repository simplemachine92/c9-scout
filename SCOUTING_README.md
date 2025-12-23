# GRID Esports Scouting Program - API Reference

This document explains the key components of the GRID GraphQL API that are essential for building an automated scouting program that analyzes upcoming opponents' recent match data.

## Core Query: `allSeries()`

**Why it's critical**: This is the heart of your scouting program. It retrieves all match/series data with powerful filtering capabilities.

**Key Parameters**:
- `filter: SeriesFilter` - **MOST IMPORTANT**: Filter by opponent team IDs, time ranges, and game types
- `orderBy: StartTimeScheduled` + `orderDirection: DESC` - Get most recent matches first
- `first: Int` - Limit to recent matches (e.g., first: 20 for last 20 matches)

**Scouting Use Case**: Get all recent competitive matches for an opponent team within the last 30 days.

## Essential Filters

### `SeriesFilter`
**Why it's critical**: Controls what match data you retrieve - the foundation of targeted scouting.

**Key Fields for Scouting**:
- `teamIds: IdFilter` - **CORE**: Filter to only matches involving your opponent
- `startTimeScheduled: DateTimeFilter` - **CORE**: Get recent matches (e.g., gte: "2024-12-01")
- `types: [ESPORTS]` - Focus on competitive matches, not scrims
- `titleIds: IdFilter` - Filter by specific games (VAL, LoL, etc.)

### `DateTimeFilter`
**Why it's critical**: Ensures you only analyze recent, relevant performance data.

**Scouting Use Case**: Set `gte` to 30 days ago to focus on current form and strategies.

## Data Structures

### `Series` Type
**Why it's critical**: Contains all match information needed for scouting reports.

**Key Fields for Scouting**:
- `title: Title` - Which game was played (VAL vs LoL strategy differences)
- `teams: [TeamParticipant]` - Who played and their score advantage (win/loss + margin)
- `players: [Player]` - Full roster for each match (comp analysis)
- `format: SeriesFormat` - BO1, BO3, etc. (strategy implications)
- `startTimeScheduled: DateTime` - When the match happened (recency)

### `TeamParticipant`
**Why it's critical**: Shows team performance in specific matches.

**Key Fields**:
- `baseInfo: Team` - Team details
- `scoreAdvantage: Int` - **CRITICAL**: Win/loss indicator and margin of victory

### `Player` Type
**Why it's critical**: Individual player analysis for tendency identification.

**Key Fields for Scouting**:
- `roles: [PlayerRole]` - **CRITICAL**: Player positions (MID, SUPPORT, etc.) for comp analysis
- `nickname: String` - Player identification
- `team: Team` - Current team affiliation
- `nationality: [Nationality]` - Regional playstyle tendencies
- `age: Int` - Experience level indicator

## Supporting Queries

### `players()` Query
**Why it's important**: Get detailed player information for opponent team analysis.

**Key Use**: After identifying an opponent team, get all their players with roles to understand their roster composition.

**Filter Strategy**: Use `teamIdFilter` to get all players on the opponent team.

### `teams()` Query
**Why it's important**: Find opponent teams and get their basic information.

**Key Use**: Search for teams by name to get their ID for series filtering.

### `playerRoles()` Query
**Why it's important**: Understand the role structure for different games.

**Key Use**: Map player roles to understand comp compositions (e.g., what makes a "standard" VAL comp).

## Ordering and Pagination

### `SeriesOrderBy.StartTimeScheduled` + `OrderDirection.DESC`
**Why it's critical**: Ensures you analyze the most recent matches first.

**Scouting Logic**: Recent matches are more indicative of current strategies than old matches.

### Pagination
**Why it's important**: Handle large result sets efficiently.

**Strategy**: Use `first: 20` to limit to most recent matches, then paginate if needed.

## Scouting Report Generation Strategy

1. **Team Identification**: Use `teams()` to find opponent team ID
2. **Recent Matches**: Query `allSeries()` with team ID filter and recent date range
3. **Player Analysis**: Use `players()` to get opponent roster with roles
4. **Comp Analysis**: Analyze player role combinations across recent series
5. **Performance Trends**: Track win/loss ratios and score advantages over time
6. **Strategy Patterns**: Identify common matchups and formats played

## Game-Specific Considerations

### Valorant (VAL)
- Focus on `playerRoles` to identify agent compositions
- Look for default site setups through repeated strategies
- Analyze team compositions for common agent picks

### League of Legends (LoL)
- Track champion pool tendencies through player roles
- Identify common comp strategies (e.g., poke vs dive)
- Analyze team synergy patterns

## Performance Optimization

- **Cache team/player IDs**: Don't query for IDs repeatedly
- **Limit date ranges**: Use 30-60 day windows for current form
- **Filter by ESPORTS only**: Exclude scrims and test matches
- **Batch requests**: Use single queries with array filters where possible

## Error Handling

- Handle pagination carefully (hasNextPage, endCursor)
- Account for missing data (optional fields)
- Implement retry logic for rate limiting
- Validate team/player IDs before querying series

This focused schema contains everything needed to build a comprehensive scouting system that can automatically generate insights about opponent strategies, player tendencies, and competitive patterns.
