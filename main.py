#! /usr/bin/env python3
from parse import HubProcesser, ConnectionProcesser, DroneNumProcesser
from parse import DataStream, ProcessedData, read_file
from algorithm import MoveDrone


def main() -> None:
    try:
        config: list[str] = read_file()
        hubprc = HubProcesser()
        conprc = ConnectionProcesser()
        dronenumprc = DroneNumProcesser()
        datastream = DataStream()
        prcddata = ProcessedData()
        datastream.register_processer(hubprc)
        datastream.register_processer(conprc)
        datastream.register_processer(dronenumprc)
        datastream.process_stream(config)
        prcddata.append_zone(hubprc.output())
        prcddata.append_connection(conprc.output())
        prcddata.create_drones(dronenumprc.output()[1])
        movedrone: MoveDrone = MoveDrone(prcddata)
        movedrone.start_algo()
        movedrone.output_log()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
