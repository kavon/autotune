
import json

OBJ_FUN_K = 'objfun'
ALL_PASSES_K = 'allpasses'
MAX_PASSES_K = 'maxpasses'
ALL_KNOBS_K = 'allknobs'
OPT_ONLY_K = 'optonly'

DEFAULT_MAX_PASSES = 200

# Returns the main structure of all optimization levels
def genOptLevels():
    opt_levels = {}
    
    ## TODO: make a dict
    
    opt_levels['-O0'] = {
                        OBJ_FUN_K : genCombineTimes(2, 1),     # objective function
                        ALL_PASSES_K : ALL_PASSES,             # optimization passes
                        MAX_PASSES_K : DEFAULT_MAX_PASSES,     # max passes
                        ALL_KNOBS_K : ALL_KNOBS                # knobs
                        }
                        
    opt_levels['-O1'] = {
                        OBJ_FUN_K : genCombineTimes(1, 2),
                        ALL_PASSES_K : ALL_PASSES,
                        MAX_PASSES_K : DEFAULT_MAX_PASSES,
                        ALL_KNOBS_K : ALL_KNOBS
                        }
                        
                        
    opt_levels['-O2'] = {
                        OBJ_FUN_K : genCombineTimes(1, 7),
                        ALL_PASSES_K : ALL_PASSES,
                        MAX_PASSES_K : DEFAULT_MAX_PASSES,
                        ALL_KNOBS_K : ALL_KNOBS
                        }
                        
                        
    opt_levels['-O3'] = {
                        OBJ_FUN_K : genCombineTimes(0, 10),
                        ALL_PASSES_K : ALL_PASSES,
                        MAX_PASSES_K : DEFAULT_MAX_PASSES,
                        ALL_KNOBS_K : ALL_KNOBS
                        }
                        
    opt_levels['optonly'] = {
                        OBJ_FUN_K : analyzeOptStats,
                        ALL_PASSES_K : ALL_PASSES,
                        MAX_PASSES_K : DEFAULT_MAX_PASSES,
                        ALL_KNOBS_K : ALL_KNOBS,
                        OPT_ONLY_K : ''  # only the presence of this key,val pair is needed
                        }
                        
    return opt_levels


def genCombineTimes(compileW, runtimeW, kind='sphere'):
    # Higher weight means that dimension is more important to minimize.
    
    def adjust(num):
        return round(num, 3) + 1.0
    
    # De Jong's spherical objective function, with tweaks.
    def spherical(compT, runT, compStats):
        compT = adjust(compT)
        runT = adjust(runT)
        return ((compileW * (compT ** 2))
                + (runtimeW * (runT ** 2)))
    
    def linear(compT, runT, compStats):
        compT = adjust(compT)
        runT = adjust(runT)
        return ((compileW * compT)
                + (runtimeW * runT))
                
    def runOnly(_, runT, compStats):
        runT += 1.0
        return (runT ** 2)
    
    switch = {
        'sphere' : spherical,
        'linear' : linear,
        'runOnly' : runOnly
    }
    
    assert kind in switch, "wrong objective function kind"
    
    return switch[kind]
    
    
