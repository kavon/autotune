# autotune
discovers good LLVM passes for GHC

## how to use

Here's an example:

```
./src/tune_llvm.py --no-dups --display-frequency=5 --parallelism 6 --stop-after=60
```

Run `./src/tune_llvm.py -h` for more options.
