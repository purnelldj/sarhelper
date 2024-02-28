import hydra
from hydra.utils import instantiate
from omegaconf import DictConfig
from omegaconf.errors import ConfigAttributeError

from datamodules.base import Datamod, Product


@hydra.main(config_path="conf", config_name="main", version_base=None)
def main(cfg: DictConfig):
    # instantiate data class
    datamod: Datamod = instantiate(cfg.dataset)

    # run processing steps
    for file in datamod.filelist:
        print(f"processing file: \n {file}")
        prod: Product = datamod.read_file(file)

        try:
            pipeline = cfg.dataset.pipeline
        except ConfigAttributeError:
            raise Exception("pipeline is missing from config file")

        for ind, action in enumerate(pipeline):
            print(f"action ({ind+1}/{len(pipeline)}): {action}")

            if action == "subset":
                prod = datamod.subset(prod, **cfg.dataset)
                print("successfully obtained subset")

            if action == "plot":
                datamod.plot(prod, **cfg.dataset)

            if action == "save":
                datamod.save(prod, **cfg.dataset)

    print(f"finished processing {len(datamod.filelist)} files")


if __name__ == "__main__":
    main()