def analyzeOptStats(compT, _ignore, compStats):
    data = json.loads(compStats)
    
    # dead simple heuristic: inlining + simplification
    # means the program is in some sense evaluated at compile time,
    # so there should be less to do at runtime.
    # machine learning to assign weights would be a lot fancier than intution :)
    
    # here are some statistics from instcount one could use:
    '''
    "instcount.NumAddInst": 100,
	"instcount.NumAllocaInst": 3,
	"instcount.NumBitCastInst": 14,
	"instcount.NumBrInst": 201,
	"instcount.NumCallInst": 74,
	"instcount.NumFAddInst": 21,
	"instcount.NumFCmpInst": 8,
	"instcount.NumFDivInst": 11,
	"instcount.NumFMulInst": 28,
	"instcount.NumFSubInst": 7,
	"instcount.NumGetElementPtrInst": 157,
	"instcount.NumICmpInst": 54,
	"instcount.NumLoadInst": 92,
	"instcount.NumMulInst": 46,
	"instcount.NumPHIInst": 67,
	"instcount.NumRetInst": 14,
	"instcount.NumSDivInst": 3,
	"instcount.NumSExtInst": 121,
	"instcount.NumSIToFPInst": 4,
	"instcount.NumSRemInst": 4,
	"instcount.NumStoreInst": 47,
	"instcount.NumSubInst": 75,
	"instcount.NumUIToFPInst": 1,
	"instcount.TotalBlocks": 215,
	"instcount.TotalFuncs": 14,
	"instcount.TotalInsts": 1152,
    '''
    
    # TODO probably worth making a multi-level dictionary
    # to handle pass.* and pass.specificStat weighting.
    
    # TODO probably worth applying linear regression or some other machine learning
    # technique to find relevant features and their weights so we can estimate the
    # level of "improvement" (running time) in a systematic way, instead of these
    # heurstics.
    
    # negative weight = we want to minimize this, positive weight = maximize this
    featureVector = [
        ("instcount.TotalInsts", -1.25),
        ("instcount.TotalBlocks", -3),
        ("instcount.TotalFuncs", -100),
        ("instcount.NumStoreInst", -10),
        ("instcount.NumLoadInst", -20),
        ("early-cse.NumSimplify", 2),
        ("early-cse.", 3),
        ("instcombine.", 2),
        ("inline.NumInlined", 100),
        ("inline.NumCallsDeleted", 100),
        ("instsimplify.", 2),
        ("adce.NumRemoved", 1),
        ("gvn.", 3),
        ("simplifycfg.", 3),
        ("loop-vectorize.LoopsVectorized", 10),
        ("licm.NumHoisted", 10),
        ("loop-delete.NumDeleted", 10),
        ("loop-unroll.NumUnrolled", 1)
    ]
    
    count = 0
    for name, val in data.iteritems():
        
        for feature, weight in featureVector:
            if name.startswith(feature):
                num = int(val)
                count += num * weight
                break
    
    # search is minimizing our output, and we
    # want to maximize our count, so we just negate.
    return -(float(count))
    
    
ALL_KNOBS = [
    # name, min, max  (inclusive)
    
    ("available-load-scan-limit", 0, 18), # uint, default = 6
    ("bonus-inst-threshold", 0, 10),      # uint, default = 1
    ("early-ifcvt-limit", 0, 90), # uint, default = 30
    
    # lower value = inline more aggressively
    # the actual min/max is INT_MIN, INT_MAX.
    # I've picked conservative values.
    ("inline-threshold", -32766, 32766),  # default = 225
    ("jump-threading-implication-search-threshold", 0, 10), # default = 3
    ("jump-threading-threshold", 0, 20), # default = 6
    ("licm-max-num-uses-traversed", 0, 24),  # uint, default = 8
    ("licm-versioning-max-depth-threshold", 0, 6), # uint, default = 2
    ("loop-distribute-scev-check-threshold", 0, 128), #uint, default = 8. 128 is the max if a pragma was given
    ("loop-interchange-threshold", -5, 5),  # default = 0
    ("loop-load-elimination-scev-check-threshold", 0, 24), # default = 8
    ("loop-unswitch-threshold", 0, 2000),  # uint, default = 100
    ("max-dependences", 0, 400), # uint, default = 100
    ("max-nested-scalar-reduction-interleave", 0, 6), # uint, default = 2
    ("max-num-inline-blocks", 0, 15), # uint, default = 5
    ("max-recurse-depth", 0, 4000),  # uint, default = 1000
    ("max-speculation-depth", 0, 30),  # uint, default = 10
    ("max-uses-for-sinking", 0, 90),  # uint, default = 30
    ("memdep-block-number-limit", 0, 3000), # uint, default = 1000
    ("memdep-block-scan-limit", 0, 300) # uint, default = 100
    
]
 
# one of these gvns is causing a segfault in opt
# 'gvn-hoist',
# 'gvn-sink',

# this causes opt to crash
# 'localizer',

