
OBJ_FUN_K = 'objfun'
ALL_PASSES_K = 'allpasses'
MAX_PASSES_K = 'maxpasses'
ALL_KNOBS_K = 'allknobs'

# Returns the main structure of all optimization levels
def genOptLevels():
    opt_levels = {}
    
    ## TODO: make a dict
    
    opt_levels['-O0'] = {
                        OBJ_FUN_K : genCombineTimes(2, 1),     # objective function
                        ALL_PASSES_K : ALL_PASSES,             # optimization passes
                        MAX_PASSES_K : 150,                    # max passes
                        ALL_KNOBS_K : ALL_KNOBS
                        }
                        
    opt_levels['-O1'] = {
                        OBJ_FUN_K : genCombineTimes(1, 2),
                        ALL_PASSES_K : ALL_PASSES,
                        MAX_PASSES_K : 150,
                        ALL_KNOBS_K : ALL_KNOBS
                        }
                        
                        
    opt_levels['-O2'] = {
                        OBJ_FUN_K : genCombineTimes(1, 7),
                        ALL_PASSES_K : ALL_PASSES,
                        MAX_PASSES_K : 150,
                        ALL_KNOBS_K : ALL_KNOBS
                        }
                        
                        
    opt_levels['-O3'] = {
                        OBJ_FUN_K : genCombineTimes(0, 10),
                        ALL_PASSES_K : ALL_PASSES,
                        MAX_PASSES_K : 150,
                        ALL_KNOBS_K : ALL_KNOBS
                        }
                        
    return opt_levels


def genCombineTimes(compileW, runtimeW, kind='sphere'):
    # Higher weight means that dimension is more important to minimize.
    
    def adjust(num):
        return round(num, 3) + 1.0
    
    # De Jong's spherical objective function, with tweaks.
    def spherical(compT, runT):
        compT = adjust(compT)
        runT = adjust(runT)
        return ((compileW * (compT ** 2))
                + (runtimeW * (runT ** 2)))
    
    def linear(compT, runT):
        compT = adjust(compT)
        runT = adjust(runT)
        return ((compileW * compT)
                + (runtimeW * runT))
                
    def runOnly(_, runT):
        runT += 1.0
        return (runT ** 2)
    
    switch = {
        'sphere' : spherical,
        'linear' : linear,
        'runOnly' : runOnly
    }
    
    assert kind in switch, "wrong objective function kind"
    
    return switch[kind]
    
    
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

# crashes
# 'loop-interchange',

# 'loop-reduce'
# 'nary-reassociate',
# 'newgvn',
# 'separate-const-offset-from-gep',
# 'simple-loop-unswitch',
# 'slsr',
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
    'constmerge',
    'correlated-propagation',
    'deadargelim',
    'demanded-bits',
    'domtree',
    'dse',
    'early-cse',
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
    # 'latesimplifycfg',   # doesn't exist in LLVM 6
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
    'loop-load-elim',
    'loop-rotate',
    'loop-simplify',
    'loop-sink',
    'loop-unroll',
    'loop-unswitch',
    'loop-vectorize',
    'loops',
    'memcpyopt',
    'memdep',
    'mldst-motion',
    # 'opt-remark-emitter',
    # 'pgo-memop-opt',
    'postdomtree',
    'prune-eh',
    'reassociate',
    'rpo-functionattrs',
    'scalar-evolution',
    'sccp',
    'simplifycfg',
    'slp-vectorizer',
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
