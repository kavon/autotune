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
import sys
import argparse
import logging

import opt_data

log = logging.getLogger('llvmpasses')

argparser = argparse.ArgumentParser(parents=opentuner.argparsers())

argparser.add_argument("makefile", help="Path to the makefile to for tuning", type=str)

argparser.add_argument('--min-trials', type=int, default=2,
help='minimum number of times a compiled program is run.')

argparser.add_argument('--max-trials', type=int, default=20,
help='maxiumum number of times a compiled program is run.')

argparser.add_argument('--max-error', type=float, default=2.0,
help='maxiumum percentage of standard error for average program running time.')

# NOTE: you have to use one consistent clang/opt/llc build

# TODO: don't hardcode some of these
OPT_LVL = 'optonly'

def meetsError(samples, mean, MAX_ERR):
    sem = np.std(samples) / np.sqrt(len(samples))
    pct = (sem / mean) * 100.0
    return pct <= MAX_ERR

# input is a float in [0, 100] representing a precentage
def update_progress(progress):
    barLen = 20
    div = 100 / barLen
    sys.stdout.write('\r[{0: <{barLen}}] {1:.2f}% complete'.format('#'*(int(progress/div)), progress, barLen=barLen))
    sys.stdout.flush()


class OptFlagsTuner(MeasurementInterface):
    
  def __init__(self, *pargs, **kwargs):
    super(OptFlagsTuner, self).__init__(program_name="program_name", *pargs,
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
    self.make("clean")
    print "Building initial bitcode ..."
    self.make("bitcode")
    print "done!"
    

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
    
    build_res = None
    opt_res = None
    try:
        # optimize
        opt_res = self.make("optimize", ID=id, PASSES=passes)
        
        if not self.optOnly:
            # build executable
            build_res = self.make("link", ID=id)
        
    except Exception as inst:
        print "---------------------------------------------"
        print inst
        # ensure we made it all the way through
        if opt_res == None:
            print "died during OPTIMIZE... trying to reduce the pass configuration."
            self.auto_reduce(passes, id, "optimize")
            assert False, "done."
            
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
    stats_res = self.make("opt_stats", ID=id)
    stats_out = stats_res['stdout']
    
    # apply the objective function
    compile_time = compile_result['time']
    total_time = self.objectiveFun(compile_time, avg_runtime, stats_out)
    
    # clean up everything
    self.make("selfclean", ID=id)
    
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
            self.args.makefile, OPT_LVL, self.build_options(configuration.data))
    print msg
    self.make("clean")
    
  def auto_reduce(self, passStr, id, target):
      print "Auto-reduce Starting..."
      
      originalPasses = passStr.split(' ')
      passes = originalPasses[:]
      idx = 0
      while idx < len(passes):
          
          print ("\n Update for ID = " + str(id))
          update_progress(100.0 * (float(idx + 1) / len(passes)))
          print "\n\n"
          
          # take a pass out and see if it crashes
          excluded = passes.pop(idx)
          
          res = None
          try:
              asStr = ' '.join(passes)
              res = self.make("optimize", ID=id, PASSES=asStr, suppressFailure=False)
              assert res != None
          except:
              ###
              # it still fails without this pass, so its irrelevant.
              # leave it off and keep going.
              continue
              
          ### 
          # it no longer fails when we take the pass out, so this pass is part of the problem. 
          # we put it back in the sequence and continue trying to look for
          # irrelevant passes.
          passes.insert(idx, excluded)
          idx += 1
      
      if passes == originalPasses:
          print "\nI was unable to reduce the pass sequence any further..."
      
      print "\nHere is the smallest failure case I've found:"
      asStr = ' '.join(passes)
      self.make("optimize", ID=id, PASSES=asStr, suppressFailure=False)
    
  
  def get_runtime(self, id):
      '''
      Runs the program until a good average running time is found.
      '''
      run_times = []
      avg_runtime = None
      run_res = None
      
      min_trials = self.args.min_trials
      max_trials = self.args.max_trials
      assert min_trials > 1, "bogus mininum"
      assert min_trials < max_trials, "bogus number of trials"
      
      for trial in xrange(max_trials):
          try:
              run_res = self.make("run", ID=id)
          except Exception as inst:
              print "---------------------------------------------"
              print inst
              print "Crashed while running output program! ID = " + str(id)
              assert False, "compiler has output a broken program!"
          
          
          time = run_res['time']
          run_times.append(time)
          mean = np.mean(run_times)
          if (trial >= (min_trials-1) 
               and meetsError(run_times, mean, self.args.max_error)):
              # accept this mean
              avg_runtime = mean
              break
          
      if avg_runtime is None:
          print "warning: running time data is noisy!"
          avg_runtime = np.mean(run_times)
          
      return (avg_runtime, run_res)

  
  def make(self, target, ID=None, PASSES=None, suppressFailure=False):
    makefile = self.args.makefile
    cmd = ''

    if ID:
        cmd += 'ID={0} '.format(ID)

    if PASSES:
      cmd += 'PASSES=\"{0}\" '.format(PASSES)

    cmd += 'make -f {0} {1}'.format(makefile, target)

    result = self.call_program(cmd)
    if result['returncode'] != 0 and not suppressFailure:
        print ("autotune error executing: \n" + cmd)
        assert False, "make command returned non-zero exit code!!"
        
    return result


if __name__ == '__main__':
  opentuner.init_logging()
  args = argparser.parse_args()
  OptFlagsTuner.main(args)