# LLVM 6 (with asserts) crashes
#     'loop-interchange',
# here's the error:
'''
Assertion failed: (i < getNumSuccessors() && "Successor # out of range for Branch!"), function getSuccessor, file /Users/kavon/msr/tot-llvm/src/include/llvm/IR/Instructions.h, line 3057.
0  opt                      0x000000010e78bd48 llvm::sys::PrintStackTrace(llvm::raw_ostream&) + 40
1  opt                      0x000000010e78c446 SignalHandler(int) + 454
2  libsystem_platform.dylib 0x00007fff89ab552a _sigtramp + 26
3  opt                      0x000000010dbeb10c llvm::SimplifyCall(llvm::ImmutableCallSite, llvm::Value*, llvm::Use*, llvm::Use*, llvm::SimplifyQuery const&) + 812
4  libsystem_c.dylib        0x00007fff936546df abort + 129
5  libsystem_c.dylib        0x00007fff9361bdd8 basename + 0
6  opt                      0x000000010e5a2f69 (anonymous namespace)::LoopInterchange::runOnFunction(llvm::Function&) + 8857
7  opt                      0x000000010e1c70f3 llvm::FPPassManager::runOnFunction(llvm::Function&) + 547
8  opt                      0x000000010e1c7353 llvm::FPPassManager::runOnModule(llvm::Module&) + 51
9  opt                      0x000000010e1c789e llvm::legacy::PassManagerImpl::run(llvm::Module&) + 958
10 opt                      0x000000010d8ac896 main + 10230
11 libdyld.dylib            0x00007fff934d95ad start + 1
Stack dump:
0.	Program arguments: /Users/kavon/msr/tot-llvm/install/bin/opt -stats -stats-json -info-output-file ./programs/linpack/stats_2.json -disable-output -targetlibinfo -tti -tbaa -scoped-noalias -assumption-cache-tracker -profile-summary-info -forceattrs -inferattrs -mem2reg -lower-expect -sccp -reassociate -speculative-execution -ipsccp -domtree -prune-eh -sroa -postdomtree -slsr -globalopt -demanded-bits -barrier -memdep -simplifycfg -loop-sink -loops -loop-unswitch -loop-deletion -mldst-motion -block-freq -loop-accesses -instcombine -prune-eh -loop-distribute -slsr -speculative-execution -loop-sink -instcombine -memcpyopt -loop-vectorize -loop-unswitch -sccp -block-freq -prune-eh -float2int -elim-avail-extern -loop-interchange -loop-distribute -loop-reduce -branch-prob -lcssa-verification -lazy-branch-prob -jump-threading -lazy-value-info -globals-aa -argpromotion -lazy-value-info -ipsccp -loop-idiom -jump-threading -demanded-bits -lcssa -loop-idiom -ipsccp -tailcallelim -domtree -memdep -tailcallelim -aa -memdep -early-cse -ipsccp -ipsccp -basiccg -simplifycfg -block-freq -sroa -constmerge -loop-reduce -indvars -domtree -lcssa-verification -domtree -loop-simplify -loop-deletion -adce -functionattrs -instcombine -block-freq -demanded-bits -deadargelim -always-inline -deadargelim -loop-accesses -domtree -early-cse -inline -available-load-scan-limit=17 -bonus-inst-threshold=9 -early-ifcvt-limit=32 -jump-threading-implication-search-threshold=4 -licm-versioning-max-depth-threshold=1 -loop-interchange-threshold=2 -loop-unswitch-threshold=1838 -max-nested-scalar-reduction-interleave=5 -max-recurse-depth=2453 -max-speculation-depth=14 -max-uses-for-sinking=79 -memdep-block-scan-limit=275 -instcount ./programs/linpack/linpack.bc -o ./programs/linpack/linpack_2.bc 
1.	Running pass 'Function Pass Manager' on module './programs/linpack/linpack.bc'.
2.	Running pass 'Interchanges loops for cache reuse' on function '@main'
make: *** [optimize] Abort trap: 6
'''


