# nsrl

Creating the NSRL RDS dataset was not straightforward and involved a lot a manual data cleaning due to the dataset's size and dirtyness.

We combined the `2025.03.1` [`modern pc`](https://s3.amazonaws.com/rds.nsrl.nist.gov/RDS/rds_2025.03.1/RDS_2025.03.1_modern_minimal.zip) and [`legacy pc`](https://s3.amazonaws.com/rds.nsrl.nist.gov/RDS/rds_2025.03.1/RDS_2025.03.1_legacy_minimal.zip) SQL databases from NIST and reduced the dataset to unique filenames.
The package and OS information are inconsistent, which is why we only used them to prune all non-UNIXoid software data and then extract the filenames. The hash datasets are of no use to juicepress since, depending on compiler settings, ELF hashes are rarely equal across multiple firmware images.

Detail information can be found in the documentation folder. We provide the resulting `nsrl_file.csv` table in this folder.
