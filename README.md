# t4auto

Automation tools for T4.

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


## License

The software is available under the Apache License Version 2.0.

This software utilizes Material Design icons by Google. The icons are used under the terms of the Apache License Version 2.0. Material Design icons are a collection of icons optimized for use with web, Android, and iOS applications, developed and maintained by Google.

We acknowledge and respect Google's copyright and the Apache License 2.0 under which the Material Design icons are distributed. For more information on the Material Design icons and to review the terms of the Apache License Version 2.0, please visit Google's [Material Design icons](https://github.com/google/material-design-icons) library.

This software is developed using PySide6, the official set of Python bindings for the Qt application framework. PySide6 is dynamically linked in this application to comply with the LGPL license under which PySide6 is distributed. This allows for the use of PySide6 within this software without requiring the entire application to be subject to the terms of the LGPL.

Users of this software are provided with the option to replace the PySide6 component in accordance with the LGPL terms. For more information on PySide6 and its licensing, please visit [the official website](https://www.qt.io/qt-for-python).
