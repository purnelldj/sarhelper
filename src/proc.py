import hydra
from hydra.utils import instantiate
from omegaconf import DictConfig
from omegaconf.errors import ConfigAttributeError

from datamodules.base import Datamod, Product


@hydra.main(config_path="conf", config_name="main", version_base=None)
def main(cfg: DictConfig):
    # instantiate data class
    datamod: Datamod = instantiate(cfg.dataset)
    print("instantiated datamodule")

    try:
        pipeline = cfg.dataset.pipeline
    except ConfigAttributeError:
        raise Exception("pipeline is missing from config file")

    if "timeseries" in pipeline:
        prods = []

    # run processing steps
    for file in datamod.filelist:
        print(f"processing file: \n {file}")
        try:
            prod: Product = datamod.read_file(file)
        except Exception as e:
            print(e)
            print("issue with file - skipping...")

        for ind, action in enumerate(pipeline):
            print(f"\n action ({ind+1}/{len(pipeline)}): {action} \n")

            if action == "subset":
                prod = datamod.subset(prod, **cfg.dataset)
                if prod is None:
                    print("skipping file")
                    break
                print("successfully obtained subset")

            if action == "plot":
                datamod.plot(prod, **cfg.dataset)

            if action == "save":
                datamod.save(prod, **cfg.dataset)

            if action == "timeseries":
                prods.append(prod)

    # now collecting data in timeseries
    if "timeseries" in pipeline:
        print("collecting time series to save")

        datamod.timeseries(prods)

    print(f"finished processing {len(datamod.filelist)} files")


if __name__ == "__main__":
    main()
