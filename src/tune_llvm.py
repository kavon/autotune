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

import numpy as np

import opt_data

# NOTE: you have to use one consistent clang/opt/llc build

# TODO: don't hardcode some of these
OPT_LVL = 'optonly'
PROG = 'linpack'
MAKEFILE = './programs/' + PROG + '/tune.mk'
MIN_TRIALS = 2
MAX_TRIALS = 50
MAX_ERR = 2.0  # provide a precentage. 1.2% = 1.2

def meetsError(samples, mean):
    sem = np.std(samples) / np.sqrt(len(samples))
    pct = (sem / mean) * 100.0
    return pct <= MAX_ERR


class OptFlagsTuner(MeasurementInterface):
    
  def __init__(self, *pargs, **kwargs):
    super(OptFlagsTuner, self).__init__(program_name=PROG, *pargs,
                                        **kwargs)
    self.parallel_compile = True
    
    problem_setup = opt_data.genOptLevels()[OPT_LVL]
    
    self.optOnly = False
    if opt_data.OPT_ONLY_K in problem_setup:
        self.optOnly = True
    
    self.objectiveFun = problem_setup[opt_data.OBJ_FUN_K]
    self.passes = problem_setup[opt_data.ALL_PASSES_K]
    self.max_passes = problem_setup[opt_data.MAX_PASSES_K]
    self.knobs = problem_setup[opt_data.ALL_KNOBS_K]
    
    # build bitcode file
    self.make(MAKEFILE, "clean")
    self.make(MAKEFILE, "bitcode")
    

  def manipulator(self):
    """
    Define the search space by creating a
    ConfigurationManipulator
    """
    manipulator = ConfigurationManipulator()
    
    num_options = len(self.passes)-1
    
    # choose for a sequence of at most `max_passes` passes
    for i in range(self.max_passes):
        passNum = 'pass_' + str(i)
        # some pass
        manipulator.add_parameter(IntegerParameter(passNum, 0, num_options))
        # and whether to turn it on or off
        manipulator.add_parameter(EnumParameter('enable_' + passNum, [True, False]))
        
    # choose from a set of knobs
    for knob, minInt, maxInt in self.knobs:
        manipulator.add_parameter(IntegerParameter(knob, minInt, maxInt))
        manipulator.add_parameter(EnumParameter('enable_' + knob, [True, False]))
    
    return manipulator

  def build_options(self, cfg):
    passes = ''
    
    if self.optOnly:
        passes = '-disable-output '
        
    passes += ' '.join(opt_data.ALWAYS_FIRST)
    
    for i in range(self.max_passes):
        passKey = 'pass_' + str(i)
        enableKey = 'enable_' + passKey
        enabled = cfg[enableKey]
        if enabled:
            num = cfg[passKey]
            chosen = self.passes[num]
            passes += ' -{0}'.format(chosen)
            
    for i in range(len(self.knobs)):
        knob = self.knobs[i][0]
        enableKnob = 'enable_' + knob
        enabled = cfg[enableKnob]
        if enabled:
            val = cfg[knob]
            passes += ' -{0}={1}'.format(knob, val)
    
    return passes


  def compile(self, cfg, id):
    """
    Compile a given configuration in parallel
    """
    
    passes = self.build_options(cfg)
    passes = "\"" + passes + "\""
    
    build_res = None
    opt_res = None
    try:
        # optimize
        opt_res = self.make(MAKEFILE, "optimize", ID=id, PASSES=passes)
        
        if not self.optOnly:
            # build executable
            build_res = self.make(MAKEFILE, "link", ID=id)
        
    except Exception as inst:
        print "---------------------------------------------"
        print inst
        # ensure we made it all the way through
        print ("\n\nCrash while compiling this config:\nID =  " + str(id) + "\npasses = " + passes + "\n") 
        assert opt_res != None, "died during OPTIMIZE"
        assert build_res != None, "died during LINK"
        assert False, "Something else went wrong!!"
        
    # we only care about optimization time
    return opt_res

  
  def run_precompiled(self, desired_result, input, limit, compile_result, id):
    '''
    the compile_result is what is returned by compile.
    this function is run seqentially with respect to itself.
    This is needed because the runtime variance is so high when run in
    parallel that it throws the search off.
    '''
    
    # run and compute an average
    avg_runtime = 0.0
    
    if not self.optOnly:
        run_time, _ = self.get_runtime(id)
        avg_runtime = run_time
    
    # grab the optimization stats
    stats_res = self.make(MAKEFILE, "opt_stats", ID=id)
    stats_out = stats_res['stdout']
    
    # apply the objective function
    compile_time = compile_result['time']
    total_time = self.objectiveFun(compile_time, avg_runtime, stats_out)
    
    # clean up everything
    self.make(MAKEFILE, "selfclean", ID=id)
    
    return Result(time=total_time)

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
            PROG, OPT_LVL, self.build_options(configuration.data))
    print msg
    self.make(MAKEFILE, "clean")
    
  
  def get_runtime(self, id):
      '''
      Runs the program until a good average running time is found.
      '''
      run_times = []
      avg_runtime = None
      run_res = None
      
      assert MIN_TRIALS > 1, "bogus mininum"
      assert MIN_TRIALS < MAX_TRIALS, "bogus number of trials"
      
      for trial in xrange(MAX_TRIALS):
          try:
              run_res = self.make(MAKEFILE, "run", ID=id)
          except Exception as inst:
              print "---------------------------------------------"
              print inst
              print "Crashed while running output program! ID = " + str(id)
              assert False, "compiler has output a broken program!"
          
          
          time = run_res['time']
          run_times.append(time)
          mean = np.mean(run_times)
          if trial >= (MIN_TRIALS-1) and meetsError(run_times, mean):
              # accept this mean
              avg_runtime = mean
              break
          
      if avg_runtime is None:
          print "warning: running time data is noisy!"
          avg_runtime = np.mean(run_times)
          
      return (avg_runtime, run_res)

  
  def make(self, makefile, target, ID=None, PASSES=None):
    cmd = ''

    if ID:
        cmd += 'ID={0} '.format(ID)

    if PASSES:
      cmd += 'PASSES={0} '.format(PASSES)

    cmd += 'make -f {0} {1}'.format(makefile, target)

    result = self.call_program(cmd)
    if result['returncode'] != 0:
        print ("autotune error executing: \n" + cmd)
        assert False, "make command returned non-zero exit code!!"
        
    return result


if __name__ == '__main__':
  argparser = opentuner.default_argparser()
  OptFlagsTuner.main(argparser.parse_args())
