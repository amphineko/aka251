# aka251.py

This tiny program monitors your GPU usage (currently NVIDIA only) and runs your command when the GPU is free.

```
usage: aka251.py [-h] [--command COMMAND] [--index DEVICE_INDEX] [--interval INTERVAL]
```

With `--index` not supplied to query available devices.

It checks every `--interval` seconds when the GPU is not in use, spawns your program and kills next `--interval` seconds when another process comes up.
