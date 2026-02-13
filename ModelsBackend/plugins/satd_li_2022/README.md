# SATD Detector Plugin (Li et al., 2022)

## Overview
This plugin provides an automated **Self-Admitted Technical Debt (SATD)** identification service for the TagDebt Bot. It implements the machine learning approach proposed by Li et al. (2022) to analyze and categorize technical debt mentioned by developers in GitHub issues.

## Research Context
This implementation is based on the following study:
**Automatic identification of self-admitted technical debt from four different sources**
*Authors: Yikun Li, Mohamed Soliman, Paris Avgeriou*

### Key Findings and Performance
- The approach achieves an average **F1-score of 0.611** across four different sources (comments, commits, pull requests, and issues).
- It is capable of detecting and distinguishing between four types of SATD:
  - **Code/Design Debt**
  - **Requirement Debt**
  - **Documentation Debt**
  - **Test Debt**

## Technical Details
The detector uses a Deep Learning model (TensorFlow/Keras) combined with FastText word embeddings. It tokenizes input text using NLTK and classifies it into `SATD` or `non-SATD` categories (configured for the bot's default behavior).

### Requirements
The following dependencies are required for this plugin (see `requirements.txt`):
- `tensorflow`
- `fasttext`
- `nltk`
- `numpy`

## Setup and Data Files
To function correctly, this plugin requires pre-trained weight and embedding files to be placed in the `data/` directory.

1. Download the required files from [Zenodo](https://zenodo.org/records/7821209).
2. Add them to `ModelsBackend/plugins/satd_li_2022/data/` as follows:
    - Rename `fasttext_issue_300.bin` to `embeddings.bin`
    - Rename `satd_detector_for_issues.hdf5` to `weights.hdf5`

## Citation
If you use this plugin or the underlying model in your research, please cite the original paper:

```bibtex
@article{li2023automatic,
  author = {Li, Yikun and Soliman, Mohamed and Avgeriou, Paris},
  title = {Automatic identification of self-admitted technical debt from four different sources},
  journal = {Empirical Software Engineering},
  year = 2023,
  month = {Apr},
  day = 15,
  volume = 28,
  number = 65,
  issn = {1573-7616},
  doi = {10.1007/s10664-023-10297-9},
}
```

## Contact
For questions regarding the original research and model:
- :email: [yikun.li@rug.nl](mailto:yikun.li@rug.nl)
