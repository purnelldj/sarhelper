import hydra
from hydra.utils import instantiate
from omegaconf import DictConfig

from datamodules.base import Datamod, Product


@hydra.main(config_path="conf", config_name="main", version_base=None)
def main(cfg: DictConfig):
    # instantiate data class
    datamod: Datamod = instantiate(cfg.dataset_inst, cfg.dataset)

    # run processing steps
    for file in datamod.filelist:
        print(f"processing file: \n {file}")

        prod: Product = datamod.read_file(file)

        if cfg.pipeline.subset:
            datamod.subset(prod)

        if cfg.pipeline.plot:
            datamod.plot(prod)

        if cfg.pipeline.save:
            datamod.save(prod)

    print(f"finished processing {len(datamod.filelist)} files")


if __name__ == "__main__":
    main()
