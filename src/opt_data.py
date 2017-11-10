

# Returns the main structure of all optimization levels
def genOptLevels():
    opt_levels = {}
    
    opt_levels['-O0'] = (genCombineTimes(2, 1),     # objective function
                         ALL_PASSES,                # passes to be considered
                         150                        # max passes applied to prog
                        )
                        
    opt_levels['-O1'] = (genCombineTimes(1, 2),
                         ALL_PASSES,
                         150
                        )
                        
    opt_levels['-O2'] = (genCombineTimes(1, 7),
                         ALL_PASSES,
                         150
                        )
                        
    opt_levels['-O3'] = (genCombineTimes(0, 10),
                         ALL_PASSES,
                         150
                        )
    return opt_levels


def genCombineTimes(compileW, runtimeW, kind='sphere'):
    # Higher weight means that dimension is more important to minimize.
    
    def adjust(num):
        return round(num, 2) + 1.0
    
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
    'latesimplifycfg',
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
