import argparse
from confluent_kafka import Consumer, Producer
from confluent_kafka.avro.cached_schema_registry_client import CachedSchemaRegistryClient
import json
import traceback
import signal

class SchemaMapper:
    def __init__(self, src_schema_conf, dst_schema_conf, subject_name):
        self.src_schema_registry = CachedSchemaRegistryClient(src_schema_conf)
        self.dst_schema_registry = CachedSchemaRegistryClient(dst_schema_conf)
        self.map = {}
        self.subject_name = subject_name

        self.dst_schema_registry.update_compatibility('NONE', subject_name)

    def get_dst_schema_id(self, src_id):
        if src_id in self.map:
            return self.map[src_id]

        avro_schema = self.src_schema_registry.get_by_id(src_id)
        dst_id = self.dst_schema_registry.register(self.subject_name, avro_schema)

        print(f'Registered source schema id {src_id} to destionation schema registry with id {dst_id}')
        self.map[src_id] = dst_id

        return dst_id


def parse_args():
    parser = argparse.ArgumentParser(description='Python Replicator with schema registry support')

    parser.add_argument(
        '-c',
        '--config',
        default='./config.json',
        dest="config_path",
        type=str,
        help="Path of config file",
    )

    args = parser.parse_args()
    return args

def config_reader(config_path):
    with open(config_path, 'r') as fp:
        return json.load(fp)

def get_consumer(kafka_config, topics):
    c = Consumer(kafka_config)
    c.subscribe(topics)
    return c

def get_producer(kafka_config):
    p = Producer(kafka_config)
    return p

def unpack(value):
    magic_byte = value[0]
    if magic_byte != 0:
        raise Exception('Magic byte should be always 0. Is data AVRO encoded?')

    schema_id = int.from_bytes(value[1:5], byteorder='big')

    data = value[5:]

    return schema_id, data

def pack(schema_id, data):
    magic_byte = 0
    magic_byte_b = magic_byte.to_bytes(1, byteorder='big')
    schema_id_b = schema_id.to_bytes(4, byteorder='big')

    return magic_byte_b + schema_id_b + data

def acked(err, msg):
    if err is not None:
        print("Failed to deliver message: %s: %s" % (str(msg), str(err)))

running = True
def exit_gracefully(signal, frame):
    global running
    running = False

def main():
    args = parse_args()
    config = config_reader(args.config_path)

    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    schema_mapper = SchemaMapper(config['src_schema_registry'], config['dst_schema_registry'], config['subject_name'])
    c = get_consumer(config['src_kafka'], config['src_topics'])
    p = get_producer(config['dst_kafka'])

    try:
        while running:
            msg = c.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue
            # https://docs.confluent.io/3.2.0/schema-registry/docs/serializer-formatter.html#wire-format
            value = msg.value()
            try:
                src_schema_id, data = unpack(value)
                dst_schema_id = schema_mapper.get_dst_schema_id(src_schema_id)
                new_value = pack(dst_schema_id, data)
                p.produce(config['dst_topic'], value=new_value, callback=acked)
                p.poll(0)
            except Exception as e:
                traceback.print_exc()
    finally:
        p.flush()
        c.close()




if __name__ == '__main__':
    main()



