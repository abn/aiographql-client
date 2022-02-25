const { ApolloServer, gql, PubSub } = require("apollo-server");
const faker = require("faker");

const pubsub = new PubSub();

const typeDefs = gql`
  type Query {
    ping: String
  }
  type Subscription {
    messageAdded: String
  }
`;

const resolvers = {
  Query: {
    ping: () => "pong"
  },
  Subscription: {
    messageAdded: {
      subscribe: () => pubsub.asyncIterator("messageAdded")
    }
  }
};

setInterval(() => {
  pubsub.publish("messageAdded", {
    messageAdded: faker.lorem.sentence()
  });
}, 1000);

const server = new ApolloServer({
  typeDefs,
  resolvers
});

server.listen().then(({ url }) => {
  console.log(`Listening at ${url}`);
});
