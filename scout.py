import os
import asyncio
from dotenv import load_dotenv
from clients.central_client.client import CentralDbClient
from clients.central_client.fragments import TeamFields
from clients.stats_client.client import StatsClient
from clients.series_client.client import SeriesClient

async def main():

    ### --- Create our clients --- ###
    load_dotenv()
    API_KEY = os.getenv("API_KEY")

    central_client = CentralDbClient(
        url="https://api-op.grid.gg/central-data/graphql",
        headers={"x-api-key": API_KEY}
    )
    print("Ariadne Client 1 initialized.")

    stats_client = StatsClient(
        url="https://api-op.grid.gg/statistics-feed/graphql",
        headers={"x-api-key": API_KEY}
    )
    print("Ariadne Client 2 initialized.")

    series_client = SeriesClient(
        url="https://api-op.grid.gg/live-data-feed/series-state/graphql",
        headers={"x-api-key": API_KEY}
    )
    print("Ariadne Client 3 initialized.")

    ### --- Get the opponents team id. --- ###
    response = await central_client.get_team_by_exact_name("LOUD")

    # Guards and validation
    try:
        team_node = response.teams.edges[0].node
        opponent = TeamFields.model_validate(team_node)
        print(opponent.id)
    except (AttributeError, IndexError):
        print("Team not found.")

asyncio.run(main())