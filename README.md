# t4morley-auto

Automation tools for T4 Morley

## Run as Python script

### Prerequisites

#### Install Dependency Packages

```
pip install selenium pandas
```

### Usage

```
python take_items_offline.py [offline_items.csv]
```

- `offline_items.csv`: The filename of a CSV file contains the items to be taken offline.
    If not specified, the default filename is `offline_items.csv`.
