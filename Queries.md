Find Loud Esports team

query GetTeam {
  teams(filter: {name : {equals: "Loud"}}) {
    edges {
      cursor
      node {
        ...teamFields
      }
    }
  }
}