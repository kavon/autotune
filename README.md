# autotune
A program that discovers good LLVM passes for GHC. Based on OpenTuner.

**NOTE** This repository is still early on in development, so it currently optimizes some simple C++ programs. Eventually it will optimize Haskell programs. I will try to structure this tuner so it works for any compiler that uses LLVM.

## setup

1. Install [OpenTuner](http://opentuner.org/tutorial/setup/).
2. Download/Install LLVM 5
3. 

## how to use

Here's an example:

```
./src/tune_llvm.py --no-dups --display-frequency=5 --parallelism 6 --stop-after=60
```

Run `./src/tune_llvm.py -h` for more options.