### crashes llvm 6 (with asserts)
# 'loop-reduce'
# here's the error:
'''
0  opt                      0x0000000106614d48 llvm::sys::PrintStackTrace(llvm::raw_ostream&) + 40
1  opt                      0x0000000106615446 SignalHandler(int) + 454
2  libsystem_platform.dylib 0x00007fff89ab552a _sigtramp + 26
3  libsystem_malloc.dylib   0x00007fff9185e154 small_malloc_from_free_list + 1200
4  opt                      0x0000000105a5cf0a llvm::IVUsers::getExpr(llvm::IVStrideUse const&) const + 26
5  opt                      0x0000000106452973 (anonymous namespace)::LSRInstance::LSRInstance(llvm::Loop*, llvm::IVUsers&, llvm::ScalarEvolution&, llvm::DominatorTree&, llvm::LoopInfo&, llvm::TargetTransformInfo const&) + 14419
6  opt                      0x000000010644e185 ReduceLoopStrength(llvm::Loop*, llvm::IVUsers&, llvm::ScalarEvolution&, llvm::DominatorTree&, llvm::LoopInfo&, llvm::TargetTransformInfo const&) + 101
7  opt                      0x000000010647431a (anonymous namespace)::LoopStrengthReduce::runOnLoop(llvm::Loop*, llvm::LPPassManager&) + 554
8  opt                      0x0000000105ad8125 llvm::LPPassManager::runOnFunction(llvm::Function&) + 1189
9  opt                      0x00000001060500f3 llvm::FPPassManager::runOnFunction(llvm::Function&) + 547
10 opt                      0x0000000105a0ab80 (anonymous namespace)::CGPassManager::runOnModule(llvm::Module&) + 1552
11 opt                      0x000000010605089e llvm::legacy::PassManagerImpl::run(llvm::Module&) + 958
12 opt                      0x0000000105735896 main + 10230
13 libdyld.dylib            0x00007fff934d95ad start + 1
Stack dump:
0.	Program arguments: /Users/kavon/msr/tot-llvm/install/bin/opt -stats -stats-json -info-output-file ./programs/linpack/stats_19.json -disable-output -targetlibinfo -tti -tbaa -scoped-noalias -assumption-cache-tracker -profile-summary-info -forceattrs -inferattrs -mem2reg -lower-expect -memdep -memcpyopt -argpromotion -speculative-execution -loop-deletion -argpromotion -lazy-value-info -basiccg -basicaa -aa -loops -loop-unroll -slsr -elim-avail-extern -elim-avail-extern -demanded-bits -lazy-branch-prob -gvn -slp-vectorizer -constmerge -loop-sink -postdomtree -barrier -aa -adce -slsr -lazy-branch-prob -constmerge -inline -sroa -constmerge -adce -libcalls-shrinkwrap -slp-vectorizer -functionattrs -dse -functionattrs -postdomtree -deadargelim -functionattrs -loop-rotate -loop-accesses -loop-distribute -gvn -early-cse -lcssa -loop-idiom -alignment-from-assumptions -slsr -licm -block-freq -sccp -inline -functionattrs -globalopt -alignment-from-assumptions -loop-vectorize -basicaa -loop-vectorize -simplifycfg -constmerge -aa -speculative-execution -loop-reduce -deadargelim -always-inline -lcssa-verification -argpromotion -loop-simplify -loop-idiom -inline -loop-distribute -speculative-execution -loop-simplify -memdep -instsimplify -always-inline -slp-vectorizer -float2int -elim-avail-extern -loop-sink -speculative-execution -loop-distribute -prune-eh -argpromotion -inline -deadargelim -instsimplify -loop-accesses -always-inline -block-freq -domtree -basiccg -loop-reduce -loop-reduce -reassociate -loop-accesses -loop-sink -slp-vectorizer -gvn -argpromotion -lcssa -available-load-scan-limit=10 -bonus-inst-threshold=8 -jump-threading-threshold=17 -loop-interchange-threshold=-5 -max-dependences=212 -max-recurse-depth=2138 -max-speculation-depth=30 -instcount ./programs/linpack/linpack.bc -o ./programs/linpack/linpack_19.bc 
1.	Running pass 'CallGraph Pass Manager' on module './programs/linpack/linpack.bc'.
2.	Running pass 'Loop Pass Manager' on function '@_Z9r8mat_genii'
3.	Running pass 'Loop Strength Reduction' on basic block '%for.body4'
make: *** [optimize] Segmentation fault: 11
bash-3.2$ 
'''


