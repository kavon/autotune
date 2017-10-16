#!/usr/bin/env python
#
# Autotune opt passes.
#

import opentuner
from opentuner import ConfigurationManipulator
from opentuner import EnumParameter
from opentuner import IntegerParameter
from opentuner import MeasurementInterface
from opentuner import Result
from opentuner.search.manipulator import (ConfigurationManipulator,
                                          PermutationParameter)
from opentuner.search.objective import SearchObjective

import opt_data

# have to use one consistent clang/opt/llc build
PATH = '/Users/kavon/msr/llvm5/bin/'
DEBUG = False
OPT_LVL = '-O3'
PROG = 'linpack'
TRIALS = 3

# use -Xclang -disable-O0-optnone on clang to prevent it from adding optnone to everything.


class OptFlagsTuner(MeasurementInterface):
    
  def __init__(self, *pargs, **kwargs):
    super(OptFlagsTuner, self).__init__(program_name=PROG, *pargs,
                                        **kwargs)
    self.parallel_compile = True
    
    problem_setup = opt_data.genOptLevels()[OPT_LVL]
    
    self.objectiveFun = problem_setup[0]
    self.passes = problem_setup[1]
    self.max_passes = problem_setup[2]
    

  def manipulator(self):
    """
    Define the search space by creating a
    ConfigurationManipulator
    """
    manipulator = ConfigurationManipulator()
    
    num_options = len(self.passes)-1
    
    # choose for a sequence of at most max_passes passes
    for i in range(self.max_passes):
        # choose any pass you would like, or -1 for nothing
        manipulator.add_parameter(IntegerParameter(i, -1, num_options))
    
    return manipulator

  def build_passes(self, cfg):
    passes = ' '.join(opt_data.ALWAYS_FIRST)
    
    for i in range(self.max_passes):
        num = cfg[i]
        if num != -1:
            chosen = self.passes[num]
            passes += ' -{0}'.format(chosen)
    
    return passes


  def compile(self, cfg, id):
    """
    Compile a given configuration in parallel
    """
    
    passes = self.build_passes(cfg)
    
    opt_outfile = './out/' + PROG + '_opt{0}.bc'.format(id)
    bin_outfile = './out/tmp{0}.bin'.format(id)
    
    build_res = None
    opt_res = None
    run_res = None
    opt_cmd = '(no opt cmd)'
    build_cmd = '(no build cmd)'
    avg_runtime = 0.0
    try:
        # optimize
        opt_cmd = (PATH + 'opt ' + passes + ' ./src/apps/' + PROG + '.bc -o '
                + opt_outfile)
        if DEBUG:
            print opt_cmd, '\n'
        opt_res = self.call_program(opt_cmd)
        assert opt_res['returncode'] == 0
        
        # build executable
        build_cmd = (PATH + 'clang++ ' + opt_outfile + ' -o ' + bin_outfile)
        build_res = self.call_program(build_cmd)
        assert build_res['returncode'] == 0
        
        # run and compute an average
        for _ in xrange(TRIALS):
            run_res = self.call_program(bin_outfile)
            assert run_res['returncode'] == 0
            avg_runtime += run_res['time']
        
        avg_runtime = avg_runtime / float(TRIALS)
    
    except:
        # ensure we made it all the way through
        print ("\n\nCRASHED IN THE FOLLOWING CONFIG:\nopt command: " + opt_cmd + "\nbuild command: " + build_cmd) 
        assert opt_res != None
        assert build_res != None
        assert run_res != None
        assert False, "Something went wrong!"
        
    finally:
        self.call_program('rm -f ' + opt_outfile + ' ' + bin_outfile)
    
    
    
    # apply the objective function
    compile_time = opt_res['time']
    total_time = self.objectiveFun(compile_time, avg_runtime)

    run_res['time'] = total_time
    
    return run_res

  
  def run_precompiled(self, desired_result, input, limit, compile_result, id):
    '''
    the compile_result is what is returned by compile
    '''
    
    return Result(time=compile_result['time'])

  def compile_and_run(self, desired_result, input, limit):
    """
    Compile and run a given configuration then
    return performance
    """
    cfg = desired_result.configuration.data
    compile_result = self.compile(cfg, 0)
    return self.run_precompiled(desired_result, input, limit, compile_result, 0)
    
    
  def save_final_config(self, configuration):
    """called at the end of tuning"""
    # outfile = 'passes_final.json'
    # print "Optimal passes written to " + outfile + ":", configuration.data
    # self.manipulator().save_to_file(configuration.data, outfile)
    msg = "Tuned on program {0}, with priority {1}. \nBest pass ordering found:\n{2}".format(
            PROG, OPT_LVL, self.build_passes(configuration.data))
    print msg
    


if __name__ == '__main__':
  argparser = opentuner.default_argparser()
  OptFlagsTuner.main(argparser.parse_args())
