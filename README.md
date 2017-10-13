# autotune
discovers good LLVM passes for GHC

## how to use

Here's an example:

```
./src/tune_llvm.py --no-dups --stop-after=30 --parallelism 8
```

Run `./src/tune_llvm.py -h` for more options.
