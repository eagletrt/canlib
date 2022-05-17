from pathlib import Path

import click

from canlib import generators


@click.group()
def main():
    pass


@main.command()
@click.argument("net", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("out", type=click.Path(file_okay=False, path_type=Path))
def generate_ids(net: Path, out: Path):
    generators.id.generate(net, out)


@main.command()
@click.argument("net", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("out", type=click.Path(file_okay=False, path_type=Path))
def generate_sources(net: Path, ids: Path, out: Path):
    generators.sources.generate(net, ids, out)


@main.command()
@click.argument("net", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("ids", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("out", type=click.Path(file_okay=False, path_type=Path))
def generate_protobuf(net: Path, ids: Path, out: Path):
    generators.protobuf.generate(net, ids, out)


@main.command()
@click.argument("net", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("ids", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("out", type=click.Path(file_okay=False, path_type=Path))
def generate_protobuf(net: Path, ids: Path, out: Path):
    generators.protobuf.generate(net, ids, out)


@main.command()
@click.argument("net", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("ids", type=click.Path(file_okay=False, path_type=Path))
@click.argument("sources", type=click.Path(file_okay=False, path_type=Path))
@click.argument("proto", type=click.Path(file_okay=False, path_type=Path))
@click.argument("sheets", type=click.Path(file_okay=False, path_type=Path))
def generate_all(net: Path, ids: Path, sources: Path, proto: Path, sheets: Path):
    generators.id.generate(net, ids)
    generators.sources.generate(net, ids, sources)
    generators.protobuf.generate(net, ids, proto)
    generators.csv.generate(net, ids, sheets)


if __name__ == "__main__":
    main()