# broken in LLVM 6 (with asserts) 'newgvn'
# output:
'''
Assertion failed: (BeforeCC->isEquivalentTo(AfterCC) && "Value number changed after main loop completed!"), function verifyIterationSettled, file /Users/kavon/msr/tot-llvm/src/lib/Transforms/Scalar/NewGVN.cpp, line 3285.
0  opt                      0x0000000105afad48 llvm::sys::PrintStackTrace(llvm::raw_ostream&) + 40
1  opt                      0x0000000105afb446 SignalHandler(int) + 454
2  libsystem_platform.dylib 0x00007fff89ab552a _sigtramp + 26
3  libsystem_platform.dylib 0x00007fff5aff3ad8 _sigtramp + 3511936456
4  libsystem_c.dylib        0x00007fff936546df abort + 129
5  libsystem_c.dylib        0x00007fff9361bdd8 basename + 0
6  opt                      0x00000001059905b7 (anonymous namespace)::NewGVN::runGVN() + 23335
7  opt                      0x0000000105992c99 (anonymous namespace)::NewGVNLegacyPass::runOnFunction(llvm::Function&) + 601
8  opt                      0x00000001055360f3 llvm::FPPassManager::runOnFunction(llvm::Function&) + 547
9  opt                      0x0000000105536353 llvm::FPPassManager::runOnModule(llvm::Module&) + 51
10 opt                      0x000000010553689e llvm::legacy::PassManagerImpl::run(llvm::Module&) + 958
11 opt                      0x0000000104c1b896 main + 10230
12 libdyld.dylib            0x00007fff934d95ad start + 1
13 libdyld.dylib            0x0000000000000086 start + 1823632090
Stack dump:
0.	Program arguments: /Users/kavon/msr/tot-llvm/install/bin/opt -stats -stats-json -info-output-file ./programs/linpack/stats_22.json -disable-output -targetlibinfo -tti -tbaa -scoped-noalias -assumption-cache-tracker -profile-summary-info -forceattrs -inferattrs -mem2reg -lower-expect -loop-vectorize -loops -barrier -loop-idiom -functionattrs -elim-avail-extern -branch-prob -argpromotion -lcssa-verification -loop-distribute -globals-aa -loop-vectorize -block-freq -scalar-evolution -globalopt -domtree -instcombine -domtree -loop-unswitch -aa -block-freq -mldst-motion -prune-eh -loop-unroll -memdep -elim-avail-extern -block-freq -basicaa -strip-dead-prototypes -constmerge -basicaa -loops -lcssa-verification -loop-rotate -bdce -float2int -lazy-value-info -prune-eh -float2int -early-cse -newgvn -basiccg -instcombine -block-freq -loops -dse -speculative-execution -domtree -tailcallelim -loop-rotate -functionattrs -memcpyopt -inline -functionattrs -loop-unswitch -loop-rotate -loop-vectorize -basiccg -scalar-evolution -licm -loop-sink -alignment-from-assumptions -instsimplify -instsimplify -ipsccp -tailcallelim -loop-distribute -lazy-block-freq -strip-dead-prototypes -elim-avail-extern -memcpyopt -bdce -globaldce -inline -constmerge -aa -mldst-motion -branch-prob -inline -scalar-evolution -loop-unswitch -early-cse -lcssa -ipsccp -memdep -deadargelim -newgvn -aa -loop-rotate -instcombine -globaldce -tailcallelim -correlated-propagation -demanded-bits -functionattrs -nary-reassociate -licm -simplifycfg -instsimplify -loop-rotate -loop-distribute -available-load-scan-limit=4 -bonus-inst-threshold=1 -early-ifcvt-limit=31 -jump-threading-implication-search-threshold=5 -licm-max-num-uses-traversed=24 -loop-load-elimination-scev-check-threshold=12 -loop-unswitch-threshold=1711 -max-dependences=300 -max-recurse-depth=1756 -max-speculation-depth=14 -max-uses-for-sinking=21 -memdep-block-number-limit=1779 -memdep-block-scan-limit=249 -instcount ./programs/linpack/linpack.bc -o ./programs/linpack/linpack_22.bc 
1.	Running pass 'Function Pass Manager' on module './programs/linpack/linpack.bc'.
2.	Running pass 'Global Value Numbering' on function '@_Z5dgeslPdiiPiS_i'
make: *** [optimize] Abort trap: 6

'''

