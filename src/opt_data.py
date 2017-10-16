

# Returns the main structure of all optimization levels
def genOptLevels():
    opt_levels = {}
    
    phase_structure1 = [
                            ('simp1', SIMPLIFY),
                            ('simp2', SIMPLIFY),
                            ('simp3', SIMPLIFY),
                            ('expand1', EXPAND),
                            ('expand2', EXPAND),
                            ('expand3', EXPAND),
                            ('anal1', ANALYSIS),
                            ('anal2', ANALYSIS),
                            ('anal3', ANALYSIS)
                       ]
    
    opt_levels['-O0'] = (genCombineTimes(2, 1),     # objective function
                         phase_structure1,          # loose phase structure
                         MISC                       # individual passes that can be interleaved between phases
                        )
                        
    opt_levels['-O1'] = (genCombineTimes(1, 3),
                         phase_structure1,
                         MISC
                        )
                        
    opt_levels['-O2'] = (genCombineTimes(1, 7),
                         phase_structure1,
                         MISC
                        )
                        
    opt_levels['-O3'] = (genCombineTimes(1, 10),
                         phase_structure1,
                         MISC
                        )
    return opt_levels


def genCombineTimes(compileW, runtimeW, kind='sphere'):
    # Higher weight means that dimension is more important to minimize.
    
    # De Jong's spherical objective function, with tweaks.
    def spherical(compT, runT):
        compT += 1.0
        runT += 1.0
        return ((compileW * (compT ** 2))
                + (runtimeW * (runT ** 2)))
    
    def linear(compT, runT):
        compT += 1.0
        runT += 1.0
        return ((compileW * compT)
                + (runtimeW * runT))
    
    switch = {
        'sphere' : spherical,
        'linear' : linear
    }
    
    assert kind in switch, "wrong objective function kind"
    
    return switch[kind]
    
    


# pass groups

SIMPLIFY = [
    'instcombine',
    'simplifycfg',
    'early-cse'
]

EXPAND = [
    'basiccg -inline',
    # a sequence that tries to unroll loops
    'loops -loop-simplify -lcssa -scalar-evolution -loop-unroll'
]

# passes that are commented out below were suspected of causing opt to crash.
MISC = [
    'adce',
    'bdce',
    'constmerge',
    'constprop',
    'correlated-propagation',
    'deadargelim',
    'die',
    'dse',
    # 'early-cse-memssa',
    'elim-avail-extern',
    'float2int',
    'strip-dead-prototypes -globaldce',
    'globalopt',
    
    # one of these gvns is causing a segfault in opt
    # 'gvn-hoist',
    # 'gvn-sink',
    
    'gvn',
    'instsimplify',
    'ipsccp',
    'ipconstprop',
    'jump-threading',
    'latesimplifycfg',
    'lcssa',
    'libcalls-shrinkwrap',
    'licm',
    'load-store-vectorizer',
    
    # this causes opt to crash
    # 'localizer',
    
    'loop-accesses',
    'loop-deletion',
    'loop-distribute',
    'loop-idiom',
    
    # crashes
    # 'loop-interchange',
    
    'loop-load-elim',
    # 'loop-reduce',
    'loop-rotate',
    'loop-simplify',
    'loop-sink',
    'loop-vectorize',
    'loop-unswitch',
    'memcpyopt',
    'mergefunc',
    'mergereturn',
    'mldst-motion',
    # 'nary-reassociate',
    # 'newgvn',
    'partial-inliner',
    'partially-inline-libcalls',
    'prune-eh',
    'reassociate',
    'rpo-functionattrs',
    'sccp',
    # 'separate-const-offset-from-gep',
    # 'simple-loop-unswitch',
    'sink',
    'slp-vectorizer',
    # 'slsr',
    'speculative-execution',
    'sroa',
    
    # structureizecfg breaks invokes in tsp-ga:
#     Block containing LandingPadInst must be jumped to only by the unwind edge of an invoke.
#   %300 = landingpad { i8*, i32 }
#           catch i8* null
# LLVM ERROR: Broken function found, compilation aborted!
    # 'structurizecfg',
    
    'tailcallelim'
]

# other interesting options
'''
- A textual description of the alias analysis pipeline for handling managed aliasing queries
    -aa-pipeline=<string>        
'''


# Help reduce the search space by pinning passes
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


ANALYSIS = [
    'basicaa -aa',
    # 'cfl-anders-aa -aa',
    # 'cfl-steens-aa -aa',
    'domtree',
    'postdomtree',
    'memdep',
    'indvars',
    'loop-accesses',
    'demanded-bits',
    'block-freq',
    'branch-prob',
    'lazy-value-info',
    'lazy-branch-prob',
    'lazy-value-info',
    'loops -loop-simplify -lcssa -scalar-evolution'
]
