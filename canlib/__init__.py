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
def generate_lib(net: Path, ids: Path, out: Path):
    generators.lib.generate(net, ids, out)


@main.command()
@click.argument("net", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("ids", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("out", type=click.Path(file_okay=False, path_type=Path))
def generate_proto(net: Path, ids: Path, out: Path):
    generators.proto.generate(net, ids, out)


@main.command()
@click.argument("net", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("ids", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("out", type=click.Path(file_okay=False, path_type=Path))
def generate_csv(net: Path, ids: Path, out: Path):
    generators.csv.generate(net, ids, out)


@main.command()
@click.argument("net", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("ids", type=click.Path(file_okay=False, path_type=Path))
@click.argument("lib", type=click.Path(file_okay=False, path_type=Path))
@click.argument("proto", type=click.Path(file_okay=False, path_type=Path))
@click.argument("csv", type=click.Path(file_okay=False, path_type=Path))
def generate_all(net: Path, ids: Path, lib: Path, proto: Path, csv: Path):
    generators.id.generate(net, ids)
    generators.lib.generate(net, ids, lib)
    generators.proto.generate(net, ids, proto)
    generators.csv.generate(net, ids, csv)


if __name__ == "__main__":
    main()