# crashes in llvm6 (with asserts)
#   early-cse-memssa  (in default ordering!)
# my hunch was that it requires -memoryssa to be run before it, but that doesn't fix it.
'''
Assertion failed: (AnalysisPass && "Expected analysis pass to exist."), function setLastUser, file /Users/kavon/msr/tot-llvm/src/lib/IR/LegacyPassManager.cpp, line 523.
0  opt                      0x000000010f4a5d48 llvm::sys::PrintStackTrace(llvm::raw_ostream&) + 40
1  opt                      0x000000010f4a6446 SignalHandler(int) + 454
2  libsystem_platform.dylib 0x00007fff89ab552a _sigtramp + 26
3  libsystem_platform.dylib 0x00007fff638e05c8 _sigtramp + 3655512248
4  libsystem_c.dylib        0x00007fff936546df abort + 129
5  libsystem_c.dylib        0x00007fff9361bdd8 basename + 0
6  opt                      0x000000010eeda34a llvm::PMTopLevelManager::setLastUser(llvm::ArrayRef<llvm::Pass*>, llvm::Pass*) + 1786
7  opt                      0x000000010eedeac2 llvm::PMDataManager::add(llvm::Pass*, bool) + 722
8  opt                      0x000000010eedb644 llvm::PMTopLevelManager::schedulePass(llvm::Pass*) + 2724
9  opt                      0x000000010e5c608d main + 8173
10 libdyld.dylib            0x00007fff934d95ad start + 1
Stack dump:
0.	Program arguments: /Users/kavon/msr/tot-llvm/install/bin/opt -stats -stats-json -info-output-file ./programs/linpack/stats_256.json -disable-output -targetlibinfo -tti -tbaa -scoped-noalias -assumption-cache-tracker -profile-summary-info -forceattrs -inferattrs -mem2reg -lower-expect -memdep -inline -globaldce -functionattrs -block-freq -basicaa -alignment-from-assumptions -elim-avail-extern -loop-accesses -barrier -scalar-evolution -argpromotion -float2int -loop-distribute -loop-sink -loop-idiom -adce -gvn -functionattrs -lcssa -simplifycfg -sccp -functionattrs -loop-unroll -loops -memdep -aa -div-rem-pairs -basiccg -sccp -jump-threading -loop-idiom -jump-threading -early-cse-memssa -lazy-block-freq -lazy-value-info -early-cse-memssa -loop-vectorize -basicaa -bdce -lcssa-verification -loop-unroll -adce -sroa -instsimplify -loop-rotate -scalar-evolution -globals-aa -basiccg -basiccg -loop-idiom -argpromotion -basiccg -globalopt -branch-prob -aa -gvn -elim-avail-extern -sroa -prune-eh -always-inline -prune-eh -adce -lazy-block-freq -loop-sink -early-cse-memssa -indvars -loop-accesses -basiccg -sroa -licm -indvars -sroa -deadargelim -prune-eh -instsimplify -postdomtree -alignment-from-assumptions -slp-vectorizer -indvars -indvars -float2int -float2int -slsr -div-rem-pairs -instsimplify -simplifycfg -sroa -prune-eh -nary-reassociate -constmerge -scalar-evolution -inline -ipsccp -lazy-value-info -scalar-evolution -inline -block-freq -postdomtree -available-load-scan-limit=6 -early-ifcvt-limit=17 -inline-threshold=29884 -loop-distribute-scev-check-threshold=74 -loop-interchange-threshold=3 -loop-load-elimination-scev-check-threshold=21 -max-dependences=173 -max-num-inline-blocks=11 -max-speculation-depth=20 -max-uses-for-sinking=58 -memdep-block-number-limit=1803 -memdep-block-scan-limit=198 -instcount ./programs/linpack/linpack.bc -o ./programs/linpack/linpack_256.bc 
make: *** [optimize] Abort trap: 6
'''



