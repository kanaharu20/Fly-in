#! /usr/bin/env python3
import sys
from config import ProcessedData, HubProcesser, ConnectionProcesser, DataStream


def read_file() -> list[str]:
    argv: list[str] = sys.argv
    filename: str = argv[1]
    try:
        with open(filename) as fd:
            ret: list[str] = fd.readlines()
    except Exception as e:
        print(e)
    return ret


def main() -> None:
    config: list[str] = read_file()
    hubprc = HubProcesser()
    conprc = ConnectionProcesser()
    datastream = DataStream()
    prcddata = ProcessedData()
    datastream.register_processer(hubprc)
    datastream.register_processer(conprc)
    datastream.process_stream(config)
    prcddata.append_zone(hubprc.output())
    prcddata.append_connection(conprc.output())
    for name in prcddata._zone_name_list:
        print(f"{prcddata._zone_dict[name]}")


if __name__ == "__main__":
    main()
