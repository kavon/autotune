

# Returns the main structure of all optimization levels
def genOptLevels():
    opt_levels = {}
    
    phase_structure1 = [
                            ('simp1', SIMPLIFY),
                            ('simp2', SIMPLIFY),
                            ('expand1', EXPAND),
                            ('expand2', EXPAND)
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


def genCombineTimes(compileW, runtimeW):
    # we use De Jong's spherical function as our objective function, with a tweak
    # to support weighting. Higher weight means that dimension is more important to
    # minimize.
    def combineTimes(compT, runT):
        return ((compileW * (compT ** 2))
                + (runtimeW * (runT ** 2)))
    
    return combineTimes


# pass groups

SIMPLIFY = [
    'instcombine',
    'dse',
    'simplifycfg',
    'early-cse',
    'latesimplifycfg'
]

EXPAND = [
    'inline',
    'loops -loop-simplify -lcssa-verification -lcssa -scalar-evolution -loop-unroll -instcombine -loop-simplify -lcssa-verification -lcssa -scalar-evolution -licm'
]

MISC = [
    'tailcallelim',
    'jump-threading',
    'sroa',
    'sink',
    'bdce',
    'early-cse-memssa',
    'adce',
    'gvn',
    'ipconstprop',
    'globaldce',
    'instsimplify',
    'reassociate',
    'correlated-propagation',
    'memcpyopt',
    'branch-prob',
    'block-freq',
    'loop-sink'
]


# Help reduce the search space by pinning passes

ALWAYS_FIRST = [
    # '-targetlibinfo',
    # '-tti',
    # '-targetpassconfig',
    # '-tbaa',
    # '-scoped-noalias',
    # '-assumption-cache-tracker',
    # '-profile-summary-info',
    '-forceattrs',
    '-inferattrs',
    '-mem2reg'
]
