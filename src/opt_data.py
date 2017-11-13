
import json

OBJ_FUN_K = 'objfun'
ALL_PASSES_K = 'allpasses'
MAX_PASSES_K = 'maxpasses'
ALL_KNOBS_K = 'allknobs'
OPT_ONLY_K = 'optonly'

# Returns the main structure of all optimization levels
def genOptLevels():
    opt_levels = {}
    
    ## TODO: make a dict
    
    opt_levels['-O0'] = {
                        OBJ_FUN_K : genCombineTimes(2, 1),     # objective function
                        ALL_PASSES_K : ALL_PASSES,             # optimization passes
                        MAX_PASSES_K : 150,                    # max passes
                        ALL_KNOBS_K : ALL_KNOBS                # knobs
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
                        
    opt_levels['optonly'] = {
                        OBJ_FUN_K : analyzeOptStats,
                        ALL_PASSES_K : ALL_PASSES,
                        MAX_PASSES_K : 150,
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
        ("instcount.TotalInsts", -1),
        ("instcount.TotalFuncs", -100),
        ("instcount.NumStoreInst", -10),
        ("instcount.NumLoadInst", -20),
        ("early-cse.NumSimplify", 2),
        ("early-cse.", 3),
        ("instcombine.", 2),
        ("inline.NumInlined", 100),
        ("inline.NumCallsDeleted", 100),
        ("instsimplify.", 2),
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
    # 'rpo-functionattrs',   # has a bug in LLVM 6
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
