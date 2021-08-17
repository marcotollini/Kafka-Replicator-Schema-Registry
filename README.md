# Kafka Replicator with Confluent Schema Registry

This simple Kafka Replicator is used to replicate all the messages from one or more kafka topics in a source Kafka Cluster, and replicate those messages into a different destination Kafka Cluster.

It works similarly to MirrorMaker2, but it has support for Confluent Schema Registry. It works similarly to Confluent Replicator, but open source. Obviously, those two solutions are way more advanced, but this script is a free alternative when you rely on two separated Schema Registries.

## Main purpose

In big infrastructure, it is possible that you need two separated environments, each one with a Confluent Schema Registry. In this case, the id of the two registries might not be align, and the follower mode might not suits all the needs.

This scripts, written in Python, reads the message encoded in Avro, parses only the magic byte and the schema id, goes to the source Schema Registry, fetches the Avro screema, registers the Avro schema into the destination schema registry, modifies the original message to substitute the new ID of the schema, and produces the message in the destination kafka topic.

You can achieve the same with Confluent Replicator (and much more), which requires and Enterprise license.

## Literature

- https://docs.confluent.io/3.2.0/schema-registry/docs/serializer-formatter.html#wire-format
- https://towardsdatascience.com/replicate-avro-messages-to-target-part1-conflicting-schema-exists-on-target-8489df60fd05
