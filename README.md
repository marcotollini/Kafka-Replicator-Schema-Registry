# Kafka Replicator with Confluent Schema Registry
This simple Kafka Replicator is used to replicate all the messages from one or more kafka topics in a source Kafka Cluster, and replicate those messages into a different destination Kafka Cluster.

It works similarly to MirrorMaker2, but it has support for Confluent Schema Registry. It works similarly to Confluent Replicator, but open source. Obviously, those two solutions are way more advanced, but this script is a free alternative when you rely on two separated Schema Registries.

## Why?
In big infrastructure, it is possible that you need two separated environments, each one with a seprated Confluent Schema Registry. In this case, the subject IDs of the two registries might not align. As a result, you can't clone the topic 1:1, as the consumer using the second schema registry would not be able to decode the avro message. Confluent Schema Registry has a "follower" mode, which might not suits all the needs. For example, in our use case we did not want to replicate all the subjects in an external schema registry.

## How?
The script does the following:

1. reads a message encoded in Avro from `src_topics`
2. parses the magic byte (the schema ID)
3. downloads the Avro schema from `src_schema_registry` using the parsed schema ID
4. uploads the downloaded Avro schema into `dst_schema_registry` with subject `subject_name`
5. get the schema ID from `dst_schema_registry`
6. substitutes the magic byte in the original kafka message
7. produces the newly composed message into `dst_topic`

Steps 3 to 5 are avoided thanks to local cache: it keeps a map between IDs from `src_schema_registry` to `dst_schema_registry`.

Important note is that the message is not decoded, with important performance benefits.

The original subject name is not respected as a schema ID might have more than one subjects.

**The compatibility mode of `subject_name` SHOULD BE NONE,** as multiple subjects in `src_schema_registry` will be mapped into a single subject in `dst_schema_registry`.

You can achieve the same with Confluent Replicator (and much more), which requires and Enterprise license.

## How to make it work

```py
python.exe .\replicator.py -h
usage: replicator.py [-h] [-c CONFIG_PATH]

Python Replicator with schema registry support

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_PATH, --config CONFIG_PATH
                        Path of config files
```


## Next?
- Add support to [NamingStrategies](https://docs.confluent.io/platform/current/schema-registry/serdes-develop/index.html#how-the-naming-strategies-work) to create a mapping between subjects in `src_schema_registry` and subjects in `dst_schema_registry`.



## Literature
- https://docs.confluent.io/3.2.0/schema-registry/docs/serializer-formatter.html#wire-format
- https://towardsdatascience.com/replicate-avro-messages-to-target-part1-conflicting-schema-exists-on-target-8489df60fd05
