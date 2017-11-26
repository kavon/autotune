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
targets of the Makefile.
In this mode, the `optimize` phase will be expected to save the optimization statistics 
in a JSON format, and the `opt_stats` target should output the JSON data to `stdout`. 
Optimization statistics can be saved by LLVM like so:

```
opt -disable-output -stats -stats-json -info-output-file <json file> <passes> <ir file> 
```

Note that you must build LLVM with either `LLVM_ENABLE_STATS` or Assertions enabled.
A Release build is reccomended to speed up tuning.


#### Fuzzing and Error Handling

When a failure is detected (currently, via non-zero exit code), the tuner will automatically
try to find a reduced subsequence of passes that causes the failure.
Thus, autotuner is also is useful for testing compiler frontends and/or LLVM itself.
Here is an example of what this process looks like:

```
➤ ./src/tune_llvm.py --no-dups --display-frequency=5 --parallelism 8 --stop-after=800
Building initial bitcode ...
done!
[    55s]    INFO opentuner.search.plugin.DisplayPlugin: tests=8, best #224, cost time=-8717.5000, found by DifferentialEvolutionAlt
[    61s]    INFO opentuner.search.plugin.DisplayPlugin: tests=16, best #261, cost time=-11607.0000, found by UniformGreedyMutation
[    66s]    INFO opentuner.search.plugin.DisplayPlugin: tests=24, best #261, cost time=-11607.0000, found by UniformGreedyMutation
[    77s]    INFO opentuner.search.plugin.DisplayPlugin: tests=40, best #261, cost time=-11607.0000, found by UniformGreedyMutation
[    84s]    INFO opentuner.search.plugin.DisplayPlugin: tests=48, best #277, cost time=-15527.2500, found by UniformGreedyMutation
autotune error executing: 
ID=55 PASSES="-disable-output -targetlibinfo -tti -tbaa -scoped-noalias -assumption-cache-tracker -profile-summary-info -forceattrs -inferattrs -mem2reg -lower-expect -loop-accesses -div-rem-pairs -lcssa -loop-distribute -indvars -lcssa-verification -globaldce -loop-deletion -alignment-from-assumptions -globaldce -loop-unroll -loop-unswitch -speculative-execution -inline -loop-vectorize -gvn -nary-reassociate -simplifycfg -gvn -globals-aa -barrier -lcssa-verification -memdep -loop-simplify -functionattrs -lazy-branch-prob -memcpyopt -jump-threading -loop-accesses -loop-unswitch -slsr -prune-eh -indvars -deadargelim -functionattrs -bdce -nary-reassociate -loop-vectorize -argpromotion -slsr -loop-unswitch -scalar-evolution -block-freq -libcalls-shrinkwrap -globaldce -memdep -memcpyopt -block-freq -sccp -reassociate -demanded-bits -prune-eh -loop-idiom -instsimplify -instcombine -loop-accesses -deadargelim -postdomtree -always-inline -nary-reassociate -sccp -adce -prune-eh -basicaa -float2int -lcssa -lazy-value-info -loop-vectorize -early-cse -instsimplify -globalopt -strip-dead-prototypes -dse -loop-vectorize -loop-deletion -inline -loop-unswitch -basicaa -elim-avail-extern -memcpyopt -argpromotion -branch-prob -basiccg -sccp -dse -sccp -instcombine -loop-accesses -branch-prob -memoryssa -reassociate -tailcallelim -memcpyopt -available-load-scan-limit=14 -inline-threshold=11855 -jump-threading-threshold=7 -loop-distribute-scev-check-threshold=6 -loop-load-elimination-scev-check-threshold=5 -loop-unswitch-threshold=1421 -max-dependences=7 -max-nested-scalar-reduction-interleave=1 -max-num-inline-blocks=14 -max-recurse-depth=201 -max-uses-for-sinking=54 -memdep-block-number-limit=291" make -f ./programs/nofib/tune.mk optimize
---------------------------------------------
make command returned non-zero exit code!!
died during OPTIMIZE... trying to reduce the pass configuration.
Auto-reduce Starting...

[ ... progress output, etc ... ]

Here is the smallest failure case I've found:
autotune error executing: 
ID=186 PASSES="-mem2reg -inline -gvn" make -f ./programs/nofib/tune.mk optimize
```
