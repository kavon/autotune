
# all passes that help simplify/shrink the program in some way
SIMPLIFY = [
    'instcombine',
    'dse',
    'simplifycfg'
]

FOLD = [
    'instcombine'
]

EXPAND = [
    'inline'
]

MISC = [
    'mem2reg',
    'tailcallelim',
    'jump-threading',
    'inferattrs',
    'sroa',
    'lcssa',
    'sink',
    'bdce',
    'early-cse-memssa',
    'adce',
    'gvn',
    'ipconstprop',
    'globaldce',
    'instsimplify',
    'reassociate'
]










# these are individial transform/analysis passes that opt can run.
# order matters, and you can run any of these more than once.
# example:
# opt -mem2reg -instsimplify -lcssa -licm -loop-sink -instcombine

# for now, a very conservative list because some of the below cause opt to crash
# OPT_PASSES = [
# 'mem2reg',
# 'instsimplify',
# 'early-cse',
# 'gvn',
# 'simplifycfg',
# 'inline',
# 'instcombine',
# 'sink',
# 'jump-threading',
# 'sroa',
# 'adce'
# ]


OPT_PASSES = [
'mem2reg',
    # 'mergereturn',
'instsimplify',
'instsimplify',
'instsimplify',
'instsimplify',
'instcombine',
'instcombine',
'instcombine',
'instcombine',
'instcombine',
'instcombine',
    # 'unreachableblockelim',
    # 'localizer',
'gvn',
'gvn',
    # 'newgvn',
    # 'gvn-hoist',
    # 'gvn-sink',
    # 'flattencfg',
# 'loop-simplify',
'lcssa',
    # 'irce',
# 'indvars',
'jump-threading',
# 'licm',
# 'loop-sink',
    # 'loop-data-prefetch',
# 'loop-deletion',
    # 'loop-accesses',
    # 'loop-instsimplify',
# 'loop-interchange',
    # 'loop-predication',
# 'loop-rotate',
    # 'loop-reduce',
    # 'loop-reroll',
# 'loop-unroll',
# 'loop-unswitch',
# 'loop-idiom',
    # 'lower-expect',
'memcpyopt',
'mldst-motion',
    # 'nary-reassociate',
'reassociate',
'sccp',
'ipsccp',
'sroa',
'simplifycfg',
'simplifycfg',
'simplifycfg',
# 'latesimplifycfg',
# 'lowerswitch',
# 'structurizecfg',
# 'simple-loop-unswitch',
'sink',
# 'tailcallelim',
# 'separate-const-offset-from-gep',
# 'speculative-execution',
# 'slsr',
# 'load-combine',
# 'loop-distribute',
# 'loop-load-elim',
# 'loop-simplifycfg',
# 'loop-versioning',
# 'loop-vectorize',
'slp-vectorizer',
# 'load-store-vectorizer',
'globaldce',
'globalopt',
'ipconstprop',
'inline',
'inline',
'inline',
'inferattrs',
# 'loop-extract',
# 'mergefunc',
# 'partial-inliner',
# 'functionattrs',
# 'bb-vectorize',
# 'early-cse',
'early-cse-memssa',
'early-cse-memssa',
'constmerge',
'deadargelim',
# 'basicaa',
# 'cfl-anders-aa',
# 'cfl-steens-aa',
# 'basiccg',
# 'da',
'adce',
'demanded-bits',
'demanded-bits',
'bdce',
# 'branch-prob',
# 'block-freq',
# 'divergence',
# 'consthoist',
# 'constprop',
'correlated-propagation',
# 'dce',
# 'die',
# 'delinearize',
'dse'
# 'codegenprepare'
]


'''
from O3
-targetlibinfo -tti -tbaa -scoped-noalias -assumption-cache-tracker -profile-summary-info -forceattrs -inferattrs -ipsccp -globalopt -domtree -mem2reg -deadargelim -domtree -basicaa -aa -instcombine -simplifycfg -basiccg -globals-aa -prune-eh -inline -functionattrs -argpromotion -domtree -sroa -basicaa -aa -memoryssa -early-cse-memssa -speculative-execution -domtree -basicaa -aa -lazy-value-info -jump-threading -lazy-value-info -correlated-propagation -simplifycfg -domtree -basicaa -aa -instcombine -libcalls-shrinkwrap -loops -branch-prob -block-freq -pgo-memop-opt -domtree -basicaa -aa -tailcallelim -simplifycfg -reassociate -domtree -loops -loop-simplify -lcssa-verification -lcssa -basicaa -aa -scalar-evolution -loop-rotate -licm -loop-unswitch -simplifycfg -domtree -basicaa -aa -instcombine -loops -loop-simplify -lcssa-verification -lcssa -scalar-evolution -indvars -loop-idiom -loop-deletion -loop-unroll -mldst-motion -aa -memdep -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -gvn -basicaa -aa -memdep -memcpyopt -sccp -domtree -demanded-bits -bdce -basicaa -aa -instcombine -lazy-value-info -jump-threading -lazy-value-info -correlated-propagation -domtree -basicaa -aa -memdep -dse -loops -loop-simplify -lcssa-verification -lcssa -aa -scalar-evolution -licm -postdomtree -adce -simplifycfg -domtree -basicaa -aa -instcombine -barrier -elim-avail-extern -basiccg -rpo-functionattrs -globals-aa -float2int -domtree -loops -loop-simplify -lcssa-verification -lcssa -basicaa -aa -scalar-evolution -loop-rotate -loop-accesses -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -loop-distribute -branch-prob -block-freq -scalar-evolution -basicaa -aa -loop-accesses -demanded-bits -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -loop-vectorize -loop-simplify -scalar-evolution -aa -loop-accesses -loop-load-elim -basicaa -aa -instcombine -scalar-evolution -demanded-bits -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -slp-vectorizer -latesimplifycfg -domtree -basicaa -aa -instcombine -loops -loop-simplify -lcssa-verification -lcssa -scalar-evolution -loop-unroll -instcombine -loop-simplify -lcssa-verification -lcssa -scalar-evolution -licm -alignment-from-assumptions -strip-dead-prototypes -globaldce -constmerge -domtree -loops -branch-prob -block-freq -loop-simplify -lcssa-verification -lcssa -basicaa -aa -scalar-evolution -branch-prob -block-freq -loop-sink -lazy-branch-prob -lazy-block-freq -opt-remark-emitter -instsimplify -simplifycfg -verify
'''
