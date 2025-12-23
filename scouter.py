import asyncio, os
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

# Environment variables (set these in your shell or use a .env file)
ENDPOINT = os.getenv("GRAPHQL_ENDPOINT", "https://api-op.grid.gg/central-data/graphql")
API_KEY = os.getenv("API_KEY")

async def create_client():
    headers = {"Content-type": "application/json"}
    if API_KEY: headers["X-API-Key"] = API_KEY
    # Disable SSL verification for development/testing
    transport = AIOHTTPTransport(url=ENDPOINT, headers=headers, ssl=False)
    return Client(transport=transport, fetch_schema_from_transport=False)

async def find_c9_organization():
    """Find Cloud9 organization and their teams - Step 1 of intelligence gathering"""
    try:
        client = await create_client()
        query = gql("""
        query FindC9Organization {
          organizations(filter: { name: { equals: "Cloud9" } }) {
            edges {
              node {
                id
                name
                teams {
                  id
                  name
                  nameShortened
                  title {
                    id
                    name
                    nameShortened
                  }
                  rating
                  logoUrl
                }
              }
            }
          }
        }
        """)
        result = await client.execute_async(query)

        organizations = result['organizations']['edges']
        if not organizations:
            print("❌ Cloud9 organization not found")
            return []

        c9_org = organizations[0]['node']
        print(f"✅ Found organization: {c9_org['name']} (ID: {c9_org['id']})")
        print(f"📊 Teams: {len(c9_org['teams'])}")

        team_ids = []
        for team in c9_org['teams']:
            print(f"🏆 {team['name']} ({team['nameShortened']})")
            print(f"   ID: {team['id']}")
            print(f"   Game: {team['title']['name']} ({team['title']['nameShortened']})")
            print(f"   Rating: {team.get('rating', 'N/A')}")
            print(f"   Logo: {team['logoUrl']}")
            team_ids.append(team['id'])
            print()

        return team_ids

    except Exception as e:
        error_msg = str(e)
        if "unauthorized" in error_msg.lower() or "unauthenticated" in error_msg.lower():
            print("❌ API authentication failed. Please check your API_KEY.")
            print("💡 Make sure to set a valid API_KEY environment variable:")
            print("   export API_KEY=your_actual_api_key_here")
        else:
            print(f"❌ Error: {error_msg}")
        return []

async def main():
    print("C9 Intelligence Scouter - Step 1: Find C9 Organization")
    if not API_KEY:
        print("No API key found! Set API_KEY environment variable.")
        return

    team_ids = await find_c9_organization()

    if team_ids:
        print(f"Collected {len(team_ids)} team IDs for next steps: {team_ids}")
    else:
        print("No teams found for Cloud9")

if __name__ == "__main__":
    asyncio.run(main())