# 'separate-const-offset-from-gep',
# 'simple-loop-unswitch',
    # structureizecfg breaks invokes in tsp-ga:
#     Block containing LandingPadInst must be jumped to only by the unwind edge of an invoke.
#   %300 = landingpad { i8*, i32 }
#           catch i8* null
# LLVM ERROR: Broken function found, compilation aborted!
    # 'structurizecfg',

# passes that are safe to run
ALL_PASSES = [
    'aa',
    'adce',
    'alignment-from-assumptions',
    'always-inline',
    'argpromotion',
    'barrier',
    'basicaa',
    'basiccg',
    'bdce',
    'block-freq',
    'branch-prob',
    'called-value-propagation',
    'callsite-splitting',
    'constmerge',
    'correlated-propagation',
    'deadargelim',
    'demanded-bits',
    'div-rem-pairs',
    'domtree',
    'dse',
    'early-cse',
    # 'early-cse-memssa',   # crashes LLVM 6, in default order.
    'elim-avail-extern',
    'float2int',
    'functionattrs',
    'globaldce',
    'globalopt',
    'globals-aa',
    'gvn',
    'indvars',
    'inline',
    'instcombine',
    'instsimplify',
    'ipsccp',
    'jump-threading',
    'lazy-block-freq',
    'lazy-branch-prob',
    'lazy-value-info',
    'lcssa',
    'lcssa-verification',
    'libcalls-shrinkwrap',
    'licm',
    'loop-accesses',
    'loop-deletion',
    'loop-distribute',
    'loop-idiom',
    # 'loop-interchange',   # CRASHES LLVM 6
    'loop-load-elim',
    # 'loop-reduce',        # CRASHES LLVM 6
    'loop-rotate',
    'loop-simplify',
    'loop-sink',
    'loop-unroll',
    'loop-unswitch',
    'loop-vectorize',
    'loops',
    'memcpyopt',
    'memdep',
    'memoryssa',
    'mldst-motion',
    'nary-reassociate',
    # 'newgvn',             # CRASHES LLVM 6
    # 'opt-remark-emitter',  # seems pointless
    # 'pgo-memop-opt',       # seems pointless
    'postdomtree',
    'prune-eh',
    'reassociate',
    # 'rpo-functionattrs',   # CRASHES LLVM 6, in default order right now!
    'scalar-evolution',
    'sccp',
    'simplifycfg',
    'slp-vectorizer',
    'slsr',
    'speculative-execution',
    'sroa',
    'strip-dead-prototypes',
    'tailcallelim'
]

# other interesting options
'''
- A textual description of the alias analysis pipeline for handling managed aliasing queries
    -aa-pipeline=<string>        
'''


# Help reduce the search space by pinning initial passes.
# must include initial dash
ALWAYS_FIRST = [
    '-targetlibinfo',
    '-tti',
    # '-targetpassconfig',
    '-tbaa',
    '-scoped-noalias',
    '-assumption-cache-tracker',
    '-profile-summary-info',
    '-forceattrs',
    '-inferattrs',
    '-mem2reg',
    '-lower-expect'
]

# TODO: this should appear first, and order matters in terms of who
# wins. BasicAA should break ties though, and should appear last?
ALIAS_QUERIES = [
    'tbaa',
    'scoped-noalias',
    'cfl-anders-aa',
    'cfl-steens-aa'
]

# TODO
ANALYSIS = [
    # 'basicaa -aa',
    # 'cfl-anders-aa -aa',
    # 'cfl-steens-aa -aa',
    
]
