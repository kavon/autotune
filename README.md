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

Here's what the progress of the tuning would look like:

```
[     6s]    INFO opentuner.search.plugin.DisplayPlugin: tests=7, best #13, cost time=20.7208, found by UniformGreedyMutation
[    13s]    INFO opentuner.search.plugin.DisplayPlugin: tests=21, best #48, cost time=19.7285, found by NormalGreedyMutation
[    19s]    INFO opentuner.search.plugin.DisplayPlugin: tests=28, best #53, cost time=19.5277, found by UniformGreedyMutation
[    27s]    INFO opentuner.search.plugin.DisplayPlugin: tests=42, best #53, cost time=19.5277, found by UniformGreedyMutation
[    36s]    INFO opentuner.search.plugin.DisplayPlugin: tests=56, best #53, cost time=19.5277, found by UniformGreedyMutation
[    44s]    INFO opentuner.search.plugin.DisplayPlugin: tests=70, best #53, cost time=19.5277, found by UniformGreedyMutation
[    51s]    INFO opentuner.search.plugin.DisplayPlugin: tests=83, best #82, cost time=19.3576, found by UniformGreedyMutation
```

Note that the value of "time" is just the output of the objective function, which the tuner is
trying to minimise. It has a relationship with the compile and run time of the program being
tuned, but it's not easy to describe what it is here.

Run `./src/tune_llvm.py -h` for more options.

#### tuning without fully compiling the program

When the tuner is set to `optonly` mode, it will only run the `optimize` and `opt_stats`
targets of the makefile.
In this mode, the `optimize` phase will be expected to save the optimization statistics 
in a JSON format, and the `opt_stats` should output the JSON data to `stdout`. 
Optimization statistics can be saved by LLVM if you pass the following flags to `opt`:

```
-stats -stats-json -info-output-file <filename>
```

Note that you must build LLVM with either `LLVM_ENABLE_STATS` or Assertions enabled.
A Release build is reccomended to speed up tuning.
