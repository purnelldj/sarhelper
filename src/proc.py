import hydra
from hydra.utils import instantiate
from omegaconf import DictConfig


@hydra.main(config_path="conf", config_name="main", version_base=None)
def main(cfg: DictConfig):
    # instantiate data class
    datamod = instantiate(cfg.dataset_inst, cfg.dataset)

    # run processing steps
    for file in datamod.filelist:
        print(f"processing file: \n {file}")

        file_data = datamod.read_file(file)

        if cfg.pipeline.subset:
            datamod.subset(file_data)

        if cfg.pipeline.plot:
            datamod.plot(file_data)

        if cfg.pipeline.save:
            datamod.save(file_data)

    print(f"finished processing {len(datamod.filelist)} files")


if __name__ == "__main__":
    main()
